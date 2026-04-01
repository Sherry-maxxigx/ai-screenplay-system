with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '分析要求' in line:
        lines[i] = '        analyze_prompt = f"你是一位专业的剧评人，请分析以下剧本的剧情结构：\\n{script}\\n\\n分析要求：\\n1. 梳理主要情节脉络\\n2. 分析人物关系\\n3. 指出剧情的高潮和转折点\\n4. 评估剧情的合理性和逻辑性"\n'
with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)