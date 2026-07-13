import { describe, expect, it } from 'vitest';

import type { SearchCondition } from '@/types';

import { buildSearchParams, parseSearchParamsWithReport } from './search';


describe('検索queryの正規化', () => {
  // 重複タグと不正な境界値を正規化することを検証する。
  it('重複タグと不正な境界値を正規化する', () => {
    // 1. 初期化
    const query = new URLSearchParams('tag=z&tag=a&tag=a&lmin=-1&sort=unknown');

    // 2. テストの実行
    const parsed = parseSearchParamsWithReport(
      query,
    );

    // 3. アサーション
    expect(parsed.condition.tags).toEqual(['a', 'z']);
    expect(parsed.condition.lmin).toBeUndefined();
    expect(parsed.condition.sort).toBe('newest');
    expect(parsed.normalized).toBe(true);
  });

  // 複数タグから安定した反復parameterを生成することを検証する。
  it('安定した反復タグparameterを生成する', () => {
    // 1. 初期化
    const condition: SearchCondition = {
      q: '歌枠',
      tags: ['z', 'a'],
      artifacts: [],
      sort: 'newest',
    };

    // 2. テストの実行
    const query = buildSearchParams({
      ...condition,
    });

    // 3. アサーション
    expect(query).toBe('q=%E6%AD%8C%E6%9E%A0&tag=a&tag=z&sort=newest');
  });
});
