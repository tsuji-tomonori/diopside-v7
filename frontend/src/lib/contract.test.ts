import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from 'zod';
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { getJson } from './contract';
import {
  aliasSchema,
  latestReleaseSchema,
  releaseIndexSchema,
  searchIndexSchema,
  tagIndexSchema,
  taxonomySchema,
  videoDetailSchema,
} from './schemas';

afterEach(() => vi.unstubAllGlobals());

describe('契約の読み込み', () => {
  // リポジトリに保存した正規fixtureが全schemaへ適合することを検証する。
  it('保存済みの正規fixtureを受理する', () => {
    // 1. 初期化
    const publicRoot = path.resolve(process.cwd(), '../backend/data/public');
    const read = (relative: string): unknown => JSON.parse(readFileSync(path.join(publicRoot, relative), 'utf8'));

    // 2. テストの実行
    const results = [
      latestReleaseSchema.safeParse(read('latest.json')),
      releaseIndexSchema.safeParse(read('releases/20260711-001/index.json')),
      searchIndexSchema.safeParse(read('releases/20260711-001/search-index.json')),
      tagIndexSchema.safeParse(read('releases/20260711-001/tag-index.json')),
      taxonomySchema.safeParse(read('releases/20260711-001/tag-taxonomy.json')),
      aliasSchema.safeParse(read('releases/20260711-001/tag-alias-index.json')),
      videoDetailSchema.safeParse(read('releases/20260711-001/videos/rY4A7Lxk12Q.json')),
    ];

    // 3. アサーション
    expect(results.every((result) => result.success)).toBe(true);
  });
  // データ欠落と有効な空データを区別することを検証する。
  it('データ欠落と有効な空データを区別する', async () => {
    // 1. 初期化
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('{}', { status: 404 }))
      .mockResolvedValueOnce(new Response('{"items":[]}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    // 2. テストの実行
    const missing = getJson('/missing', z.object({}).strict());
    const empty = getJson('/empty', z.object({ items: z.array(z.string()) }).strict());

    // 3. アサーション
    await expect(missing).rejects.toMatchObject({ kind: 'not_found' });
    await expect(empty).resolves.toEqual({ items: [] });
  });

  // 不正データを型付き値として返さず、schema差異を拒否することを検証する。
  it('不正データを返さずschema差異を拒否する', async () => {
    // 1. 初期化
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"count":"wrong"}', { status: 200 })));

    // 2. テストの実行
    const request = getJson('/schema', z.object({ count: z.number() }).strict());

    // 3. アサーション
    await expect(request).rejects.toMatchObject({ kind: 'schema' });
  });

  // サーバーエラーを専用種別へ分類することを検証する。
  it('サーバーエラーを分類する', async () => {
    // 1. 初期化
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })));

    // 2. テストの実行
    const request = getJson('/server', z.object({}));

    // 3. アサーション
    await expect(request).rejects.toMatchObject({ kind: 'server', status: 503 });
  });

  // タグ契約を持たない規約対応削除リリースを受理することを検証する。
  it('タグ契約なしの規約対応削除リリースを受理する', () => {
    // 1. 初期化
    const publicRoot = path.resolve(process.cwd(), '../backend/data/public');
    const latest = JSON.parse(readFileSync(path.join(publicRoot, 'latest.json'), 'utf8'));
    latest.releaseMode = 'compliance_purge';
    delete latest.tagTaxonomyPath;
    delete latest.tagIndexPath;
    delete latest.tagAliasIndexPath;
    latest.purgeBaseReleaseId = 'base';
    latest.purgeBaseManifestSha256 = 'sha256:base';
    latest.purgeTrigger = 'deletion:test';

    const index = JSON.parse(
      readFileSync(path.join(publicRoot, 'releases/20260711-001/index.json'), 'utf8'),
    );
    index.releaseMode = 'compliance_purge';
    delete index.taxonomyVersion;
    delete index.aliasVersion;
    for (const video of index.videos) delete video.tagIds;

    // 2. テストの実行
    const latestResult = latestReleaseSchema.safeParse(latest);
    const indexResult = releaseIndexSchema.safeParse(index);

    // 3. アサーション
    expect(latestResult.success).toBe(true);
    expect(indexResult.success).toBe(true);
  });
});
