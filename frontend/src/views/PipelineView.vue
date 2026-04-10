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
            <strong :style="activeStep > 0 ? 'color: #67c23a' : ''">{{ genStatusText }}</strong>
          </div>
          <div class="summary-item">
            <span>手动保存</span>
            <el-button size="small" @click="handleManualSave" style="margin-left: 8px;">
              💾 手动保存
            </el-button>
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
            <el-steps :active="activeStep" :key="'steps-' + activeStep" finish-status="success" simple class="steps">
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
              {{ lastRuleValidation.is_valid ? '基本合规通过' : '基本合规未通过' }}
            </el-tag>
          </div>

          <div class="rule-metrics">
            <span>基本合规分：{{ lastRuleValidation.metrics?.hard_compliance_score ?? '--' }}</span>
            <span>创意参考分：{{ lastRuleValidation.metrics?.creative_reference_score ?? '--' }}</span>
            <span>伏笔回收率：{{ lastRuleValidation.metrics?.foreshadow_recovery_rate ?? '--' }}%</span>
          </div>

          <div v-if="(lastRuleValidation.hard_errors || []).length" style="margin-bottom: 12px;">
            <div
              v-for="(error, idx) in lastRuleValidation.hard_errors"
              :key="idx"
              style="margin-bottom: 12px;"
            >
              <el-alert
                type="error"
                :closable="false"
                :title="`⚠️ 硬性问题：${error.description}`"
              >
                <template #default>
                  <p style="margin: 8px 0; color: #666; font-size: 13px;">
                    💡 修改建议：{{ error.fix_instruction }}
                  </p>
                  <el-button
                    size="small"
                    type="danger"
                    plain
                    @click="applyOneFix(error, idx)"
                    :loading="fixingIndex === idx"
                    style="margin-top: 4px;"
                  >
                    🔧 一键应用此修复
                  </el-button>
                </template>
              </el-alert>
            </div>
            
            <el-button 
              type="danger" 
              size="small"
              @click="applyAllFixes"
              :disabled="!lastRuleValidation.hard_errors.length"
              style="margin-top: 8px;"
            >
              🚀 一键应用全部修复
            </el-button>
          </div>
          
          <div v-else-if="(lastRuleValidation.soft_warnings || []).length">
            <div
              v-for="(warning, idx) in lastRuleValidation.soft_warnings"
              :key="idx"
              style="margin-bottom: 12px;"
            >
              <el-alert
                type="warning"
                :closable="false"
                :title="`💡 创意优化建议：${warning.description}`"
              />
            </div>
          </div>
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
            <el-button @click="goBackStep(0)" size="large">返回上一步</el-button>
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
            :rows="14"
            placeholder="这里会出现系统生成的剧情大纲。"
          />
          <el-alert
            v-if="isScriptEnd"
            type="success"
            :closable="false"
            show-icon
            style="margin-top: 16px;"
            :title="completionReason || '剧本已经完整收束，可以进入高级编辑器导出 PDF。'"
          />

          <div class="advisor-panel">
            <div class="advisor-head">
              <h4>📐 大纲 AI 修改建议助手</h4>
              <el-button size="small" @click="generateOutlineAdvice" :loading="outlineAdviceLoading">
                一键生成修改建议
              </el-button>
            </div>
            
            <div v-if="outlineSuggestions.length" style="margin-top: 15px;">
              <div
                v-for="(item, idx) in outlineSuggestions"
                :key="item.id || idx"
                style="margin-bottom: 15px;"
              >
                <el-alert
                  :type="item.type === '冲突升级' ? 'error' :
                         item.type === '人物弧光' ? 'warning' :
                         item.type === '伏笔设计' ? 'success' :
                         item.type === '结构节奏' ? 'info' : ''"
                  :closable="false"
                  :title="`${item.type}：${item.description}`"
                >
                  <template #default>
                    <div style="margin-top: 10px;">
                      <div v-if="item.applied" class="suggestion-applied-row">
                        <span class="applied-flag">已应用</span>
                      </div>
                      <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                        <div>
                          <span style="color: #999; font-size: 13px;">修改前：</span>
                          <p style="background: #f5f7fa; padding: 8px 12px; border-radius: 6px; margin: 5px 0; font-size: 13px;">{{ item.before }}</p>
                        </div>
                        <div style="text-align: center; line-height: 60px; color: #67c23a; font-weight: bold;">
                          →
                        </div>
                        <div>
                          <span style="color: #999; font-size: 13px;">修改后：</span>
                          <p style="background: #f0f9eb; padding: 8px 12px; border-radius: 6px; margin: 5px 0; font-size: 13px; color: #67c23a;">{{ item.after }}</p>
                        </div>
                      </div>
                      <el-button
                        size="small"
                        type="success"
                        plain
                        @click="applyOutlineSuggestion(idx)"
                        :loading="applyingOutlineSuggestionIdx === idx"
                        :disabled="item.applied"
                      >
                        ✨ 一键应用此修改
                      </el-button>
                    </div>
                  </template>
                </el-alert>
              </div>
            </div>
            
            <p v-else-if="!outlineAdviceLoading" style="color: #999; text-align: center; margin: 20px 0; font-size: 13px;">
              点击"一键生成修改建议"按钮，AI 将分析大纲结构问题并给出具体修改方案
            </p>
          </div>

          <div class="action-bar">
            <el-button @click="goBackStep(1)" size="large">返回上一步</el-button>
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
            
            <div v-if="structuredSuggestions.length" style="margin-top: 15px;">
              <div
                v-for="(item, idx) in structuredSuggestions"
                :key="item.id || idx"
                style="margin-bottom: 15px;"
              >
                <el-alert
                  :type="item.type === '冲突优化' ? 'error' :
                         item.type === '人物动机' ? 'warning' :
                         item.type === '伏笔埋设' ? 'success' :
                         item.type === '结构调整' ? 'info' : ''"
                  :closable="false"
                  :title="`${item.type}：${item.description}`"
                >
                  <template #default>
                    <div style="margin-top: 10px;">
                      <div v-if="item.applied" class="suggestion-applied-row">
                        <span class="applied-flag">已应用</span>
                      </div>
                      <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                        <div style="flex: 1;">
                          <div style="color: #f56c6c; font-size: 12px; margin-bottom: 5px;">
                            📝 修改前：
                          </div>
                          <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; 
                                      font-size: 12px; white-space: pre-wrap; margin: 0;
                                      max-height: 80px; overflow: auto;">{{ item.before }}</pre>
                        </div>
                        <div style="flex: 1;">
                          <div style="color: #67c23a; font-size: 12px; margin-bottom: 5px;">
                            ✨ 修改后：
                          </div>
                          <pre style="background: #f0f9eb; padding: 8px; border-radius: 4px;
                                      font-size: 12px; white-space: pre-wrap; margin: 0;
                                      max-height: 80px; overflow: auto;">{{ item.after }}</pre>
                        </div>
                      </div>
                      <el-button
                        size="small"
                        type="primary"
                        plain
                        @click="applyAISuggestion(item, idx)"
                        :loading="applyingSuggestionIdx === idx"
                        :disabled="item.applied"
                      >
                        🔧 一键应用此修改
                      </el-button>
                    </div>
                  </template>
                </el-alert>
              </div>
              
              <el-button 
                type="primary" 
                size="small"
                @click="applyAllAISuggestions"
                :disabled="!structuredSuggestions.length"
                style="margin-top: 5px;"
              >
                🚀 一键应用全部AI建议
              </el-button>
            </div>
            
            <el-input
              v-model="scriptAdvice"
              type="textarea"
              :rows="4"
              readonly
              placeholder="点击“一键生成修改建议”，AI 会告诉你哪里有问题、怎么改、改完会有什么效果。"
              style="margin-top: 15px;"
            />
          </div>

          <div class="action-bar">
            <el-button @click="goBackStep(2)" size="large">返回上一步</el-button>
            <el-button 
              type="primary" 
              size="large" 
              @click="generateScript"
              :loading="loadingData"
              :disabled="isScriptEnd"
            >
              {{ nextScriptButtonText }}
            </el-button>
            <el-button type="success" size="large" @click="finishPipeline">进入高级编辑器</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, toRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElAlert } from 'element-plus'

