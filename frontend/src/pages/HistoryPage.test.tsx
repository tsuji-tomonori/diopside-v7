import { cleanup, fireEvent, render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { HistoryPage } from './HistoryPage';

const publicData = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
const storage = vi.hoisted(() => ({ history: [] as string[], fail: false }));

vi.mock('@/state/PublicDataContext', () => ({
  usePublicData: () => publicData.current,
}));

vi.mock('@/lib/storage', () => ({
  clearHistory: () => {
    if (storage.fail) window.dispatchEvent(new CustomEvent('diopside:storage-error'));
    storage.history = [];
  },
  getHistoryVideoIds: () => storage.history,
  removeHistoryVideoId: (id: string) => { storage.history = storage.history.filter((item) => item !== id); },
}));

const video = {
  videoId: 'v1', title: '閲覧した配信', publishedAt: '2026-07-01T00:00:00Z', duration: 'PT1H', durationSec: 3600,
  thumbnail: { url: 'https://example.test/v1.jpg', width: 120, height: 68 }, sourceKind: 'youtube', metadataStatus: 'ok',
  sourceUpdatedAt: '2026-07-01T00:00:00Z', artifactFlags: { chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false }, provenance: {},
};

describe('HistoryPage', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    storage.history = [];
    storage.fail = false;
    publicData.current = { loading: false, release: { videos: [video] } };
  });

  // このテストケースの公開契約を検証する。
  it('履歴をVideoListItemとして描画し、全削除操作を維持する', () => {
    // 1. 初期化
    storage.history = ['v1'];
    const { getByRole, getByText } = render(<MemoryRouter><HistoryPage /></MemoryRouter>);

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: 'すべて削除' }));

    // 3. アサーション
    expect(getByText('閲覧履歴はありません')).toBeTruthy();
    expect(getByRole('link', { name: '検索を開く' }).getAttribute('href')).toBe('/search');
  });

  // このテストケースの公開契約を検証する。
  it('空状態で検索導線を表示する', () => {
    // 1. 初期化
    const { getByText, getByRole } = render(<MemoryRouter><HistoryPage /></MemoryRouter>);

    // 2. テストの実行
    const link = getByRole('link', { name: '検索を開く' });

    // 3. アサーション
    expect(getByText('閲覧履歴はありません')).toBeTruthy();
    expect(link).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('storage失敗eventを保持し、履歴の全削除を続行する', () => {
    // 1. 初期化
    storage.history = ['v1'];
    storage.fail = true;
    const failure = vi.fn();
    window.addEventListener('diopside:storage-error', failure);
    const { getByRole, getByText } = render(<MemoryRouter><HistoryPage /></MemoryRouter>);

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: 'すべて削除' }));

    // 3. アサーション
    expect(failure).toHaveBeenCalledTimes(1);
    expect(getByText('閲覧履歴はありません')).toBeTruthy();
    window.removeEventListener('diopside:storage-error', failure);
  });
});
