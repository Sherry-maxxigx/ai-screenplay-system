import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { analyzePlotWithAdvice } from '../api/ai'
import { checkScriptCompletion, generateNextBeat as generateNextBeatAPI, syncNarrativeGraph } from '../api/narrative'
import { globalState } from '../stores/project'
import { openScreenplayPdfWindow } from '../utils/pdfExport'

const AUTOSAVE_KEY = 'AI_SCREENPLAY_VERSIONS_V2'
const router = useRouter()
const chartRef = ref(null)

const normalizeText = (text, trim = true) => {
  if (!text) return ''
  const normalized = String(text)
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/[#*_`]/g, '')
    .replace(/\bEXT\.\s*/gi, '外景 ')
    .replace(/\bINT\.\s*/gi, '内景 ')
    .replace(/\n{3,}/g, '\n\n')
  return trim ? normalized.trim() : normalized
}

const inferSceneCount = (text) => {
  const normalized = normalizeText(text)
  if (!normalized) return 0
  const numbered = normalized.match(/^第\s*[一二三四五六七八九十百零\d]+\s*场/gm)
  if (numbered?.length) return numbered.length
  return normalized.match(/^(内景|外景)/gm)?.length || 0
}

const decorateSuggestions = (items = []) => items.map((item, idx) => ({ ...item, id: item.id || idx + 1, applied: Boolean(item.applied) }))

const fallbackSuggestions = (text) => {
  const lines = normalizeText(text).split('\n').map((line) => line.trim()).filter(Boolean)
  if (!lines.length) return []
  return decorateSuggestions([
    { id: 1, type: '冲突优化', description: '让这一段的外部压力更明确，人物行动会更有戏剧张力。', before: lines[Math.min(2, lines.length - 1)] || '', after: `【冲突升级】${lines[Math.min(2, lines.length - 1)] || ''}，局势因此突然失控。` },
    { id: 2, type: '人物动机', description: '补出主角此刻最想守住的东西，人物弧线会更清楚。', before: lines[Math.min(5, lines.length - 1)] || '', after: `【人物强化】${lines[Math.min(5, lines.length - 1)] || ''}，她第一次说出了自己真正害怕失去的东西。` },
    { id: 3, type: '伏笔埋设', description: '提前埋一条会在结尾回收的线索，后续收口会更自然。', before: lines[Math.min(8, lines.length - 1)] || '', after: `【伏笔埋设】${lines[Math.min(8, lines.length - 1)] || ''}，一个不起眼的细节悄悄留下。` },
  ])
}

const smartReplace = (originalText, searchText, replaceText) => {
  if (!searchText || !replaceText) return originalText
  if (originalText.includes(searchText)) return originalText.replace(searchText, replaceText)
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase()
  const normalizedSearch = normalize(searchText)
  const lines = originalText.split('\n')
  for (let i = 0; i < lines.length; i += 1) {
    if (normalize(lines[i]).includes(normalizedSearch)) {
      const nextLines = [...lines]
      nextLines[i] = replaceText
      return nextLines.join('\n')
    }
  }
  return originalText
}

const code = ref(normalizeText(globalState.scriptContent || '', false))
const loading = ref(false)
const showVersionHistory = ref(false)
const versionHistory = ref([])
const restoringVersion = ref(null)
const analysisSummary = ref('')
const suggestions = ref([])
const adviceLoading = ref(false)
const applyingSuggestionIdx = ref(-1)
const completionState = ref(null)

const sceneCount = computed(() => inferSceneCount(code.value))
const outlineCoveragePercent = computed(() => Math.round(Number(completionState.value?.outline_coverage || 0) * 100))
const pendingSuggestionCount = computed(() => suggestions.value.filter((item) => !item.applied).length)
const contentStats = computed(() => ({ characters: (code.value || '').length, paragraphs: (code.value || '').split('\n').map((line) => line.trim()).filter(Boolean).length }))
const locked = computed(() => Boolean(globalState.pipelineIsScriptEnd || completionState.value?.is_complete))
const sceneProgressText = computed(() => {
  const coverageText = globalState.pipelineOutline ? `覆盖 ${outlineCoveragePercent.value}%` : '自动判断'
  return `${sceneCount.value} 场 · ${coverageText}`
})
const completionMessage = computed(() => completionState.value?.reason || globalState.pipelineCompletionReason || '已到达当前收口点，可以停止续写并导出 PDF。')
const canGenerateNextBeat = computed(() => !loading.value && !locked.value && Boolean(normalizeText(code.value)))
const nextBeatButtonText = computed(() => (locked.value ? '已完成，可导出 PDF' : `生成下一节拍（第${sceneCount.value + 1}场）`))
const statusText = computed(() => (locked.value ? '已到达当前收口点' : loading.value ? '正在续写下一节拍' : '按大纲自动推进中'))
const editorStatusText = computed(() => (locked.value ? '已停止续写' : loading.value ? '生成中' : '可编辑'))

let myChart = null
let syncTimer = null
let completionTimer = null
let completionToken = 0
let lastSyncedContent = ''
const getVersionPreview = (version) => normalizeText(version?.data?.scriptContent || version?.data?.pipelineRequirements || '暂无内容').slice(0, 180) || '暂无内容'

const refreshVersionHistory = () => {
  try {
    const saved = localStorage.getItem(AUTOSAVE_KEY)
    versionHistory.value = saved ? JSON.parse(saved).versions || [] : []
  } catch (error) {
    console.error(error)
    versionHistory.value = []
  }
}

const syncProgress = (completion = null, sourceText = code.value) => {
  completionState.value = completion
  const countedScenes = Math.max(0, Number(completion?.scene_count ?? inferSceneCount(sourceText)))
  const completed = Boolean(completion?.is_complete)
  globalState.pipelineCurrentScene = completed ? Math.max(1, countedScenes) : Math.max(1, countedScenes + 1)
  globalState.pipelineIsScriptEnd = completed
  globalState.pipelineCompletionReason = String(completion?.reason || '')
}

const refreshCompletionStatus = async (sourceText = code.value, silent = false) => {
  const normalized = normalizeText(sourceText)
  const token = ++completionToken
  if (!normalized) {
    completionState.value = null
    globalState.pipelineCurrentScene = 1
    globalState.pipelineIsScriptEnd = false
    globalState.pipelineCompletionReason = ''
    return null
  }
  try {
    const response = await checkScriptCompletion(normalized, globalState.pipelineOutline || '')
    if (token !== completionToken) return null
    const completion = response.data?.completion || null
    syncProgress(completion, normalized)
    return completion
  } catch (error) {
    if (token !== completionToken) return null
    if (!silent) console.error(error)
    syncProgress(null, normalized)
    return null
  }
}

const queueCompletionRefresh = (content) => {
  if (completionTimer) clearTimeout(completionTimer)
  const normalized = normalizeText(content)
  if (!normalized) {
    completionState.value = null
    globalState.pipelineCurrentScene = 1
    globalState.pipelineIsScriptEnd = false
    globalState.pipelineCompletionReason = ''
    return
  }
  completionTimer = setTimeout(() => {
    if (!loading.value) refreshCompletionStatus(normalized, true)
  }, 1500)
}

const renderGraph = (graphData) => {
  if (!myChart) return
  const fallbackGraph = {
    nodes: [
      { id: 'beat:当前场景', name: '当前场景', category: 1 },
      { id: 'char:主角', name: '主角', category: 0 },
    ],
    links: [{ source: 'char:主角', target: 'beat:当前场景', name: '出现在' }],
  }
  const safeGraph = graphData?.nodes?.length ? graphData : fallbackGraph
  myChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { formatter: '{b}' },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      force: { repulsion: 260, edgeLength: 110 },
      label: { show: true, position: 'right', formatter: '{b}', color: '#eef4ff' },
      edgeSymbol: ['circle', 'arrow'],
      edgeSymbolSize: [4, 10],
      edgeLabel: { show: true, fontSize: 10, formatter: '{c}', color: '#9eb0c8' },
      data: (safeGraph.nodes || []).map((node) => ({ ...node, symbolSize: node.category === 0 ? 54 : node.category === 2 ? 34 : 42 })),
      links: (safeGraph.links || []).map((link) => ({ ...link, value: link.name })),
      categories: [{ name: '角色' }, { name: '节拍' }, { name: '伏笔' }],
      lineStyle: { color: '#7f8da3', curveness: 0.12 },
    }],
  }, true)
}