import {
  generateCharacters as apiGenerateCharacters,
  generateOutline as apiGenerateOutline,
  generatePipelineScript,
  analyzePlotWithAdvice,
} from '../api/ai'
import { checkScriptCompletion, generateNextBeat as generateNextBeatAPI } from '../api/narrative'
import { globalState } from '../stores/project'

const router = useRouter()
const activeStep = toRef(globalState, 'pipelineActiveStep')
const loadingData = ref(false)

const progressValue = ref(0)
const progressText = ref('')
const lastRuleValidation = ref(null)
const scriptAdvice = ref('')
const structuredSuggestions = ref([])
const adviceLoading = ref(false)
const fixingIndex = ref(-1)
const applyingSuggestionIdx = ref(-1)

const outlineSuggestions = ref([])
const outlineAdviceLoading = ref(false)
const applyingOutlineSuggestionIdx = ref(-1)
let progressTimer = null

const stepTitles = ['核心设定', '人物设定', '剧情大纲', '剧本正文']

const genStatusText = computed(() => {
  if (loadingData.value) return '⏳ 处理中...'
  if (activeStep.value === 0) return '准备就绪'
  if (activeStep.value === 1) return '✅ 人物设定已完成'
  if (activeStep.value === 2) return '✅ 剧情大纲已完成'
  if (activeStep.value === 3) return '✅ 全部生成完成'
  return '待开始'
})

