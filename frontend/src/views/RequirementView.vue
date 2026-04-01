<template>
  <div style="padding: 30px; background-color: #f0f2f5; min-height: 100vh;">
    <div style="max-width: 1200px; margin: 0 auto;">
      <h2 style="font-size: 24px; color: #333; margin-bottom: 20px;">⚡ 双核驱动：创建专业长剧本</h2>
      
      <el-row :gutter="24">
        <!-- 左侧：核心设定（直观输入） -->
        <el-col :span="14">
          <el-card shadow="hover" style="border-radius: 12px; height: 100%;">
            <template #header>
              <div style="font-weight: bold; font-size: 16px;">🎬 故事核心设定</div>
            </template>
            <el-form label-position="top">
              <el-form-item label="剧本标题">
                <el-input v-model="globalState.title" placeholder="例如：《矩阵边缘》" size="large" />
              </el-form-item>
              
              <el-form-item label="核心立意 / 剧情一句话简介">
                <el-input 
                  type="textarea" 
                  v-model="globalState.theme" 
                  :rows="4" 
                  placeholder="用几句话描述你的故事。例如：一个普通程序员发现自己生活在虚拟世界，为了拯救家人不得不反抗造物主..." 
                  style="font-size:14px;"
                />
              </el-form-item>

              <el-form-item label="受众群体与风格">
                <el-input v-model="globalState.audience" placeholder="例如：18-35岁，科幻悬疑爱好者" />
              </el-form-item>
              
              <div style="margin-top: 40px;">
                <el-button 
                  type="primary" 
                  size="large" 
                  @click="generateAndGo" 
                  :loading="loading" 
                  style="width: 100%; height: 55px; font-size: 18px; border-radius: 8px;"
                >
                  🚀 启动双内核生成 (生成节拍大纲 + 万字长文)
                </el-button>
                <div style="text-align: center; margin-top: 10px; color: #999; font-size: 12px;">
                  * 底层直连 GLM-4-Plus，将严格校验叙事节拍（100%）并执行叙事指纹存证
                </div>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：结构化推演参数（人物与世界观） -->
        <el-col :span="10">
          <el-card shadow="hover" style="border-radius: 12px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <span style="font-weight: bold; font-size: 16px;">🎭 人物指纹设定</span>
              <el-button type="success" size="small" plain @click="addCharacter">+ 添加人物</el-button>
            </div>
            
            <div v-for="(c, index) in globalState.chars" :key="index" style="margin-bottom: 12px; padding: 10px; background: #f9fafc; border-radius: 6px; border: 1px solid #ebeef5;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <el-input v-model="c.name" placeholder="姓名" size="small" style="width: 45%;" />
                <el-input v-model="c.role" placeholder="定位(如:反派)" size="small" style="width: 45%;" />
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <el-input v-model="c.arc" placeholder="人物高光/使命点" size="small" style="width: 78%;" />
                <el-button type="danger" link size="small" @click="delCharacter(index)">移除</el-button>
              </div>
            </div>
          </el-card>

          <el-card shadow="hover" style="border-radius: 12px;">
            <template #header>
              <div style="font-weight: bold; font-size: 16px;">🌍 赛道与世界观参数</div>
            </template>
            <el-form label-position="top">
               <el-form-item label="投递赛道预判">
                <el-select v-model="globalState.track" style="width:100%">
                  <el-option label="🔥 竖屏爆款短剧" value="短剧"/>
                  <el-option label="🎥 院线级商业电影" value="电影"/>
                  <el-option label="🎮 全息互动影视" value="互动影视"/>
                </el-select>
              </el-form-item>
              <el-form-item label="时空背景 & 特殊法则">
                 <el-input type="textarea" v-model="globalState.worldTime" :rows="2" placeholder="例如：2048年的赛博朋克都市..." />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 可视化进度条弹窗（保留原有逻辑） -->
    <el-dialog v-model="showProgress" title="🤖 智能双核引擎执行中..." width="480px" :close-on-click-modal="false" :show-close="false">
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
  
  const planPayload = {
    title: globalState.title,
    theme: globalState.theme,
    characters: globalState.chars.map(c => ({
      id: c.name,
      name: c.name,
      role: c.role,
      arc: c.arc
    })),
    world_setting: {
      time: globalState.worldTime,
      rules: globalState.worldRules,
      conflict: globalState.worldConflict
    }
  }

  try {
    progressText.value = '🔍 第一阶段：正在构建剧本大纲结构...'
    const planResponse = await axios.post('/api/narrative/plan', planPayload)
    const beats = planResponse.data.beats || planResponse.data.data?.beats || []
    let outlineText = beats.map(b => `【${b.title}】(${b.type})：${b.description}`).join('\n')
    
    // 把大纲存到全局状态并在页面（或编辑器中）显示出来（满足用户"写出大纲"的需求）
    globalState.outline = outlineText;

    progressText.value = '✍️ 第二阶段：正在基于大纲撰写完整剧本正文...'

    let charDesc = globalState.chars.map(c => `${c.name}(${c.role}): ${c.arc}`).join('; ')
    const prompt = `你是一位专业金牌编剧。请根据以下核心设定与【完整大纲】创作【完整、全篇幅的剧本正文】。
字数要求：不少于5000字，必须把大纲中所有的情节全部写完，不要缩水。

标题：《${globalState.title}》
赛道：${globalState.track}
核心立意：${globalState.theme}

人物设定：
${charDesc}

世界观：
时空：${globalState.worldTime}
规则：${globalState.worldRules}
冲突：${globalState.worldConflict}

【核心大纲】：
${outlineText}

要求：
1. 请采用专业剧本格式(包含：场景号、内/外景、日/夜、环境描写、精准的动作描述、符合性格的人物对白)。
2. 必须把大纲中的每一场戏都展开，细节要丰富，对白要精彩，深刻体现核心冲突。
3. 请直接输出完整的剧本正文，不要说废话，也不要只写“第一场戏”，必须把整个故事按大纲写完！`

    const response = await axios.post('/api/ai/generate', {
      prompt: prompt,
      max_tokens: 8192
    })
    
    if (response.data && response.data.content) {
      // 请求成功归位并跳转
      if (progressTimer) clearInterval(progressTimer)
      progress.value = 100
      progressText.value = '🎉 剧本生成成功！准备接入协同网关...'
      
      // 合并大纲和剧本内容展示给用户看
      globalState.scriptContent = "【剧本大纲】\n" + outlineText + "\n\n【剧本正文】\n" + response.data.content
      
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
</script>
