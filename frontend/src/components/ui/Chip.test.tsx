import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Chip } from './Chip';

describe('Chip', () => {
  // このテストケースの公開契約を検証する。
  it.each(['selectable', 'add', 'action', 'preset'] as const)('%s variantを描画する', (variant) => {
    // 1. 初期化
    const { container } = render(<Chip label="歌" variant={variant} />);

    // 2. テストの実行
    const chip = container.querySelector('button')!;

    // 3. アサーション
    expect(chip.className).toContain(`dio-chip--${variant}`);
  });

  // このテストケースの公開契約を検証する。
  it('selectableとpresetの選択状態をaria-pressedで公開する', () => {
    // 1. 初期化
    const { container } = render(<Chip label="歌" selected variant="selectable" />);

    // 2. テストの実行
    const chip = container.querySelector('button')!;

    // 3. アサーション
    expect(chip.getAttribute('aria-pressed')).toBe('true');
  });

  // このテストケースの公開契約を検証する。
  it('removableの本体操作と解除操作を分離する', () => {
    // 1. 初期化
    const onOpen = vi.fn();
    const onRemove = vi.fn();
    const { container } = render(
      <Chip label="期間" onClick={onOpen} onRemove={onRemove} variant="removable" />,
    );

    // 2. テストの実行
    fireEvent.click(container.querySelector('.dio-chip__label')!);
    fireEvent.click(container.querySelector('.dio-chip__remove')!);

    // 3. アサーション
    expect(onOpen).toHaveBeenCalledOnce();
    expect(onRemove).toHaveBeenCalledOnce();
  });
});
