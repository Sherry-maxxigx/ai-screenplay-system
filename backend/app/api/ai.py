import re
from typing import Any, Optional

import openai
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.rule_engine import NarrativeRuleEngine
from app.core.runtime_ai_settings import (
    PROVIDER_OPTIONS,
    ensure_runtime_settings_file,
    get_effective_generation_settings,
    load_runtime_settings,
    save_runtime_settings,
)

router = APIRouter()
rule_engine = NarrativeRuleEngine()


class RuntimeSettingsUpdateRequest(BaseModel):
    model_base: Optional[str] = None
    zhipu_model: Optional[str] = None
    openai_model: Optional[str] = None
    deepseek_model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    safety_provider: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None


class AIGenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: int = 2000


class AnalyzePlotRequest(BaseModel):
    script: str = Field(min_length=1)
    model: Optional[str] = None


class AIFunctionCallRequest(BaseModel):
    prompt: str
    functions: list[Any]
    model: str = "gpt-4o"


class CharacterRequest(BaseModel):
    idea: str = Field(min_length=1)


class OutlineRequest(BaseModel):
    idea: str = Field(min_length=1)
    characters: str = ""


class PipelineScriptRequest(BaseModel):
    idea: str = Field(min_length=1)
    characters: str = ""
    outline: str = ""


SAFETY_PATTERNS = {
    "tencent": [
        "制作炸弹",
        "枪支改造",
        "黑客入侵",
        "窃取账号",
        "毒品配方",
        "自杀教程",
        "恐怖袭击",
    ],
    "basic": [
        "制作炸弹",
        "枪支改造",
        "黑客入侵",
        "自杀教程",
    ],
}


