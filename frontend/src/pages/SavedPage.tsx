import { Link } from 'react-router-dom';
import { useMemo, useState } from 'react';
import { usePublicData } from '@/state/PublicDataContext';
import { clearSaved, getSavedVideoIds, hasActiveConsentVersion, removeSavedVideoId } from '@/lib/storage';
import { DataErrorState } from '@/components/DataErrorState';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingState } from '@/components/ui/LoadingState';
import { VideoListItem } from '@/components/ui/VideoListItem';
import { VideoIndex } from '@/types';

export function SavedPage() {
  const { loading, release, refresh, error, errorKind, latest, tagIndex } = usePublicData();
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

  const canShowTags = latest?.releaseMode === 'normal' && hasActiveConsentVersion('1');

  function tagNames(video: VideoIndex): string[] {
    if (!canShowTags) {
      return [];
    }

    return (tagIndex?.tags ?? [])
      .filter((tag) => video.tagIds?.includes(tag.tagId))
      .map((tag) => tag.displayName);
  }

  if (loading) {
    return (
      <section className="dio-library-page">
        <h1>保存した動画</h1>
        <LoadingState label="保存した動画を読み込んでいます…" />
      </section>
    );
  }

  if (error && errorKind) {
    return (
      <section className="dio-library-page">
        <h1>保存した動画</h1>
        <DataErrorState detail={error} kind={errorKind} retry={() => void refresh()} />
      </section>
    );
  }

  return (
    <section className="dio-library-page">
      <header className="dio-page-header">
        <div>
          <h1>保存した動画</h1>
          <p>あとで見返したい動画です。</p>
        </div>
        {videos.length ? <Button type="button" variant="text" onClick={clearAll}>すべて削除</Button> : null}
      </header>
      {videos.length === 0 ? (
        <EmptyState title="保存した動画はありません">
          <p>動画詳細の保存操作から追加できます。</p>
          <Link to="/search">検索を開く</Link>
        </EmptyState>
      ) : (
        <div className="video-list">
          {videos.map(({ video }) => (
            <article key={video.videoId} className="dio-library-item">
              <VideoListItem
                chatCount={video.chat?.totalCount}
                tagNames={tagNames(video)}
                video={video}
              />
              <Button type="button" variant="text" onClick={() => removeOne(video.videoId)}>保存を外す</Button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
