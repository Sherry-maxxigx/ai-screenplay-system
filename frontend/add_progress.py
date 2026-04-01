import os

filepath = r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\PipelineView.vue'

with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# ADD PROGRESS HTML
html_target = "      <!-- 步骤 1: 需求输入 -->"
progress_html = """
      <!-- 进度条区 -->
      <div v-if="loadingData" style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px dashed #ebeef5;">
        <el-progress :percentage="progressValue" :format="progressFormat" :stroke-width="18" status="success" striped striped-flow :duration="10" />
        <p style="text-align: center; color: #409EFF; margin-top: 15px; font-weight: bold; letter-spacing: 1px;">
          <el-icon class="is-loading" style="margin-right: 8px;"><Loading /></el-icon>
          {{ progressText }}
        </p>
      </div>

      <!-- 步骤 1: 需求输入 -->"""
text = text.replace(html_target, progress_html)

# ADD PROGRESS JS Variables
js_target = "const loadingData = ref(false)"
js_add = """const loadingData = ref(false)

const progressValue = ref(0)
const progressText = ref('')
let progressTimer = null

const progressFormat = (percentage) => (percentage === 100 ? '生成完成' : `${percentage}%`)

const startProgress = (text) => {
  progressValue.value = 0
  progressText.value = text
  if (progressTimer) clearInterval(progressTimer)
  
  progressTimer = setInterval(() => {
    if (progressValue.value >= 96) {
      clearInterval(progressTimer)
    } else {
      progressValue.value += Math.floor(Math.random() * 5) + 1
      if (progressValue.value > 96) progressValue.value = 96
    }
  }, 800)
}

const stopProgress = () => {
  if (progressTimer) clearInterval(progressTimer)
  progressValue.value = 100
}"""
text = text.replace(js_target, js_add)

# MODIFY generateCharacters
text = text.replace(
    "loadingData.value = true\n  try {",
    "loadingData.value = true\n  startProgress('AI正在燃烧算力，为您深度推演人物内在动机与画像...')\n  try {"
)
text = text.replace("characters.value = result.data.characters\n    activeStep.value = 1", "characters.value = result.data.characters\n    stopProgress()\n    setTimeout(() => { activeStep.value = 1 }, 500)")
text = text.replace("activeStep.value = 1\n  } finally {", "stopProgress()\n    setTimeout(() => { activeStep.value = 1 }, 500)\n  } finally {")

# MODIFY generateOutline
text = text.replace(
    "loadingData.value = true\n    try {",
    "loadingData.value = true\n    startProgress('基于人物动机，编剧引擎正在编织三幕剧结构，请稍候...')\n    try {"
)
text = text.replace("outline.value = result.data.outline\n      activeStep.value = 2", "outline.value = result.data.outline\n      stopProgress()\n      setTimeout(() => { activeStep.value = 2 }, 500)")
text = text.replace("activeStep.value = 2\n    } finally {", "stopProgress()\n      setTimeout(() => { activeStep.value = 2 }, 500)\n    } finally {")

# MODIFY generateScript
text = text.replace(
    "loadingData.value = true\n    try {",
    "loadingData.value = true\n    startProgress('最高难度挑战：AI正在将大纲逐句转化为电影级剧本正文...')\n    try {"
)
text = text.replace("script.value = result.data.script\n      activeStep.value = 3", "script.value = result.data.script\n      stopProgress()\n      setTimeout(() => { activeStep.value = 3 }, 500)")
text = text.replace("activeStep.value = 3\n    } finally {", "stopProgress()\n       setTimeout(() => { activeStep.value = 3 }, 500)\n    } finally {")

# Add Loading Icon import
import_target = "import { ElMessage } from 'element-plus'"
import_new = "import { ElMessage } from 'element-plus'\nimport { Loading } from '@element-plus/icons-vue'"
text = text.replace(import_target, import_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

print("Injected progress bar into PipelineView.vue")