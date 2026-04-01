import os

# 1. Update config.py to use Zhipu API Key
config_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\backend\app\core\config.py"
with open(config_path, "r", encoding="utf-8") as f:
    config_text = f.read()

config_text = config_text.replace(
    "ZHIPUAI_API_KEY: Optional[str] = None",
    'ZHIPUAI_API_KEY: Optional[str] = "29a636d5b47c4ba78cbe1612e60d33cd.7DCz91mVvjYCCCYI"'
)
with open(config_path, "w", encoding="utf-8") as f:
    f.write(config_text)

# 2. Update Vue Views to use glm-4 instead of deepseek
req_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\RequirementView.vue"
with open(req_path, "r", encoding="utf-8") as f:
    req_text = f.read()
req_text = req_text.replace("'deepseek'", "'glm-4'")
req_text = req_text.replace("DeepSeek", "智谱GLM-4")
with open(req_path, "w", encoding="utf-8") as f:
    f.write(req_text)

editor_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue"
with open(editor_path, "r", encoding="utf-8") as f:
    ed_text = f.read()
ed_text = ed_text.replace("'deepseek'", "'glm-4'")
ed_text = ed_text.replace("DeepSeek", "智谱GLM-4")
with open(editor_path, "w", encoding="utf-8") as f:
    f.write(ed_text)

print("Switched entirely to Zhipu GLM-4!")