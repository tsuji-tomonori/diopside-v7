import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { DataErrorState } from '@/components/DataErrorState';
import { Button } from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/LoadingState';
import { VideoGridCard } from '@/components/ui/VideoGridCard';
import { ContractError, ContractErrorKind, loadVideoDetail } from '@/lib/contract';
import { formatCount, formatDateTime, formatDuration, formatPublishedAt, formatTimestamp } from '@/lib/format';
import { POLICY_LINKS, POLICY_MAJOR_VERSION } from '@/lib/policy';
import {
  addHistoryVideoId,
  addSavedVideoId,
  clearConsent,
  getConsentMajorVersion,
  getSavedVideoIds,
  hasActiveConsentVersion,
  removeSavedVideoId,
  setConsentVersion,
} from '@/lib/storage';
import { usePublicData } from '@/state/PublicDataContext';
import { TagInfo, VideoDetail, VideoIndex } from '@/types';

const artifactLabels = {
  chat: 'チャット',
  comments: 'コメント',
  timestamps: 'タイムスタンプ',
  wordcloud: 'ワードクラウド',
} as const;

const confidenceLabels = {
  high: '高',
  medium: '中',
  low: '低',
} as const;

function formatSource(source: string): string {
  const labels: Record<string, string> = {
    live_chat_messages: 'ライブチャット',
    timestamp_learner_v1: '自動抽出',
    get_archives_info_v1: 'アーカイブ情報生成',
  };

  return labels[source] ?? '派生データ';
}

