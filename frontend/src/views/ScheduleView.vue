<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>课表筛选</span>
          <div>
            <el-button 
              v-if="!isMultiSelectMode" 
              type="success" 
              @click="batchCreateVisible = true"
              style="margin-right: 10px;"
            >
              批量排课
            </el-button>
            <el-button 
              v-if="!isMultiSelectMode" 
              type="danger" 
              @click="isMultiSelectMode = true"
            >
              批量删除
            </el-button>
            <div v-else>
              <el-button type="primary" @click="handleDeleteSelected">删除选中项</el-button>
              <el-button @click="isMultiSelectMode = false">取消</el-button>
            </div>
          </div>
        </div>
      </template>
      <!-- 筛选表单 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="教师">
          <el-select v-model="filters.teacher" placeholder="输入关键词筛选教师" clearable filterable @change="fetchScheduleEntries">
            <el-option v-for="item in teacherOptions" :key="item.id" :label="item.user_name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教室">
          <el-select v-model="filters.classroom" placeholder="输入关键词筛选教室" clearable filterable @change="fetchScheduleEntries">
            <el-option v-for="item in classroomOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="calendar-card">
      <FullCalendar ref="fullCalendar" :options="calendarOptions" />
    </el-card>

    <!-- 点击详情 Popover -->
    <el-popover
      ref="popoverRef"
      v-model:visible="popoverVisible"
      :virtual-ref="popoverTriggerRef"
      trigger="manual"
      placement="right-start"
      width="300px"
      popper-class="schedule-popover"
      virtual-triggering
    >
      <div v-if="selectedEvent" class="popover-content">
        <p><strong>班级:</strong> {{ selectedEvent.title }}</p>
        <p><strong>教师:</strong> {{ selectedEvent.extendedProps.classInfo.teacher.user_name }}</p>
        <p><strong>科目:</strong> {{ selectedEvent.extendedProps.classInfo.subject.name }}</p>
        <p><strong>时间:</strong> {{ formatEventTime(selectedEvent.start, selectedEvent.end) }}</p>
        <el-divider />
        <p><strong>班内学生:</strong></p>
        <div v-if="selectedEvent.extendedProps.classInfo.students.length > 0">
          <el-tag
            v-for="student in selectedEvent.extendedProps.classInfo.students"
            :key="student.id"
            class="student-tag"
          >
            {{ student.name }}
          </el-tag>
        </div>
        <p v-else>暂无学生</p>
        <el-divider />
        <el-button type="danger" size="small" @click="handleDeleteFromPopover" style="width: 100%;">
          删除此课程
        </el-button>
      </div>
    </el-popover>
  </div>

  <!-- 批量排课弹窗 -->
  <BatchCreateForm 
    v-model:visible="batchCreateVisible"
    @success="onFormSuccess"
  />

  <!-- 框选单节排课弹窗 -->
  <ScheduleEntryForm
    v-model:visible="entryFormVisible"
    :selection-info="selectionInfo"
    @success="onFormSuccess"
  />
</template>

<script lang="ts" setup>
import { ref, onMounted, reactive, watch } from 'vue';
import apiClient from '@/api';
import BatchCreateForm from '@/components/BatchCreateForm.vue';
import ScheduleEntryForm from '@/components/ScheduleEntryForm.vue';
import { ElMessage, ElMessageBox, ElPopover } from 'element-plus';

import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { CalendarOptions, EventApi, EventClickArg, DateSelectArg } from '@fullcalendar/core';

// --- state ---
const fullCalendar = ref(null);
const loading = ref(false);
const filters = reactive({ teacher: '', classroom: '' });
const teacherOptions = ref([]);
const classroomOptions = ref([]);
const batchCreateVisible = ref(false);
const entryFormVisible = ref(false);
const selectionInfo = ref(null);

const popoverTriggerRef = ref(null);
const popoverVisible = ref(false);
const selectedEvent = ref<EventApi | null>(null);

const isMultiSelectMode = ref(false);
const selectedEventIds = ref(new Set());

// --- Watchers ---
watch(isMultiSelectMode, (newVal) => {
  const calendarApi = fullCalendar.value.getApi();
  calendarApi.setOption('editable', !newVal);
  calendarApi.setOption('selectable', !newVal);
  popoverVisible.value = false; // Hide popover when toggling mode
  if (!newVal) {
    selectedEventIds.value.clear();
    refreshEventStyles();
  }
});

// --- Methods for Custom Rendering ---
function renderTimeGridEventContent(eventInfo) {
  return {
    html: `
      <div class="fc-event-main-frame">
        <div class="fc-event-time">${eventInfo.timeText}</div>
        <div class="fc-event-title-container">
          <div class="fc-event-title fc-sticky">${eventInfo.event.title}</div>
          <div class="event-details">
            <div>教室: ${eventInfo.event.extendedProps.classroomName}</div>
            <div>老师: ${eventInfo.event.extendedProps.classInfo.teacher.user_name}</div>
          </div>
        </div>
      </div>
    `
  };
}

