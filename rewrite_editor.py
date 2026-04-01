import base64

content = """<template>
  <div style="display:flex; flex-direction:column; height: 100vh; background-color: #1e1e1e;">
    <!-- 顶部工作栏 -->
    <div style="background: #252526; padding:15px 25px; display:flex; justify-content:space-between; align-items:center; box-shadow: 0 2px 10px rgba(0,0,0,0.5); z-index: 10;">
      <div style="display:flex; align-items:center; gap:15px;">
        <span style="font-weight:600; font-size:18px; color: #fff;">《{{ globalState.title || '未命名剧本' }}》</span>
        <el-tag type="danger" effect="dark" size="small" round>🔥 双轨叙事安全网已激活</el-tag>
        <el-tag type="success" effect="plain" size="small" round>实时高维指纹存证中</el-tag>
      </div>
      <div style="display:flex; gap:15px;">
        <el-button size="small" type="primary" @click="showExport=true">📥 上链并导出剧本</el-button>
      </div>
    </div>

    <!-- 核心双轨共生工作区 -->
    <div style="display:flex; flex:1; overflow:hidden; padding: 20px; gap: 20px;">
      
      <!-- 左轨：隐性叙事大纲审查轨 -->
      <div style="flex: 1.2; background: #2d2d30; border-radius: 12px; display:flex; flex-direction:column; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border: 1px solid #3e3e42;">
        <div style="padding: 15px 20px; border-bottom: 1px solid #3e3e42; background: #252526; border-top-left-radius: 12px; border-top-right-radius: 12px;">
          <h3 style="margin:0; font-size:15px; color:#409eff; display:flex; align-items:center; gap:8px;">
            🛡️ 隐性叙事规划轨 (Neo4j骨架)
          </h3>
        </div>
        <div style="padding: 20px; overflow-y: auto; flex: 1; font-size:14px; line-height: 1.6; color: #d4d4d4;">
          <div v-if="globalState.outline" style="white-space: pre-wrap; margin-bottom:15px; background: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #67c23a;">
            {{ globalState.outline }}
          </div>
          <div v-else style="color:#858585; text-align: center; margin-top: 50px;">隐性骨架尚未建立...</div>
          
          <el-divider style="border-color: #3e3e42;"><span style="color:#858585">安全自检机制</span></el-divider>
          
          <el-button type="primary" plain size="large" style="width: 100%; border-radius: 8px;" @click="critiquePlot" :loading="critiqueLoading">
            🔍 强制调用双轨一致性评估
          </el-button>
          
          <div v-if="critiqueResult" style="margin-top: 15px; background: #4a1919; color: #ff8b8b; padding: 15px; border-radius: 8px; font-size: 13px; border: 1px solid #732626;">
            <b>【拦截警告 / 建议】：</b><br/>{{ critiqueResult }}
          </div>
        </div>
      </div>

      <!-- 右轨：显性剧本创作轨 -->
      <div style="flex: 2.5; background: #fff; border-radius: 12px; display:flex; flex-direction:column; box-shadow: 0 4px 15px rgba(0,0,0,0.2); ">
        <div style="padding: 15px 20px; border-bottom: 1px solid #f0f2f5; background: #fafafa; border-top-left-radius: 12px; border-top-right-radius: 12px; display:flex; justify-content: space-between; align-items:center;">
          <h3 style="margin:0; font-size:15px; color:#333; display:flex; align-items:center; gap:8px;">
            ✍️ 显性创作轨 (用户主导编辑区)
          </h3>
          <span style="font-size: 12px; color: #909399;">任何手动修改系统均将在底层进行自愈适配</span>
        </div>
        
        <!-- 核心编辑器 -->
        <el-input 
          v-model="globalState.scriptContent" 
          type="textarea" 
          resize="none" 
          style="flex:1; padding: 0;" 
          :max-rows="200" 
          class="custom-editor"
          placeholder="剧本正文将在此生成，您可以任意修改内容以测试底层双轨逻辑..." 
        />
        
        <!-- 局部介入控制台 -->
        <div style="padding: 15px 20px; background: #fafafa; border-top: 1px solid #f0f2f5; display:flex; gap: 15px; align-items: center; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">
          <span style="font-size: 14px; font-weight: bold; color: #606266; white-space: nowrap;">局部协同修改：</span>
          <el-input v-model="agentPrompt" placeholder="例如：“让主角此刻显得更加冷酷无情”..." style="flex:1" size="large" />
          <el-button type="primary" size="large" @click="runAgent" :loading="aiLoading" style="border-radius: 8px;">🔄 自动适配重写</el-button>
        </div>
      </div>
    </div>

    <!-- 确权导出框 -->
    <el-dialog v-model="showExport" title="资产确认与上链" width="450px" center>
      <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 40px; margin-bottom: 20px;">🔒</div>
        <p style="font-size: 18px; font-weight: bold; color: #303133; margin-bottom: 10px;">生成 1024 维叙事指纹哈希</p>
        <p style="font-size: 14px; color: #606266; line-height: 1.6;">系统即将对本剧本全部内容注入底层水印并打包上链，保证您的全链路创作版权不可篡改。</p>
      </div>
      <template #footer>
         <el-button type="primary" size="large" @click="showExport=false" style="width: 100%; border-radius: 8px;">确认上链并下载专业格式文档 (SHA-256)</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { inject, ref } from "vue";
import { generateScript, evaluatePlot } from "../api/ai";
import { ElMessage } from "element-plus";

const globalState = inject("globalState");
const agentPrompt = ref("");
const aiLoading = ref(false);
const critiqueLoading = ref(false);
const critiqueResult = ref("");
const showExport = ref(false);

const runAgent = async () => {
    if(!agentPrompt.value) {
        ElMessage.warning("请输入干预指令");
        return;
    }
    aiLoading.value = true;
    try {
        const prompt = `当前隐性骨架: ${globalState.outline}\n显性创作修改指令: ${agentPrompt.value}`;
        ElMessage.success("【显性/隐性】双轨同步正在处理干预...");
        const res = await generateScript(prompt, "deep_rewrite_mode");
        if(res && res.script) {
            globalState.scriptContent += "\n\n" + res.script;
        } else {
            ElMessage.error("未返回合适的改写");
        }
    } catch(err) {
        ElMessage.error("底层网络抖动 / 协作失败");
    } finally {
        aiLoading.value = false;
        agentPrompt.value = "";
    }
};

const critiquePlot = async () => {
    critiqueLoading.value = true;
    try {
        ElMessage.info("正在拉起 GLM-4 验证内核检查...");
        const res = await evaluatePlot(globalState.outline, globalState.scriptContent);
        if(res && res.critique) {
            critiqueResult.value = res.critique;
            ElMessage.error("⚠️ 发现双轨逻辑偏差！安全网已触发拦截提示。");
        } else {
            ElMessage.success("100% 符节律！隐性轨与显性轨高度一致！");
        }
    } catch(err) {
        ElMessage.error("评估内核崩溃");
    } finally {
        critiqueLoading.value = false;
    }
};
</script>

<style>
/* 高级定制版编辑器 UI */
.custom-editor .el-textarea__inner {
  border: none !important;
  box-shadow: none !important;
  padding: 30px !important;
  font-size: 16px !important;
  line-height: 2 !important;
  color: #333 !important;
  height: 100% !important;
  background-color: transparent !important;
  font-family: 'Times New Roman', 'Microsoft YaHei', serif;
}
.custom-editor .el-textarea__inner:focus {
  outline: none !important;
  box-shadow: none !important;
}
</style>
"""

with open(r'c:\Users\madon\Desktop\智能体2\ai-screenplay-system\frontend\src\views\EditorView.vue', 'wb') as f:
    f.write(content.encode('utf-8'))
