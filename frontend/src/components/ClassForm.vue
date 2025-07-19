<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑班级' : '新增班级'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <!-- ... other form items ... -->
      <el-form-item label="班级名称" prop="name">
        <el-input v-model="formData.name" />
      </el-form-item>
      <el-form-item label="班级类型" prop="class_type">
        <el-select v-model="formData.class_type">
          <el-option label="小班" value="small_group" />
          <el-option label="一对一" value="one_on_one" />
        </el-select>
      </el-form-item>
      <el-form-item label="授课教师" prop="teacher_id">
        <el-select v-model="formData.teacher_id" filterable @change="onTeacherChange" placeholder="请选择授课教师">
          <el-option v-for="item in teacherOptions" :key="item.id" :label="item.user_name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label=" " v-if="selectedTeacherInfo">
        <div>
          <el-tag v-for="s in selectedTeacherInfo.subjects" :key="s.id" class="info-tag">{{ s.name }}</el-tag>
          <el-tag v-for="g in selectedTeacherInfo.grades" :key="g.id" class="info-tag" type="success">{{ g.name }}</el-tag>
        </div>
      </el-form-item>
      <el-form-item label="科目" prop="subject_id">
        <el-select v-model="formData.subject_id" placeholder="请先选择教师" :disabled="!formData.teacher_id">
          <el-option v-for="item in filteredSubjectOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="年级" prop="grade_id">
        <el-select v-model="formData.grade_id" placeholder="请先选择教师" :disabled="!formData.teacher_id">
          <el-option v-for="item in filteredGradeOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="班内学生" prop="student_ids">
        <div class="student-select-wrapper">
          <el-select 
            v-model="formData.student_ids" 
            multiple 
            filterable 
            style="width: 100%" 
            placeholder="请选择学生"
            popper-class="student-select-popper"
          >
            <el-option v-for="item in studentOptions" :key="item.id" :label="item.name" :value="item.id">
              <div class="student-option">
                <span class="student-name">{{ item.name }}</span>
                <div class="student-tags">
                  <el-tag
                    v-for="tag in item.tags"
                    :key="tag.id"
                    :type="tagColorMap[tag.group]"
                    size="small"
                    class="info-tag"
                  >
                    {{ tag.name }}
                  </el-tag>
                </div>
              </div>
            </el-option>
          </el-select>
          <el-tooltip
            content="根据当前已选学生，推荐有相似标签的其他学生"
            placement="top"
          >
            <el-button 
              @click="openRecommendDialog" 
              class="recommend-btn"
              :disabled="formData.student_ids.length === 0"
            >
              智能推荐
            </el-button>
          </el-tooltip>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>

  <!-- 推荐学生弹窗 -->
  <el-dialog v-model="recommendVisible" title="智能推荐学生" width="700px">
    <el-table :data="recommendedStudents" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column property="name" label="姓名" />
      <el-table-column label="标签">
        <template #default="scope">
          <el-tag v-for="tag in scope.row.tags" :key="tag.id" :type="tagColorMap[tag.group]" class="info-tag">
            {{ tag.name }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="recommendVisible = false">取消</el-button>
      <el-button type="primary" @click="addRecommendedStudents">添加到班级</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch, reactive, onMounted, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  visible: boolean;
  classData: any;
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const isEdit = ref(false);
const selectedTeacherInfo = ref(null);
const recommendVisible = ref(false);
const recommendedStudents = ref([]);
const selectedRecommended = ref([]);

const formData = reactive({
  id: null,
  name: '',
  class_type: 'small_group',
  teacher_id: null,
  subject_id: null,
  grade_id: null,
  student_ids: [],
});

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '班级名称不能为空', trigger: 'blur' }],
  class_type: [{ required: true, message: '必须选择班级类型', trigger: 'change' }],
  teacher_id: [{ required: true, message: '必须选择授课教师', trigger: 'change' }],
  subject_id: [{ required: true, message: '必须选择科目', trigger: 'change' }],
  grade_id: [{ required: true, message: '必须选择年级', trigger: 'change' }],
});

const teacherOptions = ref([]);
const subjectOptions = ref([]);
const gradeOptions = ref([]);
const studentOptions = ref([]);

