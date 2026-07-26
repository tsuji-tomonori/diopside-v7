import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  // このテストケースの公開契約を検証する。
  it('件数なしと未作成をpropsで区別して見出しと次の行動を表示する', () => {
    // 1. 初期化
    const { getByRole, rerender } = render(
      <EmptyState title="検索結果は0件です"><a href="/search">条件を変更する</a></EmptyState>,
    );

    // 2. テストの実行
    rerender(
      <EmptyState title="保存した検索は未作成です"><a href="/search">検索を作成する</a></EmptyState>,
    );

    // 3. アサーション
    expect(getByRole('heading', { name: '保存した検索は未作成です' })).toBeTruthy();
    expect(getByRole('link', { name: '検索を作成する' })).toBeTruthy();
  });
});
