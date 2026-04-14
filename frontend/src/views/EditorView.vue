<template>
  <div class="editor-page">
    <section class="hero">
      <div>
        <p class="kicker">Visible Writing Track</p>
        <h1>显性创作轨</h1>
        <p class="hero-copy">这一版把显性创作轨改成稳定的原生文本编辑区，并把自动续写统一改成按幕推进，方便你继续生成下一幕或手动细化。</p>
      </div>
      <div class="hero-actions">
        <span class="chip">{{ statusText }}</span>
        <el-button type="primary" :loading="loading" :disabled="!canGenerateNextAct" @click="generateNextAct">{{ nextActButtonText }}</el-button>
        <el-button plain @click="exportPdf">导出 PDF</el-button>
        <el-button plain @click="extractFingerprint">叙事指纹</el-button>
        <el-button plain @click="showVersionHistory = true">时光机（{{ versionHistory.length }}）</el-button>
      </div>
    </section>

    <section class="metrics">
      <article class="metric">
        <span>文本长度</span>
        <strong>{{ contentStats.characters }}</strong>
      </article>
      <article class="metric">
        <span>段落数量</span>
        <strong>{{ contentStats.paragraphs }}</strong>
      </article>
      <article class="metric">
        <span>剧本状态</span>
        <strong>{{ outlineStatusText }}</strong>
      </article>
    </section>

    <section v-if="locked" class="done-banner">
      <div>
        <strong>{{ latestActReviewed ? '剧本已到达当前收口点' : '当前题材已生成到最后一幕' }}</strong>
        <p>{{ completionMessage }}</p>
      </div>
      <el-button type="success" plain @click="exportPdf">导出 PDF</el-button>
    </section>

    <div class="layout">
      <div class="main-col">
        <section class="card editor-card">
          <header class="card-head">
            <div>
              <p class="kicker dark">Visible Track</p>
              <h2>显性创作轨</h2>
            </div>
            <span class="pill">{{ editorStatusText }}</span>
          </header>
          <textarea v-model="code" class="editor-textarea" spellcheck="false" placeholder="这里是剧本文本正文，支持正常左键选字、滚轮滚动和直接编辑。"></textarea>
        </section>

        <section class="card advice-card">
          <header class="card-head light">
            <div>
              <p class="kicker muted">AI Notes</p>
              <h2>当前幕 AI 修改意见</h2>
            </div>
            <div class="advice-actions">
              <el-button size="small" :loading="adviceLoading" @click="generateCurrentActReview">一键生成AI修改意见</el-button>
              <el-button
                v-if="currentActAnalysis?.has_issues && !currentActRevision"
                size="small"
                type="warning"
                :loading="revisionLoading"
                @click="generateCurrentActRevision"
              >
                一键生成修改版本
              </el-button>
              <el-button
                v-if="currentActRevision"
                size="small"
                type="success"
                :loading="applyingRevision"
                @click="applyCurrentActRevision"
              >
                一键应用修改
              </el-button>
            </div>
          </header>

          <div class="advice-body">
            <div v-if="currentActAnalysis" class="review-grid">
              <article class="review-card">
                <div class="review-card-head">
                  <span>问题 1</span>
                  <strong>当前幕是否完整覆盖本幕大纲</strong>
                </div>
                <p class="review-summary">{{ currentActAnalysis.missing_outline?.summary }}</p>
                <div
                  v-for="(item, idx) in currentActAnalysis.missing_outline?.items || []"
                  :key="`editor-missing-${idx}`"
                  class="review-row"
                >
                  <strong>缺失节点 {{ idx + 1 }}</strong>
                  <p>{{ item.text }}</p>
                </div>
                <p v-if="!(currentActAnalysis.missing_outline?.items || []).length" class="review-ok">
                  这一方面没有明显问题。
                </p>
              </article>

              <article class="review-card">
                <div class="review-card-head">
                  <span>问题 2</span>
                  <strong>当前幕是否有脱离大纲的内容</strong>
                </div>
                <p class="review-summary">{{ currentActAnalysis.off_outline?.summary }}</p>
                <div
                  v-for="(item, idx) in currentActAnalysis.off_outline?.items || []"
                  :key="`editor-off-outline-${idx}`"
                  class="review-row"
                >
                  <strong>{{ item.problem }}</strong>
                  <p>{{ item.reason }}</p>
                  <pre v-if="item.snippet">{{ item.snippet }}</pre>
                </div>
                <p v-if="!(currentActAnalysis.off_outline?.items || []).length" class="review-ok">
                  这一方面没有明显问题。
                </p>
              </article>
            </div>

            <section v-if="currentActRevision" class="revision-box">
              <div class="revision-box-head">
                <div>
                  <p class="kicker muted">AI Revision</p>
                  <h3>当前幕修改版本</h3>
                </div>
                <span class="pill">
                  可直接应用
                </span>
              </div>
              <textarea :value="currentActRevision.revisedAct" class="revision-textarea" readonly />
            </section>

            <div v-else-if="!currentActAnalysis" />
          </div>
        </section>
      </div>

      <section class="card graph-card">
        <header class="card-head">
          <div>
            <p class="kicker dark">Hidden Planning Track</p>
            <h2>隐性规划轨</h2>
          </div>
          <span class="pill blue">叙事状态网络</span>
        </header>
        <div class="legend">
          <span><i class="dot character"></i>角色</span>
          <span><i class="dot scene"></i>场景</span>
          <span><i class="dot foreshadow"></i>伏笔</span>
        </div>
        <div ref="chartRef" class="chart"></div>
      </section>
    </div>

    <el-dialog v-model="showVersionHistory" title="时光机 - 版本历史" width="720px" :close-on-click-modal="false">
      <el-empty v-if="!versionHistory.length" description="还没有可恢复的自动存档。" />
      <div v-else class="version-list">
        <article v-for="(version, idx) in versionHistory" :key="version.id" class="version-card" :class="{ latest: idx === 0 }">
          <div class="version-head">
            <div class="version-meta">
              <el-tag size="small" :type="idx === 0 ? 'success' : 'info'">{{ idx === 0 ? '最新版本' : `#${versionHistory.length - idx}` }}</el-tag>
              <strong>{{ version.savedAtReadable }}</strong>
            </div>
            <el-button size="small" type="primary" plain :loading="restoringVersion === version.id" @click="restoreToVersion(version)">恢复到此版本</el-button>
          </div>
          <pre class="version-preview">{{ getVersionPreview(version) }}</pre>
        </article>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  generateNextAct as generateNextActAPI,
  reviewCurrentAct,
  reviseCurrentAct,
  syncNarrativeGraph,
} from '../api/narrative'
import { globalState } from '../stores/project'
import { getRequestErrorMessage } from '../utils/apiError'
import { getLockedCompletionNotice } from '../utils/completionText'
import { formatActProgress, getCurrentActLabel, getNextActLabel } from '../utils/actProgress'
import { openScreenplayPdfWindow } from '../utils/pdfExport'
import { normalizeScriptText } from '../utils/scriptText'

