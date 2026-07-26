import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConditionPanel } from './ConditionPanel';

describe('ConditionPanel', () => {
  // このテストケースの公開契約を検証する。
  it('PC panelをdialogとaccessible nameで公開する', () => {
    // 1. 初期化
    const { getByRole } = render(
      <ConditionPanel open onClose={vi.fn()}><p>内容</p></ConditionPanel>,
    );

    // 2. テストの実行
    const dialog = getByRole('dialog', { name: '検索条件' });

    // 3. アサーション
    expect(dialog.getAttribute('aria-modal')).toBe('true');
  });

  // このテストケースの公開契約を検証する。
  it('閉じる操作でonCloseを呼ぶ', () => {
    // 1. 初期化
    const onClose = vi.fn();
    const { container } = render(
      <ConditionPanel open onClose={onClose}><p>内容</p></ConditionPanel>,
    );

    // 2. テストの実行
    fireEvent.click(container.querySelector<HTMLButtonElement>('[aria-label="条件を閉じる"]')!);

    // 3. アサーション
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