const calendarOptions = reactive<CalendarOptions>({
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridThreeMonth,dayGridMonth,timeGridWeek'
  },
  views: {
    dayGridMonth: {
      eventDisplay: 'block',
      eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
    },
    timeGridWeek: {
      eventContent: renderTimeGridEventContent,
    },
    timeGridDay: {
      eventContent: renderTimeGridEventContent,
    },
    dayGridThreeMonth: {
      type: 'dayGrid',
      duration: { months: 3 },
      eventDisplay: 'block',
    }
  },
  firstDay: 1,
  events: [],
  editable: true,
  selectable: true,
  select: handleDateSelect,
  eventDrop: (info) => updateScheduleEntryTime(info.event, info.revert),
  eventResize: (info) => updateScheduleEntryTime(info.event, info.revert),
  eventClick: handleEventClick,
  dateClick: () => { popoverVisible.value = false; },
  locale: 'zh-cn',
  buttonText: { 
    today: '今天', 
    month: '月', 
    week: '周', 
    dayGridThreeMonth: '季'
  },
  allDaySlot: false,
  slotMinTime: '08:00:00',
  slotMaxTime: '21:00:00',
  height: 'auto',
  slotLabelFormat: { hour: '2-digit', minute: '2-digit', meridiem: false, hour12: false },
});

// --- Color Generation ---
const colorPalette = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#34495e',
  '#f1c40f', '#e67e22', '#e74c3c', '#ecf0f1', '#95a5a6'
];

const getClassColor = (classId) => {
  if (!classId) return colorPalette[4];
  const index = classId % colorPalette.length;
  return colorPalette[index];
};

// --- Core Methods ---
const fetchScheduleEntries = async () => {
  loading.value = true;
  try {
    const params = {
      teacher: filters.teacher || undefined,
      classroom: filters.classroom || undefined,
      page_size: 500,
    };
    const response = await apiClient.get('/schedule-entries/', { params });
    
    calendarOptions.events = response.data.results.map(entry => {
      const color = getClassColor(entry.teaching_class.id);
      return {
        id: entry.id,
        title: entry.teaching_class.name,
        start: entry.start_time,
        end: entry.end_time,
        backgroundColor: color,
        borderColor: color,
        extendedProps: {
          classInfo: entry.teaching_class,
          classroomId: entry.classroom.id,
          classroomName: entry.classroom.name,
        }
      };
    });

  } catch (error) {
    console.error("Failed to fetch schedule entries:", error);
  } finally {
    loading.value = false;
  }
};

async function updateScheduleEntryTime(event: EventApi, revert: () => void) {
  popoverVisible.value = false;
  ElMessage.info(`正在更新课程: ${event.title}`);
  try {
    const payload = {
      teaching_class: event.extendedProps.classInfo.id,
      classroom: event.extendedProps.classroomId,
      start_time: event.start.toISOString(),
      end_time: event.end.toISOString(),
    };
    await apiClient.put(`/schedule-entries/${event.id}/`, payload);
    ElMessage.success('课程时间更新成功！');
  } catch (error) {
    ElMessage.error('更新失败，课程时间已还原');
    console.error("Failed to update schedule entry:", error);
    revert();
  }
}

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
    if (popoverVisible.value && popoverTriggerRef.value === info.el) {
      popoverVisible.value = false;
      return;
    }
    selectedEvent.value = info.event;
    popoverTriggerRef.value = info.el;
    popoverVisible.value = true;
  }
}

function handleDateSelect(selectInfo: DateSelectArg) {
  const { start, end } = selectInfo;
  const isMultiDay = end.getDate() - start.getDate() > 1 || (end.getDate() !== start.getDate() && end.getTime() - start.getTime() > 86400000);

  if (isMultiDay) {
    ElMessage.info('跨天批量创建功能待实现');
  } else {
    selectionInfo.value = { start, end };
    entryFormVisible.value = true;
  }
  
  const calendarApi = selectInfo.view.calendar;
  calendarApi.unselect();
}

function handleDeleteFromPopover() {
  if (!selectedEvent.value) return;
  const eventToDelete = selectedEvent.value;
  popoverVisible.value = false;

  ElMessageBox.confirm(
    `确定要删除课程 "${eventToDelete.title}" 吗？`,
    '删除确��',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/schedule-entries/${eventToDelete.id}/`);
      eventToDelete.remove();
      ElMessage.success('课程删除成功');
    } catch (error) {
      console.error('Failed to delete event:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
}

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

const fetchFilterOptions = async () => {
  try {
    const [teacherRes, classroomRes] = await Promise.all([
      apiClient.get('/teachers/', { params: { page_size: 100 } }),
      apiClient.get('/classrooms/', { params: { page_size: 100 } })
    ]);
    teacherOptions.value = teacherRes.data.results;
    classroomOptions.value = classroomRes.data.results;
  } catch (error) {
    console.error("Failed to fetch filter options:", error);
  }
};

const onFormSuccess = () => {
  fetchScheduleEntries();
};

const formatEventTime = (start, end) => {
  if (!start || !end) return '';
  const options: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  };
  const startTime = start.toLocaleTimeString('zh-CN', options);
  const endTime = end.toLocaleTimeString('zh-CN', options);
  return `${startTime} - ${endTime}`;
};

// --- lifecycle ---
onMounted(() => {
  fetchScheduleEntries();
  fetchFilterOptions();
});
</script>

<style>
/* 全局样式以覆盖 FullCalendar 的 z-index 问题 */
.el-dialog, .el-overlay {
  z-index: 2001 !important;
}
.schedule-popover {
  z-index: 2002 !important;
}
.event-details {
  font-size: 12px;
  margin-top: 4px;
  white-space: normal;
}
.fc-daygrid-event {
  border-radius: 4px !important;
  padding: 2px 4px !important;
  margin-top: 2px !important;
}
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
.popover-content p {
  margin: 8px 0;
}
.student-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}
</style>
