import re
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.api.ai import enforce_script_labels, generate_clean_content
from app.core.narrative_engine import NarrativeGenerator
from app.models.neo4j_db import neo4j_client

router = APIRouter()
narrative_gen = NarrativeGenerator()


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


def _build_next_beat_prompt(content: str, outline: str, characters: str) -> tuple[str, int, str, int, str, str, str]:
    cleaned = _normalize_script(content)
    current_scene = _extract_latest_scene(cleaned)
    protagonist = _extract_primary_character(cleaned)
    prop = _extract_recent_prop(cleaned)
    beat_index = _extract_next_beat_index(cleaned)
    act_label, section_index = _get_act_label(beat_index)
    next_scene = _infer_next_scene_title(current_scene, beat_index)
    progression_hint = _build_progression_hint(beat_index)
    last_dialogue_hint = _extract_last_dialogue_hint(cleaned)
    outline_anchor = _extract_outline_anchor(outline, act_label)

    prompt = f"""你是专业中文编剧，请基于“已有正文 + 剧情大纲 + 人物设定”续写“下一个节点（下一场）”。

硬性要求：
1. 必须严格承接已有正文，不能重写前文，不要重复已经出现的段落。
2. 必须与剧情大纲当前幕一致：{act_label}。
3. 只输出“新增这一场”的内容，不要输出解释。
4. 开头必须依次输出：
   - {act_label}·第{section_index}节
   - 第{beat_index}场
   - {next_scene}
5. 必须包含：承接上场、动作描述、人物对白。
6. 人物对白只允许真实角色名，禁止把“承接上场/推进说明”等当成角色名。

大纲锚点（必须对齐）：
{outline_anchor or '延续当前幕核心冲突推进'}

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

    return prompt, beat_index, act_label, section_index, next_scene, current_scene, outline_anchor


def _build_next_beat_text(content: str, outline: str = "", characters: str = "") -> str:
    prompt, beat_index, act_label, section_index, next_scene, current_scene, outline_anchor = _build_next_beat_prompt(
        content, outline, characters
    )

    try:
        generated, _ = generate_clean_content(prompt, max_tokens=1800)
        generated = enforce_script_labels(generated)
        normalized = _normalize_script(generated)

        if f"第{beat_index}场" not in normalized:
            normalized = _normalize_script(
                f"""{act_label}·第{section_index}节
第{beat_index}场
{next_scene}

承接上场
上一场位于：{current_scene}
大纲锚点：{outline_anchor or '延续当前幕核心冲突推进'}

{normalized}
"""
            )

        return normalized
    except Exception:
        # 最低兜底：仍可用，但优先走真实AI续写
        protagonist = _extract_primary_character(content)
        return _normalize_script(
            f"""{act_label}·第{section_index}节
第{beat_index}场
{next_scene}

承接上场
上一场位于：{current_scene}
大纲锚点：{outline_anchor or '延续当前幕核心冲突推进'}

动作描述
{protagonist}沿着上一场留下的线索继续推进，新的证据与当前幕目标形成直接冲突，剧情向下一节点收束。

{protagonist}
我已经知道下一步该去哪了。
"""
        )


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


@router.post("/sync_graph")
async def sync_narrative_graph(req: BeatRequest):
    data = neo4j_client.simulate_function_call_update(req.content)
    return {"status": "success", "data": data}


@router.post("/generate_beat")
async def generate_next_beat(req: BeatRequest):
    content = _normalize_script(req.content)
    if not content:
        raise HTTPException(status_code=400, detail="当前剧本文本为空，无法生成下一节拍")

    next_beat = _build_next_beat_text(content, outline=req.outline or "", characters=req.characters or "")
    merged = _normalize_script(f"{content}\n\n{next_beat}")
    graph_data = neo4j_client.simulate_function_call_update(merged)

    return {
        "status": "success",
        "text": next_beat,
        "data": graph_data,
    }