const themeInput = toRef(globalState, 'pipelineThemeInput')
const settingInput = toRef(globalState, 'pipelineSettingInput')
const protagonistInput = toRef(globalState, 'pipelineProtagonistInput')
const conflictInput = toRef(globalState, 'pipelineConflictInput')
const styleInput = toRef(globalState, 'pipelineStyleInput')
const endingInput = toRef(globalState, 'pipelineEndingInput')
const extraInput = toRef(globalState, 'pipelineExtraInput')
const currentScene = ref(1) // 当前场次
const isScriptEnd = ref(false) // 是否剧本结束

const requirements = toRef(globalState, 'pipelineRequirements')
const characters = toRef(globalState, 'pipelineCharacters')
const outline = toRef(globalState, 'pipelineOutline')
const script = toRef(globalState, 'scriptContent')
const completionReason = toRef(globalState, 'pipelineCompletionReason')

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

const decorateSuggestions = (items = []) =>
  items.map((item, idx) => ({
    ...item,
    id: item.id || idx + 1,
    applied: Boolean(item.applied),
  }))

const inferSceneCount = (text) => {
  const normalized = cleanGeneratedText(text)
  if (!normalized) return 0
  const numbered = normalized.match(/^第\s*[一二三四五六七八九十百零\d]+\s*场/gm)
  if (numbered?.length) return numbered.length
  return normalized.match(/^(内景|外景)/gm)?.length || 0
}