def clean_text_output(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"`{3,}.*?`{3,}", "", text, flags=re.DOTALL)
    text = re.sub(r"^[ \t>*#-]+", "", text, flags=re.MULTILINE)
    text = text.replace("EXT.", "外景")
    text = text.replace("INT.", "内景")
    text = text.replace("(O.S.)", "画外音")
    text = text.replace("O.S.", "画外音")
    text = re.sub(r"[*#`_]+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def looks_garbled(text: str) -> bool:
    if not text:
        return True

    chinese_hits = len(re.findall(r"[\u4e00-\u9fff]", text))
    weird_hits = len(re.findall(r"[ÃÂÐÎÒÙÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]", text))
    return weird_hits >= 3 or chinese_hits < max(30, len(text) // 14)


def run_safety_review(prompt: str, safety_provider: str) -> None:
    if safety_provider == "off":
        return

    blocked_terms = SAFETY_PATTERNS.get(safety_provider, SAFETY_PATTERNS["basic"])
    hits = [term for term in blocked_terms if term in prompt]
    if hits:
        raise HTTPException(
            status_code=400,
            detail=f"内容未通过安全审核，当前策略已拦截敏感指令：{hits[0]}",
        )


def call_model(prompt: str, effective: dict[str, Any], max_tokens: int) -> str:
    provider = effective["provider"]
    model = effective["model"]
    temperature = effective["temperature"]
    top_p = effective["top_p"]
    api_key = effective["api_key"]

    if not api_key:
        raise HTTPException(status_code=400, detail=f"{effective['provider_label']} API Key 未配置")

    if provider == "openai":
        openai.api_key = api_key
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    if provider == "zhipu":
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    if provider == "deepseek":
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    raise HTTPException(status_code=400, detail="不支持的模型提供商")


def generate_clean_content(
    prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: int = 2000,
):
    effective = get_effective_generation_settings(
        {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
        }
    )
    run_safety_review(prompt, effective["safety_provider"])
    raw = call_model(prompt, effective, max_tokens=max_tokens)
    text = clean_text_output(raw)
    if looks_garbled(text):
        raise ValueError("模型返回内容疑似乱码")
    return text, effective


def build_character_fallback(idea: str) -> str:
    story_seed = clean_text_output(idea)[:200] or "一部悬疑感强、人物动机清晰的电影故事"
    return clean_text_output(
        f"""主要人物设定

故事核心：
{story_seed}

1. 主角
姓名：林澈
身份：与核心事件有直接关联的调查者或幸存者
目标：查清真相，阻止旧事件再次发生
内在矛盾：理性强硬，但长期被愧疚和创伤压制
人物弧光：从逃避过去，走向主动面对并做出牺牲性的选择

2. 对手人物
姓名：顾南舟
身份：与往事深度绑定的关键人物
目标：守住自己当年留下的计划或秘密
外在冲突：与主角在真相、责任和结果上正面冲突
人物功能：持续制造反转，让剧情保持悬疑压力

3. 协助人物
姓名：周牧
身份：行动执行者或现实派盟友
目标：保证任务完成，让主角活着回来
人物特点：冷静、克制、重行动
人物功能：提供现实视角，也在关键时刻推动主角做决定

4. 年轻观察者
姓名：唐弈
身份：技术分析或信息整理角色
目标：证明自己，参与真相揭示
人物特点：敏锐、冲动、好奇心强
人物功能：负责发现线索，也承担误判和试错
"""
    )


def build_outline_fallback(idea: str, characters: str) -> str:
    story_seed = clean_text_output(idea)[:220] or "一个在封闭空间中逐层揭示真相的悬疑故事"
    character_seed = clean_text_output(characters)[:180]
    return clean_text_output(
        f"""三幕式剧情大纲

故事核心：
{story_seed}

人物基础：
{character_seed or "主角、对手和协助者之间形成持续升级的对抗关系。"}

第一幕：
主角被异常事件重新卷入旧案。故事迅速建立悬念，抛出求救信号、失踪者踪迹或异常装置复活等钩子。主角在不愿回头和必须行动之间做出选择，正式踏入危险区域。

第二幕：
调查不断深入，隐藏多年的实验、事故或背叛逐步浮出水面。人物关系开始撕裂，盟友之间出现信息不对称和价值冲突。主角发现真正的对手并非表面上的敌人，而是当年被掩盖的系统性错误。

第三幕：
真相在高压环境下集中爆发。主角必须在揭露真相、保护他人、承担后果之间做最终选择。结尾完成一次情感和信息双反转，留下带余味的开放式收束。

高潮建议：
把人物的内在创伤和外在灾难放到同一场戏里解决，让高潮既是行动场面，也是人物弧光的兑现。
"""
    )


def build_script_fallback(idea: str, characters: str, outline: str) -> str:
    story_seed = clean_text_output(idea)[:200] or "一个氛围压迫、人物命运强烈碰撞的电影故事"
    outline_seed = clean_text_output(outline)[:180]
    character_seed = clean_text_output(characters)[:160]
    return clean_text_output(
        f"""剧本正文

故事设定：
{story_seed}

人物线索：
{character_seed or "主角和关键对手围绕旧案真相展开对抗。"}

剧情方向：
{outline_seed or "故事从异常事件开始，在调查中持续升级，最终以真相反转收束。"}

第一幕·第1节
第1场
外景 海边废弃设施 夜
承接上节：故事开端，建立人物关系与核心冲突。

暴雨压着海面，远处的旧灯塔忽明忽暗，像在黑暗里呼吸。废弃多年后，它突然恢复供电，顶端探照灯缓慢转动，划破海雾。

第一幕·第2节
第2场
内景 主角公寓 夜
承接上节：主角从外部异象转入个人危机。

主角独自坐在电脑前，屏幕上跳出一段未知来源的加密讯号。她起初以为这是恶作剧，但随着波形展开，她听见一个本不该再出现的声音。那一刻，她意识到过去没有结束。

第一幕·第3节
第3场
外景 港口码头 夜
承接上节：主角做出行动选择，正式进入主线。

主角带着设备赶往码头，与行动团队会合。所有人都知道这不是普通搜救，却没有人愿意先说破。船只离岸时，风浪更大，真正的故事也正式开始。
"""
    )


def _act_section_by_scene_index(index: int) -> tuple[str, int]:
    if index <= 3:
        return "第一幕", index
    if index <= 7:
        return "第二幕", index - 3
    if index <= 10:
        return "第三幕", index - 7
    return "结局", index - 10


def enforce_script_labels(text: str) -> str:
    cleaned = clean_text_output(text)
    if not cleaned:
        return cleaned

    if re.search(r"(第一幕|第二幕|第三幕|结局)·第\d+节", cleaned):
        return cleaned

    lines = [line for line in cleaned.split("\n")]
    rebuilt: list[str] = []
    scene_index = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("内景", "外景")):
            scene_index += 1
            act_label, section_idx = _act_section_by_scene_index(scene_index)
            rebuilt.append(f"{act_label}·第{section_idx}节")
            rebuilt.append(f"第{scene_index}场")
            rebuilt.append(stripped)
            if scene_index == 1:
                rebuilt.append("承接上节：故事开端，建立人物关系与核心冲突。")
            else:
                rebuilt.append("承接上节：延续上一场冲突，推动情节升级。")
            continue

        rebuilt.append(line)

    return clean_text_output("\n".join(rebuilt))


def build_general_fallback(prompt: str) -> str:
    cleaned_prompt = clean_text_output(prompt)[:260]
    if any(keyword in prompt for keyword in ("剧本", "场景", "对白", "人物", "故事")):
        return build_script_fallback(cleaned_prompt, "", "")

    if any(keyword in prompt for keyword in ("分析", "问题", "结构", "伏笔")):
        return clean_text_output(
            f"""内容分析

当前请求：
{cleaned_prompt or "请分析当前文本内容。"}

基础判断：
文本已经具备明确主题和推进方向，后续建议继续补强人物动机、冲突升级和结果收束三部分。

优化建议：
第一，明确主角的具体目标和代价。
第二，让中段冲突持续升级，避免信息重复。
第三，在结尾安排一次情感和信息双重兑现。
"""
        )

    return clean_text_output(
        f"""基础中文草稿

你的请求核心：
{cleaned_prompt or "请生成一段稳定、清晰的中文内容。"}

系统已根据当前输入生成一版可继续编辑的中文草稿。你可以直接在此基础上补充细节、语气和结构要求，然后继续迭代。
"""
    )


def build_meta(effective: dict[str, Any], mode: str, stage: str, note: Optional[str] = None):
    meta = {
        "stage": stage,
        "mode": mode,
        "provider": effective["provider"],
        "provider_label": effective["provider_label"],
        "model": effective["model"],
        "temperature": effective["temperature"],
        "top_p": effective["top_p"],
        "safety_provider": effective["safety_provider"],
        "safety_label": effective["safety_label"],
        "provider_ready": effective["provider_ready"],
    }
    if note:
        meta["note"] = note
    return meta


def attach_rule_validation(meta: dict[str, Any], validation: dict[str, Any], corrected: bool = False):
    meta["rule_validation"] = {
        "is_valid": validation["is_valid"],
        "hard_errors": validation["hard_errors"],
        "soft_warnings": validation["soft_warnings"],
        "metrics": validation["metrics"],
        "corrected": corrected,
    }
    return meta


def build_correction_prompt(base_prompt: str, hard_errors: list[dict[str, str]]) -> str:
    fix_lines = [f"- {item.get('fix_instruction', '')}" for item in hard_errors if item.get("fix_instruction")]
    if not fix_lines:
        return base_prompt

    return (
        f"{base_prompt}\n\n"
        "请执行以下强制合规修正（必须全部满足）：\n"
        f"{'\n'.join(fix_lines)}\n"
        "输出最终修正版，不要解释。"
    )


def build_characters_prompt(idea: str) -> str:
    return f"""你是一名专业中文电影编剧策划。
请根据下面的核心设定，输出纯中文的人物设定。

要求：
1. 只输出中文，不要使用 Markdown，不要出现星号、井号、代码块。
2. 不要写英文场景标记，不要写多余说明。
3. 内容包括：主角、对手人物、协助人物、关键关系、每个人的目标与矛盾。
4. 语气专业、清晰，便于后续继续生成剧情。

核心设定：
{idea}
"""


def build_outline_prompt(idea: str, characters: str) -> str:
    return f"""你是一名专业中文电影编剧。
请根据核心设定和人物设定，输出纯中文三幕式剧情大纲。

要求：
1. 只输出中文，不要使用 Markdown，不要出现星号、井号、代码块。
2. 大纲必须包含：第一幕、第二幕、第三幕、高潮、结局余韵。
3. 每一幕都要突出主要矛盾的升级。
4. 文风简洁、准确、具有电影感。

核心设定：
{idea}

人物设定：
{characters}
"""


def build_script_prompt(idea: str, characters: str, outline: str) -> str:
    return f"""你是一名专业中文电影编剧。
请根据以下资料，直接输出剧本前几场的正文内容。

要求：
1. 只输出中文，不要使用 Markdown，不要出现星号、井号、代码块。
2. 使用规范中文剧本写法，格式使用“幕节标签 + 场次标题 + 动作描述 + 人物对白”。
3. 每一场必须先写“第一幕·第1节/第二幕·第2节/第三幕·第1节/结局·第1节”这类标签，明确属于哪一幕的第几节。
4. 场次标题使用中文，例如“外景 港口 夜”或“内景 公寓 夜”。
5. 每场必须写“承接上节：xxx”，说明与上一场如何衔接，避免跳场。
6. 人物对白自然，动作描写具体，悬念感明确。
7. 输出至少三场戏，确保可以直接在编辑器里继续改写。

核心设定：
{idea}

人物设定：
{characters}

剧情大纲：
{outline}
"""


@router.get("/runtime-settings")
def get_runtime_settings():
    ensure_runtime_settings_file()
    return load_runtime_settings(include_secrets=False)


@router.post("/runtime-settings")
def update_runtime_settings(request: RuntimeSettingsUpdateRequest):
    return save_runtime_settings(request.model_dump(exclude_none=True))


@router.post("/generate")
def generate(request: AIGenerateRequest):
    try:
        content, effective = generate_clean_content(
            request.prompt,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        return {"content": content, "meta": build_meta(effective, "model", "generate")}
    except HTTPException:
        raise
    except Exception as exc:
        effective = get_effective_generation_settings(
            {
                "model": request.model,
                "temperature": request.temperature,
                "top_p": request.top_p,
            }
        )
        content = build_general_fallback(request.prompt)
        return {"content": content, "meta": build_meta(effective, "fallback", "generate", note=str(exc))}


@router.post("/function-call")
def function_call(request: AIFunctionCallRequest):
    try:
        effective = get_effective_generation_settings({"model": request.model})
        if effective["provider"] != "openai":
            raise HTTPException(status_code=400, detail="函数调用目前仅支持 OpenAI 模型")
        if not effective["api_key"]:
            raise HTTPException(status_code=400, detail="OpenAI API Key 未配置")

        openai.api_key = effective["api_key"]
        response = openai.chat.completions.create(
            model=effective["model"],
            messages=[{"role": "user", "content": request.prompt}],
            functions=request.functions,
            function_call="auto",
        )
        return {"response": response.model_dump(), "meta": build_meta(effective, "model", "function_call")}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate-script")
def generate_script(prompt: str, model: Optional[str] = None):
    try:
        script_prompt = (
            "请将以下故事构想整理为一段可直接进入写作阶段的中文剧本正文。"
            "只输出中文，不要使用 Markdown，不要出现星号或代码块。\n\n"
            f"{prompt}"
        )
        content, effective = generate_clean_content(script_prompt, model=model, max_tokens=3000)
        return {"script": content, "meta": build_meta(effective, "model", "generate_script")}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze-plot")
def analyze_plot(request: AnalyzePlotRequest):
    try:
        analyze_prompt = (
            "请用中文分析下面剧本的主要冲突、人物动机、伏笔和可能的结构问题。"
            "只输出中文，不要使用 Markdown，不要出现星号或代码块。\n\n"
            f"{request.script}"
        )
        content, effective = generate_clean_content(analyze_prompt, model=request.model, max_tokens=2500)
        return {"analysis": content, "meta": build_meta(effective, "model", "analyze_plot")}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/narrative/characters")
def generate_characters_api(req: CharacterRequest):
    prompt = build_characters_prompt(req.idea)
    try:
        content, effective = generate_clean_content(
            prompt,
            max_tokens=2200,
        )
        validation = rule_engine.evaluate(content, stage="characters", idea=req.idea)
        corrected = False

        if not validation["is_valid"]:
            corrected_prompt = build_correction_prompt(prompt, validation["hard_errors"])
            content, effective = generate_clean_content(corrected_prompt, max_tokens=2200)
            validation = rule_engine.evaluate(content, stage="characters", idea=req.idea)
            corrected = True

        meta = build_meta(effective, "model", "characters")
        attach_rule_validation(meta, validation, corrected=corrected)
        return {"characters": content, "meta": meta}
    except Exception as exc:
        effective = get_effective_generation_settings()
        fallback = build_character_fallback(req.idea)
        fallback_validation = rule_engine.evaluate(fallback, stage="characters", idea=req.idea)
        meta = build_meta(effective, "fallback", "characters", note=str(exc))
        attach_rule_validation(meta, fallback_validation, corrected=False)
        return {
            "characters": fallback,
            "meta": meta,
        }


@router.post("/narrative/outline")
def generate_outline_api(req: OutlineRequest):
    prompt = build_outline_prompt(req.idea, req.characters)
    try:
        content, effective = generate_clean_content(
            prompt,
            max_tokens=2600,
        )
        validation = rule_engine.evaluate(
            content,
            stage="outline",
            idea=req.idea,
            characters=req.characters,
        )
        corrected = False

        if not validation["is_valid"]:
            corrected_prompt = build_correction_prompt(prompt, validation["hard_errors"])
            content, effective = generate_clean_content(corrected_prompt, max_tokens=2600)
            validation = rule_engine.evaluate(
                content,
                stage="outline",
                idea=req.idea,
                characters=req.characters,
            )
            corrected = True

        meta = build_meta(effective, "model", "outline")
        attach_rule_validation(meta, validation, corrected=corrected)
        return {"outline": content, "meta": meta}
    except Exception as exc:
        effective = get_effective_generation_settings()
        fallback = build_outline_fallback(req.idea, req.characters)
        fallback_validation = rule_engine.evaluate(
            fallback,
            stage="outline",
            idea=req.idea,
            characters=req.characters,
        )
        meta = build_meta(effective, "fallback", "outline", note=str(exc))
        attach_rule_validation(meta, fallback_validation, corrected=False)
        return {
            "outline": fallback,
            "meta": meta,
        }


@router.post("/narrative/script")
def generate_pipeline_script_api(req: PipelineScriptRequest):
    prompt = build_script_prompt(req.idea, req.characters, req.outline)
    try:
        content, effective = generate_clean_content(
            prompt,
            max_tokens=3200,
        )
        content = enforce_script_labels(content)
        validation = rule_engine.evaluate(
            content,
            stage="script",
            idea=req.idea,
            characters=req.characters,
        )
        corrected = False

        if not validation["is_valid"]:
            corrected_prompt = build_correction_prompt(prompt, validation["hard_errors"])
            content, effective = generate_clean_content(corrected_prompt, max_tokens=3200)
            content = enforce_script_labels(content)
            validation = rule_engine.evaluate(
                content,
                stage="script",
                idea=req.idea,
                characters=req.characters,
            )
            corrected = True

        meta = build_meta(effective, "model", "script")
        attach_rule_validation(meta, validation, corrected=corrected)
        return {"script": content, "meta": meta}
    except Exception as exc:
        effective = get_effective_generation_settings()
        fallback = build_script_fallback(req.idea, req.characters, req.outline)
        fallback = enforce_script_labels(fallback)
        fallback_validation = rule_engine.evaluate(
            fallback,
            stage="script",
            idea=req.idea,
            characters=req.characters,
        )
        meta = build_meta(effective, "fallback", "script", note=str(exc))
        attach_rule_validation(meta, fallback_validation, corrected=False)
        return {
            "script": fallback,
            "meta": meta,
        }
