import { cleanup, fireEvent, render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SavedPage } from './SavedPage';

const publicData = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
const storage = vi.hoisted(() => ({ saved: [] as string[], fail: false }));

vi.mock('@/state/PublicDataContext', () => ({
  usePublicData: () => publicData.current,
}));

vi.mock('@/lib/storage', () => ({
  clearSaved: () => {
    if (storage.fail) window.dispatchEvent(new CustomEvent('diopside:storage-error'));
    storage.saved = [];
  },
  getSavedVideoIds: () => storage.saved,
  hasActiveConsentVersion: () => false,
  removeSavedVideoId: (id: string) => { storage.saved = storage.saved.filter((item) => item !== id); },
}));

const video = {
  videoId: 'v1', title: '保存した配信', publishedAt: '2026-07-01T00:00:00Z', duration: 'PT1H', durationSec: 3600,
  thumbnail: { url: 'https://example.test/v1.jpg', width: 120, height: 68 }, sourceKind: 'youtube', metadataStatus: 'ok',
  sourceUpdatedAt: '2026-07-01T00:00:00Z', artifactFlags: { chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false }, provenance: {},
};

describe('SavedPage', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    storage.saved = [];
    storage.fail = false;
    publicData.current = { loading: false, error: null, errorKind: null, release: { videos: [video] }, latest: { releaseMode: 'normal' }, tagIndex: null, refresh: vi.fn() };
  });

  // このテストケースの公開契約を検証する。
  it('保存済み動画をVideoListItemとして描画し、個別に解除できる', () => {
    // 1. 初期化
    storage.saved = ['v1'];
    const { getByRole, queryByRole } = render(<MemoryRouter><SavedPage /></MemoryRouter>);

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '保存を外す' }));

    // 3. アサーション
    expect(queryByRole('link', { name: /保存した配信/ })).toBeNull();
    expect(getByRole('link', { name: '検索を開く' })).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('空状態でも検索導線を表示する', () => {
    // 1. 初期化
    const { getByText, getByRole } = render(<MemoryRouter><SavedPage /></MemoryRouter>);

    // 2. テストの実行
    const link = getByRole('link', { name: '検索を開く' });

    // 3. アサーション
    expect(getByText('保存した動画はありません')).toBeTruthy();
    expect(link.getAttribute('href')).toBe('/search');
  });

  // このテストケースの公開契約を検証する。
  it('storage失敗eventを保持し、全削除後も空状態へ遷移する', () => {
    // 1. 初期化
    storage.saved = ['v1'];
    storage.fail = true;
    const failure = vi.fn();
    window.addEventListener('diopside:storage-error', failure);
    const { getByRole, getByText } = render(<MemoryRouter><SavedPage /></MemoryRouter>);

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: 'すべて削除' }));

    // 3. アサーション
    expect(failure).toHaveBeenCalledTimes(1);
    expect(getByText('保存した動画はありません')).toBeTruthy();
    window.removeEventListener('diopside:storage-error', failure);
  });
});
