import { fireEvent, render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RangeCalendar } from './RangeCalendar';

describe('RangeCalendar', () => {
  // このテストケースの公開契約を検証する。
  it('grid rowとroving tabindexを提供する', () => {
    // 1. 初期化
    const { getByRole, getAllByRole } = render(<RangeCalendar onChange={vi.fn()} />);

    // 2. テストの実行
    const cells = getAllByRole('gridcell');

    // 3. アサーション
    expect(getByRole('grid')).toBeTruthy();
    expect(getAllByRole('row').length).toBe(6);
    expect(cells.filter((cell) => cell.getAttribute('tabindex') === '0')).toHaveLength(1);
  });

  // このテストケースの公開契約を検証する。
  it('2回の選択と逆順選択を正規化して通知する', () => {
    // 1. 初期化
    const onChange = vi.fn();
    const { container } = render(
      <RangeCalendar from="2020-01-10" onChange={onChange} to={undefined} />,
    );

    // 2. テストの実行
    fireEvent.click(container.querySelector('[data-date="2020-01-05"]')!);
    fireEvent.click(container.querySelector('.dio-calendar__clear')!);

    // 3. アサーション
    expect(onChange).toHaveBeenCalledWith({ from: '2020-01-05', to: '2020-01-10' });
    expect(onChange).toHaveBeenCalledWith({});
  });

  // このテストケースの公開契約を検証する。
  it('未来日をdisabledにし矢印キーで日付focusを移動する', () => {
    // 1. 初期化
    const { getAllByRole } = render(<RangeCalendar onChange={vi.fn()} />);
    const cells = getAllByRole('gridcell') as HTMLButtonElement[];
    const active = cells.find((cell) => cell.tabIndex === 0)!;
    const future = cells.find((cell) => cell.disabled);

    // 2. テストの実行
    fireEvent.keyDown(active, { key: 'ArrowLeft' });

    // 3. アサーション
    expect(future?.disabled).toBe(true);
    expect(active.getAttribute('aria-selected')).toBe('false');
  });
});
