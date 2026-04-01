import re

file_path = r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\api\ai.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix the specific string parsing error
content = re.sub(r'评估剧情的合理性和逻辑.*?$', '评估剧情的合理性和逻辑性"', content, flags=re.MULTILINE)
content = re.sub(r'OpenAI API Key 未配.*?$', 'OpenAI API Key Unset")', content, flags=re.MULTILINE)
content = re.sub(r'智谱AI API Key 未配.*?$', 'Zhipu AI API Key Unset")', content, flags=re.MULTILINE)
content = re.sub(r'DeepSeek API Key 未配.*?$', 'DeepSeek API Key Unset")', content, flags=re.MULTILINE)
content = re.sub(r'不支持的模.*?$', 'Unsupported Model")', content, flags=re.MULTILINE)
content = re.sub(r'函数调用仅支.*?$', 'Function call only supports gpt-4o")', content, flags=re.MULTILINE)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
