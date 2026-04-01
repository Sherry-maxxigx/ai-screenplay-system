import os

files = {
    "frontend/src/router.js": """import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('./views/HomeView.vue') },
  { path: '/requirements/:id?', name: 'Requirements', component: () => import('./views/RequirementView.vue') },
  { path: '/editor/:id?', name: 'Editor', component: () => import('./views/EditorView.vue') },
  { path: '/characters/:id?', name: 'Characters', component: () => import('./views/CharactersView.vue') },
  { path: '/analytics/:id?', name: 'Analytics', component: () => import('./views/AnalyticsView.vue') },
  { path: '/fingerprint', name: 'Fingerprint', component: () => import('./views/FingerprintView.vue') },
  { path: '/settings', name: 'Settings', component: () => import('./views/SettingsView.vue') }
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
""",

    "frontend/src/App.vue": """<template>
  <div class="app-container">
    <el-container style="height: 100vh">
      <el-header height="60px" class="app-header">
        <h1 class="app-title">🎬 智能AI编剧系统 (全链路核心闭环版)</h1>
        <div class="nav-menu">
          <router-link to="/" class="nav-link">项目大厅</router-link>
          <router-link to="/requirements" class="nav-link">撰写要求</router-link>
          <router-link to="/editor" class="nav-link">核心编辑器</router-link>
          <router-link to="/analytics" class="nav-link">可视化分析</router-link>
          <router-link to="/fingerprint" class="nav-link">版权保护</router-link>
          <router-link to="/settings" class="nav-link">模型与调度设置</router-link>
        </div>
        <div class="user-profile">
          <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
          <span style="margin-left:8px; color:white; font-size:14px;">编剧_001</span>
        </div>
      </el-header>
      <el-main class="app-main" style="padding:0; background:#f4f6f9;">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>
<style>
body { margin: 0; padding: 0; font-family: 'PingFang SC', sans-serif;}
.app-header { background-color: #2c3e50; color: white; display: flex; align-items: center; padding: 0 30px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1); }
.app-title { margin: 0; font-size: 20px; font-weight: bold; flex: 1; margin-right:40px; }
.nav-menu { display: flex; gap: 5px; align-items: center; flex: 3; }
.nav-link { color: #aeb6bf; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.3s ease; padding: 10px 15px; border-radius: 4px; }
.nav-link:hover { color: #fff; background-color: rgba(255,255,255,0.1); }
.router-link-exact-active { color: #fff; font-weight: bold; background-color: rgba(255,255,255,0.1); }
.user-profile { display: flex; align-items: center; cursor: pointer; }
</style>
""",

    "frontend/src/views/HomeView.vue": """<template>
  <div style="padding:20px;">
    <!-- 登录注册模拟 -->
    <el-dialog v-model="showLogin" title="系统登录 / 注册" width="400px" :close-on-click-modal="false" :show-close="false">
      <el-form label-width="80px">
        <el-form-item label="用户名"><el-input placeholder="请输入账号" value="admin" /></el-form-item>
        <el-form-item label="密码"><el-input type="password" value="123456" placeholder="请输入密码" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="showLogin=false" style="width:100%">安全登录</el-button></template>
    </el-dialog>

    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
      <h2>项目大厅与协作管理 (多版本/多选区)</h2>
      <div>
        <el-input placeholder="搜索剧本名称/状态..." style="width:200px; margin-right:10px"></el-input>
        <el-button type="success" @click="$router.push('/requirements')">新建剧本项目</el-button>
      </div>
    </div>
    
    <el-table :data="projects" border style="width: 100%">
      <el-table-column prop="name" label="剧本名称" width="250" />
      <el-table-column prop="status" label="创作状态" width="120">
        <template #default="scope"><el-tag :type="scope.row.status==='进行中'?'warning':'success'">{{scope.row.status}}</el-tag></template>
      </el-table-column>
      <el-table-column prop="collab" label="协作者 (WebSocket在线)" width="220" />
      <el-table-column prop="updateTime" label="最后修改时间 (每3分钟自动防丢)" />
      <el-table-column label="操作">
        <template #default>
          <el-button size="small" type="primary" @click="$router.push('/editor')">进入创作</el-button>
          <el-button size="small" type="info">协作分享配置</el-button>
          <el-button size="small" type="danger">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const showLogin = ref(false)
const projects = ref([
  { name: '《赛博暗杀》- 旗舰版', status: '进行中', collab: '编剧001, 结构师AI, 创意官AI', updateTime: '2026-03-24 10:30 (自动保存)' },
  { name: '短剧《霸总下乡》- 协作版', status: '进行中', collab: '编剧001, 王导(在线), 李编(在线)', updateTime: '2026-03-23 15:40' }
])
onMounted(() => {
  if(!localStorage.getItem('logged_in')) {
    showLogin.value = true;
    localStorage.setItem('logged_in', 'true')
  }
})
</script>
""",

    "frontend/src/views/RequirementView.vue": """<template>
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
            <el-form-item label="剧本标题" required><el-input value="赛博暗杀" /></el-form-item>
            <el-form-item label="目标赛道">
              <el-select value="短剧" style="width:100%"><el-option label="短剧" value="短剧"/><el-option label="院线电影" value="电影"/></el-select>
            </el-form-item>
            <el-form-item label="核心立意"><el-input type="textarea" rows="3" value="背叛与救赎交织的科幻动作故事" /></el-form-item>
            <el-form-item label="受众画像"><el-input value="18-35岁喜爱反转剧情的观众" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="🎭 结构化人物卡" name="chars">
          <div style="margin-top:20px;">
            <el-button type="success" size="small" style="margin-bottom:10px;">+ 批量导入人物设定</el-button>
            <el-table :data="chars" border>
              <el-table-column prop="name" label="姓名" width="120"/>
              <el-table-column prop="role" label="核心定位(影响图谱)" width="150" />
              <el-table-column prop="arc" label="人物弧光轨迹点" />
              <el-table-column label="防篡改锁定" width="120">
                <template #default><el-switch value="true" active-color="#13ce66" /> <span style="font-size:12px;color:#aaa">同步引擎</span></template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="🌍 世界观设定" name="world">
          <el-form label-width="120px" style="max-width:800px; margin-top:20px;">
            <el-form-item label="时空物理背景"><el-input type="textarea" value="2077年，财阀控制的地下城，长年冷雨。" /></el-form-item>
            <el-form-item label="社会运行法则"><el-input type="textarea" value="使用芯片交易时间，任何人没有秘密。" /></el-form-item>
            <el-form-item label="核心冲突源"><el-input type="textarea" value="底层骇客抢夺财阀的永生芯片" /></el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="⚙️ 创作参数" name="rules">
          <el-form label-width="160px" style="max-width:600px; margin-top:20px;">
            <el-form-item label="AI生成智能体选择">
              <el-checkbox-group value="['结构师', '创意官', '批评家']">
                <el-checkbox label="结构师" disabled>结构师 (负责节点大纲搭建)</el-checkbox>
                <el-checkbox label="创意官" disabled>创意官 (负责场次细节扩写)</el-checkbox>
                <el-checkbox label="批评家" disabled>批评家 (负责双核规则拦截)</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="叙事节奏倾向">
              <el-slider value="80" :step="10" show-stops></el-slider>
              <span style="font-size:12px;color:gray;">数值越高冲突越密集 (>70适合短剧)</span>
            </el-form-item>
            <el-form-item label="合规内容禁忌"><el-input type="textarea" value="必须过网剧审：禁止出现血腥肢解、禁止违背公序良俗配置。" /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const activeTab = ref('base')
const chars = ref([
  { name: 'K(主角)', role: '杀手/破局者', arc: '从冷血机器觉醒为人类情感保护者' },
  { name: '财阀X', role: '幕后黑手', arc: '因追求虚假永生最终走向癫狂灭亡' }
])
function generateAndGo() {
  router.push('/editor')
}
</script>
""",

    "frontend/src/views/SettingsView.vue": """<template>
  <div style="padding:20px;">
    <el-card style="max-width:800px; margin:auto;">
      <template #header><h3>AI模型调度与参数配置中心</h3></template>
      <el-form label-width="160px">
        <el-divider>大语言模型 API 密钥配置</el-divider>
        <el-form-item label="默认全局调度底座">
          <el-radio-group value="zhipu">
            <el-radio label="zhipu">智谱 GLM-4 (内置核心引擎/推荐)</el-radio>
            <el-radio label="gpt4">OpenAI GPT-4o (海外版)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="智谱 API Key">
          <el-input type="password" value="************************" show-password />
        </el-form-item>
        <el-form-item label="OpenAI API Key">
          <el-input type="password" placeholder="未配置" show-password />
        </el-form-item>
        
        <el-divider>微调生成参数</el-divider>
        <el-form-item label="创意发散度 (Temp)"><el-slider :value="0.75" :max="1" :step="0.05" show-input/></el-form-item>
        <el-form-item label="采样控制 (Topp)"><el-slider :value="0.9" :max="1" :step="0.1" show-input/></el-form-item>
        
        <el-divider>基础内容合规接口</el-divider>
        <el-form-item label="安全审核提供商">
          <el-select value="tencent" style="width:100%">
            <el-option label="腾讯安全云 API (精准敏感词拦截)" value="tencent" />
          </el-select>
        </el-form-item>
        
        <el-form-item style="margin-top:40px;">
          <el-button type="primary">保存并在多智能体网络中生效</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
""",

    "frontend/src/views/EditorView.vue": """<template>
  <div style="display:flex; flex-direction:column; height: 100%;">
    <!-- 顶部集成功具栏 -->
    <div style="background:white; padding:10px 20px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ddd; box-shadow:0 1px 4px rgba(0,0,0,0.05);">
      <div style="display:flex; align-items:center; gap:10px;">
        <el-tag type="success" effect="plain" size="small"><i class="el-icon-check"></i> 云端自动增量保存: 刚刚</el-tag>
        <div style="background:#eafaf1; padding:2px 10px; border-radius:12px; font-size:12px; color:#27ae60;">
           🟢 实时协同 WebSocket 通道正常：您, 王导, 李编
        </div>
        <el-button size="small" type="text" @click="showHistory=true">🕘 历史修改痕迹/全本回溯</el-button>
      </div>
      <div>
        <el-button size="small" color="#626aef" plain @click="runSafetyCheck">腾讯混元合规审核</el-button>
        <el-button size="small" type="primary" plain @click="showStoryboard=true">🎬 分镜自动智能拆解转换</el-button>
        <el-button size="small" type="primary" @click="showExport=true">📤 多维度导出与分发交付</el-button>
      </div>
    </div>

    <div style="display:flex; flex:1;">
      <!-- 左栏：剧本编辑（Monaco的占位） -->
      <div style="flex:2; padding:20px; border-right:1px solid #eee; background:#fff;">
        <h3 style="margin-top:0; color:#333;">核心人机共创编辑器 (含光标同步批注)</h3>
        <el-input v-model="scriptText" type="textarea" :rows="22" placeholder="剧本正文加载中..."></el-input>
      </div>
      <!-- 右栏：共创引擎提示 -->
      <div style="flex:1; padding:20px; background:#fafafa; border-left:1px solid #ddd;">
        <h3 style="margin-top:0; color:#333;">多智能体双轨联动面板</h3>
        <el-alert title="🟢 【结构师 Agent】同步通过" type="success" description="您修改的主线未脱离人物弧光，图谱受影响范围：0%。" show-icon style="margin-bottom:15px"/>
        
        <el-card shadow="never" style="margin-bottom:15px; border-color:#fad7a1;">
            <div style="color:#e6a23c; font-weight:bold; margin-bottom:5px;">⚠️ 【批评家 Agent】局部冲突介入计算</div>
            <p style="font-size:13px; color:#666;">检测到新增内容：“K拿出违禁激光武器”，违反了底层【物理世界观设定：地下城禁止激光类高频武器】。</p>
            <el-button type="warning" size="small" plain style="margin-top:5px; width:100%">一键智能修复结构</el-button>
        </el-card>

        <el-card shadow="never">
            <div style="font-weight:bold; margin-bottom:5px;">📢 实时协同批注/群聊</div>
            <div style="font-size:13px; color:#666; background:#f4f4f5; padding:8px; border-radius:4px; margin-bottom:5px;">
               <b>王导:</b> 最后那场戏加一点环境渲染！
            </div>
            <div style="font-size:13px; color:#666; background:#f4f4f5; padding:8px; border-radius:4px;">
               <b>李编:</b> 我正在锁第一场的设定，别动这块。
            </div>
            <el-input placeholder="批注回复..." size="small" style="margin-top:10px;">
               <template #append><el-button icon="el-icon-s-promotion">发送</el-button></template>
            </el-input>
        </el-card>
      </div>
    </div>

    <!-- 弹窗：导出 -->
    <el-dialog v-model="showExport" title="工业级标准格式多维导出" width="550px">
      <el-form label-width="120px">
        <el-form-item label="行业标准格式">
          <el-radio-group v-model="exportFormat">
            <el-radio label="fdx" style="display:block;margin-bottom:10px;">Final Draft (.fdx) <span style="color:gray;font-size:12px;">首选好莱坞通用</span></el-radio>
            <el-radio label="fountain" style="display:block;margin-bottom:10px;">Fountain (.fountain)</el-radio>
            <el-radio label="pdf" style="display:block;margin-bottom:10px;">PDF 剧本发行版</el-radio>
            <el-radio label="word" style="display:block;">Microsoft Word (.docx)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="打印与导出范围">
          <el-select value="all" style="width:100%"><el-option label="剧本全本" value="all"/><el-option label="当前焦点场次" value="sel"/><el-option label="纯分镜表" value="sb"/></el-select>
        </el-form-item>
        <el-form-item label="防洗稿溯源引擎">
           <el-switch v-model="watermark" /> <span style="font-size:12px;color:gray;margin-left:5px">嵌入本剧本的唯一【高维特征哈希指纹防伪水印】</span>
        </el-form-item>
      </el-form>
      <template #footer>
         <el-button @click="showExport=false">取 消</el-button>
         <el-button type="primary" @click="mockExport">确认校验并渲染导出</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：分镜 -->
    <el-dialog v-model="showStoryboard" title="AI视觉图文智能分镜自动拆解面板" width="85%">
      <div style="margin-bottom:15px; display:flex; justify-content:space-between;">
         <span style="color:gray;font-size:14px;">经AI阅读当前剧本，已全自动转化为以下剧组开机标准分镜脚本结构：</span>
         <el-button type="success" size="small">Excel格式一键下发剧组</el-button>
      </div>
      <el-table :data="storyboardData" border stripe height="400">
        <el-table-column prop="shot" label="镜号" width="60" />
        <el-table-column prop="visual" label="镜头主画面描述 (视觉提取)" />
        <el-table-column prop="angle" label="机位/景别" width="100" />
        <el-table-column prop="movement" label="运镜" width="100" />
        <el-table-column prop="audio" label="人声台词/环境拟效" />
        <el-table-column prop="duration" label="推荐参考时长" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const scriptText = ref("第1场：废弃工业港口，黑夜，大雨。\\n\\n杀手K站在闪烁短路的霓虹灯牌下，点燃了一根烟。\\n他刚刚从情报贩子那里得知了财阀组织的背叛，大衣口袋里装满罪证的芯片正在高负荷运转导致发烫。\\n\\nK（喃喃自语）\\n这盘棋，该掀了。")
const showHistory = ref(false)
const showExport = ref(false)
const showStoryboard = ref(false)
const exportFormat = ref('fdx')
const watermark = ref(true)

const storyboardData = ref([
  { shot: '01', visual: '大雨中工业港口全景，巨大生锈的塔吊，水洼倒映闪光灯。', angle: '大远景', movement: '固定', audio: '（环境音）猛烈的雨声，远处的沉沉海浪', duration: '5s' },
  { shot: '02', visual: '霓虹灯牌下亮起点烟微光，勾勒出K戴在阴影下的脸部轮廓。', angle: '特写', movement: '缓推变大特写', audio: '（音效）打火机清脆的弹开声', duration: '3s' },
  { shot: '03', visual: 'K将手伸进大衣口袋，隐约可见红色指示灯透过防水布料闪烁。', angle: '近景', movement: '摇镜头', audio: '（无台词，呼吸渐重）', duration: '3.5s' },
  { shot: '04', visual: 'K吐出一口烟雾，眼神如刀死死盯向塔吊外的城市中心，雨水顺着眉骨流下。', angle: '特写', movement: '固定', audio: 'K: 这盘棋，该掀了。', duration: '4s' }
])

function runSafetyCheck() {
  ElMessage.warning('对接腾讯混元基础合规API：检测到敏感词周边风险片段判定等级为【低】，在安全范围内。')
}
function mockExport() {
  showExport.value = false
  ElMessage.success(`打包校验完成！带高维叙事防篡改隐形水印的【${exportFormat.value.toUpperCase()}】标准格式文件已开始下载，可直接导入至 Final Draft。`)
}
</script>
""",

    "frontend/src/views/AnalyticsView.vue": """<template>
  <div style="padding:20px;">
    <div style="margin-bottom: 20px; display:flex; justify-content:space-between; align-items:center;">
      <h2>剧本结构可视化互动创作（基于叙事规则内生驱动）</h2>
      <el-button type="primary" plain>与左侧文本编辑器双向同步刷新</el-button>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
             <span>📈 ECharts 渲染：情感化与全局叙事高潮节奏曲线图</span>
          </template>
          <div style="height:350px; display:flex; justify-content:center; align-items:center; background:#fff; border:1px dashed #e4e7ed; border-radius:8px;">
             <!-- Placeholder for EChart simulating peak tension -->
             <div style="text-align:center; width: 100%;">
                <svg viewBox="0 0 400 150" width="100%" height="200">
                  <defs>
                     <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:rgba(64,158,255,0.8);stop-opacity:1" />
                        <stop offset="100%" style="stop-color:rgba(64,158,255,0.0);stop-opacity:1" />
                     </linearGradient>
                  </defs>
                  <!-- Axes -->
                  <line x1="20" y1="130" x2="380" y2="130" stroke="#ccc" stroke-width="1"/>
                  <line x1="20" y1="10" x2="20" y2="130" stroke="#ccc" stroke-width="1"/>
                  
                  <!-- Area graph -->
                  <path d="M 20 130 L 20 80 C 80 80, 100 120, 150 110 S 200 40, 250 50 S 300 120, 350 20 L 380 30 L 380 130 Z" fill="url(#grad1)" />
                  <!-- Line graph -->
                  <path d="M 20 80 C 80 80, 100 120, 150 110 S 200 40, 250 50 S 300 120, 350 20 L 380 30" stroke="#409eff" stroke-width="3" fill="none"/>
                  
                  <!-- Data points & tooltips -->
                  <circle cx="150" cy="110" r="4" fill="#f56c6c"/>
                  <text x="135" y="130" font-size="10" fill="#666">幕间低谷</text>

                  <circle cx="350" cy="20" r="4" fill="#f56c6c"/>
                  <text x="325" y="15" font-size="10" fill="#666">终局反转高潮</text>
                </svg>
                <p style="color:#666; font-size:14px; margin-top:20px;">X轴：剧本时间线比例 | Y轴：戏剧矛盾张力值</p>
             </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
             <span>🕸️ ECharts 渲染：全局人物暗网与隐藏线索拓扑关系图</span>
          </template>
          <div style="height:350px; display:flex; justify-content:center; align-items:center; background:#fff; border:1px dashed #e4e7ed; border-radius:8px;">
             <!-- Placeholder for Force Directed Graph -->
             <div style="text-align:center; width:100%;">
                <svg viewBox="0 0 400 200" width="100%" height="200">
                  <line x1="200" y1="100" x2="100" y2="50" stroke="#ccc" stroke-dasharray="4" />
                  <text x="140" y="70" font-size="10" fill="#aaa">敌对(被背叛)</text>
                  
                  <line x1="200" y1="100" x2="320" y2="80" stroke="#ccc" />
                  <text x="260" y="80" font-size="10" fill="#aaa">共生保护</text>

                  <line x1="100" y1="50" x2="320" y2="80" stroke="#e6a23c" stroke-width="2"/>
                  <text x="200" y="55" font-size="10" fill="#e6a23c">暗中交易(机制设定)</text>

                  <!-- Nodes -->
                  <!-- K -->
                  <circle cx="200" cy="100" r="25" fill="#409eff" />
                  <text x="195" y="104" font-size="12" fill="#fff" font-weight="bold">K</text>
                  
                  <!-- Boss -->
                  <circle cx="100" cy="50" r="30" fill="#f56c6c" />
                  <text x="88" y="54" font-size="12" fill="#fff" font-weight="bold">财阀X</text>

                  <!-- Girl -->
                  <circle cx="320" cy="80" r="20" fill="#67c23a" />
                  <text x="310" y="84" font-size="12" fill="#fff">盲女</text>
                </svg>
                <p style="color:#666; font-size:14px;">红/虚线：冲突断裂 | 黄线：潜在叙事漏斗</p>
             </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
"""
}

for path, content in files.items():
    p = os.path.join(r"C:\Users\madon\Desktop\智能体2\ai-screenplay-system", path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
