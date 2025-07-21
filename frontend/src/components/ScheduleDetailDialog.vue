<template>
  <el-dialog
    :model-value="visible"
    title="课程详情与考勤"
    width="700px"
    @close="handleClose"
  >
    <div v-if="!localScheduleEntry" class="loading-text">加载中...</div>
    <div v-else>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="课程名称">{{ localScheduleEntry.course_name }}</el-descriptions-item>
        <el-descriptions-item label="授课教师">{{ localScheduleEntry.teacher_name }}</el-descriptions-item>
        <el-descriptions-item label="教室">{{ localScheduleEntry.classroom.name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(localScheduleEntry.status)">{{ getStatusText(localScheduleEntry.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="时间" :span="2">{{ formatTimeRange(localScheduleEntry.start_time, localScheduleEntry.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          <el-input v-model="localScheduleEntry.notes" type="textarea" :rows="2" />
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">学生考勤</el-divider>

      <el-table :data="attendanceData" style="width: 100%">
        <el-table-column prop="student_name" label="学生姓名" />
        <el-table-column label="考勤状态">
          <template #default="scope">
            <el-radio-group v-model="scope.row.status">
              <el-radio label="present">出勤</el-radio>
              <el-radio label="absent">缺勤</el-radio>
              <el-radio label="leave">请假</el-radio>
            </el-radio-group>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <template #footer>
      <el-button type="danger" @click="handleDelete" :loading="saving" style="margin-right: auto;">删除课程</el-button>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch, reactive } from 'vue';
import apiClient from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import dayjs from 'dayjs';

const props = defineProps<{
  visible: boolean;
  scheduleEntry: any;
}>();

const emit = defineEmits(['update:visible', 'success']);

const saving = ref(false);
const attendanceData = ref([]);
const localScheduleEntry = ref(null);

watch(() => props.scheduleEntry, (newEntry) => {
  if (newEntry && newEntry.id) {
    // Create a local copy for editing
    localScheduleEntry.value = reactive({ ...newEntry });
    fetchAttendanceData(newEntry);
  } else {
    localScheduleEntry.value = null;
    attendanceData.value = [];
  }
});

const getStatusText = (status: string) => {
  const map = { scheduled: '已安排', completed: '已完成', cancelled: '已取消' };
  return map[status] || '未知';
};

const getStatusTagType = (status: string) => {
  const map = { scheduled: 'primary', completed: 'success', cancelled: 'danger' };
  return map[status] || 'info';
};

const fetchAttendanceData = async (entry: any) => {
  try {
    const students = entry.students;
    const attendanceResponse = await apiClient.get('/attendances/', { params: { schedule_entry: entry.id, page_size: 200 } });
    const existingRecords = attendanceResponse.data.results;

    const data = students.map(student => {
      const record = existingRecords.find(r => r.student === student.id);
      return {
        id: record ? record.id : null,
        student: student.id,
        student_name: student.name,
        status: record ? record.status : 'present',
      };
    });
    attendanceData.value = data;
  } catch (error) {
    console.error("Failed to fetch attendance data:", error);
    ElMessage.error("获取考勤数据失败");
  }
};

const formatTimeRange = (start: string, end: string) => {
  if (!start || !end) return '';
  return `${dayjs(start).format('YYYY-MM-DD HH:mm')} - ${dayjs(end).format('HH:mm')}`;
};

const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  saving.value = true;
  try {
    // 1. Save attendance records
    const attendancePromises = attendanceData.value.map(record => {
      const payload = {
        schedule_entry: props.scheduleEntry.id,
        student: record.student,
        status: record.status,
      };
      if (record.id) {
        // Update existing record
        return apiClient.put(`/attendances/${record.id}/`, payload);
      } else {
        // Create new record
        return apiClient.post('/attendances/', payload);
      }
    });
    
    // 2. Save schedule entry notes
    const schedulePayload = {
      notes: localScheduleEntry.value.notes,
    };
    const schedulePromise = apiClient.patch(`/schedule-entries/${props.scheduleEntry.id}/`, schedulePayload);

    await Promise.all([...attendancePromises, schedulePromise]);
    
    ElMessage.success('保存成功');
    emit('success');
    handleClose();
  } catch (error) {
    console.error("Failed to save data:", error);
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
};

const handleDelete = () => {
  ElMessageBox.confirm(
    `确定要删除课程 "${props.scheduleEntry.course_name}" 吗？`,
    '删除确认',
    { type: 'warning' }
  ).then(async () => {
    saving.value = true;
    try {
      await apiClient.delete(`/schedule-entries/${props.scheduleEntry.id}/`);
      ElMessage.success('课程删除成功');
      emit('success'); // Use success to trigger a refresh
      handleClose();
    } catch (error) {
      console.error('Failed to delete schedule entry:', error);
      ElMessage.error('删除失败');
    } finally {
      saving.value = false;
    }
  }).catch(() => {});
};
</script>