const AUTOSAVE_KEY = 'AI_SCREENPLAY_VERSIONS_V2'
const router = useRouter()
const chartRef = ref(null)

const normalizeText = (text, trim = true) => normalizeScriptText(text, { trim })
const resolveRequestError = (error, fallbackText) => getRequestErrorMessage(error, fallbackText)

const code = ref(normalizeText(globalState.scriptContent || '', false))
const loading = ref(false)
const showVersionHistory = ref(false)
const versionHistory = ref([])
const restoringVersion = ref(null)
const currentActAnalysis = ref(null)
const currentActRevision = ref(null)
const adviceLoading = ref(false)
const revisionLoading = ref(false)
const applyingRevision = ref(false)
const completionState = ref(globalState.pipelineCompletionSnapshot || null)
const scriptFormat = computed(() => globalState.pipelineScriptFormat || 'movie')
const latestActReviewed = computed(() => Boolean(globalState.pipelineLatestActReviewed))
const sharedGenerationBusy = computed(() => Boolean(globalState.pipelineGenerationInFlight))
const generationBusy = computed(() => loading.value || sharedGenerationBusy.value)
const generationInOtherView = computed(() => sharedGenerationBusy.value && !loading.value)

const contentStats = computed(() => ({ characters: (code.value || '').length, paragraphs: (code.value || '').split('\n').map((line) => line.trim()).filter(Boolean).length }))
const hasOutline = computed(() => Boolean(normalizeText(globalState.pipelineOutline || '')))
const completionLockedByState = computed(() => Boolean(
  globalState.pipelineIsScriptEnd ||
  completionState.value?.is_complete ||
  completionState.value?.generation_locked ||
  completionState.value?.can_continue === false
))
const currentActLabel = computed(() => getCurrentActLabel(completionState.value, code.value, scriptFormat.value))
const nextActLabel = computed(() => getNextActLabel(completionState.value, scriptFormat.value, code.value))
const locked = computed(() => completionLockedByState.value)
const outlineStatusText = computed(() => {
  if (!normalizeText(code.value)) return '尚未生成剧本'
  return formatActProgress(completionState.value, code.value, {
    scriptFormat: scriptFormat.value,
    latestActReviewed: latestActReviewed.value,
  })
})
const lockedCompletionNotice = computed(() => getLockedCompletionNotice(
  completionState.value || globalState.pipelineCompletionSnapshot || null,
  latestActReviewed.value,
))
const completionMessage = computed(() => {
  if (locked.value) return lockedCompletionNotice.value
  return '当前剧本仍在推进中。'
})
const canGenerateNextAct = computed(() => !generationBusy.value && !locked.value && Boolean(normalizeText(code.value)))
const nextActButtonText = computed(() => {
  if (generationBusy.value) return `正在生成${globalState.pipelineGenerationTargetAct || nextActLabel.value || '下一幕'}`
  if (locked.value) return latestActReviewed.value ? '已完结' : '已完结（未修改）'
  return '生成下一幕'
})
const statusText = computed(() => {
  if (loading.value) return `正在生成${nextActLabel.value || '下一幕'}`
  if (generationInOtherView.value) return `正在生成${globalState.pipelineGenerationTargetAct || nextActLabel.value || '下一幕'}`
  if (locked.value) return latestActReviewed.value ? '已完结，可生成 PDF' : '已完结（未修改）'
  return outlineStatusText.value
})
const editorStatusText = computed(() => {
  if (generationBusy.value) return '生成中'
  if (locked.value) return latestActReviewed.value ? '已完结' : '已完结（未修改）'
  return latestActReviewed.value ? '当前幕已确认' : '当前幕待复核'
})