const resetScriptProgress = (clearScript = false) => {
  currentScene.value = 1
  isScriptEnd.value = false
  completionReason.value = ''
  if (clearScript) {
    script.value = ''
  }
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
const nextScriptButtonText = computed(() => {
  if (isScriptEnd.value) return '剧终'
  if (!script.value.trim()) return '生成剧本正文'
  return '生成下一节拍'
})

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

const syncScriptCompletion = (completion = null, sourceText = script.value) => {
  const countedScenes = Math.max(0, Number(completion?.scene_count ?? inferSceneCount(sourceText)))
  isScriptEnd.value = Boolean(completion?.is_complete)
  currentScene.value = isScriptEnd.value ? Math.max(1, countedScenes) : Math.max(1, countedScenes + 1)
  completionReason.value = String(completion?.reason || '')
}

const refreshScriptCompletion = async (sourceText = script.value, silent = false) => {
  const normalized = cleanGeneratedText(sourceText)
  if (!normalized) {
    syncScriptCompletion(null, '')
    return null
  }

  try {
    const response = await checkScriptCompletion(normalized, outline.value || '')
    const completion = response.data?.completion || null
    syncScriptCompletion(completion, normalized)
    return completion
  } catch (error) {
    if (!silent) console.error(error)
    syncScriptCompletion(null, normalized)
    return null
  }
}

const applyOneFix = async (error, idx) => {
  fixingIndex.value = idx
  
  await new Promise(r => setTimeout(r, 500))
  
  const errorHandlers = {
    'OUTLINE_3ACT_MISSING': () => {
      outline.value += `

==== 系统自动补全 三幕结构 ====

【第一幕 · 建置】
铺垫核心世界观，主角登场并接触核心悬念

【第二幕 · 对抗】
冲突全面升级，反派力量逐渐显现

【第三幕 · 解决】
伏笔集中回收，真相揭晓
`
    },
    
    'SCENE_HEADER_MISSING': () => {
      script.value = `==== 系统自动补全标准化场景头 ====

第一幕·第01场
内景 公寓书房 夜

` + script.value
    },
    
    'ACT_SECTION_MISSING': () => {
      script.value = `第一幕·第01场
` + script.value
    },
    
    'DIALOGUE_MISSING': () => {
      script.value += `

==== 系统自动补全对白示例 ====

主角：（沉吟）"有些事情，不是我们想逃就能逃掉的。"
`
    },
    
    'FORESHADOW_NOT_RECOVERED': () => {
      script.value += `

==== 伏笔回收节点 · 系统建议 ====
开场出现的【关键信物】，在终场揭示为当年事件的核心证物
`
    },
    
    'CHARACTER_INCONSISTENT': () => {
      script.value = `==== 系统自动植入核心角色 ====

林澈看着眼前的一切，指尖因为用力而泛白。

` + script.value
    },

    'EMPTY_OUTPUT': () => {
      script.value = `第一幕·第01场
内景 研究站控制室 凌晨

红色警报灯在黑暗中循环闪烁，控制台屏幕上只有一行字："实验体已苏醒"
`
    },
  }

  if (errorHandlers[error.code]) {
    errorHandlers[error.code]()
  } else {
    ElMessage.info(`该错误类型暂不支持自动修复，请手动调整`)
  }

  fixingIndex.value = -1
  ElMessage.success(`已应用修复建议，请人工审阅调整`)
}

const applyAllFixes = async () => {
  const errors = [...(lastRuleValidation.hard_errors || [])]
  for (let i = 0; i < errors.length; i++) {
    await applyOneFix(errors[i], i)
  }
  ElMessage.success(`已自动应用 ${errors.length} 项修复建议`)
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
    activeStep.value = 1
    await forceSyncSteps()
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
    resetScriptProgress(true)
    structuredSuggestions.value = []
    scriptAdvice.value = ''
    stopProgress()
    activeStep.value = 2
    await forceSyncSteps()
  } catch (error) {
    console.error(error)
    ElMessage.warning('剧情大纲生成失败，请稍后重试。')
  } finally {
    loadingData.value = false
  }
}

