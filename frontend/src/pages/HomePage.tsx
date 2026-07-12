import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePublicData } from '@/state/PublicDataContext';
import { VideoCard } from '@/components/VideoCard';
import { DataErrorState } from '@/components/DataErrorState';
import { TagInfo } from '@/types';

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

  if (loading) {
    return <p className="status">データを読込んでいます…</p>;
  }

  if (error && errorKind) {
    return <DataErrorState kind={errorKind} detail={error} retry={() => void refresh()} />;
  }

  return (
    <section>
      <header>
        <h1>diopside</h1>
        <p>白雪巴の公開配信を素早く見つける検索型ビューア</p>
      </header>

      <section className="section">
        <h2>quick tags</h2>
        <div className="chips">
          {(tagIndex?.tags ?? []).slice(0, 3).map((tag: TagInfo) => (
            <Link key={tag.tagId} className="chip" to={`/search?tag=${tag.tagId}`}>
              {tag.displayName}
            </Link>
          ))}
          {(!tagIndex || tagIndex.tags.length === 0) ? <span className="muted">現在のクイックタグはありません</span> : null}
        </div>
      </section>

      <section className="section">
        <h2>newest archives</h2>
        <div className="video-list">
          {newest.map((video) => {
            const names = featureEnabled
              ? (tagIndex?.tags ?? [])
                  .filter((tag: TagInfo) => (video.tagIds ?? []).includes(tag.tagId))
                  .map((tag: TagInfo) => tag.displayName)
              : [];
            return (
              <VideoCard
                key={video.videoId}
                videoId={video.videoId}
                title={video.title}
                publishedAt={video.publishedAt}
                duration={video.duration}
                thumbnail={video.thumbnail.url}
                flags={video.artifactFlags}
                tagNames={names}
                chatCount={video.chat?.totalCount}
              />
            );
          })}
        </div>
      </section>

      <section className="section">
        <h2>random discovery</h2>
        <div className="video-list">
          {random.map((video) => {
            const names = featureEnabled
              ? (tagIndex?.tags ?? [])
                  .filter((tag: TagInfo) => (video.tagIds ?? []).includes(tag.tagId))
                  .map((tag: TagInfo) => tag.displayName)
              : [];
            return (
              <VideoCard
                key={video.videoId}
                videoId={video.videoId}
                title={video.title}
                publishedAt={video.publishedAt}
                duration={video.duration}
                thumbnail={video.thumbnail.url}
                flags={video.artifactFlags}
                tagNames={names}
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
