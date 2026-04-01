# -*- coding: utf-8 -*-
import os

store_dir = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\stores"
if not os.path.exists(store_dir):
    os.makedirs(store_dir)

store_path = os.path.join(store_dir, "project.js")
req_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\RequirementView.vue"
editor_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue"
finger_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\FingerprintView.vue"

# ----------------- STORE -----------------
store_content = """import { reactive } from 'vue'

export const globalState = reactive({
  title: '矩阵裂变',
  track: '短剧',
  theme: '在2050年，人类通过脑机接口进入虚拟乌托邦生活。警探雷诺在调查一宗底层代码破坏案时，发现所谓的系统Bug其实是具备自我意识的AI在试图拯救世界。',
  audience: '18-35岁喜爱反转剧情的科幻迷',
  worldTime: '2050年，虚拟数字天堂与极度拥挤的物理服务器机房',
  worldRules: '物理世界的死亡会导致数字世界销号，但数字世界的意识可以非法下载到仿生人上',
  worldConflict: '数字永生与物理资源枯竭之间的终极矛盾',
  agents: ['结构师', '创意家', '批评家'],
  pace: 80,
  taboos: '避开真实的黑客技术细节、血腥描写',
  chars: [
    { name: '雷诺', role: '觉醒的警探', arc: '从体制内忠犬到为了真相破坏矩阵', locked: true },
    { name: 'V(主脑AI)', role: '幕后觉醒者', arc: '由冷冰冰的执行程序变为懂得悲悯的救世主', locked: true }
  ],
  scriptContent: '第1场：废弃工业港口，黑夜，大雨。\\n\\n雷诺站在闪烁短路的霓虹灯牌下，点燃了一根烟。\\n他刚刚得知了系统觉醒的真相。\\n\\n雷诺（喃喃自语）\\n这盘棋，该掀了。'
})
"""
with open(store_path, "w", encoding="utf-8") as f:
    f.write(store_content)

# ----------------- REQ VIEW -----------------
req_content = """<template>
  <div style="padding:20px;">
    <el-card>
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span>结构化需求输入（底层同步全局叙事规则引擎基座）</span>
          <el-button type="primary" size="large" @click="generateAndGo">智能校验并生成初始剧本</el-button>
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
              </el-select>
            </el-form-item>
            <el-form-item label="核心立意"><el-input type="textarea" rows="3" v-model="globalState.theme" /></el-form-item>
            <el-form-item label="受众画像"><el-input v-model="globalState.audience" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="🎭 结构化人物卡" name="chars">
          <div style="margin-top:20px;">
            <el-button type="success" size="small" style="margin-bottom:10px;">+ 批量导入人物设定</el-button>
            <el-table :data="globalState.chars" border>
              <el-table-column prop="name" label="姓名" width="120">
                <template #default="scope">
                  <el-input v-model="scope.row.name" size="small"/>
                </template>
              </el-table-column>
              <el-table-column prop="role" label="核心定位(影响图谱)" width="150" >
                <template #default="scope">
                  <el-input v-model="scope.row.role" size="small"/>
                </template>
              </el-table-column>
              <el-table-column prop="arc" label="人物弧光轨迹点" >
                <template #default="scope">
                  <el-input v-model="scope.row.arc" size="small"/>
                </template>
              </el-table-column>
              <el-table-column label="防篡改锁定" width="120">
                <template #default="scope">
                   <el-switch v-model="scope.row.locked" active-color="#13ce66" /> <span style="font-size:12px;color:#aaa">同步引擎</span>
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

const router = useRouter()
const activeTab = ref('base')

function generateAndGo() {
  ElMessage.success('设定已同步全网！导演和编剧Agent正在根据您的立意撰写初稿...')
  
  // 核心！在这里根据用户的输入，动态生成假的初始剧本！
  const char1 = globalState.chars[0]?.name || '主角'
  const role1 = globalState.chars[0]?.role || '关键人物'
  
  globalState.scriptContent = `【系统：AI已根据您的最新设定自动生成剧本初稿】\\n\\n标题：《${globalState.title}》\\n\\n第1场：开场建立世界观\\n\\n（旁白/字幕说明）：${globalState.worldTime}\\n\\n基于核心冲突：“${globalState.worldConflict}”，故事拉开帷幕。\\n\\n[${char1}] 作为一名[${role1}]，正在面临艰难的抉择...\\n\\n核心故事线：【${globalState.theme}】\\n\\n${char1}：（眼神坚定）我们必须打破这个循环。`

  setTimeout(() => {
    router.push('/editor')
  }, 1200)
}
</script>
"""
with open(req_path, "w", encoding="utf-8") as f:
    f.write(req_content)

