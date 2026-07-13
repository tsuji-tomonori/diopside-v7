import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';


// infrastructure planが正規release pointerを読み取ることを検証する。
test('infrastructure planが正規release pointerを読み取る', () => {
  const latest = JSON.parse(readFileSync('../backend/data/public/latest.json', 'utf8'));

  assert.match(latest.releaseId, /^[A-Za-z0-9._-]+$/);
  assert.equal(latest.releaseMode, 'normal');
  assert.ok(latest.indexPath.startsWith(`data/releases/${latest.releaseId}/`));
});
