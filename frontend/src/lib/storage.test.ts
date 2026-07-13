import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { SearchCondition } from '@/types';

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
    // 1. 初期化
    localStorage.setItem('diopside_saved_v1', '{broken');
    localStorage.setItem('unrelated', 'keep');

    // 2. テストの実行
    const savedVideoIds = getSavedVideoIds();

    // 3. アサーション
    expect(savedVideoIds).toEqual([]);
    expect(localStorage.getItem('diopside_saved_v1')).toBeNull();
    expect(localStorage.getItem('unrelated')).toBe('keep');
  });

  // 正規化済みの検索条件全体を履歴へ保存することを検証する。
  it('正規検索条件全体を保存する', () => {
    // 1. 初期化
    const condition: SearchCondition = {
      q: '歌枠', tags: ['tag-1'], lmin: 10, from: '2026-01-01',
      artifacts: ['chat'], sort: 'mostChat',
    };

    // 2. テストの実行
    addRecentSearch(condition);
    const stored = getRecentSearchEntries()[0]?.condition;

    // 3. アサーション
    expect(stored).toMatchObject(condition);
  });

  // 不正な同意状態を拒否して削除することを検証する。
  it('不正な同意状態を拒否する', () => {
    // 1. 初期化
    localStorage.setItem('diopside_consent_v1', JSON.stringify({ policyMajor: '1' }));

    // 2. テストの実行
    const consentVersion = getConsentVersion();

    // 3. アサーション
    expect(consentVersion).toBeNull();
    expect(localStorage.getItem('diopside_consent_v1')).toBeNull();
  });

  // 未知のschema versionを持つデータを拒否することを検証する。
  it('未知のschema versionを拒否する', () => {
    // 1. 初期化
    localStorage.setItem('diopside_saved_v1', JSON.stringify({ schemaVersion: 999, items: ['video-1'] }));

    // 2. テストの実行
    const savedVideoIds = getSavedVideoIds();

    // 3. アサーション
    expect(savedVideoIds).toEqual([]);
  });

  // 書き込み拒否時に失敗eventを通知することを検証する。
  it('書き込み拒否時に失敗eventを通知する', () => {
    // 1. 初期化
    const listener = vi.fn();
    window.addEventListener(storageErrorEvent, listener);
    const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError');
    });

    // 2. テストの実行
    const execute = () => addSavedVideoId('video-1');

    // 3. アサーション
    expect(execute).not.toThrow();
    expect(listener).toHaveBeenCalledOnce();
    spy.mockRestore();
    window.removeEventListener(storageErrorEvent, listener);
  });
});
