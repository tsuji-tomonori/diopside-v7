import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHistoryVideoIds, clearHistory, removeHistoryVideoId } from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { VideoCard } from '@/components/VideoCard';

export function HistoryPage() {
  const { loading, release } = usePublicData();
  const [history, setHistory] = useState<string[]>(() => getHistoryVideoIds());
  const [notice, setNotice] = useState<string | null>(null);

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
    setNotice('閲覧履歴をすべて削除しました。');
  };

  const removeOne = (videoId: string): void => {
    removeHistoryVideoId(videoId);
    setHistory((prev) => prev.filter((id) => id !== videoId));
    setNotice('閲覧履歴を1件削除しました。');
  };

  if (loading) {
    return <p className="status">履歴を読込んでいます…</p>;
  }

  return (
    <section className="page library-page">
      <header className="page-header">
        <p className="eyebrow">VIEW HISTORY</p>
        <h1>閲覧履歴</h1>
        <p className="page-lead">最近開いたアーカイブへ、すぐに戻れます。</p>
      </header>
      <div className="library-toolbar">
        <p>{videos.length}本の履歴</p>
        {videos.length ? <button className="text-button danger-text" type="button" onClick={clearAll}>すべて削除</button> : null}
      </div>
      {notice ? <p className="notice" role="status">{notice}</p> : null}
      <div className="video-list">
        {videos.length === 0 ? (
          <div className="empty-state">
            <span className="empty-mark" aria-hidden="true">○</span>
            <h2>閲覧履歴はまだありません</h2>
            <p>動画詳細を開くと、この端末の履歴に追加されます。</p>
            <Link className="button button-primary" to="/search">アーカイブを探す</Link>
          </div>
        ) : null}
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
            <button className="button button-quiet remove-row-action" type="button" onClick={() => removeOne(video.videoId)}>
              履歴から削除
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
