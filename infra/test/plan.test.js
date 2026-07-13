import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';


// infrastructure planが正規release pointerを読み取ることを検証する。
test('infrastructure planが正規release pointerを読み取る', () => {
  // 1. 初期化
  const latestPath = '../backend/data/public/latest.json';

  // 2. テストの実行
  const latest = JSON.parse(readFileSync(latestPath, 'utf8'));

  // 3. アサーション
  assert.match(latest.releaseId, /^[A-Za-z0-9._-]+$/);
  assert.equal(latest.releaseMode, 'normal');
  assert.ok(latest.indexPath.startsWith(`data/releases/${latest.releaseId}/`));
});
