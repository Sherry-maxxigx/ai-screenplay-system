<template>
  <div class="pipeline-page">
    <div class="pipeline-shell">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="eyebrow">Story Automation Workshop</p>
          <h1>自动化工坊</h1>
          <p>
            把核心故事设定拆成几块来写，系统会自动整理成统一需求，再依次生成人物、大纲和剧本。功能保持不变，但整个流程会更清晰、更好编辑。
          </p>
        </div>
        <div class="hero-summary">
          <div class="summary-item">
            <span>当前步骤</span>
            <strong>{{ stepTitles[activeStep] }}</strong>
          </div>
          <div class="summary-item">
            <span>必填项</span>
            <strong>4 项</strong>
          </div>
          <div class="summary-item">
            <span>生成状态</span>
            <strong>{{ loadingData ? '处理中' : '待开始' }}</strong>
          </div>
        </div>
      </section>

      <section class="status-strip">
        <div class="status-card">
          <span>故事题材</span>
          <strong>{{ shorten(themeInput) || '待填写' }}</strong>
        </div>
        <div class="status-card">
          <span>背景设定</span>
          <strong>{{ shorten(settingInput) || '待填写' }}</strong>
        </div>
        <div class="status-card">
          <span>主角设定</span>
          <strong>{{ shorten(protagonistInput) || '待填写' }}</strong>
        </div>
        <div class="status-card">
          <span>风格要求</span>
          <strong>{{ shorten(styleInput) || '待填写' }}</strong>
        </div>
      </section>

      <el-card shadow="never" class="main-card">
        <template #header>
          <div class="card-head">
            <div>
              <h2>分步生成流程</h2>
              <p>从核心设定开始，逐步生成角色、剧情和剧本正文。</p>
            </div>
            <el-steps :active="activeStep" finish-status="success" simple class="steps">
              <el-step v-for="(title, index) in stepTitles" :key="index" :title="title" />
            </el-steps>
          </div>
        </template>

        <div v-if="loadingData" class="progress-panel">
          <div class="progress-meta">
            <div>
              <p class="progress-label">正在生成</p>
              <h3>{{ progressText }}</h3>
            </div>
            <div class="progress-number">{{ progressValue }}%</div>
          </div>
          <el-progress
            :percentage="progressValue"
            :format="progressFormat"
            :stroke-width="14"
            striped
            striped-flow
            :duration="10"
          />
        </div>

        <div v-if="lastRuleValidation" class="rule-validation-panel">
          <div class="rule-head">
            <h4>叙事规则内生引擎校验结果</h4>
            <el-tag :type="lastRuleValidation.is_valid ? 'success' : 'danger'" effect="dark" round>
              {{ lastRuleValidation.is_valid ? '强制合规通过' : '强制合规未通过' }}
            </el-tag>
          </div>

          <div class="rule-metrics">
            <span>强制合规分：{{ lastRuleValidation.metrics?.hard_compliance_score ?? '--' }}</span>
            <span>创意参考分：{{ lastRuleValidation.metrics?.creative_reference_score ?? '--' }}</span>
            <span>伏笔回收率：{{ lastRuleValidation.metrics?.foreshadow_recovery_rate ?? '--' }}%</span>
          </div>

          <el-alert
            v-if="(lastRuleValidation.hard_errors || []).length"
            type="error"
            :closable="false"
            :title="`硬性问题：${lastRuleValidation.hard_errors[0].description}`"
            class="rule-alert"
          />
          <el-alert
            v-else-if="(lastRuleValidation.soft_warnings || []).length"
            type="warning"
            :closable="false"
            :title="`创意建议：${lastRuleValidation.soft_warnings[0].description}`"
            class="rule-alert"
          />
        </div>

        <div v-show="activeStep === 0" class="step-content">
          <div class="section-head">
            <div>
              <p class="section-tag">Step 1</p>
              <h3>填写核心设定</h3>
              <p>下面四项是必须填写的，其他项如果暂时没想好，可以交给系统补全。</p>
            </div>
            <div class="section-note">
              <el-tag type="danger" effect="dark" round>故事题材 / 背景设定 / 主角设定 / 风格要求 为必填</el-tag>
            </div>
          </div>

          <div class="field-grid">
            <div class="field-card required">
              <label>故事题材 <em>必填</em></label>
              <p>告诉系统这是什么类型的故事，比如悬疑、科幻、爱情、古装、犯罪等。</p>
              <el-input
                v-model="themeInput"
                type="textarea"
                :rows="3"
                placeholder="例如：悬疑科幻电影，带封闭空间和灾难元素。"
              />
            </div>

            <div class="field-card required">
              <label>背景设定 <em>必填</em></label>
              <p>描述故事发生的世界、地点、时代和关键背景事件。</p>
              <el-input
                v-model="settingInput"
                type="textarea"
                :rows="5"
                placeholder="例如：近未来，一座废弃多年的海上研究站在台风夜重新启动，并向外界发出神秘求救信号。"
              />
            </div>

            <div class="field-card required">
              <label>主角设定 <em>必填</em></label>
              <p>写清主角是谁、有什么能力、被什么问题困住。</p>
              <el-input
                v-model="protagonistInput"
                type="textarea"
                :rows="5"
                placeholder="例如：女主角林澈，32 岁，曾是研究站工程师，也是事故唯一幸存者，长期被愧疚和创伤困住。"
              />
            </div>

            <div class="field-card optional">
              <label>核心冲突 <span>可选</span></label>
              <p>如果你已经清楚主角要对抗什么，可以写在这里；留空系统会自动补全。</p>
              <el-input
                v-model="conflictInput"
                type="textarea"
                :rows="5"
                placeholder="例如：主角必须在揭露真相和保护仍然活着的人之间做选择。"
              />
            </div>

            <div class="field-card required">
              <label>风格要求 <em>必填</em></label>
              <p>告诉系统你想要的气质、节奏、情绪和表达方式。</p>
              <el-input
                v-model="styleInput"
                type="textarea"
                :rows="4"
                placeholder="例如：压迫感强、悬念推进快、对白克制、视觉感冷冽，整体偏电影化中文表达。"
              />
            </div>

            <div class="field-card optional">
              <label>结局方向 <span>可选</span></label>
              <p>你可以提前指定结尾情绪，比如开放式、悲壮、反转、温暖等。</p>
              <el-input
                v-model="endingInput"
                type="textarea"
                :rows="4"
                placeholder="例如：结尾带悲壮感，但留下开放式余韵。"
              />
            </div>
          </div>

          <div class="wide-card">
            <label>补充说明 <span>可选</span></label>
            <p>这里适合写你突然想到的镜头感、人物关系、禁区设定或其他特殊要求。</p>
            <el-input
              v-model="extraInput"
              type="textarea"
              :rows="4"
              placeholder="例如：尽量避免网络流行语，人物对白要偏现实主义；希望第一场就出现强钩子。"
            />
          </div>

          <div class="preview-card">
            <div class="preview-head">
              <div>
                <p class="section-tag">Auto Compiled Brief</p>
                <h4>系统整理后的需求预览</h4>
              </div>
              <span>你填写的内容会被自动整理成统一指令，再送去后端生成。</span>
            </div>
            <el-input :model-value="compiledRequirements" type="textarea" :rows="12" readonly />
          </div>

          <div class="action-bar">
            <el-button
              type="primary"
              size="large"
              @click="generateCharacters"
              :loading="loadingData"
              :disabled="!hasRequiredFields"
            >
              生成人物设定
            </el-button>
          </div>
        </div>

        <div v-show="activeStep === 1" class="step-content">
          <div class="section-head">
            <div>
              <p class="section-tag">Step 2</p>
              <h3>人物设定</h3>
              <p>这里可以继续手改，确认没问题后再生成剧情大纲。</p>
            </div>
            <el-tag type="success" effect="dark" round>可编辑</el-tag>
          </div>
          <el-input
            v-model="characters"
            type="textarea"
            :rows="18"
            placeholder="这里会出现系统生成的人物设定。"
          />
          <div class="action-bar">
            <el-button @click="activeStep = 0" size="large">返回上一步</el-button>
            <el-button type="primary" size="large" @click="generateOutline" :loading="loadingData">
              生成剧情大纲
            </el-button>
          </div>
        </div>

        <div v-show="activeStep === 2" class="step-content">
          <div class="section-head">
            <div>
              <p class="section-tag">Step 3</p>
              <h3>剧情大纲</h3>
              <p>你可以在这里调整幕结构、冲突节奏和高潮设计，再继续生成剧本正文。</p>
            </div>
            <el-tag type="warning" effect="dark" round>建议检查冲突升级</el-tag>
          </div>
          <el-input
            v-model="outline"
            type="textarea"
            :rows="18"
            placeholder="这里会出现系统生成的剧情大纲。"
          />
          <div class="action-bar">
            <el-button @click="activeStep = 1" size="large">返回上一步</el-button>
            <el-button type="primary" size="large" @click="generateScript" :loading="loadingData">
              生成剧本正文
            </el-button>
          </div>
        </div>

        <div v-show="activeStep === 3" class="step-content">
          <div class="section-head">
            <div>
              <p class="section-tag">Step 4</p>
              <h3>剧本正文</h3>
              <p>生成完成后可以直接进入高级编辑器，继续做细化改写和状态网络联动。</p>
            </div>
            <el-tag type="info" effect="dark" round>可直接进入编辑器</el-tag>
          </div>
          <el-input
            v-model="script"
            type="textarea"
            :rows="22"
            placeholder="这里会出现系统生成的剧本正文。"
          />

          <div class="advisor-panel">
            <div class="advisor-head">
              <h4>AI 修改建议助手（给不懂剧本结构的用户）</h4>
              <el-button size="small" @click="generateScriptAdvice" :loading="adviceLoading">
                一键生成修改建议
              </el-button>
            </div>
            <el-input
              v-model="scriptAdvice"
              type="textarea"
              :rows="8"
              readonly
              placeholder="点击“一键生成修改建议”，AI 会告诉你哪里有问题、怎么改、改完会有什么效果。"
            />
          </div>

          <div class="action-bar">
            <el-button @click="activeStep = 2" size="large">返回上一步</el-button>
            <el-button type="success" size="large" @click="finishPipeline">进入高级编辑器</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import {
  generateCharacters as apiGenerateCharacters,
  generateOutline as apiGenerateOutline,
  generatePipelineScript,
  analyzePlotWithAdvice,
} from '../api/ai'
import { globalState } from '../stores/project'

