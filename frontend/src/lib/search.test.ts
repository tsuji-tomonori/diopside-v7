import { describe, expect, it } from 'vitest';

import { buildSearchParams, parseSearchParamsWithReport } from './search';


describe('検索queryの正規化', () => {
  // 重複タグと不正な境界値を正規化することを検証する。
  it('重複タグと不正な境界値を正規化する', () => {
    const parsed = parseSearchParamsWithReport(
      new URLSearchParams('tag=z&tag=a&tag=a&lmin=-1&sort=unknown'),
    );

    expect(parsed.condition.tags).toEqual(['a', 'z']);
    expect(parsed.condition.lmin).toBeUndefined();
    expect(parsed.condition.sort).toBe('newest');
    expect(parsed.normalized).toBe(true);
  });

  // 複数タグから安定した反復parameterを生成することを検証する。
  it('安定した反復タグparameterを生成する', () => {
    const query = buildSearchParams({
      q: '歌枠',
      tags: ['z', 'a'],
      artifacts: [],
      sort: 'newest',
    });

    expect(query).toBe('q=%E6%AD%8C%E6%9E%A0&tag=a&tag=z&sort=newest');
  });
});