const resetCurrentActAssistant = () => {
  currentActAnalysis.value = null
  currentActRevision.value = null
}

let myChart = null
let syncTimer = null
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

const syncProgress = (completion = null) => {
  const snapshot = completion ? { ...completion } : null
  completionState.value = snapshot
  globalState.pipelineCompletionSnapshot = snapshot
  const generationLocked = Boolean(snapshot?.generation_locked || snapshot?.can_continue === false)
  const completed = Boolean(snapshot?.is_complete || generationLocked)
  globalState.pipelineIsScriptEnd = completed
  globalState.pipelineCompletionReason = String(snapshot?.reason || '')
}

const refreshCompletionStatus = async (sourceText = code.value) => {
  const normalized = normalizeText(sourceText)
  if (!normalized) {
    syncProgress(null)
    return null
  }
  const completion = globalState.pipelineCompletionSnapshot || completionState.value || null
  syncProgress(completion)
  return completion
}

const renderGraph = (graphData) => {
  if (!myChart) return
  const fallbackGraph = {
    nodes: [
      { id: 'scene:当前场景', name: '当前场景', category: 1 },
      { id: 'char:主角', name: '主角', category: 0 },
    ],
    links: [{ source: 'char:主角', target: 'scene:当前场景', name: '出现在' }],
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
      categories: [{ name: '角色' }, { name: '场景' }, { name: '伏笔' }],
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
    resetCurrentActAssistant()
    syncProgress(globalState.pipelineCompletionSnapshot || version.data?.pipelineCompletionSnapshot || null)
    showVersionHistory.value = false
    ElMessage.success(`已恢复到 ${version.savedAtReadable}`)
  } catch (error) {
    console.error(error)
    ElMessage.error('恢复失败，请重试。')
  } finally {
    restoringVersion.value = null
  }
}

