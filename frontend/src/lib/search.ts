import { SearchCondition, SearchVideoIndex } from '@/types';

export const canonicalArtifactOrder = ['chat', 'comments', 'wordcloud', 'timestamps'] as const;
export type SearchVideoResult = SearchVideoIndex & { chatCount?: number };

export interface SearchParseReport {
  condition: SearchCondition;
  notices: string[];
  normalized: boolean;
}

export function parseSearchParams(input: URLSearchParams): SearchCondition {
  return parseSearchParamsWithReport(input).condition;
}

export function parseSearchParamsWithReport(input: URLSearchParams): SearchParseReport {
  const notices: string[] = [];
  const rawQ = normalizeText(input.get('q') ?? '');
  const q = rawQ.length > 200 ? '' : rawQ;
  if (rawQ.length > 200) {
    notices.push('キーワードを200文字以内に正規化しました。');
  }
  if (input.has('tags')) {
    notices.push('非対応の `tags` パラメータは無視されました。');
  }

  const rawTags = uniqueSorted((input.getAll('tag') || []).map((id) => normalizeText(id)).filter(Boolean));
  const tags = rawTags.length > 20 ? [] : rawTags;
  if (rawTags.length > 20) {
    notices.push('tag条件が20件を超えているため、tag条件を不適用にしました。');
  }
  if (input.getAll('tag').length !== rawTags.length) {
    notices.push('重複したtag条件を1件化しました。');
  }

  const parsedLMin = parseMinutes(input.get('lmin'), 'lmin');
  const parsedLMax = parseMinutes(input.get('lmax'), 'lmax');
  if (parsedLMin.notice) {
    notices.push(parsedLMin.notice);
  }
  if (parsedLMax.notice) {
    notices.push(parsedLMax.notice);
  }
  const lmin = parsedLMin.value;
  const lmax = parsedLMax.value;

  const rawFrom = normalizeDate(input.get('from'));
  const rawTo = normalizeDate(input.get('to'));

  let normalizedLMin = lmin;
  let normalizedLMax = lmax;
  if (typeof normalizedLMin === 'number' && typeof normalizedLMax === 'number' && normalizedLMin > normalizedLMax) {
    normalizedLMin = undefined;
    normalizedLMax = undefined;
    notices.push('lmin > lmax のため長さ条件を不適用にしました。');
  }

  if (rawFrom === '__invalid__') {
    notices.push('from の形式が不正なため日付条件を不適用にしました。');
  }
  if (rawTo === '__invalid__') {
    notices.push('to の形式が不正なため日付条件を不適用にしました。');
  }
  let from = rawFrom;
  let to = rawTo;
  if (from === '__invalid__' || to === '__invalid__') {
    from = undefined;
    to = undefined;
  }
  if (from && to && new Date(from).getTime() > new Date(to).getTime()) {
    from = undefined;
    to = undefined;
    notices.push('from/to の順序が不正なため日付条件を不適用にしました。');
  }

  const rawArtifacts = (input.getAll('artifact') || [])
    .map((i) => i.toLowerCase())
    .filter((i): i is 'chat' | 'comments' | 'wordcloud' | 'timestamps' =>
      i === 'chat' || i === 'comments' || i === 'wordcloud' || i === 'timestamps',
    );
  const artifacts = uniqueSorted(rawArtifacts.filter((artifact) => canonicalArtifactOrder.includes(artifact as never)));
  if (rawArtifacts.length !== artifacts.length) {
    notices.push('不明なartifact条件を除外しました。');
  }
  const unknownSort = input.get('sort');
  if (unknownSort && !['newest', 'oldest', 'longest', 'mostChat'].includes(unknownSort)) {
    notices.push('不明な並び順は newest に正規化しました。');
  }

  const sort = normalizeSort(input.get('sort'));

  return {
    condition: {
      q,
      tags: tags.sort((a, b) => a.localeCompare(b)),
      lmin: normalizedLMin,
      lmax: normalizedLMax,
      from: from && from !== '__invalid__' ? from : undefined,
      to: to && to !== '__invalid__' ? to : undefined,
      artifacts,
      sort,
    },
    notices,
    normalized:
      notices.length > 0 ||
      rawQ !== q ||
      rawTags.length !== tags.length ||
      lmin !== normalizedLMin ||
      lmax !== normalizedLMax ||
      from !== rawFrom ||
      to !== rawTo,
  };
}

export function buildSearchParams(condition: SearchCondition): string {
  const next = new URLSearchParams();
  const sort = normalizeSort(condition.sort);

  if (condition.q) {
    next.set('q', condition.q);
  }

  const normalizedTags = uniqueSorted((condition.tags || []).map((id) => normalizeText(id)).filter(Boolean)).sort((a, b) =>
    a.localeCompare(b),
  );
  for (const tagId of normalizedTags) {
    next.append('tag', tagId);
  }

  if (typeof condition.lmin === 'number') {
    next.set('lmin', String(condition.lmin));
  }
  if (typeof condition.lmax === 'number') {
    next.set('lmax', String(condition.lmax));
  }
  if (condition.from) {
    next.set('from', condition.from);
  }
  if (condition.to) {
    next.set('to', condition.to);
  }

  const normalizedArtifacts = canonicalArtifactOrder.filter((artifact) => condition.artifacts.includes(artifact));
  for (const artifact of normalizedArtifacts) {
    next.append('artifact', artifact);
  }

  next.set('sort', sort);
  return next.toString();
}

