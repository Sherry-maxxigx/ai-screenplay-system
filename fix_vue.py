import re

path = 'c:/Users/madon/Desktop/智能体2/ai-screenplay-system/frontend/src/views/EditorView.vue'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any occurrence of multiline string assignments for code.value
text = re.sub(r'code\.value \+= "\r?\n\r?\n(.*?)"', r'code.value += "\\n\\n\1"', text)
text = re.sub(r'code\.value \+= "\r?\n(.*?)"', r'code.value += "\\n\1"', text)

with open(path, 'w', encoding='utf-8') as f:
     f.write(text)