const generateCurrentActReview = async () => {
  const sourceText = normalizeText(code.value)
  if (!sourceText) {
    ElMessage.warning('请先准备当前幕正文，再生成 AI 修改意见。')
    return
  }

  adviceLoading.value = true
  currentActAnalysis.value = null
  currentActRevision.value = null
  try {
    const response = await reviewCurrentAct(
      sourceText,
      globalState.pipelineOutline || '',
      globalState.pipelineCharacters || '',
      globalState.pipelineRequirements || '',
      scriptFormat.value,
    )
    currentActAnalysis.value = response?.data?.analysis || null
    if (!currentActAnalysis.value) {
      throw new Error('当前幕问题分析结果为空')
    }
    if (currentActAnalysis.value.has_issues) {
      globalState.pipelineLatestActReviewed = false
      ElMessage.warning('已生成当前幕问题分析，可以继续一键生成修改版本。')
    } else {
      globalState.pipelineLatestActReviewed = true
      ElMessage.success(locked.value ? lockedCompletionNotice.value : '当前幕两方面暂未发现明显问题。')
    }
  } catch (error) {
    console.error(error)
    ElMessage.warning(resolveRequestError(error, '当前幕问题分析失败，请稍后重试。'))
  } finally {
    adviceLoading.value = false
  }
}

const generateCurrentActRevision = async () => {
  const sourceText = normalizeText(code.value)
  if (!sourceText) {
    ElMessage.warning('请先准备当前幕正文，再生成修改版本。')
    return
  }

  if (!currentActAnalysis.value) {
    ElMessage.warning('请先点击“一键生成AI修改意见”，确认当前幕问题后再生成修改版本。')
    return
  }

  revisionLoading.value = true
  currentActRevision.value = null
  try {
    const analysis = currentActAnalysis.value
    if (!analysis) {
      throw new Error('当前幕问题分析结果为空')
    }

    const response = await reviseCurrentAct(
      sourceText,
      globalState.pipelineOutline || '',
      globalState.pipelineCharacters || '',
      globalState.pipelineRequirements || '',
      analysis,
      scriptFormat.value,
    )
    currentActAnalysis.value = response?.data?.analysis || analysis
    if (response?.data?.generated === false) {
      currentActRevision.value = null
      globalState.pipelineLatestActReviewed = true
      ElMessage.success('当前幕暂时不需要生成修改版本。')
      return
    }
    const revisedAct = normalizeText(response?.data?.revised_act || '')
    const revisedContent = normalizeText(response?.data?.revised_content || '')
    if (!revisedAct || !revisedContent) {
      throw new Error('AI 没有返回可应用的修改版本')
    }

    currentActRevision.value = {
      revisedAct,
      revisedContent,
      sourceText,
      completion: response?.data?.completion || null,
      warning: response?.data?.warning || '',
      acceptedWithIssues: Boolean(response?.data?.accepted_with_issues),
      generated: Boolean(response?.data?.generated),
    }

    ElMessage.success(
      currentActRevision.value.acceptedWithIssues
        ? 'AI 修改版本已生成，你可以先查看下面的版本，再决定是否替换当前正文。'
        : 'AI 修改版本已生成，确认后可直接应用。'
    )
  } catch (error) {
    console.error(error)
    ElMessage.warning(resolveRequestError(error, '当前幕修改版本生成失败，请稍后重试。'))
  } finally {
    revisionLoading.value = false
  }
}

