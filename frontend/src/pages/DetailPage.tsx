import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { usePublicData } from '@/state/PublicDataContext';
import {
  clearConsent,
  getConsentMajorVersion,
  hasActiveConsentVersion,
  setConsentVersion,
} from '@/lib/storage';
import { POLICY_LINKS, POLICY_MAJOR_VERSION } from '@/lib/policy';
import { ContractError, ContractErrorKind, loadVideoDetail } from '@/lib/contract';
import { DataErrorState } from '@/components/DataErrorState';
import {
  addHistoryVideoId,
  addSavedVideoId,
  getSavedVideoIds,
  removeSavedVideoId,
} from '@/lib/storage';
import { TagInfo, VideoDetail } from '@/types';
import { NavIcon } from '@/components/NavIcon';
import { formatCount, formatDuration, formatPublishedDate } from '@/lib/format';

const confidenceLabels = {
  high: '高',
  medium: '中',
  low: '低',
} as const;

const artifactSourceLabels: Record<string, string> = {
  get_archives_info_v1: 'アーカイブ情報生成',
  live_chat_messages: 'ライブチャット',
  timestamp_learner_v1: '自動抽出',
};

function formatArtifactSource(source: string): string {
  return artifactSourceLabels[source] ?? source;
}

export function DetailPage() {
  const { id = '' } = useParams();
  const { loading, release, refresh, error, errorKind, tagIndex, latest } = usePublicData();
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<{ kind: ContractErrorKind; message: string } | null>(null);
  const [thumbnailUnavailable, setThumbnailUnavailable] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [consentVersion, setConsentVersionState] = useState(() => getConsentMajorVersion());

  const hasConsent = hasActiveConsentVersion(POLICY_MAJOR_VERSION);

  useEffect(() => {
    setIsSaved(getSavedVideoIds().includes(id));
    setConsentVersionState(getConsentMajorVersion());
    setThumbnailUnavailable(false);
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

  const artifact = useMemo(() => {
    return {
      chat: detail?.chat,
      comments: detail?.comments,
      timestamps: detail?.timestamps,
      wordcloud: detail?.wordcloud,
    };
  }, [detail]);

  const artifactNotice = useMemo(() => {
    const entries: { label: string; value: { source: string; generatedAt: string } }[] = [];
    if (artifact.chat) entries.push({ label: 'chat', value: artifact.chat });
    if (artifact.comments) entries.push({ label: 'comments', value: artifact.comments });
    if (artifact.timestamps?.items.length) {
      entries.push({ label: 'timestamps', value: artifact.timestamps });
    }
    if (artifact.wordcloud) entries.push({ label: 'wordcloud', value: artifact.wordcloud });
    return entries;
  }, [artifact]);

  if (loading || detailLoading) {
    return <p className="status">読み込み中…</p>;
  }

  if (error && errorKind) {
    return <DataErrorState kind={errorKind} detail={error} retry={() => void refresh()} />;
  }

  if (detailError) {
    return <DataErrorState kind={detailError.kind} detail={detailError.message} retry={() => window.location.reload()} />;
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
      .filter((tag: TagInfo) => (video.tagIds ?? []).includes(tag.tagId))
      .map((tag: TagInfo) => tag.displayName) ?? [];

  const canShowDerived = latest?.releaseMode === 'normal';

  const wordcloudImage = artifact.wordcloud?.svgPath
    ? `/data/${artifact.wordcloud.svgPath.replace(/^\/?(data\/)?/, '')}`
    : null;
  const wordcloudTerms = artifact.wordcloud?.topTerms ?? [];
  const largestWordCount = Math.max(...wordcloudTerms.map((term) => term.count), 1);

  return (
    <section className="page detail-page">
      <Link className="back-link" to="/search">← 検索結果へ戻る</Link>

      {!hasConsent ? (
        <section className="policy-card">
          <p className="eyebrow">BEFORE YOU CONTINUE</p>
          <h1>動画情報を表示する前に</h1>
          <p className="page-lead">
            この画面はYouTube API由来の情報を表示します。関連規約とデータの扱いを確認してから進んでください。
          </p>
          <div className="policy-links">
            <a href={POLICY_LINKS.youtubeTerms} target="_blank" rel="noreferrer">
              YouTube 利用規約
            </a>
            <a href={POLICY_LINKS.youtubePrivacy} target="_blank" rel="noreferrer">
              Google プライバシーポリシー
            </a>
            <a href={POLICY_LINKS.diopsideTerms} target="_blank" rel="noreferrer">
              diopside 利用規約
            </a>
            <a href={POLICY_LINKS.diopsidePrivacy} target="_blank" rel="noreferrer">
              diopside プライバシーポリシー
            </a>
            <a href={POLICY_LINKS.youtubeDerived} target="_blank" rel="noreferrer">
              派生指標について
            </a>
          </div>
          <div className="policy-actions">
            <button
              className="button button-primary"
              type="button"
              onClick={() => {
                setConsentVersion(POLICY_MAJOR_VERSION);
                setConsentVersionState(POLICY_MAJOR_VERSION);
                setNotice('同意を反映しました。');
              }}
            >
              内容を確認して進む
            </button>
            <Link className="button button-quiet" to="/">ホームへ戻る</Link>
          </div>
          {notice ? <p role="status">{notice}</p> : null}
        </section>
      ) : (
        <>
          <header className="detail-header">
            <p className="eyebrow">ARCHIVE DETAIL</p>
            <h1>{video.title}</h1>
            <div className="detail-meta">
              <span>{formatPublishedDate(video.publishedAt)}</span>
              <span>{formatDuration(video.duration)}</span>
            </div>
          </header>

          <div className="detail-hero">
            <div className="detail-media">
              {!thumbnailUnavailable ? (
                <img
                  src={video.thumbnail.url}
                  alt=""
                  className="detail-thumb"
                  onError={() => setThumbnailUnavailable(true)}
                />
              ) : null}
              <a className="detail-play" href={`https://www.youtube.com/watch?v=${video.videoId}`} target="_blank" rel="noreferrer">
                <NavIcon name="play" />
                <span>YouTubeで再生</span>
              </a>
            </div>
            <aside className="detail-summary">
              {tags.length ? (
                <div>
                  <p className="summary-label">テーマ</p>
                  <div className="chips">
                    {tags.map((name) => <span key={name} className="chip">{name}</span>)}
                  </div>
                  <p className="source-note">diopside独自の分類です。YouTube公式情報ではありません。</p>
                </div>
              ) : null}
              <div className="detail-actions">
                <a className="button button-primary" href={`https://www.youtube.com/watch?v=${video.videoId}`} target="_blank" rel="noreferrer">
                  <NavIcon name="external" />
                  YouTubeで見る
                </a>
                <button
                  className={isSaved ? 'button button-secondary is-selected' : 'button button-secondary'}
                  type="button"
                  aria-pressed={isSaved}
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
                  <NavIcon name="saved" />
                  {isSaved ? '保存済み' : 'あとで見る'}
                </button>
              </div>
            </aside>
          </div>
        </>
      )}

      {(notice && hasConsent) ? <p className="notice" role="status">{notice}</p> : null}

      {hasConsent && canShowDerived ? (
        <section className="section detail-insights" aria-labelledby="insights-heading">
          <div className="section-heading">
            <div>
              <p className="eyebrow">INSIGHTS</p>
              <h2 id="insights-heading">配信の手がかり</h2>
            </div>
            <span className="detail-version">データ版 {consentVersion ?? POLICY_MAJOR_VERSION}</span>
          </div>
          <p className="section-description">チャットや公開情報をもとに、配信の雰囲気と見どころ候補を整理しています。</p>

          <div className="insight-grid">
            <section className="insight-card">
              <p className="eyebrow">REACTIONS</p>
              <h3>反応の集計</h3>
              {artifact.chat || artifact.comments ? (
                <dl className="metric-list">
                  {artifact.chat ? <><dt>チャット</dt><dd>{formatCount(artifact.chat.totalCount)}件</dd></> : null}
                  {artifact.comments ? <><dt>コメント</dt><dd>{formatCount(artifact.comments.totalCount)}件</dd></> : null}
                </dl>
              ) : <p className="muted">集計データはまだありません。</p>}
            </section>

            {artifact.timestamps?.items?.length ? (
              <section className="insight-card insight-card-wide">
                <p className="eyebrow">TIMESTAMPS</p>
                <h3>見どころ候補</h3>
                <ol className="timestamp-list">
                  {artifact.timestamps.items.map((item, index) => (
                    <li key={`${item.atSec}-${index}`}>
                      <a href={`https://www.youtube.com/watch?v=${video.videoId}&t=${Math.max(item.atSec, 0)}s`} target="_blank" rel="noreferrer">
                        <span className="timestamp-time">{Math.floor(item.atSec / 60)}:{String(item.atSec % 60).padStart(2, '0')}</span>
                        <span className="timestamp-copy">
                          <span>{item.label}</span>
                          {item.confidenceLevel ? (
                            <span className="timestamp-confidence">
                              信頼度: {confidenceLabels[item.confidenceLevel]}
                            </span>
                          ) : null}
                        </span>
                        <NavIcon name="external" />
                      </a>
                    </li>
                  ))}
                </ol>
              </section>
            ) : null}

            <section className="insight-card">
              <p className="eyebrow">WORD CLOUD</p>
              <h3>よく現れた言葉</h3>
              {wordcloudTerms.length ? (
                <div className="detail-wordcloud" aria-label={`配信内でよく現れた言葉。${wordcloudTerms.slice(0, 5).map((term) => term.term).join('、')}`}>
                  {wordcloudTerms.map((term) => (
                    <span
                      key={term.term}
                      style={{ fontSize: `${1 + (term.count / largestWordCount) * 1.25}rem` }}
                    >
                      {term.term}
                    </span>
                  ))}
                </div>
              ) : artifact.wordcloud && wordcloudImage ? (
                <img
                  src={wordcloudImage}
                  alt="配信内でよく現れた言葉"
                  className="detail-wordcloud"
                />
              ) : <p className="muted">ワードクラウドはまだありません。</p>}
            </section>
          </div>

          <details className="provenance">
            <summary>データの出典と更新情報</summary>
            <p>動画情報更新: {formatPublishedDate(video.sourceUpdatedAt)}</p>
            {video.coverage ? <p>収集範囲: {video.coverage.coverageStart}〜{video.coverage.coverageEnd}</p> : null}
            {artifactNotice.map((item) => (
              <p key={item.label}>
                {item.label}: {formatArtifactSource(item.value.source)} / {formatPublishedDate(item.value.generatedAt)}
              </p>
            ))}
          </details>
        </section>
      ) : null}

      {hasConsent && !canShowDerived ? <p className="notice">このリリースでは派生情報を公開していません。</p> : null}
      {hasConsent ? (
        <button
          className="text-button consent-withdraw"
          type="button"
          onClick={() => {
            clearConsent();
            setConsentVersionState(null);
            setNotice('同意を取り下げました。');
          }}
        >
          データ表示への同意を取り下げる
        </button>
      ) : null}
    </section>
  );
}
