import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHistoryVideoIds, clearHistory, removeHistoryVideoId } from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingState } from '@/components/ui/LoadingState';
import { VideoListItem } from '@/components/ui/VideoListItem';

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
    return (
      <section className="dio-library-page">
        <h1>閲覧履歴</h1>
        <LoadingState label="閲覧履歴を読み込んでいます…" />
      </section>
    );
  }

  return (
    <section className="dio-library-page">
      <header className="dio-page-header">
        <div>
          <h1>閲覧履歴</h1>
          <p>これまでに開いた動画です。</p>
        </div>
        {videos.length ? <Button type="button" variant="text" onClick={clearAll}>すべて削除</Button> : null}
      </header>
      {videos.length === 0 ? (
        <EmptyState title="閲覧履歴はありません">
          <p>検索結果から動画を開くと、ここに表示されます。</p>
          <Link to="/search">検索を開く</Link>
        </EmptyState>
      ) : (
        <div className="video-list">
          {videos.map(({ video }) => (
            <article key={video.videoId} className="dio-library-item">
              <VideoListItem chatCount={video.chat?.totalCount} tagNames={[]} video={video} />
              <Button type="button" variant="text" onClick={() => removeOne(video.videoId)}>履歴から削除</Button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