const applyCurrentActRevision = async () => {
  if (!currentActRevision.value?.revisedContent) return
  if (normalizeText(code.value) !== currentActRevision.value.sourceText) {
    ElMessage.warning('当前幕正文已经变化，请重新生成修改版本，避免覆盖你刚刚的新改动。')
    return
  }

  applyingRevision.value = true
  try {
    const revision = currentActRevision.value
    if (!revision) return
    code.value = normalizeText(revision.revisedContent, false)
    globalState.scriptContent = normalizeText(code.value)
    globalState.pipelineLatestActReviewed = !revision.acceptedWithIssues
    syncProgress(revision.completion || completionState.value || null)
    resetCurrentActAssistant()
    ElMessage.success(
      globalState.pipelineLatestActReviewed && locked.value
        ? lockedCompletionNotice.value
        : 'AI 修改版本已应用到当前幕。'
    )
  } catch (error) {
    console.error(error)
    ElMessage.warning('应用 AI 修改版本失败，请稍后重试。')
  } finally {
    applyingRevision.value = false
  }
}

const generateNextAct = async () => {
  const normalized = normalizeText(code.value)
  if (!normalized) {
    ElMessage.warning('请先准备剧本文本，再生成下一幕。')
    return
  }
  if (locked.value) {
    ElMessage.info(completionMessage.value)
    return
  }
  if (generationBusy.value && !loading.value) {
    ElMessage.info(`当前正在生成${globalState.pipelineGenerationTargetAct || nextActLabel.value || '下一幕'}，请稍等。`)
    return
  }
  loading.value = true
  globalState.pipelineGenerationInFlight = true
  globalState.pipelineGenerationTargetAct = nextActLabel.value || '下一幕'
  resetCurrentActAssistant()
  try {
    const response = await generateNextActAPI(
      normalized,
      globalState.pipelineOutline || '',
      globalState.pipelineCharacters || '',
      globalState.pipelineRequirements || '',
      scriptFormat.value,
    )
    const nextText = normalizeText(response.data?.text || '')
    if (!nextText) {
      syncProgress(response.data?.completion || completionState.value || null)
      ElMessage.info(completionMessage.value)
      return
    }
    code.value = normalizeText(`${normalized}\n\n${nextText}`, false)
    globalState.scriptContent = normalizeText(code.value)
    if (nextText) globalState.pipelineLatestActReviewed = false
    const mergedText = nextText ? code.value : normalized
    syncProgress(response.data?.completion || null)
    if (response.data?.data) {
      renderGraph(response.data.data)
    } else {
      await syncGraph(mergedText)
    }
    if (response.data?.accepted_with_issues && nextText) {
      ElMessage.warning('下一幕已生成，但系统检测到当前幕还可继续对齐大纲。可以先生成 AI 修改意见，再决定是否生成修改版本。')
    } else if (locked.value) {
      ElMessage.success(completionMessage.value)
    } else if (nextText) {
      ElMessage.success(`下一幕已生成，当前状态：${outlineStatusText.value}。`)
    } else {
      ElMessage.warning('本次没有生成新的幕内容，请稍后重试。')
    }
  } catch (error) {
    console.error(error)
    ElMessage.warning(resolveRequestError(error, '生成下一幕失败，请稍后重试。'))
  } finally {
    loading.value = false
    globalState.pipelineGenerationInFlight = false
    globalState.pipelineGenerationTargetAct = ''
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
})