const syncGraph = async (content) => {
  if (!myChart) return
  const normalized = normalizeText(content)
  if (!normalized) {
    renderGraph(null)
    return
  }
  try {
    const response = await syncNarrativeGraph(normalized)
    renderGraph(response.data?.data)
  } catch (error) {
    console.error(error)
  }
}

const queueGraphSync = (content) => {
  if (syncTimer) clearTimeout(syncTimer)
  syncTimer = setTimeout(() => {
    const normalized = normalizeText(content)
    if (!normalized || normalized === lastSyncedContent) return
    lastSyncedContent = normalized
    syncGraph(normalized)
  }, 1200)
}

const initChart = async () => {
  if (!chartRef.value) return
  myChart = echarts.init(chartRef.value)
  myChart.showLoading({ text: '正在同步剧情状态网络...', color: '#4f8cff', textColor: '#d7e6ff', maskColor: 'rgba(9, 21, 40, 0.24)' })
  try {
    await syncGraph(globalState.scriptContent || code.value)
  } finally {
    myChart.hideLoading()
  }
}

const restoreToVersion = async (version) => {
  restoringVersion.value = version.id
  try {
    const saved = localStorage.getItem(AUTOSAVE_KEY)
    const data = JSON.parse(saved)
    data.currentVersionId = version.id
    localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(data))
    if (version.data) Object.assign(globalState, version.data)
    code.value = normalizeText(globalState.scriptContent || version.data?.scriptContent || '', false)
    suggestions.value = []
    analysisSummary.value = ''
    await refreshCompletionStatus(code.value, true)
    showVersionHistory.value = false
    ElMessage.success(`已恢复到 ${version.savedAtReadable}`)
  } catch (error) {
    console.error(error)
    ElMessage.error('恢复失败，请重试。')
  } finally {
    restoringVersion.value = null
  }
}

