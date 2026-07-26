import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AppShell } from '@/components/AppShell';
import { NotFoundPage } from './NotFoundPage';

describe('NotFoundPage', () => {
  // このテストケースの公開契約を検証する。
  it('h1、次の導線、shell navigationを維持する', () => {
    // 1. 初期化
    const { getByRole } = render(
      <MemoryRouter>
        <AppShell><NotFoundPage /></AppShell>
      </MemoryRouter>,
    );

    // 2. テストの実行
    const homeLink = getByRole('link', { name: 'ホームへ戻る' });

    // 3. アサーション
    expect(getByRole('heading', { level: 1 }).textContent).toBe('ページが見つかりません');
    expect(homeLink.getAttribute('href')).toBe('/');
    expect(getByRole('navigation', { name: 'main navigation' })).toBeTruthy();
    expect(getByRole('navigation', { name: 'mobile navigation' })).toBeTruthy();
  });
});
