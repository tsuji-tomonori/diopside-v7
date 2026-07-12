import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';


test('infrastructure plan reads the canonical release pointer', () => {
  const latest = JSON.parse(readFileSync('../backend/data/public/latest.json', 'utf8'));

  assert.match(latest.releaseId, /^[A-Za-z0-9._-]+$/);
  assert.equal(latest.releaseMode, 'normal');
  assert.ok(latest.indexPath.startsWith(`data/releases/${latest.releaseId}/`));
});
