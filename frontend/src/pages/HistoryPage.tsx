import { useEffect, useMemo, useState } from 'react';
import { getHistoryVideoIds, clearHistory, removeHistoryVideoId } from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { VideoCard } from '@/components/VideoCard';

export function HistoryPage() {
  const { loading, release } = usePublicData();
  const [history, setHistory] = useState<string[]>(() => getHistoryVideoIds());

  useEffect(() => {
    setHistory(getHistoryVideoIds());
  }, [release]);

  const videos = useMemo(
    () =>
      history
        .map((videoId) => {
          const video = release?.videos.find((item) => item.videoId === videoId);
          if (!video) {
            return null;
          }
          return { videoId, video };
        })
        .filter(
          (item): item is { videoId: string; video: NonNullable<typeof release>['videos'][number] } => Boolean(item),
        ),
    [history, release?.videos],
  );

  const clearAll = (): void => {
    clearHistory();
    setHistory([]);
  };

  const removeOne = (videoId: string): void => {
    removeHistoryVideoId(videoId);
    setHistory((prev) => prev.filter((id) => id !== videoId));
  };

  if (loading) {
    return <p className="status">履歴を読込んでいます…</p>;
  }

  return (
    <section>
      <h1>history</h1>
      <button type="button" onClick={clearAll}>
        全削除
      </button>
      <div className="video-list">
        {videos.length === 0 ? <p className="muted">履歴はありません</p> : null}
        {videos.map(({ video }) => (
          <article key={video.videoId} className="video-card-wrap">
            <VideoCard
              videoId={video.videoId}
              title={video.title}
              publishedAt={video.publishedAt}
              duration={video.duration}
              thumbnail={video.thumbnail.url}
              tagNames={[]}
              flags={video.artifactFlags}
              chatCount={video.chat?.totalCount}
            />
            <button type="button" onClick={() => removeOne(video.videoId)}>
              削除
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
