import sys
import re

filepath = r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import_old = r"import axios from 'axios'"
import_new = "import axios from 'axios'\nimport { globalState } from '../stores/project'"
content = re.sub(import_old, import_new, content, flags=re.MULTILINE)

code_old = r'const code = ref\("【场景一】\\n时间：深夜\\n地点：废弃仓库\\n\\n主角林风低头看着手中的一枚旧怀表。\\n\[系统锁定：此处伏笔必须交代怀表来源，不得篡改\]\\n\\n林风：\(自语\)\\\"十年来，我一直在寻找真相。\\\""\);'
code_new = 'const code = ref(globalState.scriptContent || "【场景一】\\n时间：深夜\\n地点：废弃仓库\\n\\n主角林风低头看着手中的一枚旧怀表。\\n[系统锁定：此处伏笔必须交代怀表来源，不得篡改]\\n\\n林风：(自语)\\\"十年来，我一直在寻找真相。\\\"");\n\nwatch(() => code.value, (newVal) => {\n  globalState.scriptContent = newVal;\n});'

content = re.sub(code_old, code_new, content, flags=re.MULTILINE)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Editor update successful.')