watch(() => globalState.scriptContent, (newValue) => {
  const normalized = normalizeText(newValue || '', false)
  if (normalized !== normalizeText(code.value, false)) {
    code.value = normalized
  }
})

watch(() => globalState.pipelineCompletionSnapshot, (value) => {
  completionState.value = value ? { ...value } : null
})

watch(showVersionHistory, (open) => {
  if (open) refreshVersionHistory()
})

onMounted(async () => {
  globalState.scriptContent = normalizeText(code.value)
  syncProgress(globalState.pipelineCompletionSnapshot || null)
  await initChart()
  refreshVersionHistory()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (syncTimer) clearTimeout(syncTimer)
  window.removeEventListener('resize', handleResize)
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
})
</script>
<style scoped>
.editor-page { min-height: 100vh; padding: 28px; background: radial-gradient(circle at top left, rgba(27, 89, 188, 0.18), transparent 28%), radial-gradient(circle at top right, rgba(9, 161, 138, 0.1), transparent 24%), linear-gradient(180deg, #eaf0fa 0%, #f7f9fd 100%); }
.hero { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.95fr); gap: 22px; padding: 30px 32px; border-radius: 28px; color: #f8fbff; background: radial-gradient(circle at top right, rgba(120, 220, 204, 0.16), transparent 34%), linear-gradient(135deg, rgba(6, 38, 84, 0.96), rgba(8, 95, 133, 0.92)); box-shadow: 0 20px 48px rgba(15, 45, 87, 0.16); }
.hero-copy { margin: 0; max-width: 760px; font-size: 15px; line-height: 1.8; color: rgba(244, 248, 255, 0.92); }
.kicker { margin: 0 0 10px; font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(248, 251, 255, 0.72); }
.kicker.dark { color: rgba(238, 244, 255, 0.72); }
.kicker.muted { color: #758399; }
.hero h1, .card-head h2 { margin: 0 0 10px; }
.hero-actions, .advice-actions { display: flex; gap: 12px; flex-wrap: wrap; align-content: flex-start; }
.chip, .pill { padding: 8px 12px; border-radius: 999px; font-size: 12px; }
.chip { border: 1px solid rgba(255, 255, 255, 0.12); background: rgba(255, 255, 255, 0.1); }
.pill { background: rgba(255, 255, 255, 0.08); color: #e8f2ff; }
.pill.blue { background: rgba(79, 140, 255, 0.14); color: #bcd5ff; }
.metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 22px 0; }
.metric, .card { border-radius: 22px; box-shadow: 0 16px 40px rgba(37, 70, 120, 0.08); }
.metric { padding: 18px 20px; border: 1px solid rgba(16, 51, 92, 0.08); background: rgba(255, 255, 255, 0.88); }
.metric span { display: block; margin-bottom: 8px; font-size: 12px; color: #758399; }
.metric strong { font-size: 24px; color: #10233e; }
.done-banner { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 22px; padding: 18px 20px; border-radius: 20px; border: 1px solid rgba(52, 168, 83, 0.14); background: linear-gradient(135deg, #effaf2, #f8fffa); color: #275a31; }
.done-banner p { margin: 6px 0 0; color: #4b6f55; line-height: 1.7; }
.layout { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(360px, 0.95fr); gap: 20px; align-items: start; }
.main-col { display: grid; gap: 20px; }
.card { overflow: hidden; background: #fff; }
.editor-card { background: linear-gradient(180deg, #0d1626 0%, #101d30 100%); border: 1px solid rgba(39, 66, 107, 0.38); }
.advice-card { border: 1px solid rgba(184, 198, 219, 0.55); background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 255, 0.96)); }
.graph-card { position: sticky; top: 20px; min-height: 1100px; border: 1px solid rgba(52, 92, 146, 0.26); background: linear-gradient(180deg, #15253a 0%, #182c46 100%); }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 18px 22px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.card-head.light { border-bottom-color: rgba(16, 51, 92, 0.08); }
.editor-card .card-head h2, .graph-card .card-head h2 { color: #eef4ff; }
.advice-card .card-head h2 { color: #10233e; }
.editor-textarea { width: 100%; min-height: 720px; border: 0; padding: 24px; resize: none; outline: none; color: #f7f9ff; background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 18%), linear-gradient(180deg, #0f1827, #101a2a); font-size: 15px; line-height: 1.95; font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; overflow: auto; white-space: pre-wrap; word-break: break-word; user-select: text; cursor: text; }
.editor-textarea::placeholder { color: rgba(222, 232, 246, 0.42); }
.advice-body { padding: 18px 20px 22px; }
.review-grid, .version-list { display: grid; gap: 14px; margin-top: 16px; }
.review-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.review-card, .version-card, .revision-box { padding: 16px; border-radius: 16px; border: 1px solid rgba(16, 51, 92, 0.08); background: #fff; }
.review-card-head, .version-head, .revision-box-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.review-card-head span { flex-shrink: 0; padding: 6px 12px; border-radius: 999px; background: rgba(16, 51, 92, 0.06); color: #12406c; font-size: 12px; font-weight: 700; }
.review-card-head strong { color: #10233e; font-size: 16px; line-height: 1.6; }
.review-summary { margin: 12px 0 0; color: #4b5870; line-height: 1.8; font-size: 14px; }
.review-row { margin-top: 12px; padding: 12px; border-radius: 14px; background: #f5f8fd; }
.review-row strong { display: block; color: #10233e; font-size: 13px; }
.review-row p { margin: 8px 0 0; color: #526178; line-height: 1.7; font-size: 13px; }
.review-row pre, .version-preview { margin: 10px 0 0; white-space: pre-wrap; word-break: break-word; font-family: inherit; color: #1b2c42; }
.review-ok, .revision-tip { margin: 12px 0 0; color: #6c7c91; line-height: 1.7; font-size: 13px; }
.revision-box { margin-top: 16px; background: linear-gradient(180deg, rgba(245, 249, 255, 0.96), rgba(255, 255, 255, 0.96)); }
.revision-box h3 { margin: 6px 0 0; color: #10233e; }
.revision-textarea { width: 100%; min-height: 280px; margin-top: 14px; padding: 16px; border: 1px solid rgba(16, 51, 92, 0.1); border-radius: 16px; background: #fff; color: #1b2c42; resize: vertical; line-height: 1.8; font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; }
.pill.warning { background: rgba(230, 162, 60, 0.14); color: #b36a0b; }
.legend { display: flex; gap: 16px; padding: 14px 22px 0; color: #d0dbed; font-size: 13px; flex-wrap: wrap; }
.dot { display: inline-block; width: 10px; height: 10px; margin-right: 8px; border-radius: 999px; }
.dot.character { background: #4f8cff; }
.dot.scene { background: #70f0a8; }
.dot.foreshadow { background: #f1d45a; }
.chart { width: 100%; min-height: 1020px; padding: 10px 16px 18px; box-sizing: border-box; }
.version-list { max-height: 520px; overflow-y: auto; }
.version-card.latest { border-color: #67c23a; box-shadow: inset 0 0 0 1px rgba(103, 194, 58, 0.12); }
.version-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
@media (max-width: 1280px) { .hero, .metrics, .layout, .review-grid { grid-template-columns: 1fr; } .graph-card { position: static; min-height: 760px; } .chart { min-height: 700px; } }
@media (max-width: 900px) { .editor-page { padding: 16px; } .hero, .done-banner, .card-head, .version-head, .review-card-head, .revision-box-head { display: flex; flex-direction: column; align-items: flex-start; } .editor-textarea { min-height: 560px; padding: 18px; } .chart { min-height: 420px; } }
</style>
