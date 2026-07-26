import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { LoadingState } from './LoadingState';

describe('LoadingState', () => {
  // このテストケースの公開契約を検証する。
  it('読み込み状態と寸法を保つplaceholderを公開する', () => {
    // 1. 初期化
    const { container, getByRole } = render(<LoadingState label="データを読込中" />);

    // 2. テストの実行
    const status = getByRole('status');

    // 3. アサーション
    expect(status.textContent).toContain('データを読込中');
    expect(container.querySelectorAll('.dio-loading-state i')).toHaveLength(3);
  });
});
