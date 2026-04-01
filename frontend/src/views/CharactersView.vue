<template>
  <div class="characters-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button size="small" @click="goBack" icon="el-icon-arrow-left">返回</el-button>
            <span class="page-title">人物管理 - {{ currentProject ? currentProject.name : '未选择项目' }}</span>
          </div>
          <el-button type="primary" @click="dialogVisible = true">新建人物</el-button>
        </div>
      </template>
      <el-table :data="characters" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="人物名称" />
        <el-table-column prop="description" label="人物描述" :show-overflow-tooltip="true" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editCharacter(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCharacter(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑人物对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form :model="characterForm" label-width="100px">
        <el-form-item label="人物名称">
          <el-input v-model="characterForm.name" placeholder="请输入人物名称" />
        </el-form-item>
        <el-form-item label="人物描述">
          <el-input type="textarea" v-model="characterForm.description" placeholder="请输入人物描述" :rows="3" />
        </el-form-item>
        <el-form-item label="人物特质">
          <el-input type="textarea" v-model="characterForm.traits" placeholder="请输入人物特质，JSON格式" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCharacter">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'CharactersView',
  data() {
    return {
      dialogVisible: false,
      dialogTitle: '新建人物',
      characterForm: {
        id: '',
        name: '',
        description: '',
        traits: ''
      },
      characters: [
        {
          id: 1,
          name: '主角',
          description: '故事的主要人物',
          traits: '{"性格": "勇敢", "爱好": "冒险", "弱点": "冲动"}'
        },
        {
          id: 2,
          name: '配角1',
          description: '主角的朋友',
          traits: '{"性格": "聪明", "爱好": "解谜", "弱点": "胆小"}'
        },
        {
          id: 3,
          name: '配角2',
          description: '反派角色',
          traits: '{"性格": "狡猾", "爱好": "权力", "弱点": "傲慢"}'
        }
      ],
      currentProject: null
    }
  },
  mounted() {
    this.loadCurrentProject()
  },
  methods: {
    editCharacter(character) {
      this.dialogTitle = '编辑人物'
      this.characterForm = { ...character }
      this.dialogVisible = true
    },
    deleteCharacter(id) {
      this.$confirm('确定要删除这个人物吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.characters = this.characters.filter(item => item.id !== id)
        this.$message.success('删除成功')
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    },
    saveCharacter() {
      if (!this.characterForm.name) {
        this.$message.error('请输入人物名称')
        return
      }
      
      if (this.characterForm.id) {
        // 编辑现有人物
        const index = this.characters.findIndex(item => item.id === this.characterForm.id)
        if (index !== -1) {
          this.characters[index] = { ...this.characterForm }
          this.$message.success('编辑成功')
        }
      } else {
        // 新建人物
        const newCharacter = {
          id: this.characters.length + 1,
          ...this.characterForm
        }
        this.characters.push(newCharacter)
        this.$message.success('创建成功')
      }
      
      this.dialogVisible = false
      this.resetForm()
    },
    resetForm() {
      this.characterForm = {
        id: '',
        name: '',
        description: '',
        traits: ''
      }
      this.dialogTitle = '新建人物'
    },
    loadCurrentProject() {
      const projectId = this.$route.params.id
      if (projectId) {
        const savedProjects = localStorage.getItem('projects')
        if (savedProjects) {
          const projects = JSON.parse(savedProjects)
          this.currentProject = projects.find(p => p.id == projectId)
        }
      }
    },
    goBack() {
      this.$router.back()
    }
  }
}
</script>

<style scoped>
.characters-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #ffffff;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
}

/* 优化卡片样式 */
.el-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.el-card__body {
  padding: 20px;
}

/* 优化按钮样式 */
.el-button {
  border-radius: 4px;
  transition: all 0.3s ease;
}

.el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.15);
}

/* 优化表格样式 */
.el-table {
  border-radius: 4px;
  overflow: hidden;
}

.el-table th {
  background-color: #f5f7fa;
  font-weight: bold;
}

.el-table tr:hover {
  background-color: #ecf5ff;
}

/* 优化输入框样式 */
.el-input__inner {
  border-radius: 4px;
  transition: all 0.3s ease;
}

.el-input__inner:focus {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
</style>