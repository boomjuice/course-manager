/**
 * Formats a date string into a localized string.
 * @param timeStr The date string to format.
 * @returns A formatted date and time string (e.g., "2025/07/20 14:30:00").
 */
export const formatTime = (timeStr: string): string => {
  if (!timeStr) return '';
  return new Date(timeStr).toLocaleString('zh-CN');
};
