import re

path = r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\narrative.py'

with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Fix f-string and quote messes
text = text.replace('f"""', '"""')
text = text.replace('\\"\\"\\"', '"""')
text = text.replace('{req.content}', '{req_content}')
text = text.replace('req.content', '{req_content}')

# Quick hack to just recreate the function to avoid the mess
new_func = '''
@router.post("/generate_beat")
async def generate_next_beat(req: BeatRequest):
    neo4j_client.simulate_function_call_update(req.content)
    generated_md = f"""
【内生引擎触发】
系统检索到最新节点上下文：{req.content}

场景内容：
林风紧握着旧怀表，里面滴答的齿轮声仿佛在向他诉说某种密文。
“原来从一开始...一切就是个局！”
(系统强制合规：已回收怀表线索)
"""
    return {"status": "success", "text": generated_md}
'''

text = re.sub(r'@router\.post\("/generate_beat"\).*?return \{"status": "success", "text": generated_md\}', new_func, text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
