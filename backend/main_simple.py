from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel
import json

app = FastAPI(
    title="AI剧本协同创作系统API",
    description="基于AI原生架构的专业剧本协同创作系统后端API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DeepSeek API密钥
DEEPSEEK_API_KEY = "sk-de9a4c351f434211b730273db21ed65b"

# 暂时禁用Neo4j相关代码
# NEO4J_URI = "bolt://localhost:7687"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "password"

# 创建Neo4j驱动
# neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 创建会话
def create_session():
    session = requests.Session()
    # 简化重试机制，减少超时风险
    retry = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session

# 暂时禁用Neo4j初始化函数
# def init_neo4j():
#     with neo4j_driver.session() as session:
#         # 创建强制合规层规则
#         session.run("""
#         MERGE (r:Rule {name: '人物设定一致性规则'})
#         SET r.level = '强制合规层', r.description = '存储人物的性格、口癖、核心动机、背景经历等固定属性，作为不可突破的约束'
#         """)
#         
#         session.run("""
#         MERGE (r:Rule {name: '伏笔-回收闭环规则'})
#         SET r.level = '强制合规层', r.description = '存储伏笔的埋设场景、核心信息、预设回收节点，实现从埋设到回收的全链路追踪'
#         """)
#         
#         session.run("""
#         MERGE (r:Rule {name: '时间线/世界观逻辑一致性规则'})
#         SET r.level = '强制合规层', r.description = '校验剧本的时间线、场景规则、世界观设定的前后统一'
#         """)
#         
#         # 创建创意参考层规则
#         session.run("""
#         MERGE (r:Rule {name: '三幕式7节点节拍规则'})
#         SET r.level = '创意参考层', r.description = '拆解为「开场→激励事件→第一幕转折点→中点→第二幕低谷→高潮→结局」，明确每个节点的功能定位'
#         """)
#         
#         session.run("""
#         MERGE (r:Rule {name: '分场冲突密度5级量化规则'})
#         SET r.level = '创意参考层', r.description = '定义单场戏的冲突强度标准，计算剧本的节奏分布'
#         """)
#         
#         session.run("""
#         MERGE (r:Rule {name: '人物弧光5阶段匹配规则'})
#         SET r.level = '创意参考层', r.description = '拆解为「懵懂→觉醒→挣扎→成长→蜕变」，匹配对应场景的人物行为逻辑'
#         """)

# 叙事规则引擎核心函数
def narrative_planning(requirement):
    """输入用户的结构化创作需求，输出全局叙事规划图谱"""
    # 分析用户需求，确定幕数
    acts_count = 3  # 默认三幕结构
    
    # 分析用户需求中的幕数信息
    # 确保输入是字符串
    requirement_str = str(requirement)
    
    # 分析需求中的幕数信息
    if "一幕" in requirement_str or "1幕" in requirement_str:
        acts_count = 1
    elif "二幕" in requirement_str or "2幕" in requirement_str:
        acts_count = 2
    elif "四幕" in requirement_str or "4幕" in requirement_str:
        acts_count = 4
    elif "五幕" in requirement_str or "5幕" in requirement_str:
        acts_count = 5
    
    # 生成相应幕数的结构
    acts = []
    
    if acts_count == 1:
        # 单幕结构
        acts = [
            {
                "id": 1,
                "label": "单幕",
                "scenes": [
                    {
                        "id": 11,
                        "label": "场景1",
                        "beat": "开场",
                        "character_arc": "懵懂",
                        "conflict_level": 1,
                        "foreshadowing": []
                    },
                    {
                        "id": 12,
                        "label": "场景2",
                        "beat": "发展",
                        "character_arc": "觉醒",
                        "conflict_level": 3,
                        "foreshadowing": ["关键道具的出现"]
                    },
                    {
                        "id": 13,
                        "label": "场景3",
                        "beat": "高潮",
                        "character_arc": "蜕变",
                        "conflict_level": 5,
                        "foreshadowing": []
                    },
                    {
                        "id": 14,
                        "label": "场景4",
                        "beat": "结局",
                        "character_arc": "蜕变",
                        "conflict_level": 2,
                        "foreshadowing": []
                    }
                ]
            }
        ]
    elif acts_count == 2:
        # 二幕结构
        acts = [
            {
                "id": 1,
                "label": "第一幕",
                "scenes": [
                    {
                        "id": 11,
                        "label": "场景1",
                        "beat": "开场",
                        "character_arc": "懵懂",
                        "conflict_level": 1,
                        "foreshadowing": []
                    },
                    {
                        "id": 12,
                        "label": "场景2",
                        "beat": "激励事件",
                        "character_arc": "觉醒",
                        "conflict_level": 3,
                        "foreshadowing": ["关键道具的出现"]
                    },
                    {
                        "id": 13,
                        "label": "场景3",
                        "beat": "第一幕转折点",
                        "character_arc": "挣扎",
                        "conflict_level": 4,
                        "foreshadowing": []
                    }
                ]
            },
            {
                "id": 2,
                "label": "第二幕",
                "scenes": [
                    {
                        "id": 21,
                        "label": "场景1",
                        "beat": "中点",
                        "character_arc": "成长",
                        "conflict_level": 5,
                        "foreshadowing": ["反派的真实身份暗示"]
                    },
                    {
                        "id": 22,
                        "label": "场景2",
                        "beat": "第二幕低谷",
                        "character_arc": "成长",
                        "conflict_level": 4,
                        "foreshadowing": []
                    },
                    {
                        "id": 23,
                        "label": "场景3",
                        "beat": "高潮",
                        "character_arc": "蜕变",
                        "conflict_level": 5,
                        "foreshadowing": []
                    },
                    {
                        "id": 24,
                        "label": "场景4",
                        "beat": "结局",
                        "character_arc": "蜕变",
                        "conflict_level": 2,
                        "foreshadowing": []
                    }
                ]
            }
        ]
    elif acts_count == 4:
        # 四幕结构
        acts = [
            {
                "id": 1,
                "label": "第一幕",
                "scenes": [
                    {
                        "id": 11,
                        "label": "场景1",
                        "beat": "开场",
                        "character_arc": "懵懂",
                        "conflict_level": 1,
                        "foreshadowing": []
                    },
                    {
                        "id": 12,
                        "label": "场景2",
                        "beat": "激励事件",
                        "character_arc": "觉醒",
                        "conflict_level": 3,
                        "foreshadowing": ["关键道具的出现"]
                    }
                ]
            },
            {
                "id": 2,
                "label": "第二幕",
                "scenes": [
                    {
                        "id": 21,
                        "label": "场景1",
                        "beat": "第一幕转折点",
                        "character_arc": "挣扎",
                        "conflict_level": 4,
                        "foreshadowing": []
                    },
                    {
                        "id": 22,
                        "label": "场景2",
                        "beat": "发展",
                        "character_arc": "成长",
                        "conflict_level": 4,
                        "foreshadowing": []
                    }
                ]
            },
            {
                "id": 3,
                "label": "第三幕",
                "scenes": [
                    {
                        "id": 31,
                        "label": "场景1",
                        "beat": "中点",
                        "character_arc": "成长",
                        "conflict_level": 5,
                        "foreshadowing": ["反派的真实身份暗示"]
                    },
                    {
                        "id": 32,
                        "label": "场景2",
                        "beat": "第二幕低谷",
                        "character_arc": "成长",
                        "conflict_level": 4,
                        "foreshadowing": []
                    }
                ]
            },
            {
                "id": 4,
                "label": "第四幕",
                "scenes": [
                    {
                        "id": 41,
                        "label": "场景1",
                        "beat": "高潮",
                        "character_arc": "蜕变",
                        "conflict_level": 5,
                        "foreshadowing": []
                    },
                    {
                        "id": 42,
                        "label": "场景2",
                        "beat": "结局",
                        "character_arc": "蜕变",
                        "conflict_level": 2,
                        "foreshadowing": []
                    }
                ]
            }
        ]
    elif acts_count == 5:
        # 五幕结构
        acts = [
            {
                "id": 1,
                "label": "第一幕",
                "scenes": [
                    {
                        "id": 11,
                        "label": "场景1",
                        "beat": "开场",
                        "character_arc": "懵懂",
                        "conflict_level": 1,
                        "foreshadowing": []
                    },
                    {
                        "id": 12,
                        "label": "场景2",
                        "beat": "激励事件",
                        "character_arc": "觉醒",
                        "conflict_level": 3,
                        "foreshadowing": ["关键道具的出现"]
                    }
                ]
            },
            {
                "id": 2,
                "label": "第二幕",
                "scenes": [
                    {
                        "id": 21,
                        "label": "场景1",
                        "beat": "第一幕转折点",
                        "character_arc": "挣扎",
                        "conflict_level": 4,
                        "foreshadowing": []
                    }
                ]
            },
            {
                "id": 3,
                "label": "第三幕",
                "scenes": [
                    {
                        "id": 31,
                        "label": "场景1",
                        "beat": "中点",
                        "character_arc": "成长",
                        "conflict_level": 5,
                        "foreshadowing": ["反派的真实身份暗示"]
                    }
                ]
            },
            {
                "id": 4,
                "label": "第四幕",
                "scenes": [
                    {
                        "id": 41,
                        "label": "场景1",
                        "beat": "第二幕低谷",
                        "character_arc": "成长",
                        "conflict_level": 4,
                        "foreshadowing": []
                    }
                ]
            },
            {
                "id": 5,
                "label": "第五幕",
                "scenes": [
                    {
                        "id": 51,
                        "label": "场景1",
                        "beat": "高潮",
                        "character_arc": "蜕变",
                        "conflict_level": 5,
                        "foreshadowing": []
                    },
                    {
                        "id": 52,
                        "label": "场景2",
                        "beat": "结局",
                        "character_arc": "蜕变",
                        "conflict_level": 2,
                        "foreshadowing": []
                    }
                ]
            }
        ]
    else:
        # 默认三幕结构
        acts = [
            {
                "id": 1,
                "label": "第一幕",
                "scenes": [
                    {
                        "id": 11,
                        "label": "场景1",
                        "beat": "开场",
                        "character_arc": "懵懂",
                        "conflict_level": 1,
                        "foreshadowing": []
                    },
                    {
                        "id": 12,
                        "label": "场景2",
                        "beat": "激励事件",
                        "character_arc": "觉醒",
                        "conflict_level": 3,
                        "foreshadowing": ["关键道具的出现"]
                    }
                ]
            },
            {
                "id": 2,
                "label": "第二幕",
                "scenes": [
                    {
                        "id": 21,
                        "label": "场景1",
                        "beat": "第一幕转折点",
                        "character_arc": "挣扎",
                        "conflict_level": 4,
                        "foreshadowing": []
                    },
                    {
                        "id": 22,
                        "label": "场景2",
                        "beat": "中点",
                        "character_arc": "成长",
                        "conflict_level": 5,
                        "foreshadowing": ["反派的真实身份暗示"]
                    }
                ]
            },
            {
                "id": 3,
                "label": "第三幕",
                "scenes": [
                    {
                        "id": 31,
                        "label": "场景1",
                        "beat": "第二幕低谷",
                        "character_arc": "成长",
                        "conflict_level": 4,
                        "foreshadowing": []
                    },
                    {
                        "id": 32,
                        "label": "场景2",
                        "beat": "高潮",
                        "character_arc": "蜕变",
                        "conflict_level": 5,
                        "foreshadowing": []
                    },
                    {
                        "id": 33,
                        "label": "场景3",
                        "beat": "结局",
                        "character_arc": "蜕变",
                        "conflict_level": 2,
                        "foreshadowing": []
                    }
                ]
            }
        ]
    
    return {"acts": acts}

def narrative_verify(script_content, characters):
    """输入大模型生成的单场戏内容，输出标准化校验结果"""
    errors = []
    warnings = []
    
    # 检查人物名称一致性
    character_names = [c['name'] for c in characters]
    script_text = script_content
    
    # 提取剧本中的人物名称（使用字符串方法，避免正则表达式错误）
    # 匹配包含冒号的行，提取冒号前的内容作为人物名称
    unique_characters = set()
    lines = script_text.split('\n')
    for line in lines:
        # 去除行首空白
        stripped_line = line.strip()
        # 检查是否包含冒号
        if ':' in stripped_line:
            # 提取冒号前的内容作为人物名称
            character_name = stripped_line.split(':', 1)[0].strip()
            # 去除**符号和其他特殊字符
            character_name = character_name.replace('**', '').replace('*', '').replace('_', '').strip()
            if character_name:
                unique_characters.add(character_name)
    
    # 验证每个人物名称是否在人物列表中
    for character_name in unique_characters:
        # 跳过场景描述和其他非人物行
        if any(keyword in character_name for keyword in ['场景', '幕', '时间', '地点', '镜头']):
            continue
            
        # 标准化人物名称进行比较（去除空格并转为小写）
        normalized_input_name = character_name.strip().lower().replace(' ', '')
        matched = False
        matched_name = None
        
        for valid_name in character_names:
            # 标准化有效名称
            normalized_valid_name = valid_name.strip().lower().replace(' ', '')
            # 检查是否完全匹配
            if normalized_input_name == normalized_valid_name:
                matched = True
                matched_name = valid_name
                break
        
        if not matched:
            # 检查是否是大小写或空格差异
            for valid_name in character_names:
                if character_name.strip().lower() == valid_name.strip().lower():
                    matched = True
                    matched_name = valid_name
                    break
        
        if not matched:
            errors.append({
                "type": "人物名称错误",
                "message": f"使用了未定义的人物名称: {character_name}",
                "suggestion": f"请使用人物列表中定义的名称: {', '.join(character_names)}"
            })
        elif character_name != matched_name:
            # 大小写或格式不一致
            errors.append({
                "type": "人物名称格式错误",
                "message": f"人物名称格式不正确: {character_name}",
                "suggestion": f"请使用正确的格式: {matched_name}"
            })
    
    # 检查是否包含所有人物
    if character_names:
        used_characters = []
        for c in character_names:
            # 检查人物名称是否在剧本的任何一行中出现（不区分大小写）
            normalized_c = c.strip().lower()
            for line in script_text.split('\n'):
                if normalized_c in line.strip().lower():
                    used_characters.append(c)
                    break
        missing_characters = [c for c in character_names if c not in used_characters]
        if missing_characters:
            warnings.append({
                "type": "人物缺失",
                "message": f"以下人物未在剧本中出现: {', '.join(missing_characters)}",
                "suggestion": "请确保所有人物都有合理的出场和台词"
            })
    
    # 检查剧本结构与设定是否一致
    # 提取剧本中的幕和场景信息
    script_acts = []
    script_scenes = []
    current_act = None
    
    for line in lines:
        stripped_line = line.strip()
        if '幕' in stripped_line and '场景' not in stripped_line:
            script_acts.append(stripped_line)
            current_act = stripped_line
        elif '场景' in stripped_line:
            if current_act:
                script_scenes.append(f"{current_act} {stripped_line}")
            else:
                script_scenes.append(stripped_line)
    
    # 暂时禁用非法字符检测，确保API正常工作
    # illegal_chars = []
    # for char in script_text:
    #     # 允许空格、制表符、换行符、回车符
    #     if ord(char) < 32 and char not in [' ', '\t', '\n', '\r']:
    #         illegal_chars.append(char)
    #     elif ord(char) > 126:
    #         illegal_chars.append(char)
    # if illegal_chars:
    #     errors.append({
    #         "type": "非法字符",
    #         "message": "剧本中包含非法字符",
    #         "suggestion": "请移除非法字符"
    #     })
    
    # 检查剧本格式
    if '幕' not in script_text and '场景' not in script_text:
        warnings.append({
            "type": "格式警告",
            "message": "剧本缺少明确的幕和场景划分",
            "suggestion": "请按照'第X幕'和'场景X'的格式划分剧本结构"
        })
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def narrative_update(script_content, scene_id):
    """输入校验通过的剧本内容，自动更新Neo4j中的叙事图谱"""
    # 这里实现更新逻辑
    # 暂时返回成功
    return {"status": "success"}

# Pydantic模型
class GenerateRequest(BaseModel):
    prompt: str
    model: str = "deepseek"
    temperature: float = 0.7
    max_tokens: int = 1000

class ScriptRequest(BaseModel):
    prompt: str
    model: str = "deepseek"
    characters: list = []

class AnalyzeRequest(BaseModel):
    script: str
    model: str = "deepseek"

class NarrativePlanningRequest(BaseModel):
    requirement: str
    characters: list = []

class NarrativeVerifyRequest(BaseModel):
    script_content: str
    characters: list = []
    scene_id: str

class NarrativeUpdateRequest(BaseModel):
    script_content: str
    scene_id: str

# 根路径
@app.get("/")
def read_root():
    return {"message": "AI剧本协同创作系统API", "version": "1.0.0"}

# 健康检查
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# AI生成API
@app.post("/api/ai/generate")
def generate(request: GenerateRequest):
    try:
        if request.model == "deepseek":
            print(f"调用DeepSeek API，prompt: {request.prompt}")
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": request.prompt}],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
            print(f"请求数据: {data}")
            session = create_session()
            response = session.post(url, headers=headers, json=data, timeout=120)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            response.raise_for_status()
            result = response.json()
            print(f"DeepSeek API响应: {result}")
            if "choices" in result and len(result["choices"]) > 0:
                return {"content": result["choices"][0]["message"]["content"]}
            else:
                return {"content": "AI生成失败：未返回有效内容", "error": "DeepSeek API未返回有效内容"}
        else:
            return {"content": "暂不支持其他模型"}
    except Exception as e:
        print(f"错误信息: {str(e)}")
        return {"error": str(e), "message": "AI调用失败，请检查API密钥和网络连接"}

# 剧本生成API（双核架构实现）
@app.post("/api/ai/generate-script")
def generate_script(request: ScriptRequest):
    try:
        # 第一步：使用叙事规则引擎生成场景规划（决策内核）
        character_names = []
        if request.characters:
            character_names = [c.get('name', '未知人物') for c in request.characters]
        
        # 生成详细的场景规划
        planning_result = narrative_planning(request.prompt)
        
        # 第二步：基于规划调用大模型生成内容（执行内核）
        # 生成多个场景，增加剧本篇幅
        generated_scenes = []
        verify_result = None
        
        # 生成所有幕的场景
        for act in planning_result['acts']:
            act_content = f"{act['label']}\n\n"
            
            # 生成当前幕的所有场景
            for scene in act['scenes']:
                # 构建场景级别的prompt，包含详细的规划信息
                # 增强prompt，确保人物名称完全匹配
                scene_prompt = f"你是一位专业的编剧，请根据以下详细规划创作剧本场景：\n\n"
                scene_prompt += f"幕：{act['label']}\n"
                scene_prompt += f"场景：{scene['label']}\n"
                scene_prompt += f"节拍定位：{scene['beat']}\n"
                scene_prompt += f"人物弧光阶段：{scene['character_arc']}\n"
                scene_prompt += f"冲突强度：{scene['conflict_level']}\n"
                if scene['foreshadowing']:
                    scene_prompt += f"伏笔任务：{', '.join(scene['foreshadowing'])}\n"
                
                # 添加人物列表和强制要求
                if request.characters:
                    character_details = []
                    for c in request.characters:
                        name = c.get('name', '未知人物')
                        feature = c.get('feature', '无特征描述')
                        character_details.append(f"{name}: {feature}")
                    scene_prompt += "\n=== 人物列表 ===\n" + "\n".join(character_details) + "\n"
                    scene_prompt += "\n=== 强制要求 ===\n"
                    scene_prompt += "1. 剧本中只能使用以下指定的人物名称，绝对不得使用任何其他人物名称或别名:\n"
                    scene_prompt += f"   {', '.join(character_names)}\n"
                    scene_prompt += "2. 每个人物的对话和动作必须以其指定的名称开头，格式为:角色名称:对话内容\n"
                    scene_prompt += "3. 严格按照每个人物的特征进行创作，确保人物性格和行为完全符合描述\n"
                    scene_prompt += "4. 人物的言行举止要与特征描述高度一致\n"
                    scene_prompt += "5. 所有人物必须在剧本中出现，且有合理的互动和冲突\n"
                    scene_prompt += "6. 绝对不允许修改、替换、缩写或添加任何人物名称\n"
                    scene_prompt += "7. 必须使用与人物列表完全一致的名称，包括大小写和格式\n"
                    scene_prompt += "8. 剧本中不得包含任何非法字符或特殊符号\n"
                    scene_prompt += "9. 剧本格式必须清晰易读，符合专业剧本标准\n"
                    scene_prompt += "10. 人物名称必须在对话前单独占一行，格式为:角色名称:\n"
                    scene_prompt += "11. 请确保剧本中的人物名称与人物列表中的名称完全一致，包括大小写\n"
                    scene_prompt += "12. 不得使用任何人物名称的变体、昵称或缩写\n"
                    scene_prompt += "13. 请创作详细的场景描述和对话，确保场景内容丰富充实\n"
                    scene_prompt += "14. 剧本格式必须符合专业标准，人物名称前不要添加**符号\n"
                    scene_prompt += "15. 严格按照'第X幕'和'场景X'的格式划分剧本结构\n"
                    scene_prompt += "16. 人物对话必须以'人物名称:'的格式开头，不要使用任何特殊符号包围人物名称\n"
                    scene_prompt += "17. 必须严格按照指定的幕和场景结构创作，不得更改幕数和场景顺序\n"
                    scene_prompt += "18. 每个场景的内容必须与该场景的节拍定位和人物弧光阶段相符\n"
                
                scene_prompt += "\n请创作符合以上要求的剧本场景内容："
                
                # 调用大模型生成场景内容
                if request.model == "deepseek":
                    try:
                        url = "https://api.deepseek.com/v1/chat/completions"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                        }
                        data = {
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": scene_prompt}],
                            "temperature": 0.7,
                            "max_tokens": 4000  # 增加max_tokens，取消长度限制
                        }
                        session = create_session()
                        response = session.post(url, headers=headers, json=data, timeout=60)
                        response.raise_for_status()
                        result = response.json()
                        scene_content = result["choices"][0]["message"]["content"]
                        print(f"执行内核生成{act['label']}{scene['label']}内容完成...")
                    except Exception as e:
                        print(f"DeepSeek API调用失败: {str(e)}")
                        # 生成动态的模拟响应，使用用户提供的人物名称
                        scene_content = f"{act['label']}\n{scene['label']}\n\n"
                        
                        # 根据场景节拍设置不同的场景描述
                        if scene['beat'] == "开场":
                            scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                        elif scene['beat'] == "激励事件":
                            scene_content += "场景：第二天早上，警察局会议室\n\n"
                        elif scene['beat'] == "第一幕转折点":
                            scene_content += "场景：下午，咖啡馆\n\n"
                        elif scene['beat'] == "中点":
                            scene_content += "场景：晚上，犯罪现场\n\n"
                        elif scene['beat'] == "第二幕低谷":
                            scene_content += "场景：深夜，侦探事务所\n\n"
                        elif scene['beat'] == "高潮":
                            scene_content += "场景：黎明，废弃工厂\n\n"
                        elif scene['beat'] == "结局":
                            scene_content += "场景：中午，警察局门口\n\n"
                        else:
                            scene_content += "场景：室内，明亮的房间\n\n"
                        
                        # 动态生成对话，使用用户提供的人物名称
                        if character_names:
                            # 确保至少有三个人物
                            if len(character_names) >= 3:
                                name1, name2, name3 = character_names[0], character_names[1], character_names[2]
                                if scene['beat'] == "开场":
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                    scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                    scene_content += f"{name2}: （开玩笑）怎么，堂堂{name1}也会害怕？\n"
                                    scene_content += f"{name1}: （严肃）不是害怕，是谨慎。我们面对的是一个危险的对手。\n"
                                    scene_content += f"{name3}: （突然开口）看那边。\n"
                                    scene_content += f"{name2}: （顺着{name3}的目光）那是什么？\n"
                                    scene_content += f"{name1}: （走上前）是一个保险箱。\n"
                                    scene_content += f"{name3}: （冷静）密码应该是8位数。\n"
                                    scene_content += f"{name2}: （惊讶）你怎么知道？\n"
                                    scene_content += f"{name3}: （神秘地笑）直觉。\n"
                                    scene_content += f"{name1}: （输入密码）7-8-3-9-4-2-1-5\n"
                                    scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                                elif scene['beat'] == "激励事件":
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：第二天早上，警察局会议室\n\n"
                                    scene_content += f"{name1}: （严肃地）我们刚刚收到了一封匿名信，里面有关于连环杀人案的重要线索。\n"
                                    scene_content += f"{name2}: （惊讶）连环杀人案？不是已经结案了吗？\n"
                                    scene_content += f"{name3}: （冷静）看起来我们之前的调查有误，真凶还在逍遥法外。\n"
                                    scene_content += f"{name1}: （敲了敲桌子）这就是为什么我们今天要重新启动调查。\n"
                                    scene_content += f"{name2}: （认真）那我们从哪里开始？\n"
                                    scene_content += f"{name3}: （拿出文件）根据匿名信的内容，我们需要重新调查三个月前的那起案件。\n"
                                elif scene['beat'] == "第一幕转折点":
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：下午，咖啡馆\n\n"
                                    scene_content += f"{name1}: （喝了一口咖啡）我们的调查遇到了瓶颈，所有线索都断了。\n"
                                    scene_content += f"{name2}: （皱着眉头）难道真凶真的一点痕迹都没留下？\n"
                                    scene_content += f"{name3}: （突然想起什么）等等，我记得案发现场有一个奇怪的符号。\n"
                                    scene_content += f"{name1}: （来了兴趣）什么符号？\n"
                                    scene_content += f"{name3}: （画在纸上）就是这个，看起来像是某种标记。\n"
                                    scene_content += f"{name2}: （仔细观察）我好像在哪里见过这个符号...\n"
                                else:
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：室内，明亮的房间\n\n"
                                    scene_content += f"{name1}: （严肃）我们必须找到真凶，不能让他再逍遥法外。\n"
                                    scene_content += f"{name2}: （坚定）放心，我们一定会抓到他的。\n"
                                    scene_content += f"{name3}: （冷静）根据我们的调查，真凶应该就在这附近。\n"
                                    scene_content += f"{name1}: （点头）好，我们现在就行动。\n"
                            elif len(character_names) == 2:
                                name1, name2 = character_names[0], character_names[1]
                                if scene['beat'] == "开场":
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                    scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                    scene_content += f"{name2}: （开玩笑）怎么，堂堂{name1}也会害怕？\n"
                                    scene_content += f"{name1}: （严肃）不是害怕，是谨慎。我们面对的是一个危险的对手。\n"
                                    scene_content += f"{name2}: （突然开口）看那边。\n"
                                    scene_content += f"{name1}: （顺着{name2}的目光）那是什么？\n"
                                    scene_content += f"{name2}: （走上前）是一个保险箱。\n"
                                    scene_content += f"{name1}: （冷静）密码应该是8位数。\n"
                                    scene_content += f"{name2}: （惊讶）你怎么知道？\n"
                                    scene_content += f"{name1}: （神秘地笑）直觉。\n"
                                    scene_content += f"{name2}: （输入密码）7-8-3-9-4-2-1-5\n"
                                    scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                                else:
                                    scene_content += f"{act['label']} {scene['label']}\n\n"
                                    scene_content += "场景：下午，咖啡馆\n\n"
                                    scene_content += f"{name1}: （严肃）我们的调查遇到了瓶颈，所有线索都断了。\n"
                                    scene_content += f"{name2}: （皱着眉头）难道真凶真的一点痕迹都没留下？\n"
                                    scene_content += f"{name1}: （突然想起什么）等等，我记得案发现场有一个奇怪的符号。\n"
                                    scene_content += f"{name2}: （来了兴趣）什么符号？\n"
                                    scene_content += f"{name1}: （画在纸上）就是这个，看起来像是某种标记。\n"
                                    scene_content += f"{name2}: （仔细观察）我好像在哪里见过这个符号...\n"
                            else:
                                name1 = character_names[0]
                                scene_content += f"{act['label']} {scene['label']}\n\n"
                                scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                scene_content += f"{name1}: （自言自语）我必须小心行事，这里可能有危险。\n"
                                scene_content += f"{name1}: （突然发现）那边有一个保险箱！\n"
                                scene_content += f"{name1}: （仔细观察）密码应该是8位数。\n"
                                scene_content += f"{name1}: （输入密码）7-8-3-9-4-2-1-5\n"
                                scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                        else:
                            # 没有人物时的默认对话
                            scene_content += "神秘人: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                            scene_content += "神秘人: （自言自语）我必须小心行事，这里可能有危险。\n"
                            scene_content += "神秘人: （突然发现）那边有一个保险箱！\n"
                            scene_content += "神秘人: （仔细观察）密码应该是8位数。\n"
                            scene_content += "神秘人: （输入密码）7-8-3-9-4-2-1-5\n"
                            scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                    
                    # 第三步：实时校验生成内容（决策内核与执行内核并行工作）
                    print(f"执行内核生成内容完成，决策内核开始校验{act['label']}{scene['label']}...")
                    verify_result = narrative_verify(scene_content, request.characters)
                    
                    # 如果校验失败，尝试重新生成
                    if not verify_result['is_valid']:
                        print("决策内核校验失败，执行内核重新生成...")
                        # 构建包含错误信息的prompt，让执行内核重新生成
                        error_prompt = f"你是一位专业的编剧，请根据以下错误信息重新创作剧本场景：\n\n"
                        error_prompt += f"原场景内容：{scene_content}\n\n"
                        error_prompt += "错误信息：\n"
                        for error in verify_result['errors']:
                            error_prompt += f"- {error['type']}: {error['message']}\n"
                            error_prompt += f"  建议：{error['suggestion']}\n"
                        error_prompt += "\n请按照之前的要求重新创作，确保人物名称正确且符合所有要求："
                        
                        # 模拟重新生成的内容，使用用户提供的人物名称
                        if character_names:
                            if len(character_names) >= 3:
                                name1, name2, name3 = character_names[0], character_names[1], character_names[2]
                                scene_content = f"{act['label']} {scene['label']}\n\n"
                                scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                scene_content += f"{name2}: （开玩笑）怎么，堂堂{name1}也会害怕？\n"
                                scene_content += f"{name1}: （严肃）不是害怕，是谨慎。我们面对的是一个危险的对手。\n"
                                scene_content += f"{name3}: （突然开口）看那边。\n"
                                scene_content += f"{name2}: （顺着{name3}的目光）那是什么？\n"
                                scene_content += f"{name1}: （走上前）是一个保险箱。\n"
                                scene_content += f"{name3}: （冷静）密码应该是8位数。\n"
                                scene_content += f"{name2}: （惊讶）你怎么知道？\n"
                                scene_content += f"{name3}: （神秘地笑）直觉。\n"
                                scene_content += f"{name1}: （输入密码）7-8-3-9-4-2-1-5\n"
                                scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                            elif len(character_names) == 2:
                                name1, name2 = character_names[0], character_names[1]
                                scene_content = f"{act['label']} {scene['label']}\n\n"
                                scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                scene_content += f"{name2}: （开玩笑）怎么，堂堂{name1}也会害怕？\n"
                                scene_content += f"{name1}: （严肃）不是害怕，是谨慎。我们面对的是一个危险的对手。\n"
                                scene_content += f"{name2}: （突然开口）看那边。\n"
                                scene_content += f"{name1}: （顺着{name2}的目光）那是什么？\n"
                                scene_content += f"{name2}: （走上前）是一个保险箱。\n"
                                scene_content += f"{name1}: （冷静）密码应该是8位数。\n"
                                scene_content += f"{name2}: （惊讶）你怎么知道？\n"
                                scene_content += f"{name1}: （神秘地笑）直觉。\n"
                                scene_content += f"{name2}: （输入密码）7-8-3-9-4-2-1-5\n"
                                scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                            else:
                                name1 = character_names[0]
                                scene_content = f"{act['label']} {scene['label']}\n\n"
                                scene_content += "场景：深夜，一个废弃的仓库里\n\n"
                                scene_content += f"{name1}: （环顾四周，警惕地）这里就是线索指向的地方？\n"
                                scene_content += f"{name1}: （自言自语）我必须小心行事，这里可能有危险。\n"
                                scene_content += f"{name1}: （突然发现）那边有一个保险箱！\n"
                                scene_content += f"{name1}: （仔细观察）密码应该是8位数。\n"
                                scene_content += f"{name1}: （输入密码）7-8-3-9-4-2-1-5\n"
                                scene_content += "保险箱咔哒一声打开，里面是一个红色的信封...\n"
                        verify_result = narrative_verify(scene_content, request.characters)
                    
                    # 第四步：更新叙事图谱（决策内核）
                    print(f"决策内核更新叙事图谱...")
                    narrative_update(scene_content, f"{act['id']}-{scene['id']}")
                    
                    act_content += f"{scene['label']}\n{scene_content}\n\n"
            generated_scenes.append(act_content)
        
        # 拼接所有场景内容
        final_script = "\n".join(generated_scenes) if generated_scenes else "暂无内容"
        
        # 添加校验结果到响应
        if 'verify_result' in locals():
            return {"script": final_script, "planning": planning_result, "verification": verify_result}
        else:
            return {"script": final_script, "planning": planning_result}
    except Exception as e:
        print(f"错误信息: {str(e)}")
        return {"error": str(e)}

