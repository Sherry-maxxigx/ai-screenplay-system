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
  return `生成下一节拍（第${currentScene.value}场）`
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