import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { DataErrorState } from '@/components/DataErrorState';
import { Button } from '@/components/ui/Button';
import { Chip } from '@/components/ui/Chip';
import { ConditionPanel } from '@/components/ui/ConditionPanel';
import { ConditionRow } from '@/components/ui/ConditionRow';
import { EmptyState } from '@/components/ui/EmptyState';
import { LengthSlider } from '@/components/ui/LengthSlider';
import { LoadingState } from '@/components/ui/LoadingState';
import { RangeCalendar } from '@/components/ui/RangeCalendar';
import { SearchBar } from '@/components/ui/SearchBar';
import { SuggestItem, SuggestList } from '@/components/ui/SuggestList';
import { VideoListItem } from '@/components/ui/VideoListItem';
import { applySearchQuery, buildSearchParams, parseSearchParamsWithReport } from '@/lib/search';
import { hasActiveConsentVersion } from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { SearchCondition, TagInfo, VideoIndex } from '@/types';

const suggestionListId = 'search-suggestions';

function normalizeTerm(value: string): string {
  return value.normalize('NFKC').trim().replace(/\s+/g, ' ');
}

function isSameCondition(left: SearchCondition, right: SearchCondition): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function formatLength(value: number, upper = false): string {
  if (upper && value >= 300) {
    return '上限なし';
  }

  const hours = Math.floor(value / 60);
  const minutes = value % 60;
  return `${hours}h${minutes ? `${minutes}m` : ''}`;
}

function formatDateRange(condition: SearchCondition): string {
  if (condition.from && condition.to) {
    return `${condition.from}〜${condition.to}`;
  }

  return condition.from ?? condition.to ?? '';
}

function toConditionList(condition: SearchCondition, tags: TagInfo[]) {
  const tagLabels = condition.tags
    .map((tagId) => tags.find((tag) => tag.tagId === tagId)?.displayName)
    .filter((label): label is string => Boolean(label));
  const conditions = tagLabels.map((label, index) => ({
    id: `tag-${condition.tags[index]}`,
    label,
    section: 'tags',
  }));

  if (typeof condition.lmin === 'number' || typeof condition.lmax === 'number') {
    conditions.push({
      id: 'length',
      label: `${formatLength(condition.lmin ?? 0)}〜${formatLength(condition.lmax ?? 300, true)}`,
      section: 'length',
    });
  }

  if (condition.from || condition.to) {
    conditions.push({ id: 'date', label: formatDateRange(condition), section: 'date' });
  }

  return conditions;
}