const generateScriptAdvice = async () => {
  const sourceText = normalizeText(code.value)
  if (!sourceText) {
    ElMessage.warning('请先准备剧本文本，再生成 AI 建议。')
    return
  }
  adviceLoading.value = true
  analysisSummary.value = ''
  suggestions.value = []
  try {
    const response = await analyzePlotWithAdvice(sourceText)
    analysisSummary.value = normalizeText(response?.data?.analysis || '')
    const items = response?.data?.suggestions || []
    suggestions.value = decorateSuggestions(items.length ? items : fallbackSuggestions(sourceText))
    ElMessage.success(`已生成 ${suggestions.value.length} 条可应用建议。`)
  } catch (error) {
    console.error(error)
    analysisSummary.value = '模型建议暂时不可用，已切换到本地兜底建议。'
    suggestions.value = fallbackSuggestions(sourceText)
    ElMessage.success(`已生成 ${suggestions.value.length} 条本地兜底建议。`)
  } finally {
    adviceLoading.value = false
  }
}
const applyAISuggestion = async (item, idx) => {
  if (!item || item.applied) return
  applyingSuggestionIdx.value = idx
  await new Promise((resolve) => setTimeout(resolve, 250))
  code.value = smartReplace(code.value, item.before, item.after)
  suggestions.value[idx].applied = true
  applyingSuggestionIdx.value = -1
  ElMessage.success(`已应用第 ${idx + 1} 条 AI 建议。`)
}

const applyAllAISuggestions = async () => {
  for (let i = 0; i < suggestions.value.length; i += 1) {
    if (!suggestions.value[i]?.applied) await applyAISuggestion(suggestions.value[i], i)
  }
  ElMessage.success('当前建议已全部应用。')
}

const generateNextBeat = async () => {
  const normalized = normalizeText(code.value)
  if (!normalized) {
    ElMessage.warning('请先准备剧本文本，再生成下一节拍。')
    return
  }
  const completionBefore = await refreshCompletionStatus(normalized, true)
  if (locked.value) {
    syncProgress(completionBefore, normalized)
    ElMessage.info(completionMessage.value)
    return
  }
  loading.value = true
  try {
    const response = await generateNextBeatAPI(normalized, globalState.pipelineOutline || '', globalState.pipelineCharacters || '')
    const nextText = normalizeText(response.data?.text || '')
    if (nextText) code.value = normalizeText(`${normalized}\n\n${nextText}`, false)
    const mergedText = nextText ? code.value : normalized
    syncProgress(response.data?.completion, mergedText)
    if (response.data?.data) {
      renderGraph(response.data.data)
    } else {
      await syncGraph(mergedText)
    }
    if (locked.value) {
      ElMessage.success(completionMessage.value)
    } else if (nextText) {
      ElMessage.success(`下一节拍已生成，当前已完成 ${sceneProgressText.value}。`)
    } else {
      ElMessage.warning('本次没有生成新的节拍内容，请稍后重试。')
    }
  } catch (error) {
    console.error(error)
    ElMessage.warning('生成下一节拍失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const exportPdf = () => {
  const exported = openScreenplayPdfWindow({ title: globalState.title, content: normalizeText(code.value) })
  if (!exported) ElMessage.warning('请先准备剧本文本，并允许浏览器弹出导出窗口。')
}

const extractFingerprint = () => {
  globalState.scriptContent = normalizeText(code.value)
  ElMessage.success('当前剧本文本已同步，正在跳转到叙事指纹页。')
  router.push({ name: 'Fingerprint' })
}

const handleResize = () => {
  if (myChart) myChart.resize()
}

watch(() => code.value, (newValue) => {
  const normalized = normalizeText(newValue)
  globalState.scriptContent = normalized
  queueGraphSync(normalized)
  queueCompletionRefresh(normalized)
})

watch(showVersionHistory, (open) => {
  if (open) refreshVersionHistory()
})

onMounted(async () => {
  globalState.scriptContent = normalizeText(code.value)
  await initChart()
  refreshVersionHistory()
  await refreshCompletionStatus(code.value, true)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (syncTimer) clearTimeout(syncTimer)
  if (completionTimer) clearTimeout(completionTimer)
  window.removeEventListener('resize', handleResize)
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
})