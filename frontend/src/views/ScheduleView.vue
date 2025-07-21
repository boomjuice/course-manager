<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>课表筛选</span>
          <div>
            <el-button
              type="success"
              @click="batchCreateVisible = true"
              style="margin-right: 10px;"
            >
              批量排课
            </el-button>
            <el-button
              type="danger"
              @click="isMultiSelectMode = !isMultiSelectMode"
            >
              {{ isMultiSelectMode ? '取消批量删除' : '批量删除' }}
            </el-button>
            <el-button v-if="isMultiSelectMode" type="primary" @click="handleDeleteSelected">删除选中项</el-button>
          </div>
        </div>
      </template>
      <!-- 筛选表单 -->
      <el-form :inline="true" :model="filters" @submit.prevent="fetchScheduleEntries" class="filter-form">
        <el-form-item label="教师">
          <el-input v-model="filters.teacher_name" placeholder="按教师姓名筛选" clearable />
        </el-form-item>
        <el-form-item label="学生">
          <el-input v-model="filters.student_name" placeholder="按学生姓名筛选" clearable />
        </el-form-item>
        <el-form-item label="教室">
          <el-select v-model="filters.classroom_id" style="width: 150px" placeholder="按教室筛选" clearable>
            <el-option v-for="item in classrooms" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchScheduleEntries">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="calendar-card">
      <FullCalendar ref="fullCalendar" :options="calendarOptions" />
    </el-card>

    <!-- 新建排课弹窗 -->
    <NewScheduleEntryForm
      v-model:visible="entryFormVisible"
      :selection-info="selectionInfo"
      @success="onFormSuccess"
    />

    <!-- 批量排课弹窗 -->
    <BatchScheduleForm
      v-model:visible="batchCreateVisible"
      @success="onFormSuccess"
    />

    <!-- 详情与考勤弹窗 -->
    <ScheduleDetailDialog
      v-model:visible="detailDialogVisible"
      :schedule-entry="selectedScheduleEntry"
      @success="onFormSuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import apiClient from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import NewScheduleEntryForm from '@/components/NewScheduleEntryForm.vue';
import BatchScheduleForm from '@/components/BatchScheduleForm.vue';
import ScheduleDetailDialog from '@/components/ScheduleDetailDialog.vue';
import type { CalendarOptions, EventApi, EventClickArg, DateSelectArg } from '@fullcalendar/core';

// --- state ---
const fullCalendar = ref(null);
const loading = ref(false);
const filters = reactive({
  teacher_name: '',
  student_name: '',
  classroom_id: '',
});
const classrooms = ref([]);
const scheduleEntries = ref([]);
const isMultiSelectMode = ref(false);
const selectedEventIds = ref(new Set());
const entryFormVisible = ref(false);
const selectionInfo = ref(null);
const detailDialogVisible = ref(false);
const selectedScheduleEntry = ref(null);
const batchCreateVisible = ref(false);

const teacherColorMap = new Map<string, string>();
const colorPalette = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c'];

const getTeacherColor = (teacherName: string) => {
  if (!teacherName) return '#909399'; // Default color for entries without a teacher
  if (!teacherColorMap.has(teacherName)) {
    const colorIndex = teacherColorMap.size % colorPalette.length;
    teacherColorMap.set(teacherName, colorPalette[colorIndex]);
  }
  return teacherColorMap.get(teacherName);
};

const getStatusText = (status: string) => {
  const map = { scheduled: '已安排', completed: '已完成', cancelled: '已取消' };
  return map[status] || '未知';
};

// --- Computed Properties ---
const calendarEvents = computed(() => {
  // Clear the map each time events are re-computed to ensure consistent coloring
  teacherColorMap.clear();
  return scheduleEntries.value.map(entry => {
    const color = getTeacherColor(entry.teacher_name);
    const statusText = getStatusText(entry.status);
    return {
      id: entry.id,
      title: `[${statusText}] ${entry.course_name} (${entry.teacher_name})`,
      start: entry.start_time,
      end: entry.end_time,
      extendedProps: { ...entry },
      backgroundColor: color,
      borderColor: color,
    }
  });
});

