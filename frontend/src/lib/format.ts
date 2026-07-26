const twoDigits = (value: number): string => String(value).padStart(2, '0');

export function formatPublishedAt(value: string): string {
  const matched = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!matched) {
    return value;
  }

  return `${matched[1]}/${matched[2]}/${matched[3]}`;
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${formatPublishedAt(value)} ${twoDigits(date.getUTCHours())}:${twoDigits(date.getUTCMinutes())}`;
}

export function formatDuration(durationSec: number): string {
  const normalized = Math.max(0, Math.floor(durationSec));
  const hours = Math.floor(normalized / 3600);
  const minutes = Math.floor((normalized % 3600) / 60);
  const seconds = normalized % 60;

  return hours > 0
    ? `${hours}:${twoDigits(minutes)}:${twoDigits(seconds)}`
    : `${minutes}:${twoDigits(seconds)}`;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat('ja-JP').format(value);
}

export function formatTimestamp(atSec: number): string {
  return formatDuration(atSec);
}
