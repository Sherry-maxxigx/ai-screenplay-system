import json
import re
from difflib import SequenceMatcher
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.api.ai import enforce_script_labels, generate_clean_content
from app.core.narrative_engine import NarrativeGenerator
from app.models.neo4j_db import neo4j_client

router = APIRouter()
narrative_gen = NarrativeGenerator()

ENDING_KEYWORDS = [
    "结局",
    "结尾",
    "尾声",
    "余韵",
    "真相",
    "揭晓",
    "落幕",
    "收束",
    "结束",
    "终于",
    "最后",
    "清晨",
    "天亮",
    "告别",
    "代价",
    "选择",
]

FORESHADOW_KEYWORDS = [
    "怀表",
    "录音",
    "旧照片",
    "坐标",
    "钥匙",
    "求救信号",
    "日志",
    "芯片",
    "信号",
    "手机",
    "门禁卡",
    "纸条",
    "录像",
    "档案",
    "U盘",
]

OUTLINE_STOPWORDS = {
    "第一幕",
    "第二幕",
    "第三幕",
    "结局",
    "结尾",
    "高潮",
    "余韵",
    "场景",
    "剧情",
    "故事",
    "主角",
    "角色",
    "人物",
    "冲突",
    "推进",
    "发展",
    "收束",
    "完成",
    "最终",
    "开始",
    "因为",
    "所以",
    "以及",
}


def _build_requirement_text(requirements: dict[str, Any]) -> str:
    req_text = (requirements.get("content") or "").strip()
    if req_text:
        return req_text

    title = requirements.get("title", "")
    theme = requirements.get("theme", "")
    audience = requirements.get("audience", "")
    world_setting = requirements.get("world_setting", {}) or {}
    characters = requirements.get("characters", []) or []

    character_lines = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        name = character.get("name", "")
        role = character.get("role", "")
        arc = character.get("arc", "")
        if name or role or arc:
            character_lines.append(f"{name}（{role}）：{arc}".strip())

    parts = [
        f"项目标题：{title}" if title else "",
        f"故事主题：{theme}" if theme else "",
        f"目标受众：{audience}" if audience else "",
        f"世界时间：{world_setting.get('time', '')}" if world_setting.get("time") else "",
        f"世界规则：{world_setting.get('rules', '')}" if world_setting.get("rules") else "",
        f"核心冲突：{world_setting.get('conflict', '')}" if world_setting.get("conflict") else "",
        "角色列表：\n" + "\n".join(character_lines) if character_lines else "",
    ]
    return "\n".join(part for part in parts if part)


