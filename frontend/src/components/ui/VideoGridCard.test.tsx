import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { VideoGridCard } from './VideoGridCard';

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
    chat: false,
    comments: false,
    timestamps: false,
    wordcloudChat: false,
    wordcloudComments: false,
    wordcloudBoth: false,
  },
  provenance: {},
};

describe('VideoGridCard', () => {
  // このテストケースの公開契約を検証する。
  it('grid card全体を動画linkにし16:9 thumbnailと最大2 tagを表示する', () => {
    // 1. 初期化
    const { container, getByRole, queryByText } = render(
      <MemoryRouter><VideoGridCard tagNames={['歌', '雑談', '外']} video={video} /></MemoryRouter>,
    );

    // 2. テストの実行
    const link = getByRole('link');

    // 3. アサーション
    expect(link.getAttribute('href')).toBe('/videos/v');
    expect(container.querySelector('.dio-video-grid-card > a')).toBe(link);
    expect(container.querySelector('.dio-video-grid-card .dio-video-thumb')).toBeTruthy();
    expect(container.querySelector('.dio-caption')?.textContent).toContain('2026/01/01 · 1:00');
    expect(queryByText('外')).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('集計がある動画のチャット数を三桁区切りで表示する', () => {
    // 1. 初期化
    const videoWithChat = { ...video, artifactFlags: { ...video.artifactFlags, chat: true } };
    const { getByText } = render(
      <MemoryRouter><VideoGridCard chatCount={12480} tagNames={[]} video={videoWithChat} /></MemoryRouter>,
    );

    // 2. テストの実行
    const count = getByText(/12,480/);

    // 3. アサーション
    expect(count.textContent).toContain('12,480');
  });
});