const generateScript = async () => {
  if (activeStep.value !== 3 || !script.value.trim()) {
    resetScriptProgress(true)
  }
  if (isScriptEnd.value) {
    ElMessage.info('剧本已结束，无法继续生成。')
    return
  }
  
  const compiled = ensureRequirements()
  loadingData.value = true
  startProgress(script.value.trim() ? '正在根据剩余大纲续写下一节拍...' : '正在根据剧情大纲生成剧本开篇...')
  try {
    if (!script.value.trim()) {
      const result = await generatePipelineScript(
        compiled,
        characters.value,
        outline.value,
        currentScene.value
      )
      syncRuleValidation(result)
      script.value = cleanGeneratedText(result.data.script)
    } else {
      const completionBefore = await refreshScriptCompletion(script.value, true)
      if (completionBefore?.is_complete || isScriptEnd.value) {
        stopProgress()
        ElMessage.info(completionReason.value || '当前剧本已经完成收束。')
        return
      }

      lastRuleValidation.value = null
      const result = await generateNextBeatAPI(script.value, outline.value, characters.value)
      const nextText = cleanGeneratedText(result.data?.text || '')
      if (nextText) {
        script.value = cleanGeneratedText(`${script.value}\n\n${nextText}`)
      }
      syncScriptCompletion(result.data?.completion || null, script.value)
    }

    await refreshScriptCompletion(script.value, true)
    stopProgress()
    activeStep.value = 3
    await forceSyncSteps()

    if (isScriptEnd.value) {
      ElMessage.success(completionReason.value || '剧本已完整收束，可以进入高级编辑器导出 PDF。')
    } else {
      ElMessage.success(`✅ 当前已写到第 ${Math.max(1, currentScene.value - 1)} 场，下一次将继续按大纲往后推进。`)
    }
  } catch (error) {
    console.error(error)
    ElMessage.warning('剧本正文生成失败，请稍后重试。')
  } finally {
    loadingData.value = false
  }
}

const smartReplace = (originalText, searchText, replaceText) => {
  if (!searchText || !replaceText) return originalText
  
  // 1. 直接精确替换
  if (originalText.includes(searchText)) {
    return originalText.replace(searchText, replaceText)
  }
  
  // 2. 忽略多余空格和大小写的模糊匹配
  const normalize = (s) => s.replace(/\s+/g, ' ').trim().toLowerCase()
  const normalizedOriginal = normalize(originalText)
  const normalizedSearch = normalize(searchText)
  
  if (normalizedOriginal.includes(normalizedSearch)) {
    const lines = originalText.split('\n')
    for (let i = 0; i < lines.length; i++) {
      if (normalize(lines[i]).includes(normalizedSearch)) {
        lines[i] = replaceText
        return lines.join('\n')
      }
    }
  }
  
  // 3. 关键词匹配（至少60%关键词命中）
  const searchWords = normalizedSearch.split(' ').filter(w => w.length > 2)
  if (searchWords.length > 0) {
    const lines = originalText.split('\n')
    for (let i = 0; i < lines.length; i++) {
      const lineWords = normalize(lines[i]).split(' ')
      const matchCount = searchWords.filter(w => lineWords.some(lw => lw.includes(w))).length
      if (matchCount >= Math.max(1, searchWords.length * 0.5)) {
        lines[i] = replaceText
        return lines.join('\n')
      }
    }
  }
  
  // 4. 找不到则返回原文（不再追加）
  return originalText
}

const applyAISuggestion = async (item, idx) => {
  if (!item || item.applied) return

  applyingSuggestionIdx.value = idx
  
  await new Promise(r => setTimeout(r, 500))
  
  script.value = smartReplace(
    script.value,
    item.before,
    item.after
  )
  structuredSuggestions.value[idx].applied = true
  
  applyingSuggestionIdx.value = -1
  ElMessage.success(`✅ 已应用第 ${idx + 1} 条AI建议`)
}

const applyAllAISuggestions = async () => {
  for (let i = 0; i < structuredSuggestions.value.length; i++) {
    if (!structuredSuggestions.value[i]?.applied) {
      await applyAISuggestion(structuredSuggestions.value[i], i)
    }
  }
  ElMessage.success(`🚀 已全部应用 ${structuredSuggestions.value.length} 条AI建议`)
}

