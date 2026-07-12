import { render } from '@testing-library/react';
import axe from 'axe-core';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AppShell } from './AppShell';

describe('AppShell accessibility', () => {
  it('has landmarks, skip navigation, and no detectable structural violations', async () => {
    const { container, getByRole, getByText } = render(
      <MemoryRouter initialEntries={['/search']}>
        <AppShell><h1>検索</h1></AppShell>
      </MemoryRouter>,
    );

    expect(getByText('本文へスキップ').getAttribute('href')).toBe('#main-content');
    expect(getByRole('main').id).toBe('main-content');
    expect(getByRole('navigation', { name: 'main navigation' })).toBeTruthy();
    expect(getByRole('navigation', { name: 'mobile navigation' })).toBeTruthy();

    const result = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false } },
    });
    expect(result.violations).toEqual([]);
  });
});
