import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePublicData } from '@/state/PublicDataContext';
import { VideoCard } from '@/components/VideoCard';
import { DataErrorState } from '@/components/DataErrorState';
import { TagInfo } from '@/types';
import { NavIcon } from '@/components/NavIcon';

export function HomePage() {
  const { loading, release, tagIndex, error, errorKind, refresh, latest } = usePublicData();

  const videos = release?.videos ?? [];
  const featureEnabled = latest?.releaseMode === 'normal';

  const newest = useMemo(
    () => [...videos].sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()),
    [videos],
  );

  const random = useMemo(() => {
    if (!videos.length) {
      return [];
    }
    const pool = [...videos];
    for (let index = pool.length - 1; index > 0; index -= 1) {
      const selected = Math.floor(Math.random() * (index + 1));
      [pool[index], pool[selected]] = [pool[selected], pool[index]];
    }
    return pool.slice(0, 2);
  }, [videos]);

  const getTagNames = (tagIds: string[] | undefined): string[] => {
    if (!featureEnabled) {
      return [];
    }
    return (tagIndex?.tags ?? [])
      .filter((tag: TagInfo) => (tagIds ?? []).includes(tag.tagId))
      .map((tag: TagInfo) => tag.displayName);
  };

  if (loading) {
    return <p className="status">データを読込んでいます…</p>;
  }

  if (error && errorKind) {
    return <DataErrorState kind={errorKind} detail={error} retry={() => void refresh()} />;
  }

  return (
    <section className="page home-page">
      <header className="page-header home-intro">
        <p className="eyebrow">SHIRAYUKI TOMOE ARCHIVE</p>
        <h1>あの配信を、<br />もう一度見つける。</h1>
        <p className="page-lead">
          白雪巴さんの公開アーカイブを、タグや覚えている言葉から探せます。
        </p>
        <Link className="button button-primary home-search-action" to="/search">
          <NavIcon name="search" />
          アーカイブを検索
        </Link>
      </header>

      <section className="section quick-section" aria-labelledby="quick-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">QUICK SEARCH</p>
            <h2 id="quick-heading">よく探されるテーマ</h2>
          </div>
          <Link className="text-link" to="/search">すべての条件を見る</Link>
        </div>
        <div className="chips quick-tags">
          {(tagIndex?.tags ?? []).slice(0, 3).map((tag: TagInfo) => (
            <Link key={tag.tagId} className="chip chip-action" to={`/search?tag=${tag.tagId}&sort=newest`}>
              {tag.displayName}
              <span aria-hidden="true">→</span>
            </Link>
          ))}
          {(!tagIndex || tagIndex.tags.length === 0) ? <span className="muted">現在のクイックタグはありません</span> : null}
        </div>
      </section>

      <section className="section" aria-labelledby="newest-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">LATEST</p>
            <h2 id="newest-heading">新着アーカイブ</h2>
          </div>
          <span className="section-count">{newest.length}本</span>
        </div>
        <div className="video-list">
          {newest.map((video) => {
            return (
              <VideoCard
                key={video.videoId}
                videoId={video.videoId}
                title={video.title}
                publishedAt={video.publishedAt}
                duration={video.duration}
                thumbnail={video.thumbnail.url}
                flags={video.artifactFlags}
                tagNames={getTagNames(video.tagIds)}
                chatCount={video.chat?.totalCount}
              />
            );
          })}
        </div>
      </section>

      <section className="section discovery-section" aria-labelledby="discovery-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">DISCOVERY</p>
            <h2 id="discovery-heading">偶然の一枠</h2>
          </div>
          <NavIcon name="shuffle" />
        </div>
        <p className="section-description">いつもの探し方から少し離れて、過去の配信に出会えます。</p>
        <div className="video-list">
          {random.map((video) => {
            return (
              <VideoCard
                key={video.videoId}
                videoId={video.videoId}
                title={video.title}
                publishedAt={video.publishedAt}
                duration={video.duration}
                thumbnail={video.thumbnail.url}
                flags={video.artifactFlags}
                tagNames={getTagNames(video.tagIds)}
                chatCount={video.chat?.totalCount}
              />
            );
          })}
          {!random.length ? <p className="muted">候補がありません</p> : null}
        </div>
      </section>
    </section>
  );
}
