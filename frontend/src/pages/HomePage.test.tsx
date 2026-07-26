import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';

import { HomePage } from './HomePage';

const publicData = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));

vi.mock('@/state/PublicDataContext', () => ({
  usePublicData: () => publicData.current,
}));

vi.mock('@/lib/storage', () => ({
  hasActiveConsentVersion: () => true,
}));

const video = {
  videoId: 'v1',
  title: '最新配信',
  publishedAt: '2026-07-01T00:00:00Z',
  duration: '1:00:00',
  durationSec: 3600,
  thumbnail: { url: '/v1.jpg', width: 120, height: 68 },
  sourceKind: 'youtube',
  metadataStatus: 'ok',
  sourceUpdatedAt: '2026-07-01T00:00:00Z',
  artifactFlags: { chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false },
  tagIds: ['song'],
  provenance: {},
};

function LocationProbe() {
  return <output data-testid="location">{useLocation().search}</output>;
}

describe('HomePage', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    publicData.current = {
      loading: false,
      error: null,
      errorKind: null,
      refresh: vi.fn(),
      latest: { releaseMode: 'normal' },
      tagIndex: { tags: [{ tagId: 'song', categoryId: 'c', subcategoryId: 's', displayName: '歌枠', count: 1, videoIds: ['v1'] }] },
      release: { videos: [video] },
    };
  });

  // このテストケースの公開契約を検証する。
  it('検索導線と実データのクイックタグを表示して検索へ遷移する', () => {
    // 1. 初期化
    const { getByRole, getByTestId } = render(
      <MemoryRouter>
        <HomePage />
        <LocationProbe />
      </MemoryRouter>,
    );

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '歌枠' }));

    // 3. アサーション
    expect(getByRole('combobox', { name: 'キーワード' })).toBeTruthy();
    expect(getByTestId('location').textContent).toContain('tag=song');
  });

  // このテストケースの公開契約を検証する。
  it('動画が空でも検索と条件の入口を残す', () => {
    // 1. 初期化
    publicData.current = { ...publicData.current, release: { videos: [] } };
    const { getByRole, getByText } = render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    // 2. テストの実行
    fireEvent.change(getByRole('combobox', { name: 'キーワード' }), { target: { value: '歌' } });

    // 3. アサーション
    expect(getByText('公開中の動画はありません')).toBeTruthy();
    expect(getByRole('button', { name: '歌枠' })).toBeTruthy();
  });
});
