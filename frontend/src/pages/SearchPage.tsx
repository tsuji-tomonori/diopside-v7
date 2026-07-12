import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { SearchCondition } from '@/types';
import {
  addRecentSearch,
  clearRecentSearches,
  getRecentSearchEntries,
  removeRecentSearchAt,
  hasActiveConsentVersion,
} from '@/lib/storage';
import {
  applySearchQuery,
  buildSearchParams,
  parseSearchParams,
  parseSearchParamsWithReport,
} from '@/lib/search';
import { usePublicData } from '@/state/PublicDataContext';
import { VideoCard } from '@/components/VideoCard';
import { DataErrorState } from '@/components/DataErrorState';

function unique<T>(values: T[]): T[] {
  return [...new Set(values)];
}

function normalizeTerm(value: string): string {
  return value
    .normalize('NFKC')
    .trim()
    .replace(/\s+/g, ' ');
}

export function SearchPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { loading, error, errorKind, release, search, tagIndex, alias, refresh, latest } = usePublicData();

  const isFeatureEnabled =
    latest?.releaseMode === 'normal' && hasActiveConsentVersion('1');

  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState(() => getRecentSearchEntries());
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);

  const parsed = useMemo(() => {
    const source = new URLSearchParams(location.search);
    return parseSearchParamsWithReport(source);
  }, [location.search]);

  const aliasMap = useMemo(() => new Map<string, string>(Object.entries(alias?.aliases ?? {})), [alias?.aliases]);
  const knownTagIds = useMemo(() => new Set((tagIndex?.tags ?? []).map((tag) => tag.tagId)), [tagIndex?.tags]);
  const canonicalizationNotices = useMemo(() => {
    if (!isFeatureEnabled) {
      return parsed.notices;
    }
    const aliases = parsed.condition.tags.map((tagId) => {
      const next = aliasMap.get(tagId) ?? tagId;
      return next.trim();
    });
    const hadAliasConversion = parsed.condition.tags.some((tagId) => {
      const mapped = aliasMap.get(tagId);
      return Boolean(mapped && mapped !== tagId);
    });
    const knownAliases = aliases.filter((tagId) => knownTagIds.has(tagId));
    const uniqueAliases = unique(knownAliases);
    const notices: string[] = [...parsed.notices];

    if (hadAliasConversion) {
      notices.push('tagエイリアスをcanonical idへ変換しました。');
    }
    if (uniqueAliases.length < aliases.length) {
      notices.push('未知/無効なtag条件を除外しました。');
    }
    return notices;
  }, [aliasMap, isFeatureEnabled, knownTagIds, parsed.condition.tags, parsed.notices]);

  const normalized = useMemo(() => {
    const base = parsed.condition;
    const tags = isFeatureEnabled
      ? base.tags
          .map((tagId) => aliasMap.get(tagId) ?? tagId)
          .map((tagId) => tagId.trim())
          .filter(Boolean)
          .filter((tagId) => knownTagIds.has(tagId))
          .filter((tagId, index, all) => all.indexOf(tagId) === index)
      : [];

    return {
      ...base,
      tags,
      artifacts: isFeatureEnabled ? base.artifacts : [],
      sort: isFeatureEnabled ? base.sort : 'newest',
    } satisfies SearchCondition;
  }, [aliasMap, isFeatureEnabled, knownTagIds, parsed.condition]);

  useEffect(() => {
    setQuery(normalized.q);
    if (parsed.normalized || isDifferent(normalized, parseSearchParams(new URLSearchParams(location.search)))) {
      const params = buildSearchParams(normalized);
      navigate(`/search${params ? `?${params}` : ''}`, { replace: true });
    }
    if (canonicalizationNotices.length) {
      setNotice(canonicalizationNotices[0]);
    }
  }, [isFeatureEnabled, location.search, navigate, normalized, canonicalizationNotices, parsed]);

  useEffect(() => {
    setRecentSearches(getRecentSearchEntries());
  }, [location.search]);

  const chatCounts = useMemo(() => {
    const map = new Map<string, number>();
    for (const video of release?.videos ?? []) {
      if (typeof video.chat?.totalCount === 'number') {
        map.set(video.videoId, video.chat.totalCount);
      }
    }
    return map;
  }, [release?.videos]);

  const videos = applySearchQuery(search?.videos ?? [], normalized, chatCounts);

  const tags = tagIndex?.tags ?? [];
  const suggestions = useMemo(() => {
    const term = normalizeTerm(query).toLocaleLowerCase('ja');
    if (!term || !isFeatureEnabled) {
      return [];
    }
    return tags
      .filter((tag) => tag.displayName.toLocaleLowerCase('ja').includes(term))
      .slice(0, 8);
  }, [isFeatureEnabled, query, tags]);

  function selectSuggestion(index: number): void {
    const selected = suggestions[index];
    if (!selected) {
      return;
    }
    toggleTag(selected.tagId);
    setSuggestionsOpen(false);
    setActiveSuggestion(-1);
    setNotice(`${selected.displayName} を検索条件へ追加しました。`);
  }

  function onSuggestionKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === 'Escape') {
      setSuggestionsOpen(false);
      setActiveSuggestion(-1);
      return;
    }
    if (event.key === 'ArrowDown' && suggestions.length) {
      event.preventDefault();
      setSuggestionsOpen(true);
      setActiveSuggestion((current) => Math.min(current + 1, suggestions.length - 1));
      return;
    }
    if (event.key === 'ArrowUp' && suggestions.length) {
      event.preventDefault();
      setSuggestionsOpen(true);
      setActiveSuggestion((current) => Math.max(current - 1, 0));
      return;
    }
    if (event.key === 'Enter' && suggestionsOpen && activeSuggestion >= 0) {
      event.preventDefault();
      selectSuggestion(activeSuggestion);
    }
  }

  function syncUrl(condition: SearchCondition, { recordRecent }: { recordRecent: boolean }): void {
    const payload: SearchCondition = {
      ...normalized,
      ...condition,
      q: normalizeTerm(condition.q),
      tags: isFeatureEnabled ? unique(condition.tags).filter(Boolean) : [],
      artifacts: isFeatureEnabled ? unique(condition.artifacts) : [],
      sort: !isFeatureEnabled && condition.sort === 'mostChat' ? 'newest' : condition.sort,
    };
    const param = buildSearchParams(payload);
    navigate(`/search${param ? `?${param}` : ''}`, { replace: true });
    if (recordRecent) {
      addRecentSearch(payload);
      setRecentSearches(getRecentSearchEntries());
    }
    setNotice('検索条件を更新しました。');
  }

  function apply(next: SearchCondition, options: { recordRecent: boolean }): void {
    syncUrl(next, options);
  }

  function applyFromInputs(next: Partial<SearchCondition>, options: { recordRecent: boolean } = { recordRecent: true }): void {
    apply(
      {
        ...normalized,
        ...next,
        q: query,
      },
      options,
    );
  }

  function onSubmit(event: FormEvent): void {
    event.preventDefault();
    applyFromInputs({ q: normalizeTerm(query) }, { recordRecent: true });
  }

  function toggleTag(candidate: string): void {
    const canonical = aliasMap.get(candidate) ?? candidate;
    const nextTags = normalized.tags.includes(canonical)
      ? normalized.tags.filter((tag) => tag !== canonical)
      : [...normalized.tags, canonical];

    applyFromInputs({ tags: nextTags }, { recordRecent: true });
  }

  function applyRecent(entryIndex: number): void {
    const entry = recentSearches[entryIndex];
    if (!entry) {
      return;
    }
    const next = {
      ...normalized,
      ...entry.condition,
    };
    syncUrl(next, { recordRecent: false });
    setQuery(next.q);
    setNotice('最近の検索条件を再適用しました。');
  }

  function removeRecent(index: number): void {
    removeRecentSearchAt(index);
    setRecentSearches(getRecentSearchEntries());
    setNotice('最近の検索条件を1件削除しました。');
  }

  function clearRecent(): void {
    clearRecentSearches();
    setRecentSearches([]);
    setNotice('最近の検索条件を全削除しました。');
  }

  if (loading) {
    return <p className="status">検索インデックスを読込んでいます…</p>;
  }

  if (error && errorKind) {
    return <DataErrorState kind={errorKind} detail={error} retry={() => void refresh()} />;
  }

  return (
    <section>
      <h1>search</h1>
      <form className="search-form" onSubmit={onSubmit}>
        <label>
          キーワード
          <input
            value={query}
            role="combobox"
            aria-autocomplete="list"
            aria-controls="tag-suggestions"
            aria-expanded={suggestionsOpen && suggestions.length > 0}
            aria-activedescendant={activeSuggestion >= 0 ? `tag-suggestion-${activeSuggestion}` : undefined}
            onChange={(event) => {
              setQuery(event.target.value);
              setSuggestionsOpen(true);
              setActiveSuggestion(-1);
            }}
            onFocus={() => setSuggestionsOpen(true)}
            onKeyDown={onSuggestionKeyDown}
            placeholder="例: 歌枠"
          />
          {suggestionsOpen && suggestions.length ? (
            <ul className="suggestions" id="tag-suggestions" role="listbox">
              {suggestions.map((tag, index) => (
                <li
                  id={`tag-suggestion-${index}`}
                  key={tag.tagId}
                  role="option"
                  aria-selected={activeSuggestion === index}
                >
                  <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => selectSuggestion(index)}>
                    {tag.displayName}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </label>
        <label>
          最短（分）
          <input
            type="number"
            value={normalized.lmin ?? ''}
            onChange={(event) =>
              applyFromInputs({
                lmin: event.target.value ? Number(event.target.value) : undefined,
              })
            }
          />
        </label>
        <label>
          最長（分）
          <input
            type="number"
            value={normalized.lmax ?? ''}
            onChange={(event) =>
              applyFromInputs({
                lmax: event.target.value ? Number(event.target.value) : undefined,
              })
            }
          />
        </label>
        <label>
          並び順
          <select
            value={normalized.sort}
            onChange={(event) =>
              applyFromInputs({
                sort: event.target.value as SearchCondition['sort'],
              })
            }
          >
            <option value="newest">newest</option>
            <option value="oldest">oldest</option>
            <option value="longest">longest</option>
            {isFeatureEnabled ? <option value="mostChat">mostChat</option> : null}
          </select>
        </label>
        <button type="submit">更新</button>
      </form>

      {isFeatureEnabled && tags.length ? (
        <section className="section">
          <h2>tag</h2>
          <div className="chips">
            {tags.slice(0, 8).map((tag) => (
              <button
                key={tag.tagId}
                type="button"
                className={normalized.tags.includes(tag.tagId) ? 'chip' : ''}
                onClick={() => toggleTag(tag.tagId)}
              >
                {tag.displayName}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <section className="section">
        <h2>recent search</h2>
        {recentSearches.length === 0 ? <p className="muted">履歴はありません</p> : null}
        {recentSearches.length > 0 ? (
          <>
            <div className="chips">
              {recentSearches.map((entry, index) => (
                <div key={`${entry.createdAt}-${index}`} className="chip-row">
                  <button
                    type="button"
                    onClick={() => applyRecent(index)}
                    aria-label={`recent search ${entry.condition.q || 'no keyword'} を再適用`}
                  >
                    {entry.condition.q || '(条件なし)'}
                    {entry.condition.tags.length ? ` / ${entry.condition.tags.length}tag` : ''}
                  </button>
                  <button type="button" onClick={() => removeRecent(index)}>
                    削除
                  </button>
                </div>
              ))}
            </div>
            <button type="button" onClick={clearRecent}>
              recent searchを全削除
            </button>
          </>
        ) : null}
      </section>

      <p className="status">{videos.length} 件</p>
      {notice ? <p role="status" aria-live="polite">{notice}</p> : null}

      <section className="video-list">
        {videos.length === 0 ? (
          <div className="status-card">
            <p>0件です。条件をゆるめると見つかりやすくなります。</p>
            <button
              type="button"
              onClick={() =>
                applyFromInputs({
                  tags: normalized.tags.slice(0, Math.max(normalized.tags.length - 1, 0)),
                })
              }
            >
              条件を1件解除
            </button>
          </div>
        ) : null}

        {videos.map((video) => {
          const names = tags
            .filter((tag) => (video.tagIds ?? []).includes(tag.tagId))
            .map((tag) => tag.displayName);
          const releaseVideo = release?.videos.find((item) => item.videoId === video.videoId);
          return (
            <VideoCard
              key={video.videoId}
              videoId={video.videoId}
              title={video.titleTokens.join(' ')}
              publishedAt={video.publishedAt}
              duration={String(releaseVideo?.duration ?? '')}
              thumbnail={releaseVideo?.thumbnail.url ?? ''}
              tagNames={isFeatureEnabled ? names : []}
              flags={video.artifactFlags}
              chatCount={releaseVideo?.chat?.totalCount}
            />
          );
        })}
      </section>
    </section>
  );
}

function isDifferent(a: SearchCondition, b: SearchCondition): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}
