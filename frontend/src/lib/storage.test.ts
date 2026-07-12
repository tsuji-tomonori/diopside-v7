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

describe('versioned local storage', () => {
  it('clears only a corrupted key', () => {
    localStorage.setItem('diopside_saved_v1', '{broken');
    localStorage.setItem('unrelated', 'keep');
    expect(getSavedVideoIds()).toEqual([]);
    expect(localStorage.getItem('diopside_saved_v1')).toBeNull();
    expect(localStorage.getItem('unrelated')).toBe('keep');
  });

  it('stores full canonical recent-search conditions', () => {
    addRecentSearch({
      q: '歌枠', tags: ['tag-1'], lmin: 10, from: '2026-01-01',
      artifacts: ['chat'], sort: 'mostChat',
    });
    expect(getRecentSearchEntries()[0]?.condition).toMatchObject({
      q: '歌枠', tags: ['tag-1'], lmin: 10, from: '2026-01-01',
      artifacts: ['chat'], sort: 'mostChat',
    });
  });

  it('rejects malformed consent state', () => {
    localStorage.setItem('diopside_consent_v1', JSON.stringify({ policyMajor: '1' }));
    expect(getConsentVersion()).toBeNull();
    expect(localStorage.getItem('diopside_consent_v1')).toBeNull();
  });

  it('rejects a payload from an unknown schema version', () => {
    localStorage.setItem('diopside_saved_v1', JSON.stringify({ schemaVersion: 999, items: ['video-1'] }));
    expect(getSavedVideoIds()).toEqual([]);
  });

  it('emits a failure event when a write is rejected', () => {
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