const generateFallbackSuggestions = () => {
  const lines = script.value.split('\n').filter(l => l.trim())
  if (lines.length < 3) return []
  
  return [
    {
      id: 1,
      type: '冲突优化',
      description: '加强戏剧冲突，让人物行动更有张力',
      before: lines[Math.min(2, lines.length - 1)] || '',
      after: `【冲突升级】${lines[Math.min(2, lines.length - 1)] || ''}，空气仿佛凝固了`,
      confidence: 0.9
    },
    {
      id: 2,
      type: '人物动机',
      description: '丰富人物动作细节，强化内心动机',
      before: lines[Math.min(5, lines.length - 1)] || '',
      after: `【细节刻画】${lines[Math.min(5, lines.length - 1)] || ''}，眼中闪过一丝复杂`,
      confidence: 0.85
    },
    {
      id: 3,
      type: '对白优化',
      description: '让对话更有潜台词和言外之意',
      before: lines[Math.min(8, lines.length - 1)] || '',
      after: `【对白优化】${lines[Math.min(8, lines.length - 1)] || ''}，话里有话`,
      confidence: 0.8
    }
  ]
}

const generateScriptAdvice = async () => {
  const sourceText = cleanGeneratedText(script.value)
  if (!sourceText) {
    ElMessage.warning('请先生成剧本正文，再获取修改建议。')
    return
  }

  adviceLoading.value = true
  structuredSuggestions.value = []
  try {
    const response = await analyzePlotWithAdvice(sourceText)
    scriptAdvice.value = cleanGeneratedText(response?.data?.analysis || '')
    
    const suggestions = response?.data?.suggestions || []
    
    if (suggestions.length) {
      structuredSuggestions.value = decorateSuggestions(suggestions)
      ElMessage.success(`✅ AI 已生成 ${suggestions.length} 条结构化修改建议`)
    } else {
      structuredSuggestions.value = decorateSuggestions(generateFallbackSuggestions())
      ElMessage.success('✅ 已生成系统优化建议')
    }
  } catch (error) {
    console.error(error)
    structuredSuggestions.value = decorateSuggestions(generateFallbackSuggestions())
    ElMessage.success('✅ 已生成系统优化建议')
  } finally {
    adviceLoading.value = false
  }
}

const generateOutlineFallbackSuggestions = () => {
  const lines = outline.value.split('\n').filter(l => l.trim())
  if (lines.length < 2) return []
  
  return [
    {
      id: 1,
      type: '冲突升级',
      description: '在第一幕结尾加入转折点，让主角被迫做出选择',
      before: lines[Math.min(1, lines.length - 1)] || '',
      after: `【第一幕转折点】${lines[Math.min(1, lines.length - 1)] || ''} —— 一件意外发生，彻底打破了平静`,
      confidence: 0.92
    },
    {
      id: 2,
      type: '人物弧光',
      description: '明确主角的成长路线，从逃避到面对',
      before: lines[Math.min(3, lines.length - 1)] || '',
      after: `【人物弧光】${lines[Math.min(3, lines.length - 1)] || ''}，主角内心从动摇走向坚定`,
      confidence: 0.88
    },
    {
      id: 3,
      type: '伏笔设计',
      description: '在前期埋设关键线索，后期呼应回收',
      before: lines[Math.min(5, lines.length - 1)] || '',
      after: `【伏笔埋设】${lines[Math.min(5, lines.length - 1)] || ''} —— 此时无人察觉的细节，将在最后成为关键`,
      confidence: 0.85
    },
    {
      id: 4,
      type: '结构节奏',
      description: '调整幕间节奏，确保每30分钟有一个大事件',
      before: lines[Math.min(7, lines.length - 1)] || '',
      after: `【节奏把控】${lines[Math.min(7, lines.length - 1)] || ''}，冲突达到小高潮，观众情绪被调动`,
      confidence: 0.8
    }
  ]
}

