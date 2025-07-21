const subgroupColors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c'];
const subgroupColorMap = new Map<string, string>();

export const getTagColor = (subgroup: string): string => {
  if (!subgroup) return '#909399'; // A neutral bright color for tags without a subgroup
  if (!subgroupColorMap.has(subgroup)) {
    const colorIndex = subgroupColorMap.size % subgroupColors.length;
    subgroupColorMap.set(subgroup, subgroupColors[colorIndex]);
  }
  return subgroupColorMap.get(subgroup);
};
