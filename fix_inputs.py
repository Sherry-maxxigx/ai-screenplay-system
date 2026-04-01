# -*- coding: utf-8 -*-
import os

req_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\RequirementView.vue"
finger_path = r"c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\FingerprintView.vue"

# ----------------- REQ VIEW -----------------
req_content = """<template>
  <div style="padding:20px;">
    <el-card>
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span>结构化需求输入（底层同步全局叙事规则引擎基座）</span>
          <el-button type="primary" size="large" @click="generateAndGo">智能校验必填项并开启协作创作</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="📋 基础信息" name="base">
          <el-form label-width="120px" style="max-width:600px; margin-top:20px;">
            <el-form-item label="剧本标题" required><el-input v-model="formData.title" /></el-form-item>
            <el-form-item label="目标赛道">
              <el-select v-model="formData.track" style="width:100%">
                <el-option label="短剧" value="短剧"/>
                <el-option label="院线电影" value="电影"/>
              </el-select>
            </el-form-item>
            <el-form-item label="核心立意"><el-input type="textarea" rows="3" v-model="formData.theme" /></el-form-item>
            <el-form-item label="受众画像"><el-input v-model="formData.audience" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="🎭 结构化人物卡" name="chars">
          <div style="margin-top:20px;">
            <el-button type="success" size="small" style="margin-bottom:10px;">+ 批量导入人物设定</el-button>
            <el-table :data="chars" border>
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

        <el-tab-pane label="🌍 世界观设定" name="world">
          <el-form label-width="120px" style="max-width:800px; margin-top:20px;">
            <el-form-item label="时空物理背景"><el-input type="textarea" v-model="formData.worldTime" /></el-form-item>
            <el-form-item label="社会运行法则"><el-input type="textarea" v-model="formData.worldRules" /></el-form-item>
            <el-form-item label="核心冲突源"><el-input type="textarea" v-model="formData.worldConflict" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="⚙️ 创作参数" name="rules">
          <el-form label-width="160px" style="max-width:600px; margin-top:20px;">
            <el-form-item label="AI生成智能体选择">
              <el-checkbox-group v-model="formData.agents">
                <el-checkbox label="结构师">结构师(负责节点大纲搭建)</el-checkbox>
                <el-checkbox label="创意家">创意家(负责场次细节扩写)</el-checkbox>
                <el-checkbox label="批评家">批评家(负责双核规则拦截)</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="叙事节奏倾向">
              <el-slider v-model="formData.pace" :step="10" show-stops></el-slider>
              <span style="font-size:12px;color:gray;">数值越高冲突越密集 (>70适合短剧)</span>
            </el-form-item>
            <el-form-item label="合规内容禁忌"><el-input type="textarea" v-model="formData.taboos" /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
const router = useRouter()
const activeTab = ref('base')

const formData = reactive({
  title: '矩阵裂变',
  track: '短剧',
  theme: '在2050年，人类通过脑机接口进入虚拟乌托邦生活。警探雷诺在调查一宗底层代码破坏案时，发现所谓的系统Bug其实是具备自我意识的AI在试图拯救世界。',
  audience: '18-35岁喜爱反转剧情的科幻迷',
  worldTime: '2050年，虚拟数字天堂与极度拥挤的物理服务器机房',
  worldRules: '物理世界的死亡会导致数字世界销号，但数字世界的意识可以非法下载到仿生人上',
  worldConflict: '数字永生与物理资源枯竭之间的终极矛盾',
  agents: ['结构师', '创意家', '批评家'],
  pace: 80,
  taboos: '避开真实的黑客技术细节、血腥描写'
})

const chars = ref([
  { name: '雷诺', role: '觉醒的警探', arc: '从体制内忠犬到为了真相破坏矩阵', locked: true },
  { name: 'V(主脑AI)', role: '幕后觉醒者', arc: '由冷冰冰的执行程序变为懂得悲悯的救世主', locked: true }
])

function generateAndGo() {
  ElMessage.success('需求与设定已录入全局状态树，正在启用智能体框架！')
  setTimeout(() => {
    router.push('/editor')
  }, 1000)
}
</script>
"""
with open(req_path, "w", encoding="utf-8") as f:
    f.write(req_content)

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
            <p><strong>🚨 测试输入区 (在此粘贴你要查重/上链的剧本片段)</strong></p>
            <el-input 
              type="textarea" 
              :rows="5" 
              placeholder="请输入需要检测或抽提版权指纹的剧本内容..." 
              v-model="scriptText" 
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
           <template #header>专业评分与优化建议页：依托教辅测评子库</template>
           <div v-if="profData" class="prof-box">
             <h2>总评分：{{ profData.total_score }}</h2>
             <div class="dim-scores">
                <div v-for="(val, key) in profData.dimensions" :key="key" class="dim-item">
                   <span>{{ key }}</span>
                   <el-progress :percentage="val" />
                </div>
             </div>
             <h4>精确到单场戏的优化建议：</h4>
             <el-timeline>
               <el-timeline-item v-for="(sugg, index) in profData.scene_suggestions" :key="index" :timestamp="'第' + sugg.scene_num + ' 场戏'">
                 {{ sugg.suggestion }}
               </el-timeline-item>
             </el-timeline>
          </div>
          <div v-else style="color:#aaa;text-align:center;padding:20px;">点击上方提取按钮后展示</div>
        </el-card>
      </el-col>

      <el-col :span="12" style="margin-top: 20px;">
        <el-card style="margin-bottom: 20px;">
          <template #header>赛道适配分析页：基于赛道核心子库</template>
          <div style="margin-bottom: 15px">
            选择发布目标赛道：
            <el-select v-model="targetTrack" @change="runTrackAnalysis">
              <el-option label="短剧" value="短剧" />
              <el-option label="影视" value="影视" />
              <el-option label="舞台剧" value="舞台剧" />
              <el-option label="剧本杀" value="剧本杀" />
            </el-select>
          </div>
          <div v-if="trackData">
             <h3 :style="{ color: trackData.match_score >= 60 ? 'green' : 'red' }">
               匹配度打分：{{ trackData.match_score }} 分
             </h3>
             <p><strong>适配差距分析：</strong>{{ trackData.analysis_gap }}</p>
             <el-alert type="warning" :title="trackData.suggestion_direction" :closable="false" />
          </div>
          <div v-else style="color:#aaa;text-align:center;padding:20px;">等待测算...</div>
        </el-card>

        <el-card>
          <template #header>版权存证功能入口</template>
          <el-button type="success" :loading="minting" @click="mintCopyright">一键区块链上链存证</el-button>
          <span style="font-size:12px;color:gray;margin-left:10px;">将提取当前输入框文本的哈希值上链</span>

          <div v-if="certData" style="margin-top: 20px; border: 1px dotted #ccc; padding: 10px; background: #f8f8f8">
            <h4>不可篡改数字存证证书</h4>
            <p><strong>上链时间:</strong> {{ certData.timestamp }}</p>
            <p><strong>证书编号:</strong> {{ certData.certificate_id }}</p>
            <p><strong>交易哈希(TxHash):</strong> <span class="hash">{{ certData.tx_hash }}</span></p>
            <p><strong>叙事指纹哈希:</strong> <span class="hash">{{ certData.fingerprint_hash }}</span></p>
            <p><strong>隐形水印种子:</strong> {{ certData.watermark_data }}</p>
            <div style="margin-top:10px">
              <el-button size="small" type="primary" plain>💾 带隐形水印导出PDF格式文件</el-button>
              <el-button size="small" type="info" plain>💾 下载全链路存证证书</el-button>
            </div>
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

