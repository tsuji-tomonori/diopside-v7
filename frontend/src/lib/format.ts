export function formatPublishedDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

export function formatDuration(value: string): string {
  const match = value.match(/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/);
  if (!match) {
    return value;
  }
  const hours = Number(match[1] ?? 0);
  const minutes = Number(match[2] ?? 0);
  const seconds = Number(match[3] ?? 0);
  if (hours > 0) {
    return `${hours}時間${minutes ? `${minutes}分` : ''}`;
  }
  if (minutes > 0) {
    return `${minutes}分${seconds ? `${seconds}秒` : ''}`;
  }
  return `${seconds}秒`;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat('ja-JP').format(value);
}
