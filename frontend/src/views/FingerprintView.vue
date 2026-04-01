<template>
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
