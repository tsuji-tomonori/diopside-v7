import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { usePublicData } from '@/state/PublicDataContext';
import { clearSaved, getSavedVideoIds, removeSavedVideoId } from '@/lib/storage';
import { VideoCard } from '@/components/VideoCard';
import { DataErrorState } from '@/components/DataErrorState';

export function SavedPage() {
  const { loading, release, refresh, error, errorKind } = usePublicData();
  const [saved, setSaved] = useState<string[]>(() => getSavedVideoIds());
  const [notice, setNotice] = useState<string | null>(null);

  const videos = useMemo(
    () =>
      saved
        .map((videoId) => {
          const video = release?.videos.find((item) => item.videoId === videoId);
          return video ? { videoId, video } : null;
        })
        .filter((item): item is { videoId: string; video: NonNullable<typeof release>['videos'][number] } => Boolean(item)),
    [saved, release?.videos],
  );

  const clearAll = (): void => {
    clearSaved();
    setSaved([]);
    setNotice('保存した動画をすべて削除しました。');
  };

  const removeOne = (videoId: string): void => {
    removeSavedVideoId(videoId);
    setSaved((prev) => prev.filter((id) => id !== videoId));
    setNotice('保存を1件解除しました。');
  };

  if (loading) {
    return <p className="status">読込中…</p>;
  }

  if (error && errorKind) {
    return <DataErrorState kind={errorKind} detail={error} retry={() => void refresh()} />;
  }

  return (
      <section className="page library-page">
        <header className="page-header">
          <p className="eyebrow">SAVED ARCHIVES</p>
          <h1>あとで見る</h1>
          <p className="page-lead">気になった配信を、この端末だけに保存しています。</p>
        </header>
        <div className="library-toolbar">
          <p>{videos.length}本を保存中</p>
          {videos.length ? <button className="text-button danger-text" type="button" onClick={clearAll}>すべて削除</button> : null}
        </div>
        {notice ? <p className="notice" role="status">{notice}</p> : null}
        <div className="video-list">
          {videos.length === 0 ? (
            <div className="empty-state">
              <span className="empty-mark" aria-hidden="true">◇</span>
              <h2>保存した動画はまだありません</h2>
              <p>動画詳細の「あとで見る」から、この端末に保存できます。</p>
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
                保存を解除
              </button>
            </article>
          ))}
        </div>
      </section>
  );
}
