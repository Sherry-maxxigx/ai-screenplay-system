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
    current_scene: int = 1


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


def build_script_prompt(idea: str, characters: str, outline: str, current_scene: int = 1) -> str:
    stage_hint = (
        "请从故事开端写起，直接生成可继续续写的开篇 2 到 3 场。"
        if current_scene <= 1
        else f"当前已经写到第 {max(1, current_scene - 1)} 场，请继续往后写新的 1 到 2 场，不要重复前文。"
    )

    return f"""你是一名专业中文电影编剧。
请根据以下资料，直接输出一段可继续接力创作的剧本正文。

要求：
1. 只输出中文，不要使用 Markdown，不要出现星号、井号、代码块。
2. 使用规范中文剧本写法，格式使用“幕节标签 + 场次标题 + 动作描述 + 人物对白”。
3. 每一场必须先写“第一幕·第1节/第二幕·第2节/第三幕·第1节/结局·第1节”这类标签，明确属于哪一幕的第几节。
4. 场次标题使用中文，例如“外景 港口 夜”或“内景 公寓 夜”。
5. 每场必须写“承接上节：xxx”，说明与上一场如何衔接，避免跳场。
6. 人物对白自然，动作描写具体，悬念感明确。
7. 不要预设固定总场次，不要写“第15场才结束”这类外部规划，是否收束只由剧情大纲决定。
8. 严格按照剧情大纲的先后顺序推进，不要重复已经发生过的信息或场景。
9. 不要把大纲逐句改写成摘要，要把每一场写成真正发生的戏：人物有目标、阻力、动作和结果。
10. 当前这次只写需要落地的开篇几场，优先把第一幕前两个关键节点写扎实，不要一上来就把后面的大纲匆忙写碎。

当前进度：
- 当前场次：第 {current_scene} 场
- 写作任务：{stage_hint}

核心设定：
{idea}

人物设定：
{characters}

剧情大纲：
{outline}
"""


def _generate_outline_aligned_opening(
    outline: str,
    characters: str,
    current_scene: int = 1,
) -> Optional[dict[str, Any]]:
    cleaned_outline = clean_text_output(outline)
    if not cleaned_outline:
        return None

    from app.api import narrative as narrative_api

    beats_to_generate = 3 if current_scene <= 1 else 2
    generation = narrative_api._generate_outline_aligned_beats(
        "",
        outline=cleaned_outline,
        characters=characters,
        max_beats=beats_to_generate,
    )
    script = narrative_api._normalize_script(generation.get("merged_content") or generation.get("text") or "")
    if not script:
        return None

    completion = generation.get("completion") or narrative_api._evaluate_script_completion(script, cleaned_outline)
    return {
        "script": enforce_script_labels(script),
        "completion": completion,
        "generation_mode": "outline_aligned_sequence",
        "generated_scene_count": generation.get("generated_count", 0),
    }


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


def extract_suggestions_from_text(text, script_content):
    import re
    suggestions = []
    
    lines = script_content.strip().split('\n')
    
    pattern = r'(\d+)[、.．]\s*(.+?)(?:[:：]\s*)(.+?)(?:。|$)'
    matches = re.findall(pattern, text)
    
    for i, match in enumerate(matches[:5]):
        raw_type, desc = match[1], match[2]
        
        type_map = {
            '冲突': '冲突优化', '矛盾': '冲突优化',
            '人物': '人物动机', '动机': '人物动机', '角色': '人物动机',
            '伏笔': '伏笔埋设', '铺垫': '伏笔埋设',
            '结构': '结构调整', '节奏': '结构调整',
            '对白': '对白优化', '对话': '对白优化', '台词': '对白优化',
        }
        
        sug_type = '结构调整'
        for k, v in type_map.items():
            if k in raw_type or k in desc:
                sug_type = v
                break
        
        line_idx = min(i * 3 + 2, len(lines) - 1)
        
        suggestions.append({
            "id": i + 1,
            "type": sug_type,
            "description": desc[:80],
            "before": lines[line_idx] if line_idx < len(lines) else lines[-1],
            "after": f"【优化】{lines[line_idx] if line_idx < len(lines) else ''}（点击按钮自动优化）",
            "confidence": 0.8
        })
    
    return suggestions


def build_plot_advice_fallback(script: str) -> dict[str, Any]:
    cleaned = clean_text_output(script)
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    if not lines:
        return {
            "analysis": "当前文本为空，建议先生成人物、大纲或剧本内容后再进行分析。",
            "suggestions": [],
        }

    total_lines = len(lines)
    scene_like_lines = [line for line in lines if line.startswith(("第", "内景", "外景", "第一幕", "第二幕", "第三幕"))]

    def pick_line(index: int) -> str:
        if not lines:
            return ""
        index = max(0, min(index, len(lines) - 1))
        return lines[index]

    suggestions = []
    preset = [
        (
            "结构调整",
            "建议在前 1/3 位置补一个更强的转折点，让主角更早做出不可逆选择。",
            1,
            "【结构优化】这一段之后插入一个更明确的外部事件，迫使主角立刻行动。",
        ),
        (
            "人物动机",
            "可以把主角的目标、代价和恐惧再写得更明确，后续冲突会更有牵引力。",
            total_lines // 2,
            "【人物强化】补出主角此刻最害怕失去的东西，并让行动目标更具体。",
        ),
        (
            "冲突优化",
            "建议在后半段增加一次正面碰撞或信息反转，避免推进过于平缓。",
            max(total_lines - 2, 0),
            "【冲突升级】在这里加入一次关键对抗或真相揭露，让剧情压强明显抬升。",
        ),
    ]

    for idx, (s_type, description, line_index, after_tip) in enumerate(preset, start=1):
        before = pick_line(line_index)
        if not before:
            continue
        suggestions.append(
            {
                "id": idx,
                "type": s_type,
                "description": description,
                "before": before,
                "after": f"{before}\n{after_tip}",
                "confidence": 0.78,
            }
        )

    summary = (
        f"当前文本共 {total_lines} 行，可识别到 {len(scene_like_lines)} 处结构节点。"
        "已返回系统兜底建议，可直接一键应用后继续改写。"
    )

    return {
        "analysis": summary,
        "suggestions": suggestions,
    }


@router.post("/analyze-plot")
def analyze_plot(request: AnalyzePlotRequest):
    try:
        analyze_prompt = f"""
你是专业的剧本编审。

!!! 最重要的规则：你必须输出合法的JSON格式，其他任何文字都不要写！!!!

输出要求：
1. 第一字符必须是左大括号，最后一个字符必须是右大括号
2. 绝对不能写任何解释、说明文字
3. 绝对不能写```json或者任何代码标记
4. 找出剧本的3-5个具体修改点

每条建议必须包含：
- type: 只能是【冲突优化、人物动机、伏笔埋设、结构调整、对白优化】五选一
- description: 详细说明为什么要改
- before: 原文中的完整一行，必须能搜索到
- after: 修改后的完整文本

严格按照下面的JSON格式输出：
{{
  "summary": "剧本整体分析总结",
  "suggestions": [
    {{
      "id": 1,
      "type": "冲突优化",
      "description": "这里冲突不够强烈，建议加强戏剧张力",
      "before": "林默看着窗外没有说话",
      "after": "林默指尖深深掐进掌心，指缝渗出鲜血却浑然不觉",
      "confidence": 0.95
    }}
  ]
}}

剧本内容：
{request.script}
"""
        content, effective = generate_clean_content(analyze_prompt, model=request.model, max_tokens=3000)
        
        try:
            import json
            start = content.find('{')
            end = content.rfind('}') + 1
            json_str = content[start:end]
            result = json.loads(json_str)
            
            suggestions = result.get("suggestions", [])
            if not suggestions:
                suggestions = extract_suggestions_from_text(content, request.script)
                
            return {
                "analysis": result.get("summary", content[:200]),
                "suggestions": suggestions,
                "raw_text": content,
                "meta": build_meta(effective, "model", "analyze_plot")
            }
        except Exception as e:
            fallback_suggestions = extract_suggestions_from_text(content, request.script)
            
            return {
                "analysis": content,
                "suggestions": fallback_suggestions,
                "meta": build_meta(effective, "model", "analyze_plot")
            }
            
    except HTTPException:
        raise
    except Exception as exc:
        fallback = build_plot_advice_fallback(request.script)
        effective = get_effective_generation_settings({"model": request.model})
        return {
            "analysis": fallback["analysis"],
            "suggestions": fallback["suggestions"],
            "meta": build_meta(effective, "fallback", "analyze_plot", note=str(exc)),
        }


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
    prompt = build_script_prompt(req.idea, req.characters, req.outline, req.current_scene)
    try:
        effective = get_effective_generation_settings()
        content = ""
        completion = None
        corrected = False
        opening_result = _generate_outline_aligned_opening(req.outline, req.characters, req.current_scene)

        if opening_result:
            content = opening_result["script"]
            completion = opening_result.get("completion")
        else:
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

        if not validation["is_valid"] and not opening_result:
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

        if completion is None and req.outline.strip():
            from app.api import narrative as narrative_api

            completion = narrative_api._evaluate_script_completion(content, req.outline)

        meta = build_meta(effective, "model", "script")
        meta["generation_mode"] = (
            opening_result.get("generation_mode", "prompt_generation") if opening_result else "prompt_generation"
        )
        if opening_result and opening_result.get("generated_scene_count"):
            meta["generated_scene_count"] = opening_result["generated_scene_count"]
        attach_rule_validation(meta, validation, corrected=corrected)
        return {
            "script": content,
            "meta": meta,
            "completion": completion,
            "is_end": bool(completion.get("is_complete")) if completion else False,
        }
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
            "completion": None,
            "is_end": False,
        }
