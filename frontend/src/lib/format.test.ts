import { describe, expect, it } from 'vitest';

import { formatCount, formatDateTime, formatDuration, formatPublishedAt, formatTimestamp } from './format';

describe('表示用整形', () => {
  // このテストケースの公開契約を検証する。
  it('投稿日と更新日時を日本語の表示形式へ整形する', () => {
    // 1. 初期化
    const publishedAt = '2026-06-30T22:10:00Z';

    // 2. テストの実行
    const date = formatPublishedAt(publishedAt);
    const dateTime = formatDateTime(publishedAt);

    // 3. アサーション
    expect(date).toBe('2026/06/30');
    expect(dateTime).toBe('2026/06/30 22:10');
  });

  // このテストケースの公開契約を検証する。
  it('秒数を動画長とタイムスタンプの表示形式へ整形する', () => {
    // 1. 初期化
    const longDuration = 9020;

    // 2. テストの実行
    const duration = formatDuration(longDuration);
    const timestamp = formatTimestamp(120);

    // 3. アサーション
    expect(duration).toBe('2:30:20');
    expect(timestamp).toBe('2:00');
  });

  // このテストケースの公開契約を検証する。
  it('件数を三桁区切りで整形する', () => {
    // 1. 初期化
    const count = 12480;

    // 2. テストの実行
    const formatted = formatCount(count);

    // 3. アサーション
    expect(formatted).toBe('12,480');
  });
});