def _normalize_script(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[*#`_]+", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _normalize_match_text(text: str) -> str:
    normalized = _normalize_script(text)
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"[，。！？；：、“”‘’（）《》【】\[\]\(\)\-—,.!?:;\"'·]", "", normalized)
    return normalized


def _clean_outline_line(raw_line: str) -> str:
    line = (raw_line or "").strip()
    line = re.sub(r"^[\-\*\d\.\s、]+", "", line)
    return line.strip("：: ")


def _detect_outline_section_label(line: str) -> str:
    if not line:
        return ""

    if "第一幕" in line:
        return "第一幕"
    if "第二幕" in line:
        return "第二幕"
    if "第三幕" in line:
        return "第三幕"
    if any(keyword in line for keyword in ("结局", "结尾", "尾声", "高潮")):
        return "结局"
    return ""


def _strip_outline_section_heading(line: str, section_label: str) -> str:
    if not line or not section_label:
        return line

    if section_label == "结局":
        return re.sub(r"^(结局|结尾|尾声|高潮)[：:\s-]*", "", line).strip()

    return re.sub(rf"^{section_label}[：:\s-]*", "", line).strip()


def _looks_like_outline_heading(line: str) -> bool:
    stripped = (line or "").strip("：: ")
    if not stripped:
        return True

    if stripped in {"三幕式剧情大纲", "剧情大纲", "故事大纲", "第一幕", "第二幕", "第三幕", "结局", "结尾", "尾声", "高潮"}:
        return True

    if re.fullmatch(r"第\s*[一二三四五六七八九十百零\d]+\s*幕", stripped):
        return True

    return False


def _looks_like_outline_meta(line: str) -> bool:
    stripped = (line or "").strip()
    if not stripped:
        return False

    meta_keywords = ("建议", "说明", "提示", "要求", "风格", "写法", "格式")
    plot_keywords = ("主角", "反派", "真相", "结局", "高潮", "事故", "线索", "选择", "代价", "冲突")
    return any(keyword in stripped for keyword in meta_keywords) and not any(
        keyword in stripped for keyword in plot_keywords
    )


def _split_outline_segments(line: str) -> list[str]:
    raw = _normalize_script(line)
    if not raw:
        return []

    primary_parts = [
        part.strip(" ，,；;：:")
        for part in re.split(r"[。！？；]+", raw)
        if part.strip(" ，,；;：:")
    ]
    segments: list[str] = []

    for part in primary_parts or [raw]:
        comma_parts = [
            chunk.strip(" ，,；;：:")
            for chunk in re.split(r"[，,]", part)
            if chunk.strip(" ，,；;：:")
        ]
        if len(comma_parts) >= 2 and len(_normalize_match_text(part)) >= 18:
            long_chunks = [chunk for chunk in comma_parts if len(_normalize_match_text(chunk)) >= 6]
            if len(long_chunks) >= 2:
                segments.extend(long_chunks)
                continue
        segments.append(part)

    cleaned_segments: list[str] = []
    seen: set[str] = set()

    for segment in segments:
        segment = re.sub(r"^(这一幕|本幕|随后|接着|然后|最终|最后)[：:\s]*", "", segment)
        segment = segment.strip(" ，,；;：:")
        if not segment or _looks_like_outline_heading(segment) or _looks_like_outline_meta(segment):
            continue

        normalized = _normalize_match_text(segment)
        if len(normalized) < 6 or normalized in seen:
            continue

        seen.add(normalized)
        cleaned_segments.append(segment)

    if cleaned_segments:
        return cleaned_segments

    if _looks_like_outline_meta(raw):
        return []
    return [raw] if len(_normalize_match_text(raw)) >= 6 else []


def _extract_outline_items(outline: str) -> list[dict[str, str]]:
    text = _normalize_script(outline)
    if not text:
        return []

    items: list[dict[str, str]] = []
    seen: set[str] = set()
    current_section = ""

    for raw_line in text.split("\n"):
        line = _clean_outline_line(raw_line)
        if not line:
            continue

        section_label = _detect_outline_section_label(line)
        if section_label:
            current_section = section_label
            line = _strip_outline_section_heading(line, section_label)
            if not line:
                continue

        if _looks_like_outline_heading(line):
            continue

        keywords = _extract_focus_keywords(line, limit=6)
        if len(keywords) < 2 and len(line) < 12:
            continue

        key = f"{current_section}|{line}"
        if key in seen:
            continue
        seen.add(key)
        items.append({"section": current_section or "剧情推进", "text": line})

    return items


def _extract_keyword_matches(reference: str, text: str, limit: int = 6) -> tuple[list[str], list[str], float]:
    keywords = _extract_focus_keywords(reference, limit=limit)
    if not keywords:
        return [], [], 0.0

    matched = [keyword for keyword in keywords if keyword in text]
    coverage = len(matched) / len(keywords)
    return keywords, matched, coverage


def _is_outline_item_covered(item_text: str, content: str) -> bool:
    keywords, matched, coverage = _extract_keyword_matches(item_text, content)
    if not keywords:
        return False

    if len(matched) >= min(2, len(keywords)):
        return True

    return coverage >= 0.5


def _extract_outline_progress(outline: str, content: str) -> dict[str, Any]:
    items = _extract_outline_items(outline)
    covered_items: list[dict[str, Any]] = []
    pending_items: list[dict[str, Any]] = []

    for item in items:
        keywords, matched_keywords, coverage = _extract_keyword_matches(item["text"], content)
        enriched = {
            **item,
            "keywords": keywords,
            "matched_keywords": matched_keywords,
            "coverage": coverage,
        }
        if _is_outline_item_covered(item["text"], content):
            covered_items.append(enriched)
        else:
            pending_items.append(enriched)

    section_label = ""
    section_index = 1
    if pending_items:
        section_label = pending_items[0]["section"]
        section_index = len([item for item in covered_items if item["section"] == section_label]) + 1
    elif covered_items:
        section_label = covered_items[-1]["section"]
        section_index = len([item for item in covered_items if item["section"] == section_label])

    return {
        "items": items,
        "covered_items": covered_items,
        "pending_items": pending_items,
        "covered_points": [item["text"] for item in covered_items],
        "pending_points": [item["text"] for item in pending_items],
        "current_target": pending_items[0]["text"] if pending_items else "",
        "next_target": pending_items[1]["text"] if len(pending_items) > 1 else "",
        "section_label": section_label,
        "section_index": max(1, section_index),
    }


def _extract_scene_blocks(text: str) -> list[str]:
    cleaned = _normalize_script(text)
    if not cleaned:
        return []

    markers = list(re.finditer(r"^(?:第\s*[一二三四五六七八九十百零\d]+\s*场|内景|外景)", cleaned, flags=re.MULTILINE))
    if not markers:
        return [cleaned]

    blocks: list[str] = []
    for index, match in enumerate(markers):
        start = match.start()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(cleaned)
        block = cleaned[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def _extract_scene_heading_from_block(scene_block: str) -> str:
    lines = [line.strip() for line in _normalize_script(scene_block).split("\n") if line.strip()]
    for line in lines:
        if line.startswith(("内景", "外景")):
            return line
    for line in lines:
        if re.match(r"^第\s*[一二三四五六七八九十百零\d]+\s*场", line):
            return line
    return lines[0] if lines else ""


def _scene_similarity(left: str, right: str) -> float:
    left_text = _normalize_match_text(left)
    right_text = _normalize_match_text(right)
    if not left_text or not right_text:
        return 0.0
    return SequenceMatcher(None, left_text[:1800], right_text[:1800]).ratio()


def _shared_line_count(left: str, right: str) -> int:
    left_lines = {
        line.strip()
        for line in _normalize_script(left).split("\n")
        if len(line.strip()) >= 8 and not line.strip().startswith(("第一幕", "第二幕", "第三幕", "结局"))
    }
    right_lines = {
        line.strip()
        for line in _normalize_script(right).split("\n")
        if len(line.strip()) >= 8 and not line.strip().startswith(("第一幕", "第二幕", "第三幕", "结局"))
    }
    return len(left_lines & right_lines)


def _detect_recent_repetition(content: str, candidate: Optional[str] = None) -> dict[str, Any]:
    scene_blocks = _extract_scene_blocks(content)
    if candidate:
        target_block = _normalize_script(candidate)
        reference_blocks = scene_blocks[-3:]
    else:
        if len(scene_blocks) < 2:
            return {"repetition_detected": False, "reason": "", "similarity": 0.0}
        target_block = scene_blocks[-1]
        reference_blocks = scene_blocks[-4:-1]

    target_heading = _extract_scene_heading_from_block(target_block)
    max_similarity = 0.0
    reasons: list[str] = []

    for block in reference_blocks:
        similarity = _scene_similarity(target_block, block)
        shared_lines = _shared_line_count(target_block, block)
        same_heading = bool(target_heading and target_heading == _extract_scene_heading_from_block(block))
        max_similarity = max(max_similarity, similarity)

        if similarity >= 0.78:
            reasons.append(f"与最近场次文本相似度过高（{similarity:.2f}）")
        elif same_heading and similarity >= 0.58:
            reasons.append("沿用了几乎相同的场景标题和推进方式")
        elif shared_lines >= 3:
            reasons.append("重复复用了最近场次的对白或动作描述")

    return {
        "repetition_detected": bool(reasons),
        "reason": reasons[0] if reasons else "",
        "similarity": max_similarity,
    }


def _build_recent_scene_digest(content: str, limit: int = 3) -> str:
    scenes = _extract_scene_blocks(content)[-limit:]
    if not scenes:
        return ""

    digest_lines: list[str] = []
    for scene in scenes:
        heading = _extract_scene_heading_from_block(scene) or "最近场次"
        keywords = "、".join(_extract_focus_keywords(scene, limit=5)[:4]) or "无"
        digest_lines.append(f"- {heading} | 关键词：{keywords}")

    return "\n".join(digest_lines)


def _build_outline_digest(items: list[dict[str, Any]], empty_text: str, limit: int = 3) -> str:
    if not items:
        return empty_text

    digest_lines: list[str] = []
    for item in items[:limit]:
        section = item.get("section") or "剧情推进"
        text = item.get("text") or ""
        digest_lines.append(f"- {section}：{text}")
    return "\n".join(digest_lines)


def _resolve_next_act_context(outline: str, content: str, beat_index: int) -> dict[str, Any]:
    outline_progress = _extract_outline_progress(outline, content)
    section_label = outline_progress.get("section_label") or ""
    section_index = int(outline_progress.get("section_index") or 1)
    current_target = outline_progress.get("current_target") or ""
    next_target = outline_progress.get("next_target") or ""

    if not section_label:
        section_label, section_index = _get_act_label(beat_index)

    if outline.strip() and not current_target:
        section_label = "结局"
        section_index = max(1, section_index)
        current_target = "完成整部剧的结尾收束，回收主要伏笔，交代最终选择带来的后果。"
        if not next_target:
            next_target = "用最后的画面、动作或对白留下余韵。"

    return {
        "outline_progress": outline_progress,
        "section_label": section_label,
        "section_index": section_index,
        "current_target": current_target,
        "next_target": next_target,
    }


def _validate_generated_beat(candidate: str, content: str, outline_progress: dict[str, Any]) -> dict[str, Any]:
    repetition = _detect_recent_repetition(content, candidate)
    if repetition.get("repetition_detected"):
        return {"ok": False, "reason": repetition.get("reason") or "新场次与最近内容重复"}

    current_target = outline_progress.get("current_target") or ""
    if current_target and not _is_outline_item_covered(current_target, candidate):
        return {"ok": False, "reason": f"新场次没有真正推进当前应写的大纲节点：{current_target}"}

    return {"ok": True, "reason": ""}


def _build_retry_prompt(base_prompt: str, fail_reason: str, current_target: str, next_target: str) -> str:
    retry_lines = [
        "上一版续写失败，请完全重写本场，不得沿用上一版的对白、动作和场景铺陈。",
        f"失败原因：{fail_reason}",
    ]

    if current_target:
        retry_lines.append(f"这一次必须实质推进的大纲节点：{current_target}")
    if next_target:
        retry_lines.append(f"推进完当前节点后，可以顺手为下一节点埋桥：{next_target}")

    retry_lines.extend(
        [
            "如果仍然回到相同地点，必须发生新的信息揭示、新障碍或新后果。",
            "不要为了拖长篇幅重复情绪、重复台词或重复场景标题。",
        ]
    )

    return f"{base_prompt}\n\n补充硬性要求：\n" + "\n".join(f"{index + 1}. {line}" for index, line in enumerate(retry_lines))


def _extract_latest_scene(text: str) -> str:
    lines = [line.strip() for line in _normalize_script(text).split("\n") if line.strip()]
    scene_lines = [line for line in lines if line.startswith(("内景", "外景"))]
    return scene_lines[-1] if scene_lines else "内景 临时空间 夜"


def _extract_primary_character(text: str) -> str:
    cleaned = _normalize_script(text)
    names = re.findall(r"^([\u4e00-\u9fff]{2,6})[:：]", cleaned, flags=re.MULTILINE)
    blocked = {"内景", "外景", "画外音", "动作描述", "承接上场", "承接上节", "推进说明", "关键对白"}
    for name in names:
        if name not in blocked:
            return name

    tokens = re.findall(r"[\u4e00-\u9fff]{2,3}", cleaned)
    for token in tokens:
        if token not in blocked:
            return token

    return "主角"


def _extract_recent_prop(text: str) -> str:
    for keyword in ["怀表", "录音", "旧照片", "坐标", "钥匙", "求救信号", "日志", "芯片", "信号"]:
        if keyword in text:
            return keyword
    return "线索"


def _infer_next_scene_title(current_scene: str, beat_index: int) -> str:
    if "港口" in current_scene:
        return "内景 科考船舱 夜"
    if "公寓" in current_scene:
        return "外景 港口 夜"
    if "研究站" in current_scene:
        return "内景 研究站走廊 夜"
    if "船舱" in current_scene:
        return "外景 研究站平台 夜"
    if beat_index % 2 == 0:
        return "外景 暴雨甲板 夜"
    return "内景 临时控制室 夜"


def _extract_next_beat_index(text: str) -> int:
    arabic_hits = [int(item) for item in re.findall(r"第\s*(\d+)\s*场", text)]
    if arabic_hits:
        return max(arabic_hits) + 1

    chinese_map = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    chinese_hits = []
    for item in re.findall(r"第\s*([一二三四五六七八九十])\s*场", text):
        if item in chinese_map:
            chinese_hits.append(chinese_map[item])

    if chinese_hits:
        return max(chinese_hits) + 1

    return len(re.findall(r"^(内景|外景)", text, flags=re.MULTILINE)) + 1


def _build_progression_hint(beat_index: int) -> str:
    hints = [
        "线索由‘异常现象’升级为‘人为布局’，主角开始怀疑内部有人提前布控。",
        "主角不再被动调查，转为主动设局试探同伴，人物关系开始出现裂痕。",
        "旧案与当下危机正式重叠，主角必须在‘保命’和‘揭真相’之间二选一。",
        "前一场留下的道具被反向利用，推动剧情进入不可逆阶段。",
    ]
    return hints[(beat_index - 1) % len(hints)]


def _get_act_label(beat_index: int) -> tuple[str, int]:
    if beat_index <= 3:
        return "第一幕", beat_index
    if beat_index <= 7:
        return "第二幕", beat_index - 3
    if beat_index <= 10:
        return "第三幕", beat_index - 7
    return "结局", beat_index - 10


def _extract_last_dialogue_hint(text: str) -> str:
    lines = [line.strip() for line in _normalize_script(text).split("\n") if line.strip()]
    dialogue_lines = []
    for i in range(len(lines) - 1):
        if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", lines[i]):
            dialogue_lines.append(f"{lines[i]}：{lines[i + 1]}")

    return dialogue_lines[-1] if dialogue_lines else "上一场的对话仍在耳边回响。"


def _extract_outline_anchor(outline: str, act_label: str) -> str:
    text = _normalize_script(outline)
    if not text:
        return ""

    section_map = {
        "第一幕": ["第一幕"],
        "第二幕": ["第二幕"],
        "第三幕": ["第三幕"],
        "结局": ["结局", "结尾", "余韵", "高潮"],
    }

    keywords = section_map.get(act_label, [])
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for idx, line in enumerate(lines):
        if any(key in line for key in keywords):
            anchor_lines = [line]
            for tail in lines[idx + 1 : idx + 4]:
                if any(mark in tail for mark in ["第一幕", "第二幕", "第三幕", "结局", "高潮"]):
                    break
                anchor_lines.append(tail)
            return "；".join(anchor_lines)

    return lines[0] if lines else ""


def _extract_scene_count(text: str) -> int:
    cleaned = _normalize_script(text)
    numbered_scenes = re.findall(r"^第\s*[一二三四五六七八九十百零\d]+\s*场", cleaned, flags=re.MULTILINE)
    if numbered_scenes:
        return len(numbered_scenes)
    return len(re.findall(r"^(内景|外景)", cleaned, flags=re.MULTILINE))


def _extract_outline_focus_points(outline: str, limit: int = 6) -> list[str]:
    text = _normalize_script(outline)
    if not text:
        return []

    prioritized: list[str] = []
    regular: list[str] = []
    for raw_line in text.split("\n"):
        line = re.sub(r"^[\-\*\d\.\s]+", "", raw_line).strip("：:；; ")
        if not line:
            continue
        target_bucket = prioritized if any(keyword in line for keyword in ENDING_KEYWORDS) else regular
        if line not in target_bucket:
            target_bucket.append(line)

    return (prioritized + regular)[:limit]


def _extract_focus_keywords(text: str, limit: int = 10) -> list[str]:
    hits: list[str] = []
    for token in re.findall(r"[\u4e00-\u9fff]{2,6}", text or ""):
        if token in OUTLINE_STOPWORDS:
            continue
        if token not in hits:
            hits.append(token)
        if len(hits) >= limit:
            break
    return hits


def _parse_json_object(raw_text: str) -> Optional[dict[str, Any]]:
    if not raw_text:
        return None

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(raw_text[start : end + 1])
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


def _build_completion_fallback(content: str, outline: str) -> dict[str, Any]:
    cleaned = _normalize_script(content)
    outline_progress = _extract_outline_progress(outline, cleaned)
    outline_points = outline_progress.get("items", [])
    scene_count = _extract_scene_count(cleaned)
    tail = cleaned[-1800:]

    matched_points = outline_progress.get("covered_points", [])
    missing_points = outline_progress.get("pending_points", [])
    outline_coverage = round(len(matched_points) / len(outline_points), 2) if outline_points else 0.0
    repetition = _detect_recent_repetition(cleaned)

    resolved_threads: list[str] = []
    dangling_threads: list[str] = []
    for keyword in FORESHADOW_KEYWORDS:
        occurrences = len(re.findall(re.escape(keyword), cleaned))
        if occurrences == 0:
            continue
        if keyword in tail:
            resolved_threads.append(keyword)
        elif occurrences == 1:
            dangling_threads.append(keyword)

    ending_reached = any(keyword in tail for keyword in ENDING_KEYWORDS)
    minimum_scenes = 2 if not outline_points else 3
    is_complete = (
        scene_count >= minimum_scenes
        and ending_reached
        and (not outline_points or outline_coverage >= 0.85)
        and not dangling_threads
        and not repetition.get("repetition_detected")
    )

    if is_complete:
        reason = "当前剧本已经覆盖大纲主体内容，并且结尾段落完成了收束。"
    elif repetition.get("repetition_detected"):
        reason = repetition.get("reason") or "最近几场出现了重复生成，当前不应继续机械续写。"
    elif missing_points:
        reason = f"仍有大纲内容未充分落地：{missing_points[0]}"
    elif dangling_threads:
        reason = f"仍有关键伏笔没有明显回收：{dangling_threads[0]}"
    elif not ending_reached:
        reason = "当前文本还没有进入明确的结尾收束段落。"
    else:
        reason = "当前剧本还在推进阶段，尚未达到自动完结条件。"

    return {
        "is_complete": is_complete,
        "reason": reason,
        "scene_count": scene_count,
        "ending_reached": ending_reached,
        "outline_coverage": outline_coverage,
        "matched_points": matched_points[:6],
        "missing_points": missing_points[:6],
        "resolved_threads": resolved_threads[:6],
        "dangling_threads": dangling_threads[:6],
        "covered_count": len(matched_points),
        "total_outline_items": len(outline_points),
        "current_target": outline_progress.get("current_target", ""),
        "next_target": outline_progress.get("next_target", ""),
        "section_label": outline_progress.get("section_label", ""),
        "repetition_detected": bool(repetition.get("repetition_detected")),
        "repetition_reason": repetition.get("reason", ""),
        "can_continue": not is_complete,
        "source": "fallback",
    }


def _assess_completion_with_model(content: str, outline: str) -> Optional[dict[str, Any]]:
    if not outline.strip() or len(content.strip()) < 600:
        return None

    prompt = f"""你是剧本完结检查器。请根据“剧情大纲”和“当前剧本正文”判断这部剧本是否已经完整讲完，并且主要伏笔是否已经回收。

判断标准：
1. 必须已经写到结尾，不是停在中段。
2. 必须基本覆盖大纲要求，不能还有核心剧情点没写。
3. 主要伏笔和关键线索不能明显悬空。
4. 如果已经完整收束，则 is_complete 必须为 true；否则必须为 false。

只输出严格 JSON，不要附加任何解释。格式如下：
{{
  "is_complete": true,
  "reason": "一句中文说明",
  "missing_points": ["如果没有就返回空数组"],
  "resolved_threads": ["已回收的关键伏笔或线索"],
  "ending_reached": true
}}

剧情大纲：
{outline}

当前剧本正文：
{content[-5000:]}
"""

    raw, _ = generate_clean_content(prompt, max_tokens=500)
    parsed = _parse_json_object(raw)
    if not parsed:
        return None

    return {
        "is_complete": bool(parsed.get("is_complete")),
        "reason": str(parsed.get("reason") or "").strip(),
        "missing_points": [str(item).strip() for item in (parsed.get("missing_points") or []) if str(item).strip()],
        "resolved_threads": [str(item).strip() for item in (parsed.get("resolved_threads") or []) if str(item).strip()],
        "ending_reached": bool(parsed.get("ending_reached")),
    }


def _evaluate_script_completion(content: str, outline: str) -> dict[str, Any]:
    fallback = _build_completion_fallback(content, outline)

    try:
        assessment = _assess_completion_with_model(content, outline)
    except Exception:
        assessment = None

    if not assessment:
        return fallback

    missing_points: list[str] = []
    for item in assessment.get("missing_points", []) + fallback.get("missing_points", []):
        if item and item not in missing_points:
            missing_points.append(item)

    resolved_threads: list[str] = []
    for item in assessment.get("resolved_threads", []) + fallback.get("resolved_threads", []):
        if item and item not in resolved_threads:
            resolved_threads.append(item)

    model_complete = bool(assessment.get("is_complete"))
    outline_coverage = float(fallback.get("outline_coverage", 0) or 0)
    fallback_complete = bool(
        fallback.get("ending_reached")
        and (outline_coverage >= 0.75 or not fallback.get("total_outline_items"))
        and not fallback.get("repetition_detected")
    )
    blocking_missing = bool(missing_points and outline_coverage < 0.85)
    blocking_dangling = bool(fallback.get("dangling_threads") and not fallback.get("ending_reached"))
    is_complete = bool(fallback.get("is_complete")) or (
        model_complete and fallback_complete and not blocking_missing and not blocking_dangling
    )

    return {
        **fallback,
        "is_complete": is_complete,
        "reason": assessment.get("reason") or fallback.get("reason"),
        "missing_points": missing_points[:6],
        "resolved_threads": resolved_threads[:6],
        "ending_reached": bool(assessment.get("ending_reached") or fallback.get("ending_reached")),
        "can_continue": not is_complete,
        "source": "model+fallback",
    }


def _build_next_beat_prompt(content: str, outline: str, characters: str) -> dict[str, Any]:
    cleaned = _normalize_script(content)
    current_scene = _extract_latest_scene(cleaned)
    prop = _extract_recent_prop(cleaned)
    beat_index = _extract_next_beat_index(cleaned)
    act_context = _resolve_next_act_context(outline, cleaned, beat_index)
    act_label = act_context["section_label"]
    section_index = act_context["section_index"]
    current_target = act_context["current_target"]
    next_target = act_context["next_target"]
    outline_progress = act_context["outline_progress"]
    progression_hint = _build_progression_hint(beat_index)
    last_dialogue_hint = _extract_last_dialogue_hint(cleaned)
    recent_scene_digest = _build_recent_scene_digest(cleaned, limit=3)
    covered_digest = _build_outline_digest(
        outline_progress.get("covered_items", [])[-2:],
        "暂无已完成节点摘要。",
        limit=2,
    )
    pending_digest = _build_outline_digest(
        outline_progress.get("pending_items", []),
        "大纲主线已基本覆盖，下一场应完成结尾收束。",
        limit=3,
    )

    prompt = f"""你是专业中文编剧，请基于“已有正文 + 剧情大纲 + 人物设定”续写“下一个节点（下一场）”。

硬性要求：
1. 必须严格承接已有正文，不能重写前文，不要重复已经出现的段落。
2. 必须实质推进当前要写的大纲节点：{current_target or '延续当前剧情主线推进'}。
3. 推进完当前节点后，可以顺手为下一节点埋桥：{next_target or '根据剧情自然衔接下一步'}。
4. 只输出“新增这一场”的内容，不要输出解释。
5. 开头必须依次输出：
   - {act_label}·第{section_index}节
   - 第{beat_index}场
   - 一个新的、与当前剧情连续的中文场景标题（例如“内景 逃生舱 清晨”）
6. 必须包含：承接上场、动作描述、人物对白。
7. 人物对白只允许真实角色名，禁止把“承接上场/推进说明”等当成角色名。
8. 不要机械沿用最近几场的相同场景标题、对白和情绪推进，尤其不要反复写同一个地点和同一时间标记。
9. 如果大纲主线已经基本写完，这一场必须承担结尾收束功能，而不是继续拖延。

最近几场（禁止复读）：
{recent_scene_digest or '- 暂无最近场次摘要'}

已经覆盖的大纲节点：
{covered_digest}

剩余待写的大纲节点：
{pending_digest}

人物设定：
{characters or '沿用现有正文已出现的人物关系'}

上一场关键信息：
- 上一场场景：{current_scene}
- 关键对白：{last_dialogue_hint}
- 关键线索：{prop}
- 节奏推进建议：{progression_hint}

已有正文（供承接，不要重复）：
{cleaned[-2200:]}
"""

    return {
        "prompt": prompt,
        "beat_index": beat_index,
        "act_label": act_label,
        "section_index": section_index,
        "current_scene": current_scene,
        "current_target": current_target,
        "next_target": next_target,
        "outline_progress": outline_progress,
    }


def _build_next_beat_text(content: str, outline: str = "", characters: str = "") -> str:
    prompt_payload = _build_next_beat_prompt(content, outline, characters)
    prompt = prompt_payload["prompt"]
    beat_index = prompt_payload["beat_index"]
    act_label = prompt_payload["act_label"]
    section_index = prompt_payload["section_index"]
    current_scene = prompt_payload["current_scene"]
    current_target = prompt_payload["current_target"]
    next_target = prompt_payload["next_target"]
    outline_progress = prompt_payload["outline_progress"]
    protagonist = _extract_primary_character(content)
    fallback_heading = _infer_next_scene_title(current_scene, beat_index)

    last_failure_reason = ""
    last_candidate = ""

    for attempt in range(3):
        attempt_prompt = (
            prompt
            if attempt == 0
            else _build_retry_prompt(prompt, last_failure_reason or "上一版没有通过校验", current_target, next_target)
        )

        try:
            generated, _ = generate_clean_content(attempt_prompt, max_tokens=1800)
            generated = enforce_script_labels(generated)
            normalized = _normalize_script(generated)
        except Exception:
            normalized = ""

        if not normalized:
            last_failure_reason = "模型没有返回可用的新场次内容"
            continue

        if f"第{beat_index}场" not in normalized or not re.search(r"^(内景|外景)", normalized, flags=re.MULTILINE):
            normalized = _normalize_script(
                f"""{act_label}·第{section_index}节
第{beat_index}场
{fallback_heading}

承接上场
上一场位于：{current_scene}
当前目标：{current_target or '延续当前剧情主线推进'}

{normalized}
"""
            )

        validation = _validate_generated_beat(normalized, content, outline_progress)
        if validation.get("ok"):
            return normalized

        last_candidate = normalized
        last_failure_reason = validation.get("reason") or "新场次校验未通过"

    fallback_target = current_target or "推动剧情进入新的阶段，并形成明确的新后果。"
    bridge_target = next_target or "为后续场次留下新的行动方向。"
    fallback_reason = last_failure_reason or "模型续写未能稳定推进当前节点"

    return _normalize_script(
        f"""{act_label}·第{section_index}节
第{beat_index}场
{fallback_heading}

承接上场
上一场位于：{current_scene}
当前目标：{fallback_target}
校验备注：{fallback_reason}

动作描述
{protagonist}没有停留在上一场的情绪里，而是立刻针对“{fallback_target}”展开行动。新的信息被揭开，局势因此发生不可逆的变化，同时也为“{bridge_target}”埋下了更具体的后果。

{protagonist}
这一次，我们不能再原地打转了。
"""
    )


def _looks_like_outline_meta(line: str) -> bool:
    stripped = (line or "").strip()
    if not stripped:
        return False

    meta_keywords = ("建议", "说明", "提示", "要求", "风格", "写法", "格式")
    plot_keywords = ("主角", "反派", "真相", "结局", "高潮", "事故", "线索", "选择", "代价", "冲突")
    return any(keyword in stripped for keyword in meta_keywords) and not any(
        keyword in stripped for keyword in plot_keywords
    )


def _split_outline_segments(line: str) -> list[str]:
    raw = _normalize_script(line)
    if not raw:
        return []

    primary_parts = [
        part.strip(" ，,；;：:")
        for part in re.split(r"[。！？；]+", raw)
        if part.strip(" ，,；;：:")
    ]
    segments: list[str] = []

    for part in primary_parts or [raw]:
        comma_parts = [
            chunk.strip(" ，,；;：:")
            for chunk in re.split(r"[，,]", part)
            if chunk.strip(" ，,；;：:")
        ]
        if len(comma_parts) >= 2 and len(_normalize_match_text(part)) >= 18:
            long_chunks = [chunk for chunk in comma_parts if len(_normalize_match_text(chunk)) >= 6]
            if len(long_chunks) >= 2:
                segments.extend(long_chunks)
                continue
        segments.append(part)

    cleaned_segments: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        segment = re.sub(r"^(这一幕|本幕|随后|接着|然后|最终|最后)[：:\s]*", "", segment)
        segment = segment.strip(" ，,；;：:")
        if not segment or _looks_like_outline_heading(segment) or _looks_like_outline_meta(segment):
            continue

        normalized = _normalize_match_text(segment)
        if len(normalized) < 6 or normalized in seen:
            continue

        seen.add(normalized)
        cleaned_segments.append(segment)

    if cleaned_segments:
        return cleaned_segments

    if _looks_like_outline_meta(raw):
        return []
    return [raw] if len(_normalize_match_text(raw)) >= 6 else []


def _extract_outline_items(outline: str) -> list[dict[str, Any]]:
    text = _normalize_script(outline)
    if not text:
        return []

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    current_section = ""

    for raw_line in text.split("\n"):
        line = _clean_outline_line(raw_line)
        if not line:
            continue

        section_label = _detect_outline_section_label(line)
        if section_label:
            current_section = section_label
            line = _strip_outline_section_heading(line, section_label)
            if not line:
                continue

        if _looks_like_outline_heading(line):
            continue

        for segment in _split_outline_segments(line):
            keywords = _extract_focus_keywords(segment, limit=6)
            if len(keywords) < 2 and len(segment) < 12:
                continue

            key = f"{current_section}|{_normalize_match_text(segment)}"
            if key in seen:
                continue

            seen.add(key)
            items.append({"section": current_section or "剧情推进", "text": segment})

    return items


def _extract_text_chunks(text: str) -> list[str]:
    cleaned = _normalize_script(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    for line in cleaned.split("\n"):
        stripped = line.strip()
        if not stripped or _looks_like_outline_heading(stripped):
            continue

        pieces = [
            chunk.strip(" ，,；;：:")
            for chunk in re.split(r"[。！？；]+", stripped)
            if chunk.strip(" ，,；;：:")
        ]
        for piece in pieces or [stripped]:
            if len(_normalize_match_text(piece)) >= 6:
                chunks.append(piece)

    return chunks or [cleaned]


def _best_chunk_similarity(reference: str, text: str) -> float:
    reference_norm = _normalize_match_text(reference)
    if not reference_norm:
        return 0.0

    best = 0.0
    for chunk in _extract_text_chunks(text):
        chunk_norm = _normalize_match_text(chunk)
        if not chunk_norm:
            continue
        best = max(best, SequenceMatcher(None, reference_norm[:180], chunk_norm[:360]).ratio())
        if best >= 0.88:
            break
    return best


def _estimate_outline_item_coverage(item_text: str, content: str) -> dict[str, Any]:
    keywords, matched, keyword_coverage = _extract_keyword_matches(item_text, content)
    similarity = _best_chunk_similarity(item_text, content)
    normalized_item = _normalize_match_text(item_text)
    normalized_content = _normalize_match_text(content)
    exact_match = bool(normalized_item and len(normalized_item) >= 10 and normalized_item in normalized_content)

    high_keyword_match = bool(keywords) and len(matched) >= min(2, len(keywords)) and keyword_coverage >= 0.55
    near_full_keyword_match = bool(keywords) and len(matched) >= max(1, len(keywords) - 1) and keyword_coverage >= 0.75
    semantic_match = similarity >= 0.72 and bool(matched)
    covered = exact_match or high_keyword_match or near_full_keyword_match or semantic_match

    return {
        "keywords": keywords,
        "matched_keywords": matched,
        "coverage": keyword_coverage,
        "similarity": similarity,
        "exact_match": exact_match,
        "covered": covered,
    }


def _is_outline_item_covered(item_text: str, content: str) -> bool:
    return _estimate_outline_item_coverage(item_text, content).get("covered", False)


def _extract_outline_progress(outline: str, content: str) -> dict[str, Any]:
    items = _extract_outline_items(outline)
    covered_items: list[dict[str, Any]] = []
    pending_items: list[dict[str, Any]] = []

    for item in items:
        coverage_info = _estimate_outline_item_coverage(item["text"], content)
        enriched = {
            **item,
            "keywords": coverage_info["keywords"],
            "matched_keywords": coverage_info["matched_keywords"],
            "coverage": coverage_info["coverage"],
            "similarity": coverage_info["similarity"],
            "exact_match": coverage_info["exact_match"],
        }
        if coverage_info["covered"]:
            covered_items.append(enriched)
        else:
            pending_items.append(enriched)

    section_label = ""
    section_index = 1
    if pending_items:
        section_label = pending_items[0]["section"]
        section_index = len([item for item in covered_items if item["section"] == section_label]) + 1
    elif covered_items:
        section_label = covered_items[-1]["section"]
        section_index = len([item for item in covered_items if item["section"] == section_label])

    return {
        "items": items,
        "covered_items": covered_items,
        "pending_items": pending_items,
        "covered_points": [item["text"] for item in covered_items],
        "pending_points": [item["text"] for item in pending_items],
        "current_target": pending_items[0]["text"] if pending_items else "",
        "next_target": pending_items[1]["text"] if len(pending_items) > 1 else "",
        "section_label": section_label,
        "section_index": max(1, section_index),
        "pending_count": len(pending_items),
    }


def _is_soft_closure_pending(item: dict[str, Any]) -> bool:
    section = str(item.get("section") or "")
    coverage = float(item.get("coverage") or 0.0)
    similarity = float(item.get("similarity") or 0.0)
    matched_keywords = item.get("matched_keywords") or []
    return section == "结局" and (coverage >= 0.45 or similarity >= 0.68 or len(matched_keywords) >= 2)


def _closure_item_is_resolved(item: dict[str, Any]) -> bool:
    coverage = float(item.get("coverage") or 0.0)
    similarity = float(item.get("similarity") or 0.0)
    matched_keywords = item.get("matched_keywords") or []
    return coverage >= 0.6 or similarity >= 0.74 or len(matched_keywords) >= 3


def _build_target_keyword_hint(target: str, empty_text: str = "根据当前节点自然推进") -> str:
    keywords = _extract_focus_keywords(target, limit=4)
    return "、".join(keywords) if keywords else empty_text


def _validate_generated_beat(
    candidate: str,
    content: str,
    outline_progress: dict[str, Any],
    outline: str = "",
) -> dict[str, Any]:
    repetition = _detect_recent_repetition(content, candidate)
    if repetition.get("repetition_detected"):
        return {"ok": False, "reason": repetition.get("reason") or "新场次与最近内容重复"}

    current_target = outline_progress.get("current_target") or ""
    if current_target:
        target_eval = _estimate_outline_item_coverage(current_target, candidate)
        if not target_eval.get("covered"):
            return {"ok": False, "reason": f"新场次没有真正推进当前应写的大纲节点：{current_target}"}

    if outline.strip() and outline_progress.get("items"):
        before_covered = len(outline_progress.get("covered_items") or [])
        merged_progress = _extract_outline_progress(outline, f"{content}\n\n{candidate}")
        after_covered = len(merged_progress.get("covered_items") or [])
        target_still_pending = False

        if current_target:
            normalized_target = _normalize_match_text(current_target)
            for item in merged_progress.get("pending_items", []):
                if _normalize_match_text(item.get("text", "")) == normalized_target:
                    target_still_pending = True
                    break

        if target_still_pending:
            return {"ok": False, "reason": f"新场次写完后，大纲节点仍未完成：{current_target}"}

        if outline_progress.get("pending_items") and after_covered <= before_covered:
            return {"ok": False, "reason": "新场次没有让大纲覆盖进度继续前进"}

    return {"ok": True, "reason": ""}


def _build_completion_fallback(content: str, outline: str) -> dict[str, Any]:
    cleaned = _normalize_script(content)
    outline_progress = _extract_outline_progress(outline, cleaned)
    outline_points = outline_progress.get("items", [])
    scene_count = _extract_scene_count(cleaned)
    tail = cleaned[-1800:]

    covered_items = outline_progress.get("covered_items", [])
    pending_items = outline_progress.get("pending_items", [])
    critical_pending_items: list[dict[str, Any]] = []
    soft_pending_items: list[dict[str, Any]] = []

    for item in pending_items:
        if _is_soft_closure_pending(item):
            soft_pending_items.append(item)
        else:
            critical_pending_items.append(item)

    matched_points = [item["text"] for item in covered_items]
    missing_points = [item["text"] for item in critical_pending_items]
    soft_missing_points = [item["text"] for item in soft_pending_items]
    outline_coverage = round(len(matched_points) / len(outline_points), 2) if outline_points else 0.0
    repetition = _detect_recent_repetition(cleaned)
    closure_ready = not soft_pending_items or all(_closure_item_is_resolved(item) for item in soft_pending_items)

    resolved_threads: list[str] = []
    dangling_threads: list[str] = []
    for keyword in FORESHADOW_KEYWORDS:
        occurrences = len(re.findall(re.escape(keyword), cleaned))
        if occurrences == 0:
            continue
        if keyword in tail:
            resolved_threads.append(keyword)
        elif occurrences == 1:
            dangling_threads.append(keyword)

    ending_reached = any(keyword in tail for keyword in ENDING_KEYWORDS)
    minimum_scenes = 2 if not outline_points else 3
    is_complete = (
        scene_count >= minimum_scenes
        and ending_reached
        and (
            not outline_points
            or (not critical_pending_items and closure_ready and outline_coverage >= 0.88)
        )
        and not dangling_threads
        and not repetition.get("repetition_detected")
    )

    if is_complete:
        reason = "当前剧本已经完整覆盖大纲主线，并且结尾段落完成了收束。"
    elif repetition.get("repetition_detected"):
        reason = repetition.get("reason") or "最近几场出现了重复生成，当前不应继续机械续写。"
    elif missing_points:
        reason = f"仍有大纲内容未充分落地：{missing_points[0]}"
    elif soft_missing_points:
        reason = f"结尾节点还没有完全收束：{soft_missing_points[0]}"
    elif dangling_threads:
        reason = f"仍有关键伏笔没有明显回收：{dangling_threads[0]}"
    elif not ending_reached:
        reason = "当前文本还没有进入明确的结尾收束段落。"
    else:
        reason = "当前剧本还在推进阶段，尚未达到自动完结条件。"

    return {
        "is_complete": is_complete,
        "reason": reason,
        "scene_count": scene_count,
        "ending_reached": ending_reached,
        "outline_coverage": outline_coverage,
        "matched_points": matched_points[:6],
        "missing_points": missing_points[:6],
        "soft_missing_points": soft_missing_points[:3],
        "resolved_threads": resolved_threads[:6],
        "dangling_threads": dangling_threads[:6],
        "covered_count": len(matched_points),
        "total_outline_items": len(outline_points),
        "current_target": outline_progress.get("current_target", ""),
        "next_target": outline_progress.get("next_target", ""),
        "section_label": outline_progress.get("section_label", ""),
        "repetition_detected": bool(repetition.get("repetition_detected")),
        "repetition_reason": repetition.get("reason", ""),
        "can_continue": not is_complete,
        "source": "fallback",
    }


def _evaluate_script_completion(content: str, outline: str) -> dict[str, Any]:
    fallback = _build_completion_fallback(content, outline)

    try:
        assessment = _assess_completion_with_model(content, outline)
    except Exception:
        assessment = None

    if not assessment:
        return fallback

    missing_points: list[str] = []
    for item in assessment.get("missing_points", []) + fallback.get("missing_points", []):
        if item and item not in missing_points:
            missing_points.append(item)

    resolved_threads: list[str] = []
    for item in assessment.get("resolved_threads", []) + fallback.get("resolved_threads", []):
        if item and item not in resolved_threads:
            resolved_threads.append(item)

    fallback_complete = bool(
        fallback.get("ending_reached")
        and not fallback.get("missing_points")
        and not fallback.get("soft_missing_points")
        and not fallback.get("repetition_detected")
        and not fallback.get("dangling_threads")
    )
    blocking_missing = bool(missing_points)
    blocking_soft_missing = bool(fallback.get("soft_missing_points"))
    blocking_dangling = bool(fallback.get("dangling_threads"))
    is_complete = bool(fallback.get("is_complete")) or (
        bool(assessment.get("is_complete"))
        and fallback_complete
        and not blocking_missing
        and not blocking_soft_missing
        and not blocking_dangling
    )

    if is_complete:
        reason = str(assessment.get("reason") or fallback.get("reason") or "当前剧本已经完成收束。").strip()
    elif fallback.get("repetition_detected"):
        reason = fallback.get("reason") or "最近几场出现了重复生成，当前不应继续机械续写。"
    elif missing_points:
        reason = f"仍有大纲内容未充分落地：{missing_points[0]}"
    elif blocking_soft_missing:
        reason = f"结尾节点还没有完全收束：{fallback['soft_missing_points'][0]}"
    elif blocking_dangling:
        reason = f"仍有关键伏笔没有明显回收：{fallback['dangling_threads'][0]}"
    elif not fallback.get("ending_reached"):
        reason = "当前文本还没有进入明确的结尾收束段落。"
    else:
        reason = str(assessment.get("reason") or fallback.get("reason") or "当前剧本还在推进阶段。").strip()

    merged = fallback.copy()
    merged.update(
        {
            "is_complete": is_complete,
            "reason": reason,
            "missing_points": missing_points[:6],
            "resolved_threads": resolved_threads[:6],
            "source": "hybrid",
            "can_continue": not is_complete,
        }
    )
    return merged


def _build_next_beat_prompt(content: str, outline: str, characters: str) -> dict[str, Any]:
    cleaned = _normalize_script(content)
    current_scene = _extract_latest_scene(cleaned)
    prop = _extract_recent_prop(cleaned)
    beat_index = _extract_next_beat_index(cleaned)
    act_context = _resolve_next_act_context(outline, cleaned, beat_index)
    act_label = act_context["section_label"]
    section_index = act_context["section_index"]
    current_target = act_context["current_target"]
    next_target = act_context["next_target"]
    outline_progress = act_context["outline_progress"]
    progression_hint = _build_progression_hint(beat_index)
    last_dialogue_hint = _extract_last_dialogue_hint(cleaned)
    recent_scene_digest = _build_recent_scene_digest(cleaned, limit=3)
    covered_digest = _build_outline_digest(
        outline_progress.get("covered_items", [])[-2:],
        "暂无已完成节点摘要。",
        limit=2,
    )
    pending_digest = _build_outline_digest(
        outline_progress.get("pending_items", []),
        "大纲主线已基本覆盖，下一场应完成结尾收束。",
        limit=3,
    )
    remaining_count = len(outline_progress.get("pending_items", []))
    current_target_keywords = _build_target_keyword_hint(current_target)
    next_target_keywords = _build_target_keyword_hint(next_target, empty_text="根据剧情自然衔接")
    should_force_closure = bool(
        outline_progress.get("items")
        and (
            remaining_count <= 1
            or len(outline_progress.get("covered_items", [])) >= max(1, len(outline_progress.get("items", [])) - 1)
        )
    )
    closure_instruction = (
        "本场必须完成主线冲突结算、关键伏笔回收和结局余韵，不要再开启新的主线。"
        if should_force_closure
        else "本场必须让大纲覆盖进度前进一步，只允许引出与当前节点直接相关的新后果。"
    )

    prompt = f"""你是专业中文编剧，请只续写“下一场”，并严格对齐剧情大纲。
硬性要求：
1. 只输出新增这一场的正文，不要解释，不要总结，不要重复前文。
2. 本场唯一必须完成的大纲节点：{current_target or '延续当前主线推进'}。
3. 写完本场后，大纲覆盖进度必须前进一步；如果没有推进到这个节点，这次续写视为失败。
4. {closure_instruction}
5. 开头必须依次输出：
   - {act_label}·第{section_index}节
   - 第{beat_index}场
   - 一个新的中文场景标题（内景/外景 + 场所 + 时间）
6. 必须包含：承接上场、动作描述、人物对白、明确的新后果；本场结尾要能看出节点已经被推进。
7. 禁止复用最近几场的场景标题、核心对白、动作调度和情绪铺陈。
8. 禁止空转、重复解释、只抒情不推进，也不要突然跳去无关支线。
9. 不要把大纲改写成碎片化摘要，每场只完成一到两个核心动作，场与场之间要有清晰因果。
10. 不允许只“提到”当前节点关键词，必须让它在本场里变成行动、揭示、决定或后果。

当前场次目标：
- 当前节点：{current_target or '延续当前主线推进'}
- 当前节点关键词：{current_target_keywords}
- 下一节点：{next_target or '根据剧情自然衔接下一步'}
- 下一节点关键词：{next_target_keywords}
- 剩余待完成节点数：{remaining_count}
- 本场策略：{closure_instruction}

最近几场摘要：
{recent_scene_digest or '- 暂无最近场次摘要'}

已经完成的大纲节点：
{covered_digest}

仍待完成的大纲节点：
{pending_digest}

人物设定：
{characters or '沿用已有正文中的人物关系'}

上一场关键信息：
- 上一场场景：{current_scene}
- 关键对白：{last_dialogue_hint}
- 关键线索：{prop}
- 推进提示：{progression_hint}

已有正文（只供承接，不要重写）：
{cleaned[-2200:]}
"""

    return {
        "prompt": prompt,
        "beat_index": beat_index,
        "act_label": act_label,
        "section_index": section_index,
        "current_scene": current_scene,
        "current_target": current_target,
        "next_target": next_target,
        "outline_progress": outline_progress,
    }


def _build_next_beat_text(content: str, outline: str = "", characters: str = "") -> str:
    prompt_payload = _build_next_beat_prompt(content, outline, characters)
    prompt = prompt_payload["prompt"]
    beat_index = prompt_payload["beat_index"]
    act_label = prompt_payload["act_label"]
    section_index = prompt_payload["section_index"]
    current_scene = prompt_payload["current_scene"]
    current_target = prompt_payload["current_target"]
    next_target = prompt_payload["next_target"]
    outline_progress = prompt_payload["outline_progress"]
    protagonist = _extract_primary_character(content)
    fallback_heading = _infer_next_scene_title(current_scene, beat_index)

    last_failure_reason = ""

    for attempt in range(3):
        attempt_prompt = (
            prompt
            if attempt == 0
            else _build_retry_prompt(prompt, last_failure_reason or "上一版没有通过校验", current_target, next_target)
        )

        try:
            generated, _ = generate_clean_content(attempt_prompt, max_tokens=1800)
            generated = enforce_script_labels(generated)
            normalized = _normalize_script(generated)
        except Exception:
            normalized = ""

        if not normalized:
            last_failure_reason = "模型没有返回可用的新场次内容"
            continue

        if f"第{beat_index}场" not in normalized or not re.search(r"^(内景|外景)", normalized, flags=re.MULTILINE):
            normalized = _normalize_script(
                f"""{act_label}·第{section_index}节
第{beat_index}场
{fallback_heading}

承接上场
上一场位于：{current_scene}
当前目标：{current_target or '延续当前主线推进'}

{normalized}
"""
            )

        validation = _validate_generated_beat(normalized, content, outline_progress, outline)
        if validation.get("ok"):
            return normalized

        last_failure_reason = validation.get("reason") or "新场次校验未通过"

    fallback_target = current_target or "推动剧情进入新的阶段，并形成明确的新后果。"
    bridge_target = next_target or "为后续场次留下新的行动方向。"
    fallback_reason = last_failure_reason or "模型续写未能稳定推进当前节点"

    return _normalize_script(
        f"""{act_label}·第{section_index}节
第{beat_index}场
{fallback_heading}

承接上场
上一场位于：{current_scene}
当前目标：{fallback_target}
校验备注：{fallback_reason}

动作描述
{protagonist}没有停留在上一场的情绪里，而是立刻针对“{fallback_target}”展开行动。新的信息被揭开，局势因此发生了不可逆的变化，同时也为“{bridge_target}”埋下了更具体的后果。

{protagonist}
这一次，我们不能再原地打转了。
"""
    )


def _generate_outline_aligned_beats(
    content: str,
    outline: str = "",
    characters: str = "",
    max_beats: int = 1,
) -> dict[str, Any]:
    merged_content = _normalize_script(content)
    completion = _evaluate_script_completion(merged_content, outline)
    generated_beats: list[str] = []
    max_beats = max(1, int(max_beats or 1))

    for _ in range(max_beats):
        if completion.get("is_complete"):
            break

        next_beat = _normalize_script(_build_next_beat_text(merged_content, outline=outline, characters=characters))
        if not next_beat:
            break

        generated_beats.append(next_beat)
        merged_content = _normalize_script(f"{merged_content}\n\n{next_beat}") if merged_content else next_beat
        completion = _evaluate_script_completion(merged_content, outline)

    return {
        "text": _normalize_script("\n\n".join(generated_beats)) if generated_beats else "",
        "generated_beats": generated_beats,
        "generated_count": len(generated_beats),
        "merged_content": merged_content,
        "completion": completion,
        "is_complete": bool(completion.get("is_complete")),
    }


@router.post("/plan")
async def plan_narrative(requirements: dict[str, Any] = Body(...)):
    try:
        req_text = _build_requirement_text(requirements)
        graph_plan = await narrative_gen.narrative_planning(req_text)
        return {
            "status": "success",
            "beats": graph_plan.get("beats", []),
            "data": graph_plan,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate_scene")
async def generate_scene(scene_req: dict[str, Any] = Body(...)):
    context = scene_req.get("context", {})
    rules = scene_req.get("rules", {})
    max_retries = 2
    attempts = 0
    last_errors = []
    logs = []

    while attempts <= max_retries:
        req_str = context.get("description", "")
        scene_content = await narrative_gen.generate_scene_with_rules(req_str, rules)
        logs.append(f"attempt {attempts + 1}: {scene_content}")

        verify_result = await narrative_gen.narrative_verify(scene_content, rules)

        if verify_result.get("is_valid"):
            await narrative_gen.narrative_update(verify_result, graph_db=None)
            return {
                "status": "success",
                "scene_content": scene_content,
                "warnings": verify_result.get("soft_warnings", []),
                "logs": logs,
            }

        last_errors = verify_result.get("hard_errors", [])
        if last_errors:
            logs.append(f"attempt {attempts + 1} failed: {last_errors[0].get('description', '')}")
            rules["fix_instructions"] = [err.get("fix_instruction", "") for err in last_errors]
        attempts += 1

    return {
        "status": "failed",
        "error_msg": "scene generation failed after retries",
        "suggestions": last_errors,
        "logs": logs,
    }


@router.get("/graph")
async def get_narrative_graph():
    return {"status": "success", "data": neo4j_client.get_graph_data()}


class BeatRequest(BaseModel):
    content: str
    outline: Optional[str] = None
    characters: Optional[str] = None


class CompletionRequest(BaseModel):
    content: str
    outline: Optional[str] = None


@router.post("/sync_graph")
async def sync_narrative_graph(req: BeatRequest):
    data = neo4j_client.simulate_function_call_update(req.content)
    return {"status": "success", "data": data}


@router.post("/check_completion")
async def check_script_completion(req: CompletionRequest):
    content = _normalize_script(req.content)
    if not content:
        raise HTTPException(status_code=400, detail="当前剧本文本为空，无法检查完成度")

    completion = _evaluate_script_completion(content, req.outline or "")
    return {"status": "success", "completion": completion}


@router.post("/generate_beat")
async def generate_next_beat(req: BeatRequest):
    content = _normalize_script(req.content)
    if not content:
        raise HTTPException(status_code=400, detail="当前剧本文本为空，无法生成下一节拍")

    completion_before = _evaluate_script_completion(content, req.outline or "")
    if completion_before.get("is_complete"):
        graph_data = neo4j_client.simulate_function_call_update(content)
        return {
            "status": "success",
            "text": "",
            "data": graph_data,
            "completion": completion_before,
            "is_complete": True,
        }

    generation = _generate_outline_aligned_beats(
        content,
        outline=req.outline or "",
        characters=req.characters or "",
        max_beats=1,
    )
    next_beat = generation.get("text", "")
    merged = generation.get("merged_content") or content
    graph_data = neo4j_client.simulate_function_call_update(merged)
    completion = generation.get("completion") or _evaluate_script_completion(merged, req.outline or "")

    return {
        "status": "success",
        "text": next_beat,
        "data": graph_data,
        "completion": completion,
        "generated_count": generation.get("generated_count", 0),
        "is_complete": bool(completion.get("is_complete")),
    }