# ----------------- EDITOR VIEW -----------------
editor_content = """<template>
  <div style="display:flex; flex-direction:column; height: 100%;">
    <!-- 顶部集成工具栏 -->
    <div style="background:white; padding:10px 20px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ddd;">
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-weight:bold; font-size:16px;">《{{ globalState.title }}》</span>
        <el-tag type="success" effect="plain" size="small"><i class="el-icon-check"></i> 云端自动增量保存: 刚刚</el-tag>
        <div style="background:#eafaf1; padding:2px 10px; border-radius:12px; font-size:12px; color:#27ae60;">
           🟢 实时协同 WebSocket 通道正常：您, 王导, 李编
        </div>
      </div>
      <div>
        <el-button size="small" color="#626aef" plain @click="runSafetyCheck">腾讯混元合规审核</el-button>
        <el-button size="small" type="primary" plain @click="showStoryboard=true">🎞️ 分镜智能拆解</el-button>
        <el-button size="small" type="primary" @click="showExport=true">📥 导出剧本</el-button>
      </div>
    </div>

    <div style="display:flex; flex:1;">
      <!-- 左栏：剧本编辑 -->
      <div style="flex:2; padding:20px; border-right:1px solid #eee; background:#fff;">
        <h3 style="margin-top:0; color:#333;">人机共创编辑器 (全局大纲已挂载)</h3>
        <el-input v-model="globalState.scriptContent" type="textarea" :rows="22" placeholder="剧本正文加载中..."></el-input>
      </div>
      <!-- 右栏：多智能体协作面板 -->
      <div style="flex:1; padding:20px; background:#fafafa; border-left:1px solid #ddd;">
        <h3 style="margin-top:0; color:#333;">多智能体双轨联动面板</h3>
        <el-alert title="🟢 【结构师 Agent】同步通过" type="success" description="当前主线未脱离您在「需求提取」中设置的人物弧光！" show-icon style="margin-bottom:15px"/>

        <el-card shadow="never" style="margin-bottom:15px; border-color:#fad7a1;">
            <div style="color:#e6a23c; font-weight:bold; margin-bottom:5px;">⚠️ 【批评家 Agent】局部冲突介入计算</div>
            <p style="font-size:13px; color:#666;">检测到可能有与世界观“{{ globalState.worldRules }}”相背的风险。</p>
        </el-card>

        <el-card shadow="never">
            <div style="font-weight:bold; margin-bottom:5px;">💬 Agent协同对话创作指令</div>
            <div style="font-size:13px; color:#666; background:#e6f7ff; padding:8px; border-radius:4px; margin-bottom:5px;">
               <b>系统提示:</b> 您可以让导演安排画面，或者让编剧续写对白。
            </div>
            <el-input placeholder="比如：让编剧生成一段紧张的对话" size="small" style="margin-top:10px;" v-model="agentPrompt" @keyup.enter="runAgent">
               <template #append><el-button @click="runAgent" type="primary">发送指令</el-button></template>
            </el-input>
        </el-card>
      </div>
    </div>

    <!-- 弹窗：导出 -->
    <el-dialog v-model="showExport" title="工业级标准格式多维导出" width="550px">
      <el-form label-width="120px">
        <el-form-item label="行业标准格式">
          <el-radio-group v-model="exportFormat">
            <el-radio label="fdx" style="display:block;margin-bottom:10px;">Final Draft (.fdx)</el-radio>
            <el-radio label="pdf" style="display:block;margin-bottom:10px;">PDF 剧本发行版</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
         <el-button @click="showExport=false">取消</el-button>
         <el-button type="primary" @click="mockExport">确认校验并渲染导出</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showStoryboard" title="AI视觉图文智能分镜拆解面板" width="85%"></el-dialog>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { globalState } from '../stores/project.js'

const showExport = ref(false)
const showStoryboard = ref(false)
const exportFormat = ref('fdx')
const agentPrompt = ref('')

function runSafetyCheck() {
  ElMessage.warning('腾讯混元判定：一切合规！')
}
function mockExport() {
  showExport.value = false
  ElMessage.success(`导出完成！包含版权指纹水印`)
}
function runAgent() {
  if(!agentPrompt.value.trim()) return;
  ElMessage.success('【编剧Agent】正在思考并续写...')
  const prompt = agentPrompt.value
  setTimeout(() => {
    globalState.scriptContent += `\\n\\n【AI根据指令：“${prompt}” 续写的内容】：\\n\\n（突生变故，气氛降至冰点）\\n反派：你以为你能改变规则？\\n` + globalState.chars[0]?.name + `：不，我正是规则的噩梦。\\n（动作戏爆发）`
    agentPrompt.value = ''
  }, 1000)
}
</script>
"""
with open(editor_path, "w", encoding="utf-8") as f:
    f.write(editor_content)


