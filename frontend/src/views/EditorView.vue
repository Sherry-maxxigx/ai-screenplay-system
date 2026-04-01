<template>
  <div class="editor-page">
    <div class="editor-shell">
      <section class="editor-hero">
        <div class="hero-left">
          <p class="eyebrow">Advanced Screenplay Editor</p>
          <h1>高级编辑器</h1>
          <p>
            保留原来的显性创作轨和隐性规划轨联动能力，只把界面层升级成更清晰、更有氛围感的工作台。
          </p>
        </div>
        <div class="hero-actions">
          <div class="hero-chip danger">防篡改编辑区</div>
          <div class="hero-chip success">{{ loading ? '正在生成下一节拍' : '引擎状态稳定' }}</div>
          <div class="hero-chip info">右侧图谱实时同步</div>
          <el-button type="primary" @click="generateNextBeat" :loading="loading">生成下一节拍</el-button>
          <el-button plain @click="extractFingerprint">提取叙事指纹</el-button>
        </div>
      </section>

      <section class="metrics-strip">
        <article class="metric-card">
          <span>当前文本长度</span>
          <strong>{{ contentStats.characters }}</strong>
          <small>字符</small>
        </article>
        <article class="metric-card">
          <span>段落数量</span>
          <strong>{{ contentStats.paragraphs }}</strong>
          <small>段</small>
        </article>
        <article class="metric-card">
          <span>图谱同步</span>
          <strong>{{ loading ? '处理中' : '实时联动' }}</strong>
          <small>右侧状态网络</small>
        </article>
      </section>

      <div class="workspace-grid">
        <section class="panel editor-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">Visible Track</p>
              <h2>显性创作轨</h2>
            </div>
            <span class="panel-status">{{ loading ? '生成中' : '空闲' }}</span>
          </div>

          <div class="panel-body editor-body">
            <vue-monaco-editor
              v-model:value="code"
              theme="vs-dark"
              language="plaintext"
              :options="MONACO_OPTIONS"
              @change="handleEditorChange"
            />
          </div>
        </section>

        <section class="panel graph-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">Hidden Planning Track</p>
              <h2>隐性规划轨</h2>
            </div>
            <span class="panel-status blue">Neo4j 实时状态网络</span>
          </div>

          <div class="graph-legend">
            <span><i class="dot character"></i>角色 Character</span>
            <span><i class="dot beat"></i>剧本节拍 Beat</span>
            <span><i class="dot foreshadow"></i>伏笔 Foreshadowing</span>
          </div>

          <div class="panel-body graph-body">
            <div id="chart-container" class="chart-container"></div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import axios from 'axios'

import { globalState } from '../stores/project'

const DEFAULT_SCRIPT = `第一场
内景 公寓 夜

主角独自坐在电脑前，桌面上只有一盏冷白色台灯。屏幕里不断闪烁的旧信号像在提醒她，过去还没有结束。

第二场
外景 港口 夜

风把雨线压成斜角，远处的船灯在黑海上摇晃。主角提着设备箱赶到码头，准备踏上回到事故现场的旅程。`

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

const code = ref(cleanGeneratedText(globalState.scriptContent || DEFAULT_SCRIPT))
const loading = ref(false)

let myChart = null
let syncTimer = null

const contentStats = computed(() => {
  const value = code.value || ''
  const paragraphs = value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean).length

  return {
    characters: value.length,
    paragraphs,
  }
})

watch(
  () => code.value,
  (newVal) => {
    globalState.scriptContent = cleanGeneratedText(newVal)
    queueGraphSync(globalState.scriptContent)
  }
)

const MONACO_OPTIONS = {
  automaticLayout: true,
  wordWrap: 'on',
  minimap: { enabled: false },
  lineNumbersMinChars: 3,
  fontSize: 15,
  fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
  padding: { top: 18, bottom: 18 },
  smoothScrolling: true,
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

  const safeGraph =
    graphData?.nodes?.length && graphData?.links?.length !== undefined ? graphData : fallbackGraph

  const normalizedNodes = (safeGraph.nodes || []).map((node) => ({
    ...node,
    symbolSize: node.category === 0 ? 54 : node.category === 2 ? 34 : 42,
  }))

  myChart.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: { formatter: '{b}' },
      animationDurationUpdate: 800,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: 'force',
          force: { repulsion: 280, edgeLength: 120 },
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
            color: '#eef4ff',
          },
          edgeSymbol: ['circle', 'arrow'],
          edgeSymbolSize: [4, 10],
          edgeLabel: {
            show: true,
            fontSize: 10,
            formatter: '{c}',
            color: '#9eb0c8',
          },
          data: normalizedNodes,
          links: (safeGraph.links || []).map((link) => ({ ...link, value: link.name })),
          categories: [
            { name: '角色 Character' },
            { name: '剧本节拍 Beat' },
            { name: '伏笔 Foreshadowing' },
          ],
          lineStyle: { color: '#7f8da3', curveness: 0.1 },
        },
      ],
    },
    true
  )
}