const scriptText = ref("第1场：黑夜，杀手得知了组织的背叛，决定进行最后的复仇。")
const reportData = ref(null)
const profData = ref(null)
const trackData = ref(null)
const certData = ref(null)
const targetTrack = ref("短剧")
const minting = ref(false)

async function runCheck() {
  if(!scriptText.value.trim()){
    ElMessage.warning("请先在输入框输入检测文本");
    return;
  }
  try {
    const res = await axios.post('/api/fingerprint/check_originality', { content: scriptText.value })
    reportData.value = res.data

    const res2 = await axios.post('/api/fingerprint/evaluate_professional', { content: scriptText.value })
    profData.value = res2.data

    runTrackAnalysis()
    ElMessage.success('成功提取五大核心叙事指纹并完成高维比对')
  } catch (err) {
    ElMessage.error('指纹提取失败')
  }
}

async function runTrackAnalysis() {
  if(!scriptText.value.trim()) return;
  try {
    const res3 = await axios.post('/api/fingerprint/analyze_track', { content: scriptText.value, target_track: targetTrack.value })
    trackData.value = res3.data
  } catch(e) {}
}

async function mintCopyright() {
  if(!scriptText.value.trim()){
    ElMessage.warning("没有可存证的文本");
    return;
  }
  minting.value = true
  try {
    const res = await axios.post('/api/fingerprint/copyright_proof', { content: scriptText.value })
    certData.value = res.data
    ElMessage.success('叙事指纹已成功锚定区块链数据节点！')
  } catch (err) {
    ElMessage.error('存证接口调用异常')
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
.dim-scores { margin: 15px 0; }
.dim-item { display: flex; align-items: center; margin-bottom: 10px; }
.dim-item span { width: 150px; text-align: right; margin-right: 15px; }
.dim-item .el-progress { flex: 1; }
.hash { font-family: monospace; word-break: break-all; color: #555; }
</style>
"""
with open(finger_path, "w", encoding="utf-8") as f:
    f.write(finger_content)

print("Files updated successfully!")
