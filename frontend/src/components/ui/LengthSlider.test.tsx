import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LengthSlider } from './LengthSlider';

describe('LengthSlider', () => {
  // このテストケースの公開契約を検証する。
  it('下限が上限を超えないrangeを通知する', () => {
    // 1. 初期化
    const onChange = vi.fn();
    const { getByRole } = render(<LengthSlider max={60} min={30} onChange={onChange} />);

    // 2. テストの実行
    fireEvent.change(getByRole('slider', { name: '長さの下限' }), { target: { value: '90' } });

    // 3. アサーション
    expect(onChange).toHaveBeenCalledWith({ min: 60, max: 60 });
  });

  // このテストケースの公開契約を検証する。
  it('native range keyboard操作とaria-valuetextを利用できる', () => {
    // 1. 初期化
    const { container } = render(<LengthSlider max={300} min={15} onChange={vi.fn()} />);

    // 2. テストの実行
    const lower = container.querySelector<HTMLInputElement>('[aria-label="長さの下限"]')!;

    // 3. アサーション
    expect(lower.getAttribute('step')).toBe('15');
    expect(lower.getAttribute('aria-valuetext')).toBe('0h15m');
    expect(container.querySelectorAll('.dio-length-slider__thumb')).toHaveLength(2);
    expect(container.querySelector('.dio-length-slider__inputs')).toBeTruthy();
  });
});
