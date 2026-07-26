import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SearchBar } from './SearchBar';

describe('SearchBar', () => {
  // このテストケースの公開契約を検証する。
  it('tokenを描画して解除する', () => {
    // 1. 初期化
    const onTokenRemove = vi.fn();
    const { getByRole, getByText } = render(
      <SearchBar
        onQueryChange={vi.fn()}
        onTokenRemove={onTokenRemove}
        query=""
        tokens={[{ id: 'song', label: '歌' }]}
      />,
    );

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '歌の条件を解除' }));

    // 3. アサーション
    expect(getByText('歌')).toBeTruthy();
    expect(onTokenRemove).toHaveBeenCalledWith('song');
  });

  // このテストケースの公開契約を検証する。
  it('候補listboxとactive optionをcomboboxへ関連付ける', () => {
    // 1. 初期化
    const { container } = render(
      <SearchBar
        activeSuggestionId="suggestions-1"
        onQueryChange={vi.fn()}
        query="歌"
        suggestionListId="suggestions"
        suggestionsOpen
      />,
    );

    // 2. テストの実行
    const input = container.querySelector('[role="combobox"]')!;

    // 3. アサーション
    expect(input.getAttribute('aria-expanded')).toBe('true');
    expect(input.getAttribute('aria-controls')).toBe('suggestions');
    expect(input.getAttribute('aria-activedescendant')).toBe('suggestions-1');
  });
});
