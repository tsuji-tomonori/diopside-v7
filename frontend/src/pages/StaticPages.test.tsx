import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { PrivacyPage } from './PrivacyPage';
import { TermsPage } from './TermsPage';

describe('静的ページ', () => {
  // このテストケースの公開契約を検証する。
  it('利用規約の本文と外部規約linkを維持する', () => {
    // 1. 初期化
    const { getByRole, getByText } = render(<MemoryRouter><TermsPage /></MemoryRouter>);

    // 2. テストの実行
    const link = getByRole('link', { name: 'YouTube API Services Terms / Developer Policies' });

    // 3. アサーション
    expect(getByText('diopsideは公開YouTubeアーカイブを検索・再訪するための非公式サービスです。')).toBeTruthy();
    expect(link.getAttribute('href')).toContain('developers.google.com');
  });

  // このテストケースの公開契約を検証する。
  it('プライバシー・削除窓口と削除・訂正依頼linkを維持する', () => {
    // 1. 初期化
    const { getByRole, getByText } = render(<MemoryRouter><PrivacyPage /></MemoryRouter>);

    // 2. テストの実行
    const link = getByRole('link', { name: 'GitHub Issueで削除・訂正を依頼' });

    // 3. アサーション
    expect(getByText('削除・問い合わせ窓口')).toBeTruthy();
    expect(link.getAttribute('href')).toContain('/issues/new');
  });
});