export function applySearchQuery(
  index: SearchVideoIndex[],
  condition: SearchCondition,
  chatCounts?: Map<string, number>,
): SearchVideoResult[] {
  const enriched = index.map((video) => {
    const count = chatCounts?.get(video.videoId);
    return {
      ...video,
      ...(typeof count === 'number' ? { chatCount: count } : {}),
    };
  });
  const qTokens = tokenize(condition.q).map((t) => t.toLowerCase());

  const filterBase: SearchVideoResult[] = enriched.filter((video) => {
    if (qTokens.length) {
      const titleTokens = video.titleTokens.map((token) => token.toLowerCase());
      const hasAll = qTokens.every((token) => titleTokens.includes(token));
      if (!hasAll) {
        return false;
      }
    }

    if (condition.tags.length) {
      const hasAllTags = condition.tags.every((tag) => video.tagIds.includes(tag));
      if (!hasAllTags) {
        return false;
      }
    }

    if (typeof condition.lmin === 'number' && typeof video.durationSec === 'number') {
      if (video.durationSec < condition.lmin * 60) {
        return false;
      }
    }

    if (typeof condition.lmax === 'number' && typeof video.durationSec === 'number') {
      if (video.durationSec > condition.lmax * 60) {
        return false;
      }
    }

    if (condition.from && new Date(video.publishedDate) < new Date(condition.from)) {
      return false;
    }
    if (condition.to && new Date(video.publishedDate) > new Date(condition.to)) {
      return false;
    }

    if (condition.artifacts.length) {
      return condition.artifacts.some((artifact) => {
        if (artifact === 'chat') return video.artifactFlags.chat;
        if (artifact === 'comments') return video.artifactFlags.comments;
        if (artifact === 'timestamps') return video.artifactFlags.timestamps;
        if (artifact === 'wordcloud') return video.artifactFlags.wordcloud;
        return false;
      });
    }

    return true;
  });

  return sortVideos(filterBase, condition.sort);
}

export function sortVideos<T extends SearchVideoIndex>(videos: T[], sort: SearchCondition['sort']): T[] {
  const copy = [...videos] as Array<T & { chatCount?: number }>;
  const cmp = (a: T, b: T): number => {
    const nextA = a as T & { chatCount?: number };
    const nextB = b as T & { chatCount?: number };
    if (sort === 'oldest') {
      return compareDate(a.publishedAt, b.publishedAt) || a.videoId.localeCompare(b.videoId);
    }
    if (sort === 'longest') {
      const aDuration = a.durationSec ?? Number.NEGATIVE_INFINITY;
      const bDuration = b.durationSec ?? Number.NEGATIVE_INFINITY;
      if (bDuration === aDuration) {
        return a.videoId.localeCompare(b.videoId);
      }
      return bDuration - aDuration;
    }
    if (sort === 'mostChat') {
      const aHas = typeof nextA.chatCount === 'number';
      const bHas = typeof nextB.chatCount === 'number';
      if (aHas !== bHas) {
        return aHas ? -1 : 1;
      }
      const aCount = nextA.chatCount ?? 0;
      const bCount = nextB.chatCount ?? 0;
      if (bCount === aCount) {
        return compareDate(b.publishedAt, a.publishedAt) || a.videoId.localeCompare(b.videoId);
      }
      return bCount - aCount;
    }
    return compareDate(b.publishedAt, a.publishedAt) || a.videoId.localeCompare(b.videoId);
  };
  copy.sort(cmp);
  return copy;
}

function compareDate(a: string, b: string): number {
  return new Date(a).getTime() - new Date(b).getTime();
}

function normalizeText(value: string): string {
  return value.trim().replace(/\s+/g, ' ');
}

export function normalizeSearchTokens(value: string): string[] {
  if (!value) {
    return [];
  }
  const normalized = value
    .normalize('NFKC')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
  if (!normalized) {
    return [];
  }
  return normalized.split(/\s+/u).filter(Boolean);
}

function parseMinutes(value: string | null, field: 'lmin' | 'lmax'): { value: number | undefined; notice: string | null } {
  if (!value) {
    return { value: undefined, notice: null };
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return { value: undefined, notice: `${field} は数値に正規化できなかったため無効です。` };
  }
  if (numeric < 0) {
    return { value: undefined, notice: `${field} は負数のため無効です。` };
  }
  return { value: Math.floor(numeric), notice: null };
}

function normalizeDate(value: string | null): string | undefined | '__invalid__' {
  if (!value) {
    return undefined;
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return '__invalid__';
  }
  return value;
}

function normalizeSort(value: string | null): SearchCondition['sort'] {
  if (value === 'oldest' || value === 'longest' || value === 'mostChat') {
    return value;
  }
  return 'newest';
}

function uniqueSorted<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function tokenize(value: string): string[] {
  if (!value) {
    return [];
  }
  const normalized = value
    .normalize('NFKC')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
  if (!normalized) {
    return [];
  }
  return normalized.split(/[^\p{L}\p{N}]+/u).filter(Boolean);
}
