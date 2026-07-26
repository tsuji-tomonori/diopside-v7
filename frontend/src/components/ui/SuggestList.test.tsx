import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SuggestList } from './SuggestList';

const items = [
  { id: 'song', label: '歌' },
  { id: 'talk', label: '雑談' },
  { id: 'date', label: '今週' },
  { id: 'keyword', label: 'キーワード' },
  { id: 'hidden', label: '5件目' },
];

describe('SuggestList', () => {
  // このテストケースの公開契約を検証する。
  it('最大4行のlistboxとしてactive optionを公開する', () => {
    // 1. 初期化
    const { getAllByRole, getByRole } = render(
      <SuggestList activeIndex={1} items={items} onSelect={vi.fn()} />,
    );

    // 2. テストの実行
    const options = getAllByRole('option');

    // 3. アサーション
    expect(getByRole('listbox')).toBeTruthy();
    expect(options).toHaveLength(4);
    expect(options[0].getAttribute('aria-selected')).toBe('false');
    expect(options[1].getAttribute('aria-selected')).toBe('true');
  });

  // このテストケースの公開契約を検証する。
  it('clickとEnterのどちらでも候補を選択する', () => {
    // 1. 初期化
    const onSelect = vi.fn();
    const { container } = render(
      <SuggestList activeIndex={0} items={items} onSelect={onSelect} />,
    );

    // 2. テストの実行
    const buttons = container.querySelectorAll<HTMLButtonElement>('button');
    fireEvent.click(buttons[0]);
    fireEvent.keyDown(buttons[1], { key: 'Enter' });

    // 3. アサーション
    expect(onSelect).toHaveBeenNthCalledWith(1, items[0]);
    expect(onSelect).toHaveBeenNthCalledWith(2, items[1]);
  });
});
