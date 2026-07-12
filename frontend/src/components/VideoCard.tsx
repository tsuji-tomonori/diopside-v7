import { Link } from 'react-router-dom';
import { ArtifactFlags } from '@/types';

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
  return (
    <article className="video-card">
      <Link className="video-card-link" to={`/videos/${videoId}`}>
        <img src={thumbnail} alt="" className="video-thumb" />
        <div className="video-meta">
          <h3>{title}</h3>
          <p>
            {publishedAt} · {duration}
          </p>
          <div className="chips">
            {tagNames.slice(0, 2).map((tag) => (
              <span className="chip" key={tag}>
                {tag}
              </span>
            ))}
            {flags.chat && typeof chatCount === 'number' ? <span className="chip">chat {chatCount}</span> : null}
          </div>
        </div>
      </Link>
      <a
        className="yt-action"
        href={`https://www.youtube.com/watch?v=${videoId}`}
        target="_blank"
        rel="noreferrer"
      >
        YouTube へ
      </a>
    </article>
  );
}
