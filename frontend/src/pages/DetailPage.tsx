import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { usePublicData } from '@/state/PublicDataContext';
import {
  clearConsent,
  getConsentMajorVersion,
  hasActiveConsentVersion,
  setConsentVersion,
} from '@/lib/storage';
import { POLICY_LINKS, POLICY_MAJOR_VERSION } from '@/lib/policy';
import { loadVideoDetail } from '@/lib/contract';
import {
  addHistoryVideoId,
  addSavedVideoId,
  getSavedVideoIds,
  removeSavedVideoId,
} from '@/lib/storage';
import { TagInfo, VideoDetail } from '@/types';

export function DetailPage() {
  const { id = '' } = useParams();
  const { loading, release, refresh, error, tagIndex, latest } = usePublicData();
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [consentVersion, setConsentVersionState] = useState(() => getConsentMajorVersion());

  const hasConsent = hasActiveConsentVersion(POLICY_MAJOR_VERSION);

  useEffect(() => {
    setIsSaved(getSavedVideoIds().includes(id));
    setConsentVersionState(getConsentMajorVersion());
  }, [id]);

  useEffect(() => {
    if (!latest) {
      return;
    }
    setDetailLoading(true);
    void loadVideoDetail(latest.releaseId, id)
      .then((nextDetail) => {
        setDetail(nextDetail);
      })
      .catch(() => {
        setDetail(null);
      })
      .finally(() => {
        setDetailLoading(false);
      });

    if (id) {
      addHistoryVideoId(id);
    }
  }, [id, latest?.releaseId]);

  if (loading || detailLoading) {
    return <p className="status">読み込み中…</p>;
  }

  if (error) {
    return (
      <section className="status-card">
        <p>データ取得エラー: {error}</p>
        <button type="button" onClick={() => void refresh()}>
          再取得
        </button>
      </section>
    );
  }

  if (!release) {
    return <p className="status">公開データがありません</p>;
  }

  const video = release.videos.find((item) => item.videoId === id);
  if (!video) {
    return <p className="status">対象動画が見つかりません</p>;
  }

  const tags =
    tagIndex?.tags
      .filter((tag: TagInfo) => video.tagIds.includes(tag.tagId))
      .map((tag: TagInfo) => tag.displayName) ?? [];

  const canShowDerived = latest?.releaseMode === 'normal';

  const artifact = useMemo(() => {
    return {
      chat: detail?.chat,
      comments: detail?.comments,
      timestamps: detail?.timestamps,
      wordcloud: detail?.wordcloud,
    };
  }, [detail]);

  const wordcloudImage = artifact.wordcloud?.svgPath
    ? `/data/${artifact.wordcloud.svgPath.replace(/^\/?(data\/)?/, '')}`
    : null;

  const artifactNotice = useMemo(() => {
    const entries: { label: string; value: { source: string; generatedAt: string } }[] = [];
    if (artifact.chat) entries.push({ label: 'chat', value: artifact.chat });
    if (artifact.comments) entries.push({ label: 'comments', value: artifact.comments });
    if (artifact.timestamps) entries.push({ label: 'timestamps', value: artifact.timestamps });
    if (artifact.wordcloud) entries.push({ label: 'wordcloud', value: artifact.wordcloud });
    return entries;
  }, [artifact]);

  return (
    <section>
      <h1>video detail</h1>
      <p className="status">{video.publishedAt} · {video.duration}</p>

      {!hasConsent ? (
        <section className="policy-card">
          <p>YouTube/API由来の情報・派生表示は同意後に有効です。</p>
          <div className="chips">
            <a href={POLICY_LINKS.youtubeTerms} target="_blank" rel="noreferrer">
              YouTube Terms
            </a>
            <a href={POLICY_LINKS.youtubePrivacy} target="_blank" rel="noreferrer">
              Google Privacy Policy
            </a>
            <a href={POLICY_LINKS.diopsideTerms} target="_blank" rel="noreferrer">
              diopside利用規約
            </a>
            <a href={POLICY_LINKS.diopsidePrivacy} target="_blank" rel="noreferrer">
              diopsideプライバシーポリシー
            </a>
            <a href={POLICY_LINKS.youtubeDerived} target="_blank" rel="noreferrer">
              YouTube Derived Metrics
            </a>
          </div>
          <p>
            同意後、YouTube導線・派生データを確認できます。
          </p>
          <button
            type="button"
            onClick={() => {
              setConsentVersion(POLICY_MAJOR_VERSION);
              setConsentVersionState(POLICY_MAJOR_VERSION);
              setNotice('同意を反映しました。');
            }}
          >
            同意して進む
          </button>
          <button
            type="button"
            onClick={() => {
              clearConsent();
              setConsentVersionState(null);
              setNotice('同意を取り下げました。');
            }}
          >
            同意を取り下げる
          </button>
          <a href="https://www.youtube.com/channel/UCdummy" target="_blank" rel="noreferrer">
            運営者チャンネル（固定）
          </a>
          {notice ? <p role="status">{notice}</p> : null}
        </section>
      ) : (
        <>
          <p>
            受理バージョン: {consentVersion ?? POLICY_MAJOR_VERSION}
          </p>
          <img src={video.thumbnail.url} alt="thumbnail" className="detail-thumb" />
          <h2>{video.title}</h2>
          <p className="chips">
            {tags.map((name) => (
              <span key={name} className="chip">
                {name}
              </span>
            ))}
          </p>
          <p>
            <a className="yt-button" href={`https://www.youtube.com/watch?v=${video.videoId}`} target="_blank" rel="noreferrer">
              YouTubeで見る
            </a>
          </p>

          <p>
            <button
              type="button"
              onClick={() => {
                if (isSaved) {
                  removeSavedVideoId(video.videoId);
                  setIsSaved(false);
                  setNotice('保存を解除しました。');
                } else {
                  addSavedVideoId(video.videoId);
                  setIsSaved(true);
                  setNotice('保存しました。');
                }
              }}
            >
              {isSaved ? '保存を外す' : '保存する'}
            </button>
          </p>
        </>
      )}

      {(notice && hasConsent) ? <p role="status">{notice}</p> : null}

      {hasConsent && canShowDerived ? (
        <section>
          <h3>metadata</h3>
          <p>sourceUpdatedAt: {video.sourceUpdatedAt}</p>
          {video.coverage ? (
            <p>
              coverage: {video.coverage.coverageStart} - {video.coverage.coverageEnd}
            </p>
          ) : null}

          <h3>derived artifacts</h3>
          {artifactNotice.length ? (
            artifactNotice.map((artifactItem) => (
              <section key={artifactItem.label}>
                <h4>{artifactItem.label}</h4>
                <p>
                  source: {artifactItem.value.source} / generatedAt: {artifactItem.value.generatedAt}
                </p>
              </section>
            ))
          ) : (
            <p>派生データは未作成です</p>
          )}

          <h3>chat</h3>
          {artifact.chat ? <p>{artifact.chat.totalCount}件 / source: {artifact.chat.source}</p> : <p>未作成</p>}

          <h3>comments</h3>
          {artifact.comments ? <p>{artifact.comments.totalCount}件 / source: {artifact.comments.source}</p> : <p>未作成</p>}

          <h3>timestamps</h3>
          {artifact.timestamps?.items?.length ? (
            <ul>
              {artifact.timestamps.items.map((item, index) => (
                <li key={`${item.atSec}-${index}`}>
                  <a href={`https://www.youtube.com/watch?v=${video.videoId}&t=${Math.max(item.atSec, 0)}s`} target="_blank" rel="noreferrer">
                    {item.atSec}s · {item.label}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p>未作成</p>
          )}

          <h3>wordcloud</h3>
          {artifact.wordcloud ? <img src={wordcloudImage ?? ''} alt="wordcloud" className="detail-wordcloud" /> : <p>未作成</p>}
        </section>
      ) : null}

      {hasConsent && !canShowDerived ? <p>このリリースは派生公開対象外です。</p> : null}
    </section>
  );
}
