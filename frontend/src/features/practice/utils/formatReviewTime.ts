const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;

export function formatRelativeTime(date: Date | string | null, future: boolean): string {
  if (!date) return future ? 'soon' : 'new';

  const d = typeof date === 'string' ? new Date(date) : date;
  const diff = Math.abs(d.getTime() - Date.now());

  if (diff < HOUR) {
    const mins = Math.max(1, Math.round(diff / MINUTE));
    return future ? `in ${mins} min` : `${mins} min ago`;
  }
  if (diff < DAY) {
    const hrs = Math.round(diff / HOUR);
    return future ? `in ${hrs}h` : `${hrs}h ago`;
  }
  if (diff < MONTH) {
    const days = Math.round(diff / DAY);
    return future ? `in ${days}d` : `${days}d ago`;
  }
  const months = Math.round(diff / MONTH);
  return future ? `in ${months}mo` : `${months}mo ago`;
}
