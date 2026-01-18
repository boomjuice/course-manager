<template>
  <div class="dictionary-view">
    <div class="page-header">
      <h1>数据字典</h1>
      <el-button v-permission="['dictionary', 'edit']" type="primary" @click="showTypeDialog()">
        <el-icon><Plus /></el-icon>
        新增字典类型
      </el-button>
    </div>

    <div class="dictionary-container">
      <!-- Left: Type List -->
      <div class="type-list">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索字典类型..."
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-scrollbar height="calc(100vh - 240px)">
          <div
            v-for="item in filteredTypes"
            :key="item.id"
            :class="['type-item', { active: selectedType?.id === item.id }]"
            @click="selectType(item)"
          >
            <div class="type-info">
              <span class="type-name">{{ item.name }}</span>
              <span class="type-code">{{ item.code }}</span>
            </div>
            <el-tag v-if="item.is_system" size="small" type="info">系统</el-tag>
          </div>
        </el-scrollbar>
      </div>

      <!-- Right: Item List -->
      <div class="item-list">
        <template v-if="selectedType">
          <div class="item-header">
            <div class="header-info">
              <h2>{{ selectedType.name }}</h2>
              <span class="code-badge">{{ selectedType.code }}</span>
            </div>
            <div class="header-actions">
              <el-button v-permission="['dictionary', 'edit']" @click="showTypeDialog(selectedType)" :disabled="selectedType.is_system">
                编辑类型
              </el-button>
              <el-button v-permission="['dictionary', 'edit']" type="primary" @click="showItemDialog()">
                <el-icon><Plus /></el-icon>
                新增字典项
              </el-button>
            </div>
          </div>

          <el-table :data="selectedType.items" stripe style="width: 100%">
            <el-table-column prop="sort_order" label="排序" width="70" />
            <el-table-column prop="value" label="值" width="120" />
            <el-table-column prop="label" label="显示标签" min-width="120">
              <template #default="{ row }">
                <el-tag v-if="row.color" :color="row.color" style="color: #fff">
                  {{ row.label }}
                </el-tag>
                <span v-else>{{ row.label }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
            <el-table-column prop="is_default" label="默认" width="70">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success" size="small">是</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_time" label="创建时间" width="170">
              <template #default="{ row }">
                {{ formatDate(row.created_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button v-permission="['dictionary', 'edit']" link type="primary" @click="showItemDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除该字典项？" @confirm="handleDeleteItem(row.id)">
                  <template #reference>
                    <el-button v-permission="['dictionary', 'delete']" link type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </template>

        <el-empty v-else description="请选择左侧字典类型" />
      </div>
    </div>

    <!-- Type Dialog -->
    <el-dialog
      v-model="typeDialogVisible"
      :title="editingType ? '编辑字典类型' : '新增字典类型'"
      width="500px"
    >
      <el-form ref="typeFormRef" :model="typeForm" :rules="typeRules" label-width="100px">
        <el-form-item label="类型编码" prop="code">
          <el-input v-model="typeForm.code" :disabled="!!editingType" placeholder="如: student_status" />
        </el-form-item>
        <el-form-item label="类型名称" prop="name">
          <el-input v-model="typeForm.name" placeholder="如: 学生状态" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="typeForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="typeForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveType" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- Item Dialog -->
    <el-dialog
      v-model="itemDialogVisible"
      :title="editingItem ? '编辑字典项' : '新增字典项'"
      width="500px"
    >
      <el-form ref="itemFormRef" :model="itemForm" :rules="itemRules" label-width="100px">
        <el-form-item label="字典值" prop="value">
          <el-input v-model="itemForm.value" placeholder="如: active" />
        </el-form-item>
        <el-form-item label="显示标签" prop="label">
          <el-input v-model="itemForm.label" placeholder="如: 在读" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="itemForm.color" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="itemForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="itemForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="itemForm.is_default" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="itemForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveItem" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getDictTypes, getDictType, createDictType, updateDictType,
  createDictItem, updateDictItem, deleteDictItem,
  type DictType, type DictItem
} from '@/api/dictionary'

// State
const types = ref<DictType[]>([])
const selectedType = ref<DictType | null>(null)
const searchKeyword = ref('')
const loading = ref(false)
const saving = ref(false)

// Type Dialog
const typeDialogVisible = ref(false)
const editingType = ref<DictType | null>(null)
const typeFormRef = ref<FormInstance>()
const typeForm = ref({
  code: '',
  name: '',
  description: '',
  is_active: true,
})
const typeRules: FormRules = {
  code: [
    { required: true, message: '请输入类型编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '编码必须以小写字母开头，只能包含小写字母、数字和下划线', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入类型名称', trigger: 'blur' }],
}

// Item Dialog
const itemDialogVisible = ref(false)
const editingItem = ref<DictItem | null>(null)
const itemFormRef = ref<FormInstance>()
const itemForm = ref({
  value: '',
  label: '',
  description: '',
  color: '',
  is_default: false,
  is_active: true,
  sort_order: 0,
})
const itemRules: FormRules = {
  value: [{ required: true, message: '请输入字典值', trigger: 'blur' }],
  label: [{ required: true, message: '请输入显示标签', trigger: 'blur' }],
}

// Computed
const filteredTypes = computed(() => {
  if (!searchKeyword.value) return types.value
  const keyword = searchKeyword.value.toLowerCase()
  return types.value.filter(t =>
    t.name.toLowerCase().includes(keyword) ||
    t.code.toLowerCase().includes(keyword)
  )
})

// Methods
const loadTypes = async () => {
  loading.value = true
  try {
    const res = await getDictTypes(true)
    types.value = res || []
  } finally {
    loading.value = false
  }
}

const selectType = async (type: DictType) => {
  const res = await getDictType(type.id)
  selectedType.value = res || null
}

const showTypeDialog = (type?: DictType) => {
  editingType.value = type || null
  if (type) {
    typeForm.value = {
      code: type.code,
      name: type.name,
      description: type.description || '',
      is_active: type.is_active,
    }
  } else {
    typeForm.value = { code: '', name: '', description: '', is_active: true }
  }
  typeDialogVisible.value = true
}

const handleSaveType = async () => {
  await typeFormRef.value?.validate()
  saving.value = true
  try {
    if (editingType.value) {
      await updateDictType(editingType.value.id, typeForm.value)
      ElMessage.success('更新成功')
    } else {
      await createDictType(typeForm.value)
      ElMessage.success('创建成功')
    }
    typeDialogVisible.value = false
    await loadTypes()
    if (selectedType.value) {
      await selectType(selectedType.value)
    }
  } finally {
    saving.value = false
  }
}

const showItemDialog = (item?: DictItem) => {
  editingItem.value = item || null
  if (item) {
    itemForm.value = {
      value: item.value,
      label: item.label,
      description: item.description || '',
      color: item.color || '',
      is_default: item.is_default,
      is_active: item.is_active,
      sort_order: item.sort_order,
    }
  } else {
    const maxOrder = selectedType.value?.items?.length || 0
    itemForm.value = {
      value: '', label: '', description: '', color: '',
      is_default: false, is_active: true, sort_order: maxOrder,
    }
  }
  itemDialogVisible.value = true
}

const handleSaveItem = async () => {
  await itemFormRef.value?.validate()
  if (!selectedType.value) return
  saving.value = true
  try {
    if (editingItem.value) {
      await updateDictItem(editingItem.value.id, itemForm.value)
      ElMessage.success('更新成功')
    } else {
      await createDictItem(selectedType.value.id, itemForm.value)
      ElMessage.success('创建成功')
    }
    itemDialogVisible.value = false
    await selectType(selectedType.value)
  } finally {
    saving.value = false
  }
}

const handleDeleteItem = async (itemId: number) => {
  await deleteDictItem(itemId)
  ElMessage.success('删除成功')
  if (selectedType.value) {
    await selectType(selectedType.value)
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTypes()
})
</script>

<style scoped lang="scss">
.dictionary-view {
  padding: 20px;
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }
}

.dictionary-container {
  display: flex;
  gap: 20px;
  height: calc(100vh - 180px);
}

.type-list {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--gray-200);

  .search-input {
    margin-bottom: 12px;
  }

  .type-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: var(--gray-50);
    }

    &.active {
      background: var(--primary-50);
      border-left: 3px solid var(--primary-500);
    }

    .type-info {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .type-name {
        font-weight: 500;
        color: var(--gray-900);
      }

      .type-code {
        font-size: 12px;
        color: var(--gray-500);
        font-family: monospace;
      }
    }
  }
}

.item-list {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--gray-200);

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-info {
      display: flex;
      align-items: center;
      gap: 12px;

      h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .code-badge {
        font-size: 12px;
        padding: 2px 8px;
        background: var(--gray-100);
        border-radius: 4px;
        font-family: monospace;
        color: var(--gray-600);
      }
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
}
</style>