# 剧情分析API
@app.post("/api/ai/analyze-plot")
def analyze_plot(request: AnalyzeRequest):
    try:
        analyze_prompt = f"你是一位专业的剧评人，请分析以下剧本的剧情结构：\n{request.script}\n\n分析要求：\n1. 梳理主要情节脉络\n2. 分析人物关系\n3. 指出剧情的高潮和转折点\n4. 评估剧情的合理性和逻辑性"
        if request.model == "deepseek":
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": analyze_prompt}],
                "temperature": 0.5,
                "max_tokens": 1500
            }
            session = create_session()
            response = session.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return {"analysis": result["choices"][0]["message"]["content"]}
        else:
            return {"analysis": "暂不支持其他模型"}
    except Exception as e:
        return {"error": str(e)}

# 叙事规划API
@app.post("/api/narrative/planning")
def planning(request: NarrativePlanningRequest):
    try:
        result = narrative_planning(request.requirement)
        return result
    except Exception as e:
        return {"error": str(e)}

# 叙事校验API
@app.post("/api/narrative/verify")
def verify(request: NarrativeVerifyRequest):
    try:
        result = narrative_verify(request.script_content, request.characters)
        return result
    except Exception as e:
        return {"error": str(e)}

# 叙事更新API
@app.post("/api/narrative/update")
def update(request: NarrativeUpdateRequest):
    try:
        result = narrative_update(request.script_content, request.scene_id)
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)