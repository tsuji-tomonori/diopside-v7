import { describe, expect, it } from 'vitest';
import { formatCount, formatDuration, formatPublishedDate } from './format';

describe('表示用フォーマット', () => {
  it('ISO durationを日本語の時間表現へ変換する', () => {
    expect(formatDuration('PT2H30M20S')).toBe('2時間30分');
    expect(formatDuration('PT22M')).toBe('22分');
    expect(formatDuration('PT45S')).toBe('45秒');
  });

  it('不正な値を架空値へ置き換えない', () => {
    expect(formatDuration('unknown')).toBe('unknown');
    expect(formatPublishedDate('unknown')).toBe('unknown');
  });

  it('件数をロケールに合わせる', () => {
    expect(formatCount(12345)).toBe('12,345');
  });
});
