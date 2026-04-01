with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'if model == "glm-4":' in line and lines[i+1].find('OPENAI_API_KEY') != -1:
        lines[i] = '    if model == "gpt-4o":\n'
    if 'model="glm-4",' in line and lines[i+1].find('messages=[{"role": "user",') != -1:
        lines[i] = '            model="gpt-4o",\n'
with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)