<template>
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
