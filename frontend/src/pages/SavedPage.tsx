import { useMemo, useState } from 'react';
import { usePublicData } from '@/state/PublicDataContext';
import { addSavedVideoId, clearSaved, getSavedVideoIds, removeSavedVideoId } from '@/lib/storage';
import { VideoCard } from '@/components/VideoCard';

export function SavedPage() {
  const { loading, release, refresh, error } = usePublicData();
  const [saved, setSaved] = useState<string[]>(() => getSavedVideoIds());

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
  };

  const removeOne = (videoId: string): void => {
    removeSavedVideoId(videoId);
    setSaved((prev) => prev.filter((id) => id !== videoId));
  };

  const addFirst = (): void => {
    if (!release?.videos.length) {
      return;
    }
    const videoId = release.videos[0].videoId;
    addSavedVideoId(videoId);
    setSaved((prev) => Array.from(new Set([videoId, ...prev])));
  };

  if (loading) {
    return <p className="status">読込中…</p>;
  }

  if (error) {
    return (
      <section className="status-card">
        <p>公開データの取得に失敗しました: {error}</p>
        <button onClick={() => void refresh()}>再取得</button>
      </section>
    );
  }

    return (
      <section>
        <h1>saved</h1>
        <button type="button" onClick={clearAll}>
          全削除
        </button>
        <div className="video-list">
          {videos.length === 0 ? <p className="muted">保存した動画はありません</p> : null}
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
        <button
          type="button"
          onClick={addFirst}
        >
          動作確認: 先頭を保存
        </button>
      </section>
  );
}
