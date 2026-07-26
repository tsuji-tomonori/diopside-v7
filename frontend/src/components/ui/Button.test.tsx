import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Button } from './Button';

describe('Button', () => {
  // このテストケースの公開契約を検証する。
  it.each(['primary', 'secondary', 'text'] as const)('%s variantのclassを設定する', (variant) => {
    // 1. 初期化
    const { container } = render(<Button variant={variant}>表示</Button>);

    // 2. テストの実行
    const button = container.querySelector('button')!;

    // 3. アサーション
    expect(button.className).toContain(`dio-button--${variant}`);
  });

  // このテストケースの公開契約を検証する。
  it('disabled時にclick handlerを呼ばない', () => {
    // 1. 初期化
    const onClick = vi.fn();
    const { container } = render(<Button disabled onClick={onClick}>表示</Button>);

    // 2. テストの実行
    fireEvent.click(container.querySelector('button')!);

    // 3. アサーション
    expect(onClick).not.toHaveBeenCalled();
  });
});
