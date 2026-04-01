# -*- coding: utf-8 -*-
import os

req_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\RequirementView.vue"
editor_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue"

req_content = """<template>
  <div style="padding:20px;">
    <el-card>
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span>结构化需求输入（底层已接入 DeepSeek API）</span>
          <el-button type="primary" size="large" @click="generateAndGo" :loading="loading">智能校验并生成初始剧本</el-button>
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
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { globalState } from '../stores/project.js'
import axios from 'axios'

const router = useRouter()
const activeTab = ref('base')
const loading = ref(false)

function addCharacter() {
  globalState.chars.push({ name: '新角色', role: '配角', arc: '无', locked: false })
}
function delCharacter(index) {
  globalState.chars.splice(index, 1)
}

async function generateAndGo() {
  if (!globalState.title || !globalState.theme) {
    ElMessage.warning('请输入剧本标题和核心主题')
    return
  }

  loading.value = true
  ElMessage.info('正在调用大模型生成专属剧本初稿，约需十多秒，请耐心等待...')
  
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
      model: 'deepseek',
      temperature: 0.7,
      max_tokens: 2000
    })
    
    if (response.data && response.data.content) {
      globalState.scriptContent = response.data.content
      ElMessage.success('DeepSeek模型创作成功！即将接入共创编辑器...')
      setTimeout(() => {
        router.push('/editor')
      }, 1000)
    } else {
      throw new Error('未获取到返回结果')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('调用AI大模型失败，请检查网络或后端的 API Key 配置')
  } finally {
    loading.value = false
  }
}
</script>"""

editor_content = """<template>
  <div style="display:flex; flex-direction:column; height: 100%;">
    <div style="background:white; padding:10px 20px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ddd;">
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-weight:bold; font-size:16px;">《{{ globalState.title }}》</span>
        <el-tag type="success" effect="plain" size="small"><i class="el-icon-check"></i> 实时云端同步</el-tag>
      </div>
      <div>
        <el-button size="small" type="primary" @click="showExport=true">📥 导出剧本</el-button>
      </div>
    </div>

    <div style="display:flex; flex:1;">
      <div style="flex:2; padding:20px; border-right:1px solid #eee; background:#fff;">
        <h3 style="margin-top:0; color:#333;">实时人机共创编辑器</h3>
        <el-input v-model="globalState.scriptContent" type="textarea" :rows="26" placeholder="等待剧本正文生成或加载..."></el-input>
      </div>
      <div style="flex:1; padding:20px; background:#fafafa; border-left:1px solid #ddd;">
        <h3 style="margin-top:0; color:#333;">智能剧本辅助系统</h3>
        
        <el-card shadow="never" style="margin-bottom:15px">
            <div style="font-weight:bold; margin-bottom:5px;">💡 AI灵感续写 (基于DeepSeek大模型)</div>
            <div style="font-size:13px; color:#666; margin-bottom:10px;">告诉AI接下来发生了什么，AI会帮你生成正文：</div>
            <el-input type="textarea" :rows="3" placeholder="例如：主人公突然发现了一个隐藏的秘密..." v-model="agentPrompt"></el-input>
            <el-button style="margin-top:10px; width: 100%;" type="primary" :loading="aiLoading" @click="runAgent">指令生成</el-button>
        </el-card>

        <el-card shadow="never">
            <div style="font-weight:bold; margin-bottom:5px;">📊 剧情合理性批判 (多Agent反思)</div>
            <div style="font-size:13px; color:#666; margin-bottom:10px;">结合目前的世界观（{{globalState.worldRules}}），判断逻辑漏洞。</div>
            <el-button style="margin-top:10px; width: 100%;" @click="critiquePlot" :loading="critiqueLoading">一键批判查漏补缺</el-button>
            <div style="margin-top:15px; font-size:13px; white-space:pre-wrap; color:#d35400" v-if="critiqueResult">
               {{ critiqueResult }}
            </div>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="showExport" title="导出剧本" width="400px">
      <p>正在开发中的功能扩展点...</p>
      <template #footer>
         <el-button @click="showExport=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { globalState } from '../stores/project.js'
import axios from 'axios'

const showExport = ref(false)
const agentPrompt = ref('')
const aiLoading = ref(false)
const critiqueLoading = ref(false)
const critiqueResult = ref('')

async function critiquePlot() {
  if(!globalState.scriptContent) {
    ElMessage.warning('剧本当前为空。')
    return
  }
  critiqueLoading.value = true
  critiqueResult.value = '正在思考批判逻辑...'
  const prompt = `你是一个专业的剧本剧评人。请基于以下正在创作的剧本和设定的世界观，挑出逻辑硬伤，或者给出让剧情更加跌宕起伏的建议。请直接说重点，最多列取3条痛点。
剧本体裁：${globalState.track}
世界观：${globalState.worldRules}
当前剧本内容：${globalState.scriptContent}`

  try {
     const response = await axios.post('/api/ai/generate', {
      prompt: prompt,
      model: 'deepseek',
      temperature: 0.8,
      max_tokens: 800
    })
    critiqueResult.value = response.data.content
  } catch(e) {
    critiqueResult.value = '请求AI接口批判失败。'
  } finally {
    critiqueLoading.value = false
  }
}

async function runAgent() {
  if(!agentPrompt.value.trim()) {
    ElMessage.warning('请输入想要AI续写的指令/情节方向')
    return;
  }
  
  aiLoading.value = true
  ElMessage.info('正在请求AI大模型续写情节，请稍候...')
  
  const promptStr = `你是一位专业编剧。我们需要接着现有的剧本内容继续往下写。
全局设定如下：标题《${globalState.title}》，核心冲突是${globalState.worldConflict}。
已有剧本正文：
${globalState.scriptContent}

【当前的续写要求】：${agentPrompt.value}

要求：不需要说废话或者解释，只管输出接着写的剧情即可。`

  try {
    const response = await axios.post('/api/ai/generate', {
      prompt: promptStr,
      model: 'deepseek',
      temperature: 0.8,
      max_tokens: 1200
    })
    
    if (response.data && response.data.content) {
      globalState.scriptContent += `\n\n` + response.data.content
      agentPrompt.value = ''
      ElMessage.success('AI续写成功并已拼接进大纲文本框！')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('调用真实AI续写失败，请检查连接')
  } finally {
    aiLoading.value = false
  }
}
</script>"""

with open(req_path, "w", encoding="utf-8") as f:
    f.write(req_content)

with open(editor_path, "w", encoding="utf-8") as f:
    f.write(editor_content)

print("Actual AI views connected successfully")