const tagColorMap = {
  'performance': 'danger',
  'school_info': 'success',
  'personality': 'primary',
  'source': 'warning',
  'other': 'info',
};

const filteredSubjectOptions = computed(() => {
  if (!selectedTeacherInfo.value) return [];
  const teacherSubjectIds = selectedTeacherInfo.value.subjects.map(s => s.id);
  return subjectOptions.value.filter(s => teacherSubjectIds.includes(s.id));
});

const filteredGradeOptions = computed(() => {
  if (!selectedTeacherInfo.value) return [];
  const teacherGradeIds = selectedTeacherInfo.value.grades.map(g => g.id);
  return gradeOptions.value.filter(g => teacherGradeIds.includes(g.id));
});

watch(() => props.classData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.name = newData.name;
    formData.class_type = newData.class_type;
    formData.teacher_id = newData.teacher.id;
    formData.subject_id = newData.subject.id;
    formData.grade_id = newData.grade.id;
    formData.student_ids = newData.students.map((s: any) => s.id);
    selectedTeacherInfo.value = newData.teacher;
  } else {
    isEdit.value = false;
    formRef.value?.resetFields();
    formData.id = null;
    selectedTeacherInfo.value = null;
  }
});

const onTeacherChange = (teacherId: number) => {
  if (teacherId) {
    selectedTeacherInfo.value = teacherOptions.value.find(t => t.id === teacherId) || null;
    if (selectedTeacherInfo.value) {
      const teacherSubjectIds = selectedTeacherInfo.value.subjects.map(s => s.id);
      if (!teacherSubjectIds.includes(formData.subject_id)) formData.subject_id = null;
      const teacherGradeIds = selectedTeacherInfo.value.grades.map(g => g.id);
      if (!teacherGradeIds.includes(formData.grade_id)) formData.grade_id = null;
    }
  } else {
    selectedTeacherInfo.value = null;
    formData.subject_id = null;
    formData.grade_id = null;
  }
};

const openRecommendDialog = () => {
  // 统一使用前端逻辑进行推荐
  const selectedStudents = studentOptions.value.filter(s => formData.student_ids.includes(s.id));
  const targetTagIds = new Set(selectedStudents.flatMap(s => s.tags.map(t => t.id)));
  
  const unselectedStudents = studentOptions.value.filter(s => !formData.student_ids.includes(s.id));
  
  recommendedStudents.value = unselectedStudents.filter(s => 
    s.tags.some(t => targetTagIds.has(t.id))
  );
  
  if (recommendedStudents.value.length === 0) {
    ElMessage.info('暂无更多具有相似标签的学生可推荐');
    return;
  }
  recommendVisible.value = true;
};

const handleSelectionChange = (val) => {
  selectedRecommended.value = val;
};

const addRecommendedStudents = () => {
  const newStudentIds = selectedRecommended.value.map(s => s.id);
  const currentStudentIds = new Set(formData.student_ids);
  newStudentIds.forEach(id => currentStudentIds.add(id));
  formData.student_ids = Array.from(currentStudentIds);
  recommendVisible.value = false;
};

const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const payload = { ...formData };
        if (isEdit.value) {
          await apiClient.put(`/teaching-classes/${payload.id}/`, payload);
        } else {
          await apiClient.post('/teaching-classes/', payload);
        }
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to save class:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchOptions = async () => {
  try {
    const [teacherRes, subjectRes, gradeRes, studentRes] = await Promise.all([
      apiClient.get('/teachers/', { params: { page_size: 100 } }),
      apiClient.get('/subjects/', { params: { page_size: 100 } }),
      apiClient.get('/grades/', { params: { page_size: 100 } }),
      apiClient.get('/students/', { params: { page_size: 200 } })
    ]);
    teacherOptions.value = teacherRes.data.results;
    subjectOptions.value = subjectRes.data.results;
    gradeOptions.value = gradeRes.data.results;
    studentOptions.value = studentRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>

<style>
.student-select-popper .el-select-dropdown__item {
  height: auto;
  padding-top: 8px;
  padding-bottom: 8px;
}
</style>

<style scoped>
.info-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}
.student-option {
  line-height: 1.5;
}
.student-name {
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.student-tags {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.student-select-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}
.recommend-btn {
  margin-left: 8px;
}
</style>