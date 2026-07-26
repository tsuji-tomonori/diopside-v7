import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Icon } from './Icon';

describe('Icon', () => {
  // このテストケースの公開契約を検証する。
  it('装飾iconをaria-hiddenにしaccessible nameを持たせない', () => {
    // 1. 初期化
    const { container } = render(<Icon name="search" />);

    // 2. テストの実行
    const icon = container.querySelector('svg')!;

    // 3. アサーション
    expect(icon.getAttribute('aria-hidden')).toBe('true');
    expect(icon.querySelector('title')).toBeNull();
  });

  for (const size of [16, 20, 24] as const) {
    // このテストケースの公開契約を検証する。
    it('sizeを寸法とcurrentColorへ反映する', () => {
    // 1. 初期化
    const { container } = render(<Icon name="star_filled" size={size} />);

    // 2. テストの実行
    const icon = container.querySelector('svg')!;

    // 3. アサーション
    expect(icon.getAttribute('width')).toBe(String(size));
    expect(icon.getAttribute('height')).toBe(String(size));
    expect(icon.getAttribute('fill')).toBe('currentColor');
    expect(icon.getAttribute('stroke')).toBe('currentColor');
    });
  }
});