export function SearchPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { loading, error, errorKind, release, search, tagIndex, alias, refresh, latest } = usePublicData();
  const featureEnabled = latest?.releaseMode === 'normal' && hasActiveConsentVersion('1');
  const [query, setQuery] = useState('');
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [notice, setNotice] = useState('');
  const [panelOpen, setPanelOpen] = useState(false);
  const [initialSection, setInitialSection] = useState<string | undefined>();
  const [calendarOpen, setCalendarOpen] = useState(false);

  const parsed = useMemo(
    () => parseSearchParamsWithReport(new URLSearchParams(location.search)),
    [location.search],
  );
  const tags = tagIndex?.tags ?? [];
  const aliasMap = useMemo(() => new Map(Object.entries(alias?.aliases ?? {})), [alias?.aliases]);
  const knownTagIds = useMemo(() => new Set(tags.map((tag) => tag.tagId)), [tags]);
  const normalized = useMemo(() => {
    const tagIds = featureEnabled
      ? Array.from(new Set(parsed.condition.tags.map((tag) => aliasMap.get(tag) ?? tag)))
        .filter((tag) => knownTagIds.has(tag))
      : [];

    return {
      ...parsed.condition,
      tags: tagIds,
      artifacts: featureEnabled ? parsed.condition.artifacts : [],
      sort: featureEnabled ? parsed.condition.sort : 'newest',
    } satisfies SearchCondition;
  }, [aliasMap, featureEnabled, knownTagIds, parsed.condition]);

  useEffect(() => {
    setQuery(normalized.q);
    if (parsed.normalized || !isSameCondition(parsed.condition, normalized)) {
      const params = buildSearchParams(normalized);
      navigate(`/search${params ? `?${params}` : ''}`, { replace: true });
    }
  }, [navigate, normalized, parsed.condition, parsed.normalized]);

  const chatCounts = useMemo(
    () => new Map(
      (release?.videos ?? [])
        .filter((video) => typeof video.chat?.totalCount === 'number')
        .map((video) => [video.videoId, video.chat!.totalCount]),
    ),
    [release?.videos],
  );
  const results = useMemo(
    () => applySearchQuery(search?.videos ?? [], normalized, chatCounts),
    [chatCounts, normalized, search?.videos],
  );
  const videosById = useMemo(
    () => new Map((release?.videos ?? []).map((video) => [video.videoId, video])),
    [release?.videos],
  );
  const suggestions = useMemo<SuggestItem[]>(() => {
    const term = normalizeTerm(query).toLocaleLowerCase('ja');
    if (!featureEnabled || !term) {
      return [];
    }

    const tagSuggestions = tags
      .filter((tag) => tag.displayName.toLocaleLowerCase('ja').includes(term))
      .sort((left, right) => right.count - left.count || left.displayName.localeCompare(right.displayName, 'ja'))
      .slice(0, 2)
      .map((tag) => ({
        id: `tag:${tag.tagId}`,
        label: tag.displayName,
        detail: `${tag.count}件`,
      }));

    return [...tagSuggestions, { id: 'keyword', label: `「${normalizeTerm(query)}」を検索` }].slice(0, 4);
  }, [featureEnabled, query, tags]);
  const conditions = toConditionList(normalized, tags);
  const streamedDates = useMemo(
    () => (release?.videos ?? []).map((video) => video.publishedAt.slice(0, 10)),
    [release?.videos],
  );

  function updateCondition(next: SearchCondition): void {
    const params = buildSearchParams({ ...next, q: normalizeTerm(next.q) });
    navigate(`/search${params ? `?${params}` : ''}`);
  }

  function updatePartial(next: Partial<SearchCondition>): void {
    updateCondition({ ...normalized, ...next, q: query });
  }

  function openConditions(section?: string): void {
    setInitialSection(section);
    setCalendarOpen(false);
    setPanelOpen(true);
  }

  function removeCondition(id: string): void {
    if (id.startsWith('tag-')) {
      updatePartial({ tags: normalized.tags.filter((tag) => `tag-${tag}` !== id) });
      return;
    }
    if (id === 'length') {
      updatePartial({ lmin: undefined, lmax: undefined });
      return;
    }
    updatePartial({ from: undefined, to: undefined });
  }

  function selectSuggestion(item: SuggestItem): void {
    if (item.id.startsWith('tag:')) {
      const tagId = item.id.slice(4);
      if (!normalized.tags.includes(tagId)) {
        updatePartial({ tags: [...normalized.tags, tagId] });
      }
      const label = tags.find((tag) => tag.tagId === tagId)?.displayName ?? 'タグ';
      setNotice(`${label} を検索条件へ追加しました。`);
    } else {
      updatePartial({ q: normalizeTerm(query) });
      setNotice('キーワードを検索条件へ追加しました。');
    }
    setSuggestionsOpen(false);
    setActiveSuggestion(-1);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
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
      selectSuggestion(suggestions[activeSuggestion]);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    updatePartial({ q: normalizeTerm(query) });
    setSuggestionsOpen(false);
  }

  function tagNames(video: VideoIndex): string[] {
    if (!featureEnabled) {
      return [];
    }

    return tags
      .filter((tag) => video.tagIds?.includes(tag.tagId))
      .map((tag) => tag.displayName);
  }

  if (loading) {
    return (
      <section className="dio-search-page">
        <h1>検索</h1>
        <LoadingState label="検索インデックスを読み込んでいます…" />
      </section>
    );
  }

  if (error && errorKind) {
    return <DataErrorState detail={error} kind={errorKind} retry={() => void refresh()} />;
  }

  if (!search || !release) {
    return <DataErrorState detail="公開artifactが不足しているため検索結果を表示できません。" kind="not_found" retry={() => void refresh()} />;
  }

  return (
    <section className="dio-search-page">
      <h1>検索</h1>
      <div className="dio-search-page__input">
        <SearchBar
          activeSuggestionId={activeSuggestion >= 0 ? `${suggestionListId}-${activeSuggestion}` : undefined}
          onKeyDown={onKeyDown}
          onQueryChange={(value) => {
            setQuery(value);
            setSuggestionsOpen(true);
            setActiveSuggestion(-1);
          }}
          onSubmit={onSubmit}
          onTokenRemove={(tagId) => updatePartial({ tags: normalized.tags.filter((tag) => tag !== tagId) })}
          query={query}
          suggestionListId={suggestionListId}
          suggestionsOpen={suggestionsOpen && suggestions.length > 0}
          tokens={normalized.tags.map((tagId) => ({
            id: tagId,
            label: tags.find((tag) => tag.tagId === tagId)?.displayName ?? tagId,
          }))}
        />
        {suggestionsOpen ? (
          <SuggestList
            activeIndex={activeSuggestion}
            id={suggestionListId}
            items={suggestions}
            onSelect={selectSuggestion}
          />
        ) : null}
      </div>
      <ConditionRow conditions={conditions} onOpen={openConditions} onRemove={removeCondition} />
      <div aria-live="polite" className="sr-only" role="status">
        {notice || `${results.length}件の検索結果です。`}
      </div>
      <header className="dio-search-page__results-header">
        <p className="dio-num">{results.length}件</p>
        <label>
          並び順
          <select
            onChange={(event) => updatePartial({ sort: event.target.value as SearchCondition['sort'] })}
            value={normalized.sort}
          >
            <option value="newest">新しい順</option>
            <option value="oldest">古い順</option>
            <option value="longest">長い順</option>
            {featureEnabled ? <option value="mostChat">チャット数順</option> : null}
          </select>
        </label>
      </header>
      <div className="video-list">
        {results.length === 0 ? (
          <EmptyState title="条件に合う動画はありません">
            <p>条件をゆるめると見つかりやすくなります。</p>
            <Button
              onClick={() => updatePartial({ tags: [], lmin: undefined, lmax: undefined, from: undefined, to: undefined })}
              type="button"
            >
              条件をゆるめる
            </Button>
          </EmptyState>
        ) : null}
        {results.map((result) => {
          const video = videosById.get(result.videoId);
          if (!video) {
            return null;
          }

          return (
            <VideoListItem
              chatCount={result.chatCount}
              key={video.videoId}
              tagNames={tagNames(video)}
              video={video}
            />
          );
        })}
      </div>
      <ConditionPanel
        initialSection={initialSection}
        onClose={() => setPanelOpen(false)}
        open={panelOpen}
        resultCount={results.length}
      >
        {calendarOpen ? (
          <section className="dio-condition-section">
            <RangeCalendar
              from={normalized.from}
              onBack={() => setCalendarOpen(false)}
              onChange={(range) => updatePartial(range)}
              streamedDates={streamedDates}
              to={normalized.to}
            />
          </section>
        ) : (
          <div className="dio-condition-sections">
            <section className="dio-condition-section" id="tags">
              <h3>タグ</h3>
              <div className="chips">
                {tags.map((tag) => (
                  <Chip
                    key={tag.tagId}
                    label={tag.displayName}
                    onClick={() => updatePartial({
                      tags: normalized.tags.includes(tag.tagId)
                        ? normalized.tags.filter((tagId) => tagId !== tag.tagId)
                        : [...normalized.tags, tag.tagId],
                    })}
                    selected={normalized.tags.includes(tag.tagId)}
                  />
                ))}
              </div>
            </section>
            <section className="dio-condition-section" id="length">
              <h3>長さ</h3>
              <LengthSlider
                max={normalized.lmax ?? 300}
                min={normalized.lmin ?? 0}
                onChange={(range) => updatePartial({
                  lmin: range.min === 0 ? undefined : range.min,
                  lmax: range.max === 300 ? undefined : range.max,
                })}
              />
            </section>
            <section className="dio-condition-section" id="date">
              <h3>{formatDateRange(normalized) || '投稿日'}</h3>
              <div className="chips">
                <Chip
                  label="3ヶ月以内"
                  onClick={() => {
                    const to = new Date().toISOString().slice(0, 10);
                    const from = new Date();
                    from.setMonth(from.getMonth() - 3);
                    updatePartial({ from: from.toISOString().slice(0, 10), to });
                  }}
                  variant="preset"
                />
                <Chip
                  label="今年"
                  onClick={() => updatePartial({ from: `${new Date().getFullYear()}-01-01`, to: undefined })}
                  variant="preset"
                />
                <Chip label="カレンダー" onClick={() => setCalendarOpen(true)} variant="action" />
              </div>
            </section>
          </div>
        )}
      </ConditionPanel>
    </section>
  );
}