const router = useRouter()
const activeStep = toRef(globalState, 'pipelineActiveStep')
const loadingData = ref(false)

const progressValue = ref(0)
const progressText = ref('')
const lastRuleValidation = ref(null)
const scriptAdvice = ref('')
const adviceLoading = ref(false)
let progressTimer = null

const stepTitles = ['核心设定', '人物设定', '剧情大纲', '剧本正文']

const themeInput = toRef(globalState, 'pipelineThemeInput')
const settingInput = toRef(globalState, 'pipelineSettingInput')
const protagonistInput = toRef(globalState, 'pipelineProtagonistInput')
const conflictInput = toRef(globalState, 'pipelineConflictInput')
const styleInput = toRef(globalState, 'pipelineStyleInput')
const endingInput = toRef(globalState, 'pipelineEndingInput')
const extraInput = toRef(globalState, 'pipelineExtraInput')

const requirements = toRef(globalState, 'pipelineRequirements')
const characters = toRef(globalState, 'pipelineCharacters')
const outline = toRef(globalState, 'pipelineOutline')
const script = toRef(globalState, 'scriptContent')

const cleanGeneratedText = (text) => {
  if (!text) return ''
  return text
    .replace(/\r\n/g, '\n')
    .replace(/[#*_`]/g, '')
    .replace(/EXT\./g, '外景')
    .replace(/INT\./g, '内景')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

const shorten = (text) => {
  const value = (text || '').trim()
  if (!value) return ''
  return value.length > 16 ? `${value.slice(0, 16)}...` : value
}

const hasRequiredFields = computed(() =>
  [themeInput.value, settingInput.value, protagonistInput.value, styleInput.value].every(
    (value) => value && value.trim()
  )
)

const buildRequirementsText = () => {
  const requiredSections = [
    ['故事题材', themeInput.value],
    ['背景设定', settingInput.value],
    ['主角设定', protagonistInput.value],
    ['风格要求', styleInput.value],
  ]

  const optionalSections = [
    ['核心冲突', conflictInput.value || '如果用户没有明确填写，请根据题材、背景与主角状态自动补全最能推动剧情的核心冲突。'],
    ['结局方向', endingInput.value || '如果用户没有明确填写，请自行设计一个与整体风格一致、带余味的结局方向。'],
    ['补充说明', extraInput.value || '如果用户没有填写补充说明，请在不偏离核心设定的前提下，自主补足适合故事成立的细节。'],
  ]

  return [...requiredSections, ...optionalSections]
    .filter(([, value]) => value && value.trim())
    .map(([title, value]) => `${title}\n${value.trim()}`)
    .join('\n\n')
}

const compiledRequirements = computed(() => buildRequirementsText())

const progressFormat = (percentage) => (percentage === 100 ? '完成' : `${percentage}%`)

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
}

const ensureRequirements = () => {
  const text = buildRequirementsText()
  requirements.value = text
  return text
}

const syncRuleValidation = (result) => {
  lastRuleValidation.value = result?.data?.meta?.rule_validation || null
}

const generateCharacters = async () => {
  const compiled = ensureRequirements()
  if (!hasRequiredFields.value) {
    ElMessage.warning('请先填写故事题材、背景设定、主角设定和风格要求。')
    return
  }

  loadingData.value = true
  startProgress('正在根据核心设定生成人物设定...')
  try {
    const result = await apiGenerateCharacters(compiled)
    syncRuleValidation(result)
    characters.value = cleanGeneratedText(result.data.characters)
    stopProgress()
    setTimeout(() => {
      activeStep.value = 1
    }, 300)
  } catch (error) {
    console.error(error)
    ElMessage.warning('人物设定生成失败，请稍后重试。')
  } finally {
    loadingData.value = false
  }
}

const generateOutline = async () => {
  const compiled = ensureRequirements()
  loadingData.value = true
  startProgress('正在根据人物设定生成剧情大纲...')
  try {
    const result = await apiGenerateOutline(compiled, characters.value)
    syncRuleValidation(result)
    outline.value = cleanGeneratedText(result.data.outline)
    stopProgress()
    setTimeout(() => {
      activeStep.value = 2
    }, 300)
  } catch (error) {
    console.error(error)
    ElMessage.warning('剧情大纲生成失败，请稍后重试。')
  } finally {
    loadingData.value = false
  }
}

const generateScript = async () => {
  const compiled = ensureRequirements()
  loadingData.value = true
  startProgress('正在根据剧情大纲生成剧本正文...')
  try {
    const result = await generatePipelineScript(compiled, characters.value, outline.value)
    syncRuleValidation(result)
    script.value = cleanGeneratedText(result.data.script)
    stopProgress()
    setTimeout(() => {
      activeStep.value = 3
    }, 300)
  } catch (error) {
    console.error(error)
    ElMessage.warning('剧本正文生成失败，请稍后重试。')
  } finally {
    loadingData.value = false
  }
}

const generateScriptAdvice = async () => {
  const sourceText = cleanGeneratedText(script.value)
  if (!sourceText) {
    ElMessage.warning('请先生成剧本正文，再获取修改建议。')
    return
  }

  adviceLoading.value = true
  try {
    const response = await analyzePlotWithAdvice(sourceText)
    scriptAdvice.value = cleanGeneratedText(response?.data?.analysis || '')
    ElMessage.success('AI 修改建议已生成。')
  } catch (error) {
    console.error(error)
    ElMessage.warning('建议生成失败，请稍后重试。')
  } finally {
    adviceLoading.value = false
  }
}

const finishPipeline = async () => {
  globalState.scriptContent = cleanGeneratedText(script.value)
  ElMessage.success('剧本已整理完成，正在进入高级编辑器。')

  try {
    await router.push({ name: 'Editor' })
  } catch (error) {
    console.error(error)
    const base = import.meta.env.BASE_URL || '/'
    window.location.href = `${base}#/editor`
  }
}
</script>

<style scoped>
.pipeline-page {
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(34, 115, 255, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(10, 181, 134, 0.12), transparent 24%),
    linear-gradient(180deg, #eef3fb 0%, #f7f9fd 100%);
}

.pipeline-shell {
  max-width: 1320px;
  margin: 0 auto;
}

.hero-panel {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 20px;
  padding: 28px 32px;
  border-radius: 24px;
  color: #f8fbff;
  background:
    linear-gradient(135deg, rgba(5, 36, 88, 0.95), rgba(12, 92, 138, 0.88)),
    linear-gradient(135deg, #0f2d57, #1f7a8c);
  box-shadow: 0 18px 50px rgba(15, 45, 87, 0.18);
}

.eyebrow,
.section-tag {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #7a879b;
}

.hero-copy .eyebrow {
  color: rgba(248, 251, 255, 0.74);
}

.hero-copy h1 {
  margin: 0 0 10px;
  font-size: 34px;
}

.hero-copy p:last-child {
  margin: 0;
  max-width: 760px;
  line-height: 1.75;
  font-size: 15px;
  color: rgba(248, 251, 255, 0.9);
}

.hero-summary {
  display: grid;
  gap: 14px;
}

.summary-item {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
}

.summary-item span,
.status-card span {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}

.summary-item strong {
  font-size: 19px;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin: 22px 0;
}

.status-card {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 10px 30px rgba(37, 70, 120, 0.08);
  border: 1px solid rgba(16, 51, 92, 0.08);
}

.status-card span {
  color: #748297;
}

.status-card strong {
  display: block;
  font-size: 16px;
  color: #10233e;
}

.main-card {
  border: none;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18px 50px rgba(37, 70, 120, 0.08);
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.card-head h2 {
  margin: 0;
  font-size: 22px;
  color: #10233e;
}

.card-head p {
  margin: 8px 0 0;
  color: #7a879b;
  font-size: 13px;
}

.steps {
  min-width: 420px;
}

.progress-panel {
  margin-bottom: 24px;
  padding: 22px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
  border: 1px solid rgba(59, 93, 159, 0.12);
}

.rule-validation-panel {
  margin-bottom: 20px;
  padding: 16px 18px;
  border-radius: 14px;
  background: #f9fbff;
  border: 1px solid rgba(59, 93, 159, 0.18);
}

.rule-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.rule-head h4 {
  margin: 0;
  font-size: 16px;
  color: #113661;
}

.rule-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 10px;
  color: #4f6582;
  font-size: 13px;
}

.rule-alert {
  margin-top: 6px;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 12px;
}

.progress-label {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6d7c92;
}

.progress-meta h3 {
  margin: 8px 0 0;
  font-size: 22px;
  color: #12305c;
}

.progress-number {
  font-size: 28px;
  font-weight: 700;
  color: #0a4db3;
}

.step-content {
  padding-top: 4px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 20px;
}

.section-head h3 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #10233e;
}

.section-head p:last-child {
  margin: 0;
  color: #70809a;
  line-height: 1.7;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.field-card,
.wide-card,
.preview-card {
  padding: 20px;
  border-radius: 20px;
  border: 1px solid rgba(16, 51, 92, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92) 0%, rgba(247, 250, 255, 0.9) 100%);
}

.field-card.required {
  box-shadow: inset 0 0 0 1px rgba(210, 77, 87, 0.08);
}

.field-card.optional,
.wide-card {
  box-shadow: inset 0 0 0 1px rgba(26, 100, 155, 0.06);
}

.field-card label,
.wide-card label {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #12263f;
}

.field-card label em {
  margin-left: 8px;
  font-style: normal;
  color: #d54c4c;
  font-size: 12px;
}

.field-card label span,
.wide-card label span {
  margin-left: 8px;
  color: #6e7d92;
  font-size: 12px;
  font-weight: 500;
}

.field-card p,
.wide-card p {
  margin: 0 0 14px;
  color: #71829a;
  line-height: 1.7;
  font-size: 14px;
}

.wide-card,
.preview-card {
  margin-top: 18px;
}

.preview-card {
  background: linear-gradient(135deg, #f0f6ff 0%, #f8fbff 100%);
}

.advisor-panel {
  margin-top: 18px;
  padding: 16px;
  border-radius: 14px;
  background: #f7fbff;
  border: 1px solid rgba(33, 104, 173, 0.18);
}

.advisor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.advisor-head h4 {
  margin: 0;
  font-size: 15px;
  color: #12406c;
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.preview-head h4 {
  margin: 0;
  font-size: 20px;
  color: #10305b;
}

.preview-head span {
  max-width: 380px;
  color: #6d7c92;
  line-height: 1.6;
  font-size: 13px;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-top: 26px;
}

@media (max-width: 1100px) {
  .hero-panel,
  .status-strip {
    grid-template-columns: 1fr;
  }

  .card-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .steps {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 900px) {
  .pipeline-page {
    padding: 16px;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }

  .preview-head,
  .section-head {
    flex-direction: column;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
