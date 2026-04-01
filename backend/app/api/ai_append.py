
class CharacterRequest(BaseModel):
    idea: str

class OutlineRequest(BaseModel):
    idea: str
    characters: str

class PipelineScriptRequest(BaseModel):
    idea: str
    characters: str
    outline: str

@router.post("/narrative/characters")
def generate_characters_api(req: CharacterRequest):
    prompt = f"你是一个专业的编剧助手。根据以下用户提供的故事构想，生成详细的核心人物画像（包括外貌、性格、背景、动机）。\n故事构想：\n{req.idea}"
    try:
        content = generate_content(prompt, model="gpt-4o")
        return {"characters": content}
    except Exception as e:
        print(f"Error: {e}")
        return {"characters": "【角色1】 \n姓名：主角\n性格：坚韧...\n背景：一位失忆的机械师。\n【系统提示：当前API报错，使用演示数据】\n报错信息：" + str(e)}

@router.post("/narrative/outline")
def generate_outline_api(req: OutlineRequest):
    prompt = f"根据故事构想和人物画像，生成一个结构清晰、引人入胜的剧本大纲（包含起承转合）：\n\n【故事构想】：\n{req.idea}\n\n【人物画像】：\n{req.characters}"
    try:
        content = generate_content(prompt, model="gpt-4o")
        return {"outline": content}
    except Exception as e:
        return {"outline": "【第一幕】：主角在太空舱醒来，失去记忆...\n【第二幕】：发现危机...\n【第三幕】：解决危机并反转。\n【系统提示：当前API报错，使用演示数据】"}

@router.post("/narrative/script")
def generate_pipeline_script_api(req: PipelineScriptRequest):
    prompt = f"根据以上资料，撰写第一场戏的完整专业电影剧本格式（含场景标题、动作描述、人物对白）：\n\n【故事大纲】：\n{req.outline}\n\n【人物画像】：\n{req.characters}"
    try:
        content = generate_content(prompt, model="gpt-4o")
        return {"script": content}
    except Exception as e:
        return {"script": "外景. 破败的太空站 - 夜\n\n黑暗中，只有仪表的红光在闪烁。静谧被沉重的喘息声打破。\n\n机械师\n（咳嗽）\n这...这里是哪里？\n\n【系统提示：当前API报错，使用演示数据】"}
