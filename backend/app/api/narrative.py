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


def _build_next_beat_text(content: str) -> str:
    cleaned = _normalize_script(content)
    current_scene = _extract_latest_scene(cleaned)
    protagonist = _extract_primary_character(cleaned)
    prop = _extract_recent_prop(cleaned)
    beat_index = len(re.findall(r"^(内景|外景)", cleaned, flags=re.MULTILINE)) + 1
    next_scene = _infer_next_scene_title(current_scene, beat_index)

    return _normalize_script(
        f"""第{beat_index}场
{next_scene}

风声逼近，空间里的警报声比刚才更清晰。{protagonist}顺着上一场留下的异常痕迹继续推进，在新的区域里发现与“{prop}”相关的第二层线索，这让事件不再只是回忆，而是正在发生的现实。

动作描述
{protagonist}停下脚步，借着忽明忽暗的灯光检查眼前的装置。屏幕上短暂跳出一串新的时间戳，与之前掌握的记录完全对不上。她意识到，有人比她更早一步来到这里，并故意留下了可被发现的痕迹。

{protagonist}
这不是求救，这是引我继续往里走。

同伴
如果这是陷阱，你现在回头还来得及。

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
