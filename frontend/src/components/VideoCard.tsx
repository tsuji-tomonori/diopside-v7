import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArtifactFlags } from '@/types';
import { NavIcon } from '@/components/NavIcon';
import { formatCount, formatDuration, formatPublishedDate } from '@/lib/format';

interface Props {
  videoId: string;
  title: string;
  publishedAt: string;
  duration: string;
  thumbnail: string;
  tagNames: string[];
  flags: ArtifactFlags;
  chatCount?: number;
}

export function VideoCard({
  videoId,
  title,
  publishedAt,
  duration,
  thumbnail,
  tagNames,
  flags,
  chatCount,
}: Props) {
  const [thumbnailUnavailable, setThumbnailUnavailable] = useState(false);

  return (
    <article className="video-card">
      <Link className="video-card-link" to={`/videos/${videoId}`}>
        <span className="video-thumb-wrap">
          {thumbnailUnavailable ? (
            <span className="video-thumb-fallback">
              <NavIcon name="play" />
              <span className="sr-only">サムネイルを表示できません</span>
            </span>
          ) : (
            <img
              src={thumbnail}
              alt=""
              className="video-thumb"
              loading="lazy"
              onError={() => setThumbnailUnavailable(true)}
            />
          )}
          <span className="duration-badge">{formatDuration(duration)}</span>
        </span>
        <div className="video-meta">
          <h3>{title}</h3>
          <p className="video-date">{formatPublishedDate(publishedAt)}</p>
          <div className="chips video-tags">
            {tagNames.slice(0, 2).map((tag) => (
              <span className="chip" key={tag}>
                {tag}
              </span>
            ))}
            {flags.chat && typeof chatCount === 'number' ? (
              <span className="video-count">チャット {formatCount(chatCount)}件</span>
            ) : null}
          </div>
        </div>
      </Link>
      <a
        className="button button-quiet yt-action"
        href={`https://www.youtube.com/watch?v=${videoId}`}
        target="_blank"
        rel="noreferrer"
        aria-label={`${title}をYouTubeで見る`}
      >
        <NavIcon name="external" />
        YouTube
      </a>
    </article>
  );
}