const syncGraph = async (content) => {
  if (!myChart) return
  try {
    const res = await axios.post('/api/narrative/sync_graph', { content })
    renderGraph(res.data.data)
  } catch (error) {
    console.error(error)
  }
}

const queueGraphSync = (content) => {
  if (syncTimer) clearTimeout(syncTimer)
  syncTimer = setTimeout(() => {
    syncGraph(content)
  }, 400)
}

const initChart = async () => {
  const chartDom = document.getElementById('chart-container')
  if (!chartDom) return

  myChart = echarts.init(chartDom)
  myChart.showLoading({
    text: '正在同步剧情状态网络...',
    color: '#4f8cff',
    textColor: '#d7e6ff',
    maskColor: 'rgba(9, 21, 40, 0.2)',
  })

  try {
    await syncGraph(globalState.scriptContent || code.value)
  } finally {
    myChart.hideLoading()
  }
}

const handleEditorChange = (value) => {
  if (typeof value === 'string') {
    code.value = cleanGeneratedText(value)
  }
}

const generateNextBeat = async () => {
  loading.value = true
  try {
    const res = await axios.post('/api/narrative/generate_beat', { content: code.value })
    code.value = cleanGeneratedText(`${code.value}\n\n${res.data.text}`)
    if (res.data?.data) {
      renderGraph(res.data.data)
    } else {
      await syncGraph(code.value)
    }
    ElMessage.success('下一节拍已生成，右侧状态网络也已同步刷新。')
  } catch (error) {
    console.error(error)
    ElMessage.warning('生成下一节拍失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const extractFingerprint = () => {
  ElMessage({
    message: '叙事指纹提取功能已触发，当前版本保留原有逻辑入口。',
    type: 'success',
    duration: 3000,
  })
}

const handleResize = () => {
  if (myChart) myChart.resize()
}

onMounted(() => {
  setTimeout(() => {
    initChart()
  }, 200)
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
.editor-page {
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(34, 115, 255, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(10, 181, 134, 0.1), transparent 24%),
    linear-gradient(180deg, #eaf0fa 0%, #f7f9fd 100%);
}

.editor-shell {
  max-width: 1440px;
  margin: 0 auto;
}

.editor-hero {
  display: flex;
  justify-content: space-between;
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
.panel-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(248, 251, 255, 0.72);
}

.hero-left h1 {
  margin: 0 0 10px;
  font-size: 34px;
}

.hero-left p:last-child {
  margin: 0;
  max-width: 700px;
  line-height: 1.75;
  font-size: 15px;
}

.hero-actions {
  display: flex;
  align-items: center;
  align-content: flex-start;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  max-width: 520px;
}

.hero-chip {
  padding: 10px 14px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.1);
}

.hero-chip.danger {
  color: #ffd6d6;
}

.hero-chip.success {
  color: #ddffe2;
}

.hero-chip.info {
  color: #dbeaff;
}

.metrics-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 22px 0;
}

.metric-card {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 10px 30px rgba(37, 70, 120, 0.08);
  border: 1px solid rgba(16, 51, 92, 0.08);
}

.metric-card span {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #748297;
}

.metric-card strong {
  font-size: 22px;
  color: #10233e;
}

.metric-card small {
  margin-left: 8px;
  color: #7d8a9d;
}

.workspace-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 20px;
}

.panel {
  min-height: 720px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 18px 50px rgba(37, 70, 120, 0.08);
}

.editor-panel {
  background: linear-gradient(180deg, #0d1626 0%, #101d30 100%);
  border: 1px solid rgba(39, 66, 107, 0.4);
}

.graph-panel {
  background: linear-gradient(180deg, #15253a 0%, #182c46 100%);
  border: 1px solid rgba(52, 92, 146, 0.26);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.panel-head h2 {
  margin: 0;
  font-size: 22px;
  color: #eef4ff;
}

.panel-status {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #e8f2ff;
  font-size: 12px;
}

.panel-status.blue {
  background: rgba(79, 140, 255, 0.14);
  color: #bcd5ff;
}

.panel-body {
  height: calc(100% - 85px);
}

.editor-body {
  background: transparent;
}

.graph-legend {
  display: flex;
  gap: 16px;
  padding: 14px 22px 0;
  color: #d0dbed;
  font-size: 13px;
  flex-wrap: wrap;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 8px;
  border-radius: 999px;
}

.dot.character {
  background: #4f8cff;
}

.dot.beat {
  background: #70f0a8;
}

.dot.foreshadow {
  background: #f1d45a;
}

.graph-body {
  padding: 10px 16px 18px;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 610px;
}

:deep(.monaco-editor),
:deep(.monaco-editor .overflow-guard) {
  border-radius: 0 0 24px 24px;
}

:deep(.monaco-editor) {
  padding-top: 10px;
}

@media (max-width: 1180px) {
  .editor-hero,
  .workspace-grid,
  .metrics-strip {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .editor-hero {
    align-items: flex-start;
  }

  .hero-actions {
    justify-content: flex-start;
    max-width: none;
  }
}

@media (max-width: 900px) {
  .editor-page {
    padding: 16px;
  }

  .panel-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-container {
    min-height: 420px;
  }
}
</style>
