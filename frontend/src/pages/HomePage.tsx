import { FormEvent, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { DataErrorState } from '@/components/DataErrorState';
import { Chip } from '@/components/ui/Chip';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingState } from '@/components/ui/LoadingState';
import { SearchBar } from '@/components/ui/SearchBar';
import { VideoGridCard } from '@/components/ui/VideoGridCard';
import { VideoListItem } from '@/components/ui/VideoListItem';
import { buildSearchParams } from '@/lib/search';
import { hasActiveConsentVersion } from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { SearchCondition, VideoIndex } from '@/types';

const emptyCondition: SearchCondition = {
  q: '',
  tags: [],
  artifacts: [],
  sort: 'newest',
};

export function HomePage() {
  const navigate = useNavigate();
  const { loading, release, tagIndex, error, errorKind, refresh, latest } = usePublicData();
  const [query, setQuery] = useState('');
  const featureEnabled = latest?.releaseMode === 'normal' && hasActiveConsentVersion('1');
  const videos = release?.videos ?? [];
  const latestVideos = useMemo(
    () => [...videos].sort((left, right) => right.publishedAt.localeCompare(left.publishedAt)),
    [videos],
  );
  const quickTags = featureEnabled ? tagIndex?.tags.slice(0, 8) ?? [] : [];

  function search(condition: SearchCondition): void {
    const params = buildSearchParams(condition);
    navigate(`/search${params ? `?${params}` : ''}`);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    search({ ...emptyCondition, q: query.trim() });
  }

  function tagNames(video: VideoIndex): string[] {
    if (!featureEnabled) {
      return [];
    }

    return (tagIndex?.tags ?? [])
      .filter((tag) => video.tagIds?.includes(tag.tagId))
      .map((tag) => tag.displayName);
  }

  if (loading) {
    return (
      <section className="dio-home-page">
        <h1>diopside</h1>
        <SearchBar onQueryChange={setQuery} onSubmit={onSubmit} query={query} />
        <LoadingState label="データを読み込んでいます…" />
      </section>
    );
  }

  if (error && errorKind) {
    return <DataErrorState detail={error} kind={errorKind} retry={() => void refresh()} />;
  }

  return (
    <section className="dio-home-page">
      <header>
        <h1>diopside</h1>
        <p>白雪巴の公開配信を素早く見つける検索型ビューア</p>
      </header>
      <SearchBar onQueryChange={setQuery} onSubmit={onSubmit} query={query} />
      <section className="section" aria-labelledby="quick-tags-title">
        <h2 id="quick-tags-title">クイックタグ</h2>
        <div className="chips">
          {quickTags.map((tag) => (
            <Chip
              key={tag.tagId}
              label={tag.displayName}
              onClick={() => search({ ...emptyCondition, tags: [tag.tagId] })}
            />
          ))}
          {!quickTags.length ? <p className="muted">現在のクイックタグはありません。</p> : null}
        </div>
      </section>
      <section className="section" aria-labelledby="latest-videos-title">
        <h2 id="latest-videos-title">最新の動画</h2>
        {latestVideos.length === 0 ? (
          <EmptyState title="公開中の動画はありません">
            <p>キーワードや条件から、公開データを検索できます。</p>
            <Link to="/search">検索を開く</Link>
          </EmptyState>
        ) : null}
        <div className="dio-home-page__videos">
          {latestVideos.map((video) => (
            <VideoGridCard chatCount={video.chat?.totalCount} key={video.videoId} tagNames={tagNames(video)} video={video} />
          ))}
        </div>
        <div className="dio-home-page__mobile-videos">
          {latestVideos.map((video) => (
            <VideoListItem
              chatCount={video.chat?.totalCount}
              key={video.videoId}
              tagNames={tagNames(video)}
              video={video}
            />
          ))}
        </div>
      </section>
    </section>
  );
}
