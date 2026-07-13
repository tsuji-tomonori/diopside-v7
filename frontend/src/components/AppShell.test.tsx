import { render } from '@testing-library/react';
import axe from 'axe-core';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AppShell } from './AppShell';

describe('AppShellのアクセシビリティ', () => {
  // landmarkとskip navigationがあり、検出可能な構造違反がないことを検証する。
  it('landmarkとskip navigationを備え、構造違反がない', async () => {
    // 1. 初期化
    const initialEntries = ['/search'];

    // 2. テストの実行
    const { container, getByRole, getByText } = render(
      <MemoryRouter initialEntries={initialEntries}>
        <AppShell><h1>検索</h1></AppShell>
      </MemoryRouter>,
    );
    const result = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false } },
    });

    // 3. アサーション
    expect(getByText('本文へスキップ').getAttribute('href')).toBe('#main-content');
    expect(getByRole('main').id).toBe('main-content');
    expect(getByRole('navigation', { name: 'main navigation' })).toBeTruthy();
    expect(getByRole('navigation', { name: 'mobile navigation' })).toBeTruthy();
    expect(result.violations).toEqual([]);
  });
});
