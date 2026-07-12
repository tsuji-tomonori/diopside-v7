import { SearchCondition } from '@/types';

const schemaVersion = 1;
const savedKey = 'diopside_saved_v1';
const historyKey = 'diopside_history_v1';
const recentKey = 'diopside_recent_v1';
const consentKey = 'diopside_consent_v1';
const policyMajorVersion = '1';
const schemaVersionConsent = 1;
export const storageErrorEvent = 'diopside:storage-error';

interface SavedPayload {
  schemaVersion: number;
  items: string[];
}

interface HistoryPayload {
  schemaVersion: number;
  items: HistoryItem[];
}

interface HistoryItem {
  videoId: string;
  viewedAt: string;
}

interface RecentPayload {
  schemaVersion: number;
  items: RecentSearchItem[];
}

export interface RecentSearchItem {
  schemaVersion: number;
  createdAt: string;
  condition: SearchCondition;
}

export interface ConsentState {
  schemaVersion: number;
  policyMajor: string;
  acceptedAt: string;
}

export interface RecentSearchPayload {
  items: RecentSearchItem[];
}

function normalizeStringList(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return uniquePreserveOrder(raw.filter((item): item is string => typeof item === 'string'));
  }

  if (
    raw && typeof raw === 'object'
    && (raw as SavedPayload).schemaVersion === schemaVersion
    && Array.isArray((raw as SavedPayload).items)
  ) {
    const nested = (raw as SavedPayload).items;
    return uniquePreserveOrder(nested.filter((item): item is string => typeof item === 'string'));
  }

  return [];
}

function normalizeHistoryItems(raw: unknown): HistoryItem[] {
  if (!raw) {
    return [];
  }

  const items = Array.isArray(raw)
    ? raw
    : typeof raw === 'object'
      && (raw as HistoryPayload).schemaVersion === schemaVersion
      && Array.isArray((raw as HistoryPayload).items)
      ? (raw as HistoryPayload).items
      : [];

  const now = new Date().toISOString();
  return items
    .filter((entry): entry is HistoryItem => {
      return Boolean(entry && typeof entry === 'object' && typeof (entry as HistoryItem).videoId === 'string');
    })
    .map((entry) => ({
      videoId: String(entry.videoId),
      viewedAt: normalizeTime(entry.viewedAt ?? now),
    }));
}

function normalizeCondition(item: unknown): SearchCondition | null {
  if (!item || typeof item !== 'object') {
    return null;
  }

  const next = item as SearchCondition;
  const q = typeof next.q === 'string' ? next.q.trim() : '';
  const tags = uniquePreserveOrder(
    Array.isArray(next.tags)
      ? next.tags.filter((tag): tag is string => typeof tag === 'string').map((tag) => tag.trim()).filter(Boolean)
      : [],
  );
  const lmin = typeof next.lmin === 'number' && Number.isFinite(next.lmin) && next.lmin >= 0
    ? next.lmin
    : undefined;
  const lmax = typeof next.lmax === 'number' && Number.isFinite(next.lmax) && next.lmax >= 0
    ? next.lmax
    : undefined;
  const from = typeof next.from === 'string' && next.from ? next.from : undefined;
  const to = typeof next.to === 'string' && next.to ? next.to : undefined;
  const artifacts =
    Array.isArray(next.artifacts)
      ? uniquePreserveOrder(
          next.artifacts.filter(
            (artifact): artifact is 'chat' | 'comments' | 'wordcloud' | 'timestamps' =>
              artifact === 'chat' || artifact === 'comments' || artifact === 'wordcloud' || artifact === 'timestamps',
          ),
        )
      : [];

  return {
    q,
    tags,
    lmin,
    lmax,
    from,
    to,
    artifacts,
    sort: normalizeSort(next.sort),
  };
}

function normalizeRecentItems(raw: unknown): RecentSearchItem[] {
  if (!raw) {
    return [];
  }

  const items = Array.isArray(raw)
    ? raw
    : typeof raw === 'object'
      && (raw as RecentPayload).schemaVersion === schemaVersion
      && Array.isArray((raw as RecentPayload).items)
      ? (raw as RecentPayload).items
      : [];

  const now = new Date().toISOString();
  const list = items
    .map((entry) => {
      if (!entry || typeof entry !== 'object') {
        return null;
      }
      const condition = normalizeCondition((entry as RecentSearchItem).condition);
      if (!condition) {
        return null;
      }
      return {
        schemaVersion,
        createdAt: normalizeTime((entry as RecentSearchItem).createdAt ?? now),
        condition,
      };
    })
    .filter((entry): entry is RecentSearchItem => Boolean(entry));

  return uniqueRecentConditions(list);
}

function uniqueRecentConditions(items: RecentSearchItem[]): RecentSearchItem[] {
  const seen = new Set<string>();
  const filtered: RecentSearchItem[] = [];

  for (const item of items) {
    const key = JSON.stringify(item.condition);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    filtered.push(item);
  }

  return filtered;
}

function uniquePreserveOrder<T extends string>(items: T[]): T[] {
  return [...new Set(items)];
}

function normalizeTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return new Date().toISOString();
  }
  return parsed.toISOString();
}

function normalizeSort(value: SearchCondition['sort']): SearchCondition['sort'] {
  if (value === 'oldest' || value === 'longest' || value === 'mostChat') {
    return value;
  }
  return 'newest';
}

export function getSavedVideoIds(): string[] {
  return normalizeStringList(safeRead<unknown>(savedKey, []));
}

export function setSavedVideoIds(ids: string[]): void {
  safeWrite(savedKey, {
    schemaVersion,
    items: uniquePreserveOrder(ids),
  } satisfies SavedPayload);
}

export function getHistoryEntries(): HistoryItem[] {
  const raw = safeRead<unknown>(historyKey, []);
  const items = normalizeHistoryItems(raw).map((entry) => ({
    ...entry,
    viewedAt: normalizeTime(entry.viewedAt),
  }));
  const latestFirst = uniqueLatestFirst(items, (entry) => entry.videoId);
  return latestFirst;
}

export function getHistoryVideoIds(): string[] {
  return getHistoryEntries().map((entry) => entry.videoId);
}

export function addHistoryVideoId(videoId: string): void {
  const next = [
    { videoId, viewedAt: new Date().toISOString() },
    ...getHistoryEntries().filter((entry) => entry.videoId !== videoId),
  ];
  safeWrite(historyKey, {
    schemaVersion,
    items: uniqueLatestFirst(next, (entry) => entry.videoId),
  });
}

export function removeHistoryVideoId(videoId: string): void {
  const next = getHistoryEntries().filter((entry) => entry.videoId !== videoId);
  safeWrite(historyKey, {
    schemaVersion,
    items: next,
  });
}

export function clearHistoryItem(videoId: string): void {
  removeHistoryVideoId(videoId);
}

export function clearHistory(): void {
  safeRemove(historyKey);
}

export function addSavedVideoId(videoId: string): void {
  const next = uniquePreserveOrder([videoId, ...getSavedVideoIds()]);
  setSavedVideoIds(next);
}

export function removeSavedVideoId(videoId: string): void {
  safeWrite(savedKey, {
    schemaVersion,
    items: getSavedVideoIds().filter((id) => id !== videoId),
  } satisfies SavedPayload);
}

export function clearSaved(): void {
  safeRemove(savedKey);
}

export function removeRecentSearchAt(index: number): void {
  const current = getRecentSearchEntries();
  if (index < 0 || index >= current.length) {
    return;
  }

  safeWrite(recentKey, {
    schemaVersion,
    items: current.filter((_, i) => i !== index),
  });
}

export function clearRecentSearch(index: number): void {
  removeRecentSearchAt(index);
}

export function clearRecentSearches(): void {
  safeRemove(recentKey);
}

export function addRecentSearch(item: SearchCondition): void {
  const normalized = normalizeCondition(item);
  if (!normalized) {
    return;
  }

  const current = getRecentSearchEntries();
  const next = [
    {
      schemaVersion,
      createdAt: new Date().toISOString(),
      condition: normalized,
    },
    ...current.filter((entry) => JSON.stringify(entry.condition) !== JSON.stringify(normalized)),
  ].slice(0, 20);
  safeWrite(recentKey, {
    schemaVersion,
    items: next,
  });
}

export function getRecentSearchEntries(): RecentSearchItem[] {
  const raw = safeRead<unknown>(recentKey, []);
  return normalizeRecentItems(raw);
}

export function getRecentSearches(): SearchCondition[] {
  return getRecentSearchEntries().map((item) => item.condition);
}

export function getConsentVersion(): ConsentState | null {
  const raw = safeRead<unknown>(consentKey, null);
  if (!raw || typeof raw !== 'object') {
    return null;
  }
  const candidate = raw as Partial<ConsentState>;
  if (
    candidate.schemaVersion !== schemaVersionConsent
    || typeof candidate.policyMajor !== 'string'
    || !candidate.policyMajor
    || typeof candidate.acceptedAt !== 'string'
    || Number.isNaN(new Date(candidate.acceptedAt).getTime())
  ) {
    safeRemove(consentKey);
    return null;
  }
  return candidate as ConsentState;
}

export function getConsentMajorVersion(): string | null {
  const consent = getConsentVersion();
  return consent?.policyMajor ?? null;
}

export function hasActiveConsentVersion(expected: string = policyMajorVersion): boolean {
  const consent = getConsentVersion();
  return consent?.policyMajor === expected;
}

export function setConsentVersion(policyMajor: string = policyMajorVersion): void {
  safeWrite(consentKey, {
    schemaVersion: schemaVersionConsent,
    policyMajor,
    acceptedAt: new Date().toISOString(),
  });
}

export function clearConsent(): void {
  safeRemove(consentKey);
}

export function clearAllStorage(): void {
  clearSaved();
  clearHistory();
  clearRecentSearches();
  clearConsent();
}

function uniqueLatestFirst<T>(items: T[], selector: (item: T) => string): T[] {
  const next = [...items];
  const output: T[] = [];
  const seen = new Set<string>();

  for (const item of next) {
    const key = selector(item);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    output.push(item);
  }

  return output;
}

function safeRead<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    const parsed = JSON.parse(raw);
    if (!parsed) {
      return fallback;
    }
    return parsed as T;
  } catch {
    try {
      localStorage.removeItem(key);
    } catch {
      // Storage may be entirely unavailable; fallback remains local and empty.
    }
    return fallback;
  }
}

function safeWrite<T>(key: string, value: T): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    window.dispatchEvent(new CustomEvent(storageErrorEvent, { detail: { key } }));
    return false;
  }
}

function safeRemove(key: string): boolean {
  try {
    localStorage.removeItem(key);
    return true;
  } catch {
    window.dispatchEvent(new CustomEvent(storageErrorEvent, { detail: { key } }));
    return false;
  }
}