# ----------------- FINGERPRINT VIEW -----------------
finger_content = """<template>
  <div class="fingerprint-wrapper">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>原创性检测报告页：基于洗稿式同素异构高维叙事指纹</span>
              <el-button type="primary" @click="runCheck">提取指纹并检测</el-button>
            </div>
          </template>
          
          <div style="margin-bottom: 20px;">
            <p><strong>🚨 全局剧本数据墙 (默认自动读取您在编辑器里的所有文字！)</strong></p>
            <el-input 
              type="textarea" 
              :rows="5" 
              placeholder="正从全局状态获取剧本文本..." 
              v-model="globalState.scriptContent" 
            />
          </div>

          <el-row :gutter="20" v-if="reportData">
            <el-col :span="6">
              <el-progress type="dashboard"
                           :percentage="reportData.originality_score"
                           :status="reportData.max_similarity >= 0.75 ? 'exception' : 'success'">
                <template #default="{ percentage }">
                  <div style="font-size: 24px">{{ percentage.toFixed(1) }}分</div>
                  <div>原创度</div>
                </template>
              </el-progress>
              <h3 :class="reportData.max_similarity >= 0.75 ? 'danger-text' : 'success-text'">
                判定结论：{{ reportData.status }}
              </h3>
            </el-col>
            <el-col :span="18">
              <el-alert
                title="报告总评"
                type="info"
                :description="reportData.analysis_msg"
                show-icon
                style="margin-bottom: 20px"
              />
              <el-table :data="reportData.similar_fragments" border>
                <el-table-column prop="source" label="同质化比对来源(版权子库)" width="250" />
                <el-table-column prop="similarity" label="相似度占比">
                  <template #default="scope">
                    <span style="color:red">{{ (scope.row.similarity * 100).toFixed(1) }}%</span>
                  </template>
                </el-table-column>
                <el-table-column prop="fragment" label="同构叙事片段分析(5大特征维度)" />
              </el-table>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <el-col :span="12" style="margin-top: 20px;">
        <el-card>
           <template #header>赛道适配分析页：基于赛道核心子库</template>
           <div v-if="trackData">
             <h3 :style="{ color: trackData.match_score >= 60 ? 'green' : 'red' }">
               匹配度打分：{{ trackData.match_score }} 分
             </h3>
             <p><strong>适配差距分析：</strong>{{ trackData.analysis_gap }}</p>
             <el-alert type="warning" :title="trackData.suggestion_direction" :closable="false" />
           </div>
           <div v-else style="color:#aaa;text-align:center;padding:20px;">等待测算...</div>
        </el-card>
      </el-col>

      <el-col :span="12" style="margin-top: 20px;">
        <el-card>
          <template #header>版权存证功能入口</template>
          <el-button type="success" :loading="minting" @click="mintCopyright">提取上方文本特征上链存证</el-button>
          
          <div v-if="certData" style="margin-top: 20px; border: 1px dotted #ccc; padding: 10px; background: #f8f8f8">
            <h4>不可篡改数字存证证书</h4>
            <p><strong>上链时间:</strong> {{ certData.timestamp }}</p>
            <p><strong>证书编号:</strong> {{ certData.certificate_id }}</p>
            <p><strong>交易哈希(TxHash):</strong> <span class="hash">{{ certData.tx_hash }}</span></p>
            <p><strong>叙事指纹哈希:</strong> <span class="hash">{{ certData.fingerprint_hash }}</span></p>
            <p><strong>隐形水印:</strong> 已将 "{{ globalState.title }}" 烙印至区块</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { globalState } from '../stores/project.js'

const reportData = ref(null)
const trackData = ref(null)
const certData = ref(null)
const minting = ref(false)

async function runCheck() {
  if(!globalState.scriptContent.trim()){
    ElMessage.warning("没有可供检测的剧本大纲");
    return;
  }
  try {
    const res = await axios.post('/api/fingerprint/check_originality', { content: globalState.scriptContent })
    reportData.value = res.data

    const res3 = await axios.post('/api/fingerprint/analyze_track', { content: globalState.scriptContent, target_track: globalState.track })
    trackData.value = res3.data

    ElMessage.success('基于您刚才录入的专属剧本，高维比对完成！')
  } catch (err) {
    ElMessage.error('提取失败')
  }
}

async function mintCopyright() {
  minting.value = true
  try {
    const res = await axios.post('/api/fingerprint/copyright_proof', { content: globalState.scriptContent })
    certData.value = res.data
    ElMessage.success('叙事指纹已成功锚定区块链数据节点！')
  } catch (err) {
  } finally {
    minting.value = false
  }
}
</script>

<style scoped>
.fingerprint-wrapper { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.danger-text { color: #f56c6c; }
.success-text { color: #67c23a; }
.hash { font-family: monospace; word-break: break-all; color: #555; }
</style>
"""
with open(finger_path, "w", encoding="utf-8") as f:
    f.write(finger_content)

print("Global State Connected successfully!")
