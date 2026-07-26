import { cleanup, fireEvent, render } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SearchPage } from './SearchPage';

const publicData = vi.hoisted(() => ({ current: {} as Record<string, unknown> }));

vi.mock('@/state/PublicDataContext', () => ({
  usePublicData: () => publicData.current,
}));

vi.mock('@/lib/storage', () => ({
  hasActiveConsentVersion: () => true,
}));

const tags = [
  { tagId: 'song', categoryId: 'c', subcategoryId: 's', displayName: '歌枠', count: 8, videoIds: ['v1'] },
  { tagId: 'talk', categoryId: 'c', subcategoryId: 's', displayName: '雑談', count: 3, videoIds: ['v2'] },
  { tagId: 'sing', categoryId: 'c', subcategoryId: 's', displayName: '歌', count: 1, videoIds: ['v1'] },
];

const videos = [
  {
    videoId: 'v1',
    title: '歌枠アーカイブ',
    publishedAt: '2026-07-01T00:00:00Z',
    duration: '1:00:00',
    durationSec: 3600,
    thumbnail: { url: '/v1.jpg', width: 120, height: 68 },
    sourceKind: 'youtube',
    metadataStatus: 'ok',
    sourceUpdatedAt: '2026-07-01T00:00:00Z',
    artifactFlags: { chat: true, comments: false, timestamps: false, wordcloudChat: false, wordcloudComments: false, wordcloudBoth: false },
    tagIds: ['song', 'sing'],
    provenance: {},
    chat: { totalCount: 10 },
  },
];

function LocationProbe() {
  return <output data-testid="location">{useLocation().search}</output>;
}

function renderPage(initialEntry = '/search') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <SearchPage />
      <LocationProbe />
    </MemoryRouter>,
  );
}

describe('SearchPage', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    publicData.current = {
      loading: false,
      error: null,
      errorKind: null,
      refresh: vi.fn(),
      latest: { releaseMode: 'normal' },
      alias: { aliases: {} },
      tagIndex: { tags },
      release: { videos },
      search: {
        videos: [{
          videoId: 'v1',
          titleTokens: ['歌枠', 'アーカイブ'],
          sourceKind: 'youtube',
          metadataStatus: 'ok',
          publishedAt: '2026-07-01T00:00:00Z',
          publishedDate: '2026-07-01',
          durationSec: 3600,
          artifactFlags: videos[0].artifactFlags,
          tagIds: ['song', 'sing'],
        }],
      },
    };
  });

  // このテストケースの公開契約を検証する。
  it('入力中だけ実タグ由来の最大4行候補を出し、選択を条件へ追加する', () => {
    // 1. 初期化
    const { getByRole, queryByRole, getAllByRole } = renderPage();
    const input = getByRole('combobox', { name: 'キーワード' });

    // 2. テストの実行
    fireEvent.change(input, { target: { value: '歌' } });
    const optionCount = getByRole('listbox').querySelectorAll('[role="option"]').length;
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    // 3. アサーション
    expect(optionCount).toBeLessThanOrEqual(4);
    expect(getAllByRole('status').some((status) => status.textContent?.includes('検索条件へ追加しました'))).toBe(true);
    expect(queryByRole('listbox')).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('条件ゼロの追加chipと適用後のremovable chipを切り替え、closeで即時解除する', () => {
    // 1. 初期化
    const { getAllByRole, queryAllByRole, getByRole } = renderPage('/search?tag=song&sort=newest');

    // 2. テストの実行
    fireEvent.click(getAllByRole('button', { name: '歌枠の条件を解除' })[0]);

    // 3. アサーション
    expect(queryAllByRole('button', { name: '歌枠の条件を解除' })).toHaveLength(0);
    expect(getByRole('button', { name: '＋タグ' })).toBeTruthy();
    expect(getByRole('button', { name: '＋長さ' })).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('条件シートのCTAとlive regionを件数に応じて更新する', () => {
    // 1. 初期化
    const { getByRole, getAllByRole } = renderPage('/search?tag=talk&sort=newest');

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '条件 (1)' }));

    // 3. アサーション
    expect(getByRole('dialog')).toBeTruthy();
    expect(getByRole('button', { name: '0件 — 条件をゆるめる' })).toBeTruthy();
    expect(getAllByRole('status').some((status) => status.textContent?.includes('0件の検索結果です。'))).toBe(true);
  });

  // このテストケースの公開契約を検証する。
  it('URL queryを条件へ反映し、tag操作をURLへ戻す', () => {
    // 1. 初期化
    const { getAllByRole, getByTestId } = renderPage('/search?tag=song&lmin=30&sort=newest');

    // 2. テストの実行
    fireEvent.click(getAllByRole('button', { name: '歌枠の条件を解除' })[0]);

    // 3. アサーション
    expect(getByTestId('location').textContent).toContain('lmin=30');
    expect(getByTestId('location').textContent).not.toContain('tag=song');
  });

  // このテストケースの公開契約を検証する。
  it('loading、公開artifact欠落、取得エラーを空結果と区別する', () => {
    // 1. 初期化
    publicData.current = { ...publicData.current, loading: true };
    const { container, rerender, getByRole, queryByText } = renderPage();
    const loadingLabel = container.querySelector('.dio-loading-state')?.textContent;

    // 2. テストの実行
    publicData.current = { ...publicData.current, loading: false, search: null };
    rerender(
      <MemoryRouter initialEntries={['/search']}>
        <SearchPage />
      </MemoryRouter>,
    );

    // 3. アサーション
    expect(loadingLabel).toContain('読み込んでいます');
    expect(getByRole('alert').textContent).toContain('公開artifactが不足している');
    expect(queryByText('条件に合う動画はありません')).toBeNull();
  });

  // このテストケースの公開契約を検証する。
  it('retryableとpermanentな取得エラーをDataErrorStateとして表示する', () => {
    // 1. 初期化
    publicData.current = {
      ...publicData.current,
      error: '接続を確認してください。',
      errorKind: 'network',
    };
    const { rerender, getByRole, getByText } = renderPage();
    const retryableLabel = getByText('ネットワーク接続を確認してください。').textContent;

    // 2. テストの実行
    publicData.current = {
      ...publicData.current,
      error: '公開済みartifactはありません。',
      errorKind: 'not_found',
    };
    rerender(
      <MemoryRouter initialEntries={['/search']}>
        <SearchPage />
      </MemoryRouter>,
    );

    // 3. アサーション
    expect(retryableLabel).toContain('ネットワーク接続を確認してください。');
    expect(getByRole('alert')).toBeTruthy();
    expect(getByText('公開データが見つかりません。')).toBeTruthy();
  });
});
