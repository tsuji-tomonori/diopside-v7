import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  addRecentSearch,
  addSavedVideoId,
  getConsentVersion,
  getRecentSearchEntries,
  getSavedVideoIds,
  storageErrorEvent,
} from './storage';

beforeEach(() => localStorage.clear());

describe('version付きlocal storage', () => {
  // 破損したkeyだけを削除し、無関係な値を維持することを検証する。
  it('破損したkeyだけを削除する', () => {
    localStorage.setItem('diopside_saved_v1', '{broken');
    localStorage.setItem('unrelated', 'keep');
    expect(getSavedVideoIds()).toEqual([]);
    expect(localStorage.getItem('diopside_saved_v1')).toBeNull();
    expect(localStorage.getItem('unrelated')).toBe('keep');
  });

  // 正規化済みの検索条件全体を履歴へ保存することを検証する。
  it('正規検索条件全体を保存する', () => {
    addRecentSearch({
      q: '歌枠', tags: ['tag-1'], lmin: 10, from: '2026-01-01',
      artifacts: ['chat'], sort: 'mostChat',
    });
    expect(getRecentSearchEntries()[0]?.condition).toMatchObject({
      q: '歌枠', tags: ['tag-1'], lmin: 10, from: '2026-01-01',
      artifacts: ['chat'], sort: 'mostChat',
    });
  });

  // 不正な同意状態を拒否して削除することを検証する。
  it('不正な同意状態を拒否する', () => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify({ policyMajor: '1' }));
    expect(getConsentVersion()).toBeNull();
    expect(localStorage.getItem('diopside_consent_v1')).toBeNull();
  });

  // 未知のschema versionを持つデータを拒否することを検証する。
  it('未知のschema versionを拒否する', () => {
    localStorage.setItem('diopside_saved_v1', JSON.stringify({ schemaVersion: 999, items: ['video-1'] }));
    expect(getSavedVideoIds()).toEqual([]);
  });

  // 書き込み拒否時に失敗eventを通知することを検証する。
  it('書き込み拒否時に失敗eventを通知する', () => {
    const listener = vi.fn();
    window.addEventListener(storageErrorEvent, listener);
    const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError');
    });
    expect(() => addSavedVideoId('video-1')).not.toThrow();
    expect(listener).toHaveBeenCalledOnce();
    spy.mockRestore();
    window.removeEventListener(storageErrorEvent, listener);
  });
});