// --- Watchers ---
watch(isMultiSelectMode, (newVal) => {
  const calendarApi = fullCalendar.value.getApi();
  calendarApi.setOption('editable', !newVal);
  calendarApi.setOption('selectable', !newVal);
  if (!newVal) {
    selectedEventIds.value.clear();
    refreshEventStyles();
  }
});

watch(filters, () => fetchScheduleEntries());

// --- Calendar Options ---
const calendarOptions = reactive<CalendarOptions>({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay'
  },
  events: calendarEvents,
  editable: true,
  selectable: true,
  select: handleDateSelect,
  eventClick: handleEventClick,
  eventDrop: (info) => updateScheduleEntryTime(info.event, info.revert),
  eventResize: (info) => updateScheduleEntryTime(info.event, info.revert),
  eventOverlap: true, // Allow events to be dragged over each other, backend will handle conflict
  locale: 'zh-cn',
  buttonText: { today: '今天', month: '月', week: '周', day: '日' },
  allDaySlot: false,
  slotMinTime: '08:00:00',
  slotMaxTime: '21:00:00',
  height: 'auto',
  firstDay:1,
});

// --- Core Methods ---
const fetchScheduleEntries = async () => {
  loading.value = true;
  try {
    const params = {
      teacher_name: filters.teacher_name || undefined,
      student_name: filters.student_name || undefined,
      classroom_id: filters.classroom_id || undefined,
      page_size: 500,
    };
    const response = await apiClient.get('/schedule-entries/', { params });
    scheduleEntries.value = response.data.results;
  } catch (error) {
    console.error("Failed to fetch schedule entries:", error);
  } finally {
    loading.value = false;
  }
};

const fetchFilterData = async () => {
  try {
    const response = await apiClient.get('/classrooms/', { params: { page_size: 100 } });
    classrooms.value = response.data.results;
  } catch (error) {
    console.error("Failed to fetch classrooms:", error);
  }
};

function handleEventClick(info: EventClickArg) {
  if (isMultiSelectMode.value) {
    const eventId = info.event.id;
    if (selectedEventIds.value.has(eventId)) {
      selectedEventIds.value.delete(eventId);
      info.el.classList.remove('selected-event');
    } else {
      selectedEventIds.value.add(eventId);
      info.el.classList.add('selected-event');
    }
  } else {
    // Open the detail/attendance dialog on single click
    selectedScheduleEntry.value = info.event.extendedProps;
    detailDialogVisible.value = true;
  }
}

function handleDateSelect(selectInfo: DateSelectArg) {
  selectionInfo.value = selectInfo;
  entryFormVisible.value = true;
  const calendarApi = selectInfo.view.calendar;
  calendarApi.unselect();
}

const onFormSuccess = () => {
  fetchScheduleEntries();
};

async function handleDeleteSelected() {
  const idsToDelete = Array.from(selectedEventIds.value);
  if (idsToDelete.length === 0) {
    ElMessage.warning('请至少选择一个课程进行删除');
    return;
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${idsToDelete.length} 节课程吗？`,
    '批量删除确认',
    { type: 'warning' }
  ).then(async () => {
    try {
      await apiClient.post('/schedule-entries/batch-delete/', { ids: idsToDelete });
      ElMessage.success('批量删除成功');
      isMultiSelectMode.value = false;
      fetchScheduleEntries();
    } catch (error) {
      console.error('Failed to batch delete events:', error);
    }
  }).catch(() => ElMessage.info('已取消删除'));
}

function refreshEventStyles() {
  const calendarApi = fullCalendar.value.getApi();
  calendarApi.getEvents().forEach(event => {
    const el = event.el;
    if (el) {
      el.classList.remove('selected-event');
    }
  });
}

// --- lifecycle ---
onMounted(() => {
  fetchScheduleEntries();
  fetchFilterData();
});
</script>

<style>
.selected-event {
  border: 2px solid #F56C6C !important;
  box-shadow: 0 0 5px rgba(245, 108, 108, 0.7);
}
</style>

<style scoped>
.filter-form {
  margin-bottom: -18px;
}
.calendar-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
