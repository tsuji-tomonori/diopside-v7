import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
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
import { NavIcon } from '@/components/NavIcon';

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
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const closeFilterRef = useRef<HTMLButtonElement>(null);

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
      .slice(0, 4);
  }, [isFeatureEnabled, query, tags]);

  const activeConditionCount =
    normalized.tags.length
    + normalized.artifacts.length
    + Number(normalized.lmin !== undefined)
    + Number(normalized.lmax !== undefined)
    + Number(normalized.from !== undefined)
    + Number(normalized.to !== undefined)
    + Number(normalized.sort !== 'newest');

  useEffect(() => {
    if (!filtersOpen) {
      return undefined;
    }
    closeFilterRef.current?.focus();
    const handleFilterKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        setFiltersOpen(false);
        filterButtonRef.current?.focus();
        return;
      }
      if (event.key !== 'Tab') {
        return;
      }

      const panel = document.getElementById('search-filters');
      const focusable = panel?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener('keydown', handleFilterKeyDown);
    return () => window.removeEventListener('keydown', handleFilterKeyDown);
  }, [filtersOpen]);

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
    <section className="page search-page">
      <header className="page-header">
        <p className="eyebrow">ARCHIVE SEARCH</p>
        <h1>アーカイブを探す</h1>
        <p className="page-lead">覚えている言葉、テーマ、配信の長さから絞り込めます。</p>
      </header>

      <form className="search-toolbar" onSubmit={onSubmit}>
        <label className="search-field">
          <span className="sr-only">キーワード</span>
          <NavIcon name="search" />
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
            placeholder="タイトルや覚えている言葉"
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
                    <span>{tag.displayName}</span>
                    <span className="suggestion-meta">{tag.count}本</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </label>
        <button className="button button-primary search-submit" type="submit">検索</button>
        <button
          className="button button-secondary filter-trigger"
          type="button"
          ref={filterButtonRef}
          aria-expanded={filtersOpen}
          aria-controls="search-filters"
          onClick={() => setFiltersOpen(true)}
        >
          条件{activeConditionCount ? `（${activeConditionCount}）` : ''}
        </button>
      </form>

      {normalized.tags.length ? (
        <div className="active-conditions" aria-label="適用中の条件">
          {normalized.tags.map((tagId) => {
            const tag = tags.find((item) => item.tagId === tagId);
            return (
              <button className="chip chip-selected" key={tagId} type="button" onClick={() => toggleTag(tagId)}>
                {tag?.displayName ?? tagId}
                <span aria-hidden="true">×</span>
                <span className="sr-only">の条件を解除</span>
              </button>
            );
          })}
        </div>
      ) : null}

      {filtersOpen ? <button className="filter-backdrop" type="button" aria-label="検索条件を閉じる" onClick={() => setFiltersOpen(false)} /> : null}

      <div className="search-layout">
        <div className="search-results">
          <div className="result-heading">
            <h2>検索結果</h2>
            <p className="result-count" aria-live="polite">{videos.length}件</p>
          </div>
          {notice ? <p className="notice" role="status" aria-live="polite">{notice}</p> : null}

          <section className="video-list" aria-label="検索結果の動画">
            {videos.length === 0 ? (
              <div className="empty-state">
                <span className="empty-mark" aria-hidden="true">0</span>
                <h3>条件に合うアーカイブがありません</h3>
                <p>キーワードを短くするか、適用中の条件をひとつ外してみてください。</p>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => {
                    if (normalized.tags.length) {
                      applyFromInputs({ tags: normalized.tags.slice(0, -1) });
                    } else {
                      setQuery('');
                      applyFromInputs({ q: '' });
                    }
                  }}
                >
                  条件をひとつ解除
                </button>
              </div>
            ) : null}

            {videos.map((video) => {
              const releaseVideo = release?.videos.find((item) => item.videoId === video.videoId);
              if (!releaseVideo) {
                return null;
              }
              const names = tags
                .filter((tag) => (video.tagIds ?? []).includes(tag.tagId))
                .map((tag) => tag.displayName);
              return (
                <VideoCard
                  key={video.videoId}
                  videoId={video.videoId}
                  title={releaseVideo.title}
                  publishedAt={video.publishedAt}
                  duration={releaseVideo.duration}
                  thumbnail={releaseVideo.thumbnail.url}
                  tagNames={isFeatureEnabled ? names : []}
                  flags={video.artifactFlags}
                  chatCount={releaseVideo.chat?.totalCount}
                />
              );
            })}
          </section>

          <section className="section recent-section" aria-labelledby="recent-heading">
            <div className="section-heading">
              <div>
                <p className="eyebrow">RECENT</p>
                <h2 id="recent-heading">最近の検索</h2>
              </div>
              {recentSearches.length ? (
                <button className="text-button danger-text" type="button" onClick={clearRecent}>すべて削除</button>
              ) : null}
            </div>
            {recentSearches.length === 0 ? <p className="muted">検索条件を保存すると、ここからすぐに再開できます。</p> : null}
            {recentSearches.length > 0 ? (
              <div className="recent-list">
                {recentSearches.map((entry, index) => (
                  <div key={`${entry.createdAt}-${index}`} className="recent-row">
                    <button
                      className="recent-apply"
                      type="button"
                      onClick={() => applyRecent(index)}
                      aria-label={`${entry.condition.q || '条件のみの検索'}を再適用`}
                    >
                      <NavIcon name="history" />
                      <span>{entry.condition.q || '条件のみの検索'}</span>
                      {entry.condition.tags.length ? <small>{entry.condition.tags.length}タグ</small> : null}
                    </button>
                    <button className="icon-button" type="button" onClick={() => removeRecent(index)} aria-label="この検索履歴を削除">×</button>
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        </div>

        <aside className={filtersOpen ? 'condition-panel is-open' : 'condition-panel'} id="search-filters" aria-label="検索条件">
          <div className="panel-header">
            <div>
              <p className="eyebrow">FILTER</p>
              <h2>検索条件</h2>
            </div>
            <button
              className="icon-button panel-close"
              type="button"
              ref={closeFilterRef}
              onClick={() => {
                setFiltersOpen(false);
                filterButtonRef.current?.focus();
              }}
              aria-label="検索条件を閉じる"
            >
              ×
            </button>
          </div>

          {isFeatureEnabled && tags.length ? (
            <fieldset className="filter-group">
              <legend>テーマ</legend>
              <div className="chips">
                {tags.slice(0, 8).map((tag) => (
                  <button
                    key={tag.tagId}
                    type="button"
                    className={normalized.tags.includes(tag.tagId) ? 'chip chip-selected' : 'chip chip-selectable'}
                    aria-pressed={normalized.tags.includes(tag.tagId)}
                    onClick={() => toggleTag(tag.tagId)}
                  >
                    {tag.displayName}
                  </button>
                ))}
              </div>
            </fieldset>
          ) : null}

          <fieldset className="filter-group">
            <legend>配信の長さ</legend>
            <div className="range-fields">
              <label>
                <span>最短</span>
                <span className="field-with-unit">
                  <input
                    type="number"
                    min="0"
                    inputMode="numeric"
                    value={normalized.lmin ?? ''}
                    onChange={(event) => applyFromInputs({ lmin: event.target.value ? Number(event.target.value) : undefined })}
                  />
                  <span>分</span>
                </span>
              </label>
              <span aria-hidden="true">—</span>
              <label>
                <span>最長</span>
                <span className="field-with-unit">
                  <input
                    type="number"
                    min="0"
                    inputMode="numeric"
                    value={normalized.lmax ?? ''}
                    onChange={(event) => applyFromInputs({ lmax: event.target.value ? Number(event.target.value) : undefined })}
                  />
                  <span>分</span>
                </span>
              </label>
            </div>
          </fieldset>

          <fieldset className="filter-group">
            <legend>投稿日</legend>
            <div className="date-fields">
              <label>
                <span>開始日</span>
                <input
                  type="date"
                  max={normalized.to ?? new Date().toISOString().slice(0, 10)}
                  value={normalized.from ?? ''}
                  onChange={(event) => applyFromInputs({ from: event.target.value || undefined })}
                />
              </label>
              <label>
                <span>終了日</span>
                <input
                  type="date"
                  min={normalized.from}
                  max={new Date().toISOString().slice(0, 10)}
                  value={normalized.to ?? ''}
                  onChange={(event) => applyFromInputs({ to: event.target.value || undefined })}
                />
              </label>
            </div>
          </fieldset>

          <label className="filter-group select-label">
            <span>並び順</span>
            <select
              value={normalized.sort}
              onChange={(event) => applyFromInputs({ sort: event.target.value as SearchCondition['sort'] })}
            >
              <option value="newest">新しい順</option>
              <option value="oldest">古い順</option>
              <option value="longest">長い順</option>
              {isFeatureEnabled ? <option value="mostChat">チャットが多い順</option> : null}
            </select>
          </label>

          <div className="panel-actions">
            <button
              className="button button-quiet"
              type="button"
              onClick={() => {
                setQuery('');
                apply({
                  q: '',
                  tags: [],
                  artifacts: [],
                  lmin: undefined,
                  lmax: undefined,
                  from: undefined,
                  to: undefined,
                  sort: 'newest',
                }, { recordRecent: false });
              }}
            >
              リセット
            </button>
            <button className="button button-primary" type="button" onClick={() => setFiltersOpen(false)}>
              {videos.length}件を見る
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}

function isDifferent(a: SearchCondition, b: SearchCondition): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}
