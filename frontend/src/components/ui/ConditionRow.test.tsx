import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConditionRow } from './ConditionRow';

describe('ConditionRow', () => {
  // このテストケースの公開契約を検証する。
  it('zero stateで3つのadd chipとsticky containerを表示する', () => {
    // 1. 初期化
    const onOpen = vi.fn();
    const { container, getByRole } = render(
      <ConditionRow conditions={[]} onOpen={onOpen} onRemove={vi.fn()} />,
    );

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '＋タグ' }));

    // 3. アサーション
    expect(getByRole('button', { name: '＋長さ' })).toBeTruthy();
    expect(getByRole('button', { name: '＋投稿日' })).toBeTruthy();
    expect(container.querySelector('.dio-condition-row')).toBeTruthy();
    expect(onOpen).toHaveBeenCalledWith('tags');
  });

  // このテストケースの公開契約を検証する。
  it('applied stateでremovable chipと条件数に一致するaction chipを表示する', () => {
    // 1. 初期化
    const onOpen = vi.fn();
    const onRemove = vi.fn();
    const { getByRole } = render(
      <ConditionRow
        conditions={[
          { id: 'tag', label: '歌', section: 'tags' },
          { id: 'length', label: '10分以上', section: 'length' },
        ]}
        onOpen={onOpen}
        onRemove={onRemove}
      />,
    );

    // 2. テストの実行
    fireEvent.click(getByRole('button', { name: '歌の条件を解除' }));
    fireEvent.click(getByRole('button', { name: '条件 (2)' }));

    // 3. アサーション
    expect(getByRole('button', { name: '歌' })).toBeTruthy();
    expect(onRemove).toHaveBeenCalledWith('tag');
    expect(onOpen).toHaveBeenLastCalledWith();
  });
});
