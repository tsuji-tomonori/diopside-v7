import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { VideoListItem } from './VideoListItem';

const video = {
  videoId: 'v',
  title: '題名',
  publishedAt: '2026-01-01',
  duration: '1:00',
  durationSec: 60,
  thumbnail: { url: '/x', width: 1, height: 1 },
  sourceKind: 'x',
  metadataStatus: 'x',
  sourceUpdatedAt: 'x',
  artifactFlags: {
    chat: true,
    comments: false,
    timestamps: false,
    wordcloudChat: false,
    wordcloudComments: false,
    wordcloudBoth: false,
  },
  provenance: {},
};

describe('VideoListItem', () => {
  // このテストケースの公開契約を検証する。
  it('行全体を動画linkにし、長さbadge・2行title用class・最大2 tagを表示する', () => {
    // 1. 初期化
    const { container, getByRole, queryByText } = render(
      <MemoryRouter>
        <VideoListItem chatCount={12} tagNames={['歌', '雑談', '外']} video={video} />
      </MemoryRouter>,
    );

    // 2. テストの実行
    const link = getByRole('link');

    // 3. アサーション
    expect(link.getAttribute('href')).toBe('/videos/v');
    expect(container.querySelector('.dio-video-list-item > a')).toBe(link);
    expect(container.querySelector('.dio-video-thumb b')?.textContent).toBe('1:00');
    expect(container.querySelector('.dio-caption')?.textContent).toContain('2026/01/01 · 1:00');
    expect(container.querySelector('.dio-caption')?.textContent).toContain('12');
    expect(container.querySelector('.dio-video-list-item h3')).toBeTruthy();
    expect(queryByText('外')).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('chat artifactが無い動画では渡された集計値を表示しない', () => {
    // 1. 初期化
    const videoWithoutChat = {
      ...video,
      artifactFlags: { ...video.artifactFlags, chat: false },
    };
    const { container } = render(
      <MemoryRouter>
        <VideoListItem chatCount={12} tagNames={[]} video={videoWithoutChat} />
      </MemoryRouter>,
    );

    // 2. テストの実行
    const chatCount = container.querySelector('small');

    // 3. アサーション
    expect(chatCount).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('集計がある動画のチャット数を三桁区切りで表示する', () => {
    // 1. 初期化
    const { getByText } = render(
      <MemoryRouter>
        <VideoListItem chatCount={12480} tagNames={[]} video={video} />
      </MemoryRouter>,
    );

    // 2. テストの実行
    const count = getByText(/12,480/);

    // 3. アサーション
    expect(count.textContent).toContain('12,480');
  });
});
