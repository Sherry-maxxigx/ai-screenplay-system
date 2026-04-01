import sys

filepath = r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('const code = ref(globalState.scriptContent || "【场景一】'):
        skip = True
        new_lines.append('const code = ref(globalState.scriptContent || "【场景一】\\n时间：深夜\\n地点：废弃仓库\\n\\n主角林风低头看着手中的一枚旧怀表。\\n[系统锁定：此处伏笔必须交代怀表来源，不得篡改]\\n\\n林风：(自语)\\"十年来，我一直在寻找真相。\\"");\n')
        continue
    if skip:
        if '林风：(自语)"十年来，我一直在寻找真相。"' in line or '林风：(自语)\\"十年来，我一直在寻找真相。\\"' in line:
            skip = False
        continue
    new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("done")
