import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ConditionSheet } from './ConditionSheet';

describe('ConditionSheet', () => {
  // このテストケースの公開契約を検証する。
  it('modal dialogとして公開し、Escと背景clickで閉じる', () => {
    // 1. 初期化
    const onClose = vi.fn();
    const { container, getByRole } = render(
      <ConditionSheet onClose={onClose} open resultCount={0}><button>内容</button></ConditionSheet>,
    );

    // 2. テストの実行
    fireEvent.keyDown(getByRole('dialog'), { key: 'Escape' });
    fireEvent.mouseDown(container.querySelector('.dio-sheet-backdrop')!);

    // 3. アサーション
    expect(getByRole('dialog').getAttribute('aria-modal')).toBe('true');
    expect(onClose).toHaveBeenCalledTimes(2);
    expect(getByRole('button', { name: '0件 — 条件をゆるめる' })).toBeTruthy();
  });

  // このテストケースの公開契約を検証する。
  it('Tabを最初と最後のfocusable要素で循環させる', () => {
    // 1. 初期化
    const { container } = render(
      <ConditionSheet onClose={vi.fn()} open><button>内容</button></ConditionSheet>,
    );
    const close = container.querySelector<HTMLButtonElement>('[aria-label="条件を閉じる"]')!;
    const cta = container.querySelector<HTMLButtonElement>('.dio-condition-sheet__cta')!;

    // 2. テストの実行
    cta.focus();
    fireEvent.keyDown(cta, { key: 'Tab' });

    // 3. アサーション
    expect(document.activeElement).toBe(close);
  });

  // このテストケースの公開契約を検証する。
  it('実際に開いた後だけclose時にtriggerへfocusを戻す', () => {
    // 1. 初期化
    const trigger = document.createElement('button');
    document.body.append(trigger);
    trigger.focus();
    const { rerender } = render(
      <ConditionSheet onClose={vi.fn()} open><button>内容</button></ConditionSheet>,
    );

    // 2. テストの実行
    rerender(<ConditionSheet onClose={vi.fn()} open={false}><button>内容</button></ConditionSheet>);

    // 3. アサーション
    expect(document.activeElement).toBe(trigger);
    trigger.remove();
  });
});
