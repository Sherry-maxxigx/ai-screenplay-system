<template>
  <div class="project-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>项目详情</span>
        </div>
      </template>
      <div class="project-info">
        <el-descriptions :column="1">
          <el-descriptions-item label="项目名称">
            {{ project.name }}
          </el-descriptions-item>
          <el-descriptions-item label="项目类型">
            {{ project.type }}
          </el-descriptions-item>
          <el-descriptions-item label="项目简介">
            {{ project.description }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ project.created_at }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <div class="project-actions" style="margin-top: 20px">
        <el-button type="primary" @click="goToEditor">进入编辑器</el-button>
        <el-button @click="goToCharacters">管理人物</el-button>
        <el-button @click="goToAnalytics">分析工具</el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'ProjectView',
  data() {
    return {
      project: {
        id: this.$route.params.id,
        name: '测试项目',
        type: '电影',
        description: '这是一个测试项目',
        created_at: '2026-03-18 10:00:00'
      }
    }
  },
  methods: {
    goToEditor() {
      this.$router.push(`/editor/${this.project.id}`)
    },
    goToCharacters() {
      this.$router.push(`/characters/${this.project.id}`)
    },
    goToAnalytics() {
      this.$router.push(`/analytics/${this.project.id}`)
    }
  }
}
</script>

<style scoped>
.project-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-actions {
  display: flex;
  gap: 10px;
}
</style>