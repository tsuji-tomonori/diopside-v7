import { describe, expect, it } from 'vitest';

import { buildSearchParams, parseSearchParamsWithReport } from './search';


describe('search query canonicalization', () => {
  it('normalizes duplicate tags and invalid boundaries', () => {
    const parsed = parseSearchParamsWithReport(
      new URLSearchParams('tag=z&tag=a&tag=a&lmin=-1&sort=unknown'),
    );

    expect(parsed.condition.tags).toEqual(['a', 'z']);
    expect(parsed.condition.lmin).toBeUndefined();
    expect(parsed.condition.sort).toBe('newest');
    expect(parsed.normalized).toBe(true);
  });

  it('builds stable repeated tag parameters', () => {
    const query = buildSearchParams({
      q: '歌枠',
      tags: ['z', 'a'],
      artifacts: [],
      sort: 'newest',
    });

    expect(query).toBe('q=%E6%AD%8C%E6%9E%A0&tag=a&tag=z&sort=newest');
  });
});
