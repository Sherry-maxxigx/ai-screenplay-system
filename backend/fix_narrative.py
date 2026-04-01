import re
with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\narrative.py', 'r', encoding='utf-8') as f: text = f.read()
text = text.replace('f"""', '"""')
text = text.replace('{req.content}', 'req.content')
with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\narrative.py', 'w', encoding='utf-8') as f: f.write(text)