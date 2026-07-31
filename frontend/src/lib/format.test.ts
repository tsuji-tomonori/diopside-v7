import { describe, expect, it } from 'vitest';
import { formatCount, formatDuration, formatPublishedDate } from './format';

describe('表示用フォーマット', () => {
  // ISO 8601 durationを読みやすい日本語表現へ変換することを検証する。
  it('ISO durationを日本語の時間表現へ変換する', () => {
    // 1. 初期化
    const longDuration = 'PT2H30M20S';

    // 2. テストの実行
    const formattedDuration = formatDuration(longDuration);

    // 3. アサーション
    expect(formattedDuration).toBe('2時間30分');
    expect(formatDuration('PT22M')).toBe('22分');
    expect(formatDuration('PT45S')).toBe('45秒');
  });

  // 不正な入力をもっともらしい日時や配信時間へ改変しないことを検証する。
  it('不正な値を架空値へ置き換えない', () => {
    // 1. 初期化
    const unknownValue = 'unknown';

    // 2. テストの実行
    const duration = formatDuration(unknownValue);
    const publishedDate = formatPublishedDate(unknownValue);

    // 3. アサーション
    expect(duration).toBe(unknownValue);
    expect(publishedDate).toBe(unknownValue);
  });

  // 集計件数を日本語UIで読みやすい桁区切りへ整形することを検証する。
  it('件数をロケールに合わせる', () => {
    // 1. 初期化
    const count = 12345;

    // 2. テストの実行
    const formattedCount = formatCount(count);

    // 3. アサーション
    expect(formattedCount).toBe('12,345');
  });
});
