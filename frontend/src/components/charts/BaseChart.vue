<template>
  <div ref="chartRef" :style="{ height, width }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts/core';
import {
  BarChart,
  LineChart,
  PieChart
} from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  BarChart,
  LineChart,
  PieChart,
  CanvasRenderer
]);

const props = defineProps({
  width: {
    type: String,
    default: '100%',
  },
  height: {
    type: String,
    default: '400px',
  },
  options: {
    type: Object as () => EChartsOption,
    required: true,
  },
});

const chartRef = ref<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    chartInstance.setOption(props.options);
  }
};

const resizeChart = () => {
  chartInstance?.resize();
};

onMounted(() => {
  nextTick(() => {
    initChart();
  });
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  chartInstance?.dispose();
  window.removeEventListener('resize', resizeChart);
});

watch(
  () => props.options,
  (newOptions) => {
    if (chartInstance) {
      chartInstance.setOption(newOptions);
    }
  },
  { deep: true }
);
</script>