export function DetailPage() {
  const { id = '' } = useParams();
  const { loading, release, refresh, error, errorKind, tagIndex, latest } = usePublicData();
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<{ kind: ContractErrorKind; message: string } | null>(null);
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
    setDetailError(null);
    void loadVideoDetail(latest.releaseId, id)
      .then((nextDetail) => {
        setDetail(nextDetail);
        if (id) {
          addHistoryVideoId(id);
        }
      })
      .catch((caught: unknown) => {
        setDetail(null);
        setDetailError({
          kind: caught instanceof ContractError ? caught.kind : 'network',
          message: caught instanceof Error ? caught.message : 'video detail load failed',
        });
      })
      .finally(() => {
        setDetailLoading(false);
      });
  }, [id, latest?.releaseId]);

  const artifact = useMemo(() => ({
    chat: detail?.chat,
    comments: detail?.comments,
    timestamps: detail?.timestamps,
    wordcloud: detail?.wordcloud,
  }), [detail]);

  const artifactNotice = useMemo(() => {
    const entries: { label: keyof typeof artifactLabels; value: { source: string; generatedAt: string } }[] = [];
    if (artifact.chat) entries.push({ label: 'chat', value: artifact.chat });
    if (artifact.comments) entries.push({ label: 'comments', value: artifact.comments });
    if (artifact.timestamps) entries.push({ label: 'timestamps', value: artifact.timestamps });
    if (artifact.wordcloud) entries.push({ label: 'wordcloud', value: artifact.wordcloud });
    return entries;
  }, [artifact]);

  const video = release?.videos.find((item) => item.videoId === id) ?? null;
  const tags = tagIndex?.tags
    .filter((tag: TagInfo) => video?.tagIds?.includes(tag.tagId))
    .map((tag: TagInfo) => tag.displayName) ?? [];
  const canShowDerived = latest?.releaseMode === 'normal';
  const wordcloudImage = artifact.wordcloud?.svgPath
    ? `/data/${artifact.wordcloud.svgPath.replace(/^\/?(data\/)?/, '')}`
    : null;
  const relatedVideos = useMemo(() => {
    if (!video || !hasConsent || !canShowDerived) {
      return [];
    }

    return (release?.videos ?? [])
      .filter((candidate) => candidate.videoId !== video.videoId)
      .filter((candidate) => candidate.tagIds?.some((tagId) => video.tagIds?.includes(tagId)))
      .slice(0, 4);
  }, [canShowDerived, hasConsent, release?.videos, video]);

  function tagNames(candidate: VideoIndex): string[] {
    return (tagIndex?.tags ?? [])
      .filter((tag) => candidate.tagIds?.includes(tag.tagId))
      .map((tag) => tag.displayName);
  }

  function acceptConsent(): void {
    setConsentVersion(POLICY_MAJOR_VERSION);
    setConsentVersionState(POLICY_MAJOR_VERSION);
    setNotice('同意を反映しました。');
  }

  function withdrawConsent(): void {
    clearConsent();
    setConsentVersionState(null);
    setNotice('同意を取り下げました。');
  }

  function toggleSaved(): void {
    if (!video) {
      return;
    }

    if (isSaved) {
      removeSavedVideoId(video.videoId);
      setIsSaved(false);
      setNotice('保存を解除しました。');
      return;
    }

    addSavedVideoId(video.videoId);
    setIsSaved(true);
    setNotice('保存しました。');
  }

  if (loading || detailLoading) {
    return (
      <section className="dio-detail-page">
        <h1>動画詳細</h1>
        <LoadingState label="動画詳細を読み込んでいます…" />
      </section>
    );
  }

  if (error && errorKind) {
    return (
      <section className="dio-detail-page">
        <h1>動画詳細</h1>
        <DataErrorState detail={error} kind={errorKind} retry={() => void refresh()} />
      </section>
    );
  }

  if (detailError) {
    return (
      <section className="dio-detail-page">
        <h1>動画詳細</h1>
        <DataErrorState
          detail={detailError.message}
          kind={detailError.kind}
          retry={() => window.location.reload()}
        />
      </section>
    );
  }

  if (!release) {
    return (
      <section className="dio-detail-page">
        <h1>動画詳細</h1>
        <p className="status">公開データがありません</p>
      </section>
    );
  }

  if (!video) {
    return (
      <section className="dio-detail-page">
        <h1>動画詳細</h1>
        <p className="status">対象動画が見つかりません</p>
      </section>
    );
  }

  return (
    <section className="dio-detail-page">
      {!hasConsent ? (
        <>
          <h1>動画詳細</h1>
          <section className="policy-card" aria-labelledby="consent-title">
            <h2 id="consent-title">利用前の確認</h2>
            <p>YouTube/API由来の情報・派生表示は同意後に有効です。</p>
            <ul className="dio-policy-links" aria-label="確認する規約と方針">
              <li><a href={POLICY_LINKS.youtubeTerms} target="_blank" rel="noreferrer">YouTube Terms</a></li>
              <li><a href={POLICY_LINKS.youtubePrivacy} target="_blank" rel="noreferrer">Google Privacy Policy</a></li>
              <li><a href={POLICY_LINKS.diopsideTerms} target="_blank" rel="noreferrer">diopside利用規約</a></li>
              <li><a href={POLICY_LINKS.diopsidePrivacy} target="_blank" rel="noreferrer">diopsideプライバシーポリシー</a></li>
              <li><a href={POLICY_LINKS.youtubeDerived} target="_blank" rel="noreferrer">YouTubeの派生指標に関する方針</a></li>
            </ul>
            <p>同意後、YouTube導線・派生データを確認できます。</p>
            <div className="dio-page-actions">
              <Button type="button" variant="primary" onClick={acceptConsent}>同意して進む</Button>
            </div>
            <p className="dio-policy-channel"><a href="https://www.youtube.com/channel/UCdummy" target="_blank" rel="noreferrer">運営者チャンネル（固定）</a></p>
            {notice ? <p role="status">{notice}</p> : null}
          </section>
        </>
      ) : (
        <>
          <img alt="" className="detail-thumb" src={video.thumbnail.url} />
          <h1>{video.title}</h1>
          <p className="dio-caption dio-num">
            {formatPublishedAt(video.publishedAt)} · {formatDuration(video.durationSec)}
            {typeof video.chat?.totalCount === 'number' ? ` · チャット ${formatCount(video.chat.totalCount)}` : ''}
          </p>
          {tags.length ? (
            <div className="chips" aria-label="動画のタグ">
              {tags.map((name) => <span key={name} className="chip">{name}</span>)}
            </div>
          ) : null}
          <p>
            <a
              className="yt-button dio-button--primary"
              href={`https://www.youtube.com/watch?v=${video.videoId}`}
              target="_blank"
              rel="noreferrer"
            >
              YouTubeで見る
            </a>
          </p>
          <div className="dio-page-actions">
            <Button type="button" onClick={toggleSaved}>{isSaved ? '保存を外す' : '保存する'}</Button>
            <Button type="button" variant="text" onClick={withdrawConsent}>同意を取り下げる</Button>
          </div>
          <p className="dio-caption">受理バージョン: {consentVersion ?? POLICY_MAJOR_VERSION}</p>
          {notice ? <p role="status">{notice}</p> : null}
          {canShowDerived ? (
            <section className="section" aria-labelledby="derived-title">
              <h2 id="derived-title">派生情報</h2>
              <p className="dio-caption">データ更新日: {formatDateTime(video.sourceUpdatedAt)}</p>
              {video.coverage ? <p className="dio-caption">対象期間: {formatDateTime(video.coverage.coverageStart)} 〜 {formatDateTime(video.coverage.coverageEnd)}</p> : null}
              {artifactNotice.length ? (
                <div className="dio-artifact-list">
                  {artifactNotice.map((item) => (
                    <section key={item.label}>
                      <h3>{artifactLabels[item.label]}</h3>
                      <p className="dio-caption">{formatSource(item.value.source)}から作成 · 作成日: {formatDateTime(item.value.generatedAt)}</p>
                      <p className="dio-caption dio-source-id">識別子: {item.value.source}</p>
                    </section>
                  ))}
                </div>
              ) : <p>派生データは未作成です</p>}
              <section>
                <h3>チャット</h3>
                {artifact.chat ? <p>{formatCount(artifact.chat.totalCount)}件</p> : <p>未作成</p>}
              </section>
              <section>
                <h3>コメント</h3>
                {artifact.comments ? <p>{formatCount(artifact.comments.totalCount)}件</p> : <p>未作成</p>}
              </section>
              {artifact.timestamps?.items?.length ? (
                <section>
                  <h3>タイムスタンプ</h3>
                  <ul>
                    {artifact.timestamps.items.map((item, index) => (
                      <li key={`${item.atSec}-${index}`}>
                        <a href={`https://www.youtube.com/watch?v=${video.videoId}&t=${Math.max(item.atSec, 0)}s`} target="_blank" rel="noreferrer">
                          {formatTimestamp(item.atSec)} · {item.label}
                        </a>
                        {item.confidenceLevel ? <span className="dio-caption">（信頼度: {confidenceLabels[item.confidenceLevel]}）</span> : null}
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}
              <section>
                <h3>ワードクラウド</h3>
                {artifact.wordcloud && wordcloudImage ? <img alt="wordcloud" className="detail-wordcloud" src={wordcloudImage} /> : <p>未作成</p>}
              </section>
            </section>
          ) : <p className="status">このリリースは派生公開対象外です。</p>}
          {relatedVideos.length ? (
            <section className="section" aria-labelledby="related-videos-title">
              <h2 id="related-videos-title">関連動画</h2>
              <div className="dio-related-videos">
                {relatedVideos.map((candidate) => (
                  <VideoGridCard chatCount={candidate.chat?.totalCount} key={candidate.videoId} tagNames={tagNames(candidate)} video={candidate} />
                ))}
              </div>
            </section>
          ) : null}
        </>
      )}
    </section>
  );
}
