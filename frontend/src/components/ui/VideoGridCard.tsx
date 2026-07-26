import { Link } from 'react-router-dom';

import { VideoIndex } from '@/types';
import { formatCount, formatDuration, formatPublishedAt } from '@/lib/format';
import { Icon } from './Icon';

export function VideoGridCard({ video, tagNames, chatCount }: { video: VideoIndex; tagNames: string[]; chatCount?: number }) {
  return (
    <article className="dio-video-grid-card">
      <Link to={`/videos/${video.videoId}`}>
        <span className="dio-video-thumb">
          <img alt="" src={video.thumbnail.url} />
          <b>{formatDuration(video.durationSec)}</b>
        </span>
        <h3>{video.title}</h3>
        <p className="dio-caption dio-num">
          {formatPublishedAt(video.publishedAt)} · {formatDuration(video.durationSec)}
          {video.artifactFlags.chat && typeof chatCount === 'number' ? ` · ` : ''}
          {video.artifactFlags.chat && typeof chatCount === 'number' ? <><Icon name="chat_bubble" size={16} /> {formatCount(chatCount)}</> : null}
        </p>
        <span className="dio-video-tags">
          {tagNames.slice(0, 2).map((tag) => <em key={tag}>{tag}</em>)}
        </span>
      </Link>
    </article>
  );
}