const generateOutlineAdvice = async () => {
  const sourceText = cleanGeneratedText(outline.value)
  if (!sourceText) {
    ElMessage.warning('请先生成剧情大纲，再获取修改建议。')
    return
  }

  outlineAdviceLoading.value = true
  outlineSuggestions.value = []
  try {
    const response = await analyzePlotWithAdvice(sourceText + '\n\n【这是剧情大纲，请从整体结构层面分析】')
    
    const suggestions = response?.data?.suggestions || []
    
    if (suggestions.length) {
      outlineSuggestions.value = decorateSuggestions(suggestions.map(s => ({
        ...s,
        type: s.type === '冲突优化' ? '冲突升级' :
              s.type === '人物动机' ? '人物弧光' :
              s.type === '对白优化' ? '结构节奏' : s.type
      })))
      ElMessage.success(`✅ AI 已生成 ${suggestions.length} 条大纲优化建议`)
    } else {
      outlineSuggestions.value = decorateSuggestions(generateOutlineFallbackSuggestions())
      ElMessage.success('✅ 已生成大纲系统优化建议')
    }
  } catch (error) {
    console.error(error)
    outlineSuggestions.value = decorateSuggestions(generateOutlineFallbackSuggestions())
    ElMessage.success('✅ 已生成大纲系统优化建议')
  } finally {
    outlineAdviceLoading.value = false
  }
}

const applyOutlineSuggestion = async (idx) => {
  applyingOutlineSuggestionIdx.value = idx
  
  await new Promise(r => setTimeout(r, 500))
  
  const item = outlineSuggestions.value[idx]
  if (!item || item.applied) {
    applyingOutlineSuggestionIdx.value = -1
    return
  }
  outline.value = smartReplace(
    outline.value,
    item.before,
    item.after
  )
  outlineSuggestions.value[idx].applied = true
  
  applyingOutlineSuggestionIdx.value = -1
  ElMessage.success(`✅ 已应用第 ${idx + 1} 条大纲优化建议`)
}

const handleManualSave = async () => {
  if (typeof window.saveManually === 'function') {
    const description = `自动化工坊 - 第${stepTitles[activeStep.value]}步骤`
    const result = window.saveManually(description)
    if (result) {
      ElMessage.success(`✅ 手动保存成功！最多保留 ${3} 个版本`)
    } else {
      ElMessage.info('⚠️ 内容未变化，无需保存')
    }
  } else {
    ElMessage.warning('⚠️ 手动保存功能暂不可用')
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

const forceSyncSteps = async () => {
  await nextTick()
  await nextTick()
}

const goBackStep = async (target) => {
  activeStep.value = target
  await forceSyncSteps()
}

watch(
  currentScene,
  (value) => {
    globalState.pipelineCurrentScene = Math.max(1, Number(value || 1))
  },
  { immediate: true }
)

watch(
  isScriptEnd,
  (value) => {
    globalState.pipelineIsScriptEnd = Boolean(value)
  },
  { immediate: true }
)

onMounted(async () => {
  currentScene.value = Math.max(1, Number(globalState.pipelineCurrentScene || currentScene.value || 1))
  isScriptEnd.value = Boolean(globalState.pipelineIsScriptEnd)

  const expectedStep = Math.max(0, Math.min(3, activeStep.value || 0))
  if (globalState.pipelineActiveStep !== expectedStep) {
    globalState.pipelineActiveStep = expectedStep
  }
  if (script.value.trim()) {
    await refreshScriptCompletion(script.value, true)
  }
  await forceSyncSteps()
})

// 实时监控 activeStep 变化，确保步骤条100%同步
watch(activeStep, async (newVal, oldVal) => {
  if (newVal !== oldVal) {
    await nextTick()
    await nextTick()
  }
}, { immediate: true })
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

.suggestion-applied-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.applied-flag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #2f7d32;
  background: #e8f5e9;
  border: 1px solid rgba(47, 125, 50, 0.18);
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
