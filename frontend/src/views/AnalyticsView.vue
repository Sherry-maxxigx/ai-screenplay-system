<template>
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
