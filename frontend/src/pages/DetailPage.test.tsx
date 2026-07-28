import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { DetailPage } from './DetailPage';

const publicData = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));
const storage = vi.hoisted(() => ({ consent: false, saved: [] as string[] }));
const loadVideoDetail = vi.hoisted(() => vi.fn());

vi.mock('@/state/PublicDataContext', () => ({
  usePublicData: () => publicData.current,
}));

vi.mock('@/lib/contract', () => ({
  ContractError: class ContractError extends Error {
    kind = 'server';
  },
  loadVideoDetail,
}));

vi.mock('@/lib/storage', () => ({
  addHistoryVideoId: vi.fn(),
  addSavedVideoId: (id: string) => storage.saved.unshift(id),
  clearConsent: () => { storage.consent = false; },
  getConsentMajorVersion: () => storage.consent ? '1' : null,
  getSavedVideoIds: () => storage.saved,
  hasActiveConsentVersion: () => storage.consent,
  removeSavedVideoId: (id: string) => { storage.saved = storage.saved.filter((item) => item !== id); },
  setConsentVersion: () => { storage.consent = true; },
}));

const video = {
  videoId: 'v1',
  title: '動画タイトル',
  publishedAt: '2026-07-01T00:00:00Z',
  duration: 'PT1H',
  durationSec: 3600,
  thumbnail: { url: 'https://example.test/v1.jpg', width: 120, height: 68 },
  sourceKind: 'youtube',
  metadataStatus: 'ok',
  sourceUpdatedAt: '2026-07-01T00:00:00Z',
  artifactFlags: { chat: false, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false },
  tagIds: ['song'],
  provenance: {},
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/videos/v1']}>
      <Routes><Route path="/videos/:id" element={<DetailPage />} /></Routes>
    </MemoryRouter>,
  );
}

describe('DetailPage', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    storage.consent = false;
    storage.saved = [];
    loadVideoDetail.mockResolvedValue(video);
    publicData.current = {
      loading: false,
      error: null,
      errorKind: null,
      refresh: vi.fn(),
      latest: { releaseId: 'r1', releaseMode: 'normal' },
      release: { videos: [video] },
      tagIndex: { tags: [{ tagId: 'song', displayName: '歌枠' }] },
    };
  });

  // このテストケースの公開契約を検証する。
  it('未同意時はYouTube導線と派生情報を表示しない', async () => {
    // 1. 初期化
    const { getByRole, queryByText } = renderPage();

    // 2. テストの実行
    await waitFor(() => expect(getByRole('button', { name: '同意して進む' })).toBeTruthy());

    // 3. アサーション
    expect(queryByText('YouTubeで見る')).toBeNull();
    expect(queryByText('派生情報')).toBeNull();
    expect(queryByText('同意を取り下げる')).toBeNull();
    expect(getByRole('list', { name: '確認する規約と方針' })).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('同意後にYouTube導線と派生情報を表示する', async () => {
    // 1. 初期化
    const { getByRole, getByText } = renderPage();
    await waitFor(() => expect(getByRole('button', { name: '同意して進む' })).toBeTruthy());

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '同意して進む' }));

    // 3. アサーション
    expect(getByText('YouTubeで見る')).toBeTruthy();
    expect(getByText('派生情報')).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('artifact未作成を0件として表示しない', async () => {
    // 1. 初期化
    storage.consent = true;
    const { getAllByText, getByText, queryByText } = renderPage();

    // 2. テストの実行
    await waitFor(() => expect(getByText('派生データは未作成です')).toBeTruthy());

    // 3. アサーション
    expect(getAllByText('未作成')).toHaveLength(3);
    expect(queryByText('0件')).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('派生情報を日本語ラベルと整形済み日時で表示する', async () => {
    // 1. 初期化
    storage.consent = true;
    publicData.current = {
      ...publicData.current,
      release: {
        videos: [{
          ...video,
          sourceUpdatedAt: '2026-06-30T22:12:00Z',
          coverage: {
            coverageStart: '2026-06-30T22:10:00Z', coverageEnd: '2026-07-01T00:43:00Z', completeFromStart: true, sourceUpdatedAt: '2026-06-30T22:12:00Z',
          },
        }],
      },
    };
    loadVideoDetail.mockResolvedValue({
      ...video,
      sourceUpdatedAt: '2026-06-30T22:12:00Z',
      coverage: {
        coverageStart: '2026-06-30T22:10:00Z', coverageEnd: '2026-07-01T00:43:00Z', completeFromStart: true, sourceUpdatedAt: '2026-06-30T22:12:00Z',
      },
      chat: { totalCount: 12480, source: 'live_chat_messages', generatedAt: '2026-07-01T00:45:00Z', status: 'ready' },
      timestamps: { items: [{ atSec: 120, label: '開始', confidenceLevel: 'high' }], source: 'get_archives_info_v1', generatedAt: '2026-07-01T00:45:00Z', status: 'ready' },
    });
    const { getAllByText, getByText, queryByText } = renderPage();

    // 2. テストの実行
    await waitFor(() => expect(getByText('データ更新日: 2026/06/30 22:12')).toBeTruthy());

    // 3. アサーション
    expect(getByText('対象期間: 2026/06/30 22:10 〜 2026/07/01 00:43')).toBeTruthy();
    expect(getAllByText('チャット')).toHaveLength(2);
    expect(getByText(/12,480件/)).toBeTruthy();
    expect(getByText(/2:00 · 開始/)).toBeTruthy();
    expect(getByText('（信頼度: high）')).toBeTruthy();
    expect(getByText('アーカイブ情報生成から作成 · 作成日: 2026/07/01 00:45')).toBeTruthy();
    expect(queryByText(/sourceUpdatedAt:/)).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('公開データサーバーのエラー文言をalertで維持する', () => {
    // 1. 初期化
    publicData.current = { ...publicData.current, error: 'HTTP 500', errorKind: 'server', latest: null };

    // 2. テストの実行
    const { getByRole } = renderPage();

    // 3. アサーション
    expect(getByRole('alert').textContent).toContain('公開データサーバーでエラー');
  });

  // エラーの主表示を日本語の利用者向け説明にする。
  it('技術エラー詳細を補助表示へ分離する', () => {
    // 1. 初期化
    publicData.current = { ...publicData.current, error: 'failed to load /data/latest.json: HTTP 503', errorKind: 'server', latest: null };

    // 2. テストの実行
    const { getByRole, getByText } = renderPage();

    // 3. アサーション
    expect(getByRole('alert').textContent).toContain('しばらく待ってから');
    expect(getByText('技術情報を表示')).toBeTruthy();
  });
});
