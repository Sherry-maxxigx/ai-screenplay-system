import re
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

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
    names = re.findall(r"^([\u4e00-\u9fff]{2,4})[:：]", cleaned, flags=re.MULTILINE)
    for name in names:
        if name not in {"内景", "外景", "画外音", "动作描述"}:
            return name
    tokens = re.findall(r"[\u4e00-\u9fff]{2,3}", cleaned)
    for token in tokens:
        if token not in {"内景", "外景", "画外音", "动作描述"}:
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


def _build_next_beat_text(content: str) -> str:
    cleaned = _normalize_script(content)
    current_scene = _extract_latest_scene(cleaned)
    protagonist = _extract_primary_character(cleaned)
    prop = _extract_recent_prop(cleaned)
    beat_index = _extract_next_beat_index(cleaned)
    act_label, section_index = _get_act_label(beat_index)
    next_scene = _infer_next_scene_title(current_scene, beat_index)
    progression_hint = _build_progression_hint(beat_index)
    last_dialogue_hint = _extract_last_dialogue_hint(cleaned)

    partner_lines = [
        "你现在继续追下去，可能就回不了头。",
        "这条线索像是故意留给我们的，你确定要踩进去吗？",
        "如果这一层也是假象，我们就只剩最后一次机会了。",
        "你有没有发现，所有证据都在把你往同一个方向推。",
    ]
    protagonist_lines = [
        "我不追下去，真相就永远埋在这里。",
        "既然有人想让我看到这些，那我就看到最后。",
        "现在停下才是最危险的。",
        "他在等我做选择，我偏不按他的剧本走。",
    ]

    partner_line = partner_lines[(beat_index - 1) % len(partner_lines)]
    protagonist_line = protagonist_lines[(beat_index - 1) % len(protagonist_lines)]

    return _normalize_script(
        f"""{act_label}·第{section_index}节
第{beat_index}场
{next_scene}

承接上场
上一场位于：{current_scene}
关键对白：{last_dialogue_hint}

风声逼近，空间里的警报声比刚才更清晰。{protagonist}顺着上一场留下的异常痕迹继续推进，在新的区域里发现与“{prop}”相关的第二层线索，事件从回忆追查转入现实对抗。

动作描述
{protagonist}停下脚步，借着忽明忽暗的灯光检查眼前装置。屏幕跳出一串新的时间戳，与此前记录形成矛盾闭环，说明有人在实时篡改信息流。

推进说明
{progression_hint}

{protagonist}
{protagonist_line}

同伴
{partner_line}

{protagonist}
已经来不及了。真正的问题，是里面还有谁在等我们。
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

        if verify_result["is_valid"]:
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


@router.post("/sync_graph")
async def sync_narrative_graph(req: BeatRequest):
    data = neo4j_client.simulate_function_call_update(req.content)
    return {"status": "success", "data": data}


@router.post("/generate_beat")
async def generate_next_beat(req: BeatRequest):
    content = _normalize_script(req.content)
    if not content:
        raise HTTPException(status_code=400, detail="当前剧本文本为空，无法生成下一节拍")

    next_beat = _build_next_beat_text(content)
    merged = _normalize_script(f"{content}\n\n{next_beat}")
    graph_data = neo4j_client.simulate_function_call_update(merged)

    return {
        "status": "success",
        "text": next_beat,
        "data": graph_data,
    }
