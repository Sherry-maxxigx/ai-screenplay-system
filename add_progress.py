import os

vue_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\RequirementView.vue"

new_content = """<template>
  <div style="padding:20px;">
    <el-card>
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span>结构化需求输入（底层已接入 智谱GLM-4 API）</span>
          <el-button type="primary" size="large" @click="generateAndGo" :loading="loading">智能大模型生成剧本初稿</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="📋 基础信息" name="base">
          <el-form label-width="120px" style="max-width:600px; margin-top:20px;">
            <el-form-item label="剧本标题" required><el-input v-model="globalState.title" /></el-form-item>
            <el-form-item label="目标赛道">
              <el-select v-model="globalState.track" style="width:100%">
                <el-option label="短剧" value="短剧"/>
                <el-option label="院线电影" value="电影"/>
                <el-option label="互动影视" value="互动影视"/>
              </el-select>
            </el-form-item>
            <el-form-item label="核心立意"><el-input type="textarea" rows="3" v-model="globalState.theme" /></el-form-item>
            <el-form-item label="受众画像"><el-input v-model="globalState.audience" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="🎭 结构化人物卡" name="chars">
          <div style="margin-top:20px;">
            <el-button type="success" size="small" style="margin-bottom:10px;" @click="addCharacter">+ 添加人物设定</el-button>
            <el-table :data="globalState.chars" border>
              <el-table-column prop="name" label="姓名" width="120">
                <template #default="scope">
                  <el-input v-model="scope.row.name" size="small"/>
                </template>
              </el-table-column>
              <el-table-column prop="role" label="核心定位" width="150" >
                <template #default="scope">
                  <el-input v-model="scope.row.role" size="small"/>
                </template>
              </el-table-column>
              <el-table-column prop="arc" label="人物高光/使命点" >
                <template #default="scope">
                  <el-input v-model="scope.row.arc" size="small"/>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="scope">
                   <el-button type="danger" size="small" @click="delCharacter(scope.$index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="🌍 世界观背景" name="world">
          <el-form label-width="120px" style="max-width:800px; margin-top:20px;">
            <el-form-item label="时空物理背景"><el-input type="textarea" v-model="globalState.worldTime" /></el-form-item>
            <el-form-item label="社会运行法则"><el-input type="textarea" v-model="globalState.worldRules" /></el-form-item>
            <el-form-item label="核心冲突源"><el-input type="textarea" v-model="globalState.worldConflict" /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 可视化进度条弹窗 -->
    <el-dialog v-model="showProgress" title="🤖 智谱 GLM-4 剧本推演中..." width="450px" :close-on-click-modal="false" :show-close="false">
      <div style="text-align: center; padding: 20px 0;">
        <el-progress type="dashboard" :percentage="progress" :color="progressColors"></el-progress>
        <p style="margin-top: 20px; font-weight: bold; color: #409eff; font-size: 15px;">{{ progressText }}</p>
        <p style="font-size: 12px; color: #999; margin-top: 8px;">大型模型分析推理及文本生成通常需要 10~25 秒，请耐心等待</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { globalState } from '../stores/project.js'
import axios from 'axios'

const router = useRouter()
const activeTab = ref('base')
const loading = ref(false)

// 进度条状态控制
const showProgress = ref(false)
const progress = ref(0)
const progressText = ref('')
let progressTimer = null

const progressColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 }
]

function addCharacter() {
  globalState.chars.push({ name: '新角色', role: '配角', arc: '无', locked: false })
}
function delCharacter(index) {
  globalState.chars.splice(index, 1)
}

onUnmounted(() => {
  if (progressTimer) clearInterval(progressTimer)
})

async function generateAndGo() {
  if (!globalState.title || !globalState.theme) {
    ElMessage.warning('请输入剧本标题和核心主题')
    return
  }

  // 展开进度条弹窗
  loading.value = true
  showProgress.value = true
  progress.value = 0
  progressText.value = '正在进行环境初始化...'
  
  // 模拟各个认知阶段的进度加载（大模型无法直接提供百分比，通过时间估算）
  progressTimer = setInterval(() => {
    if (progress.value < 98) {
      let increment = 5;
      if (progress.value > 85) increment = 1;      // 接近尾声时放缓
      else if (progress.value > 50) increment = 2; // 中期平缓
      
      progress.value = Math.min(progress.value + increment, 98)

      if (progress.value < 20) progressText.value = '✅ 正在提取世界观、人物传记与设定...'
      else if (progress.value < 45) progressText.value = '🧠 智谱 GLM-4 正在分析人物底层弧光...'
      else if (progress.value < 70) progressText.value = '⚔️ 正在组织全局冲突与矛盾情节...'
      else if (progress.value < 90) progressText.value = '✍️ 正在逐字撰写剧本对白、刻画场景...'
      else progressText.value = '⏳ 文本内容已基本成型，等待模型输出最终片段...'
    }
  }, 600) // 整体达到98需要约 15~20 秒左右，完美契合 GLM-4 的响应时间
  
  let charDesc = globalState.chars.map(c => `${c.name}(${c.role}): ${c.arc}`).join('; ')
  const prompt = `你是一位专业编剧。请根据以下大纲创作剧本的【第一场戏】：
标题：《${globalState.title}》
赛道：${globalState.track}
受众：${globalState.audience}
核心立意：${globalState.theme}
世界观设定：${globalState.worldTime}。规则：${globalState.worldRules}。
核心冲突：${globalState.worldConflict}
主要人物：${charDesc}

要求：
1. 采用专业剧本格式(包含：场景标题、内/外景、日/夜、动作描述、人物对白)。
2. 大量刻画人物情感与矛盾，体现核心冲突。
3. 请直接输出剧本内容，不要说废话。`

  try {
    const response = await axios.post('/api/ai/generate', {
      prompt: prompt,
      model: 'glm-4',
      temperature: 0.7,
      max_tokens: 2000
    })
    
    if (response.data && response.data.content) {
      // 请求成功归位并跳转
      if (progressTimer) clearInterval(progressTimer)
      progress.value = 100
      progressText.value = '🎉 剧本生成成功！准备接入协同网关...'
      
      globalState.scriptContent = response.data.content
      
      setTimeout(() => {
        showProgress.value = false
        router.push('/editor')
      }, 1200)
    } else {
      throw new Error('未获取到返回结果')
    }
  } catch (error) {
    console.error(error)
    if (progressTimer) clearInterval(progressTimer)
    showProgress.value = false
    ElMessage.error('调用大模型失败或超时，请检查服务及网络状态。')
  } finally {
    loading.value = false
  }
}
</script>"""

with open(vue_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Added visual progress bar successfully!")