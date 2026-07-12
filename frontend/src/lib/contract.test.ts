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

describe('contract loading', () => {
  it('accepts the checked-in canonical fixture', () => {
    const publicRoot = path.resolve(process.cwd(), '../backend/data/public');
    const read = (relative: string): unknown => JSON.parse(readFileSync(path.join(publicRoot, relative), 'utf8'));
    expect(latestReleaseSchema.safeParse(read('latest.json')).error?.issues).toBeUndefined();
    expect(releaseIndexSchema.safeParse(read('releases/20260711-001/index.json')).error?.issues).toBeUndefined();
    expect(searchIndexSchema.safeParse(read('releases/20260711-001/search-index.json')).error?.issues).toBeUndefined();
    expect(tagIndexSchema.safeParse(read('releases/20260711-001/tag-index.json')).error?.issues).toBeUndefined();
    expect(taxonomySchema.safeParse(read('releases/20260711-001/tag-taxonomy.json')).error?.issues).toBeUndefined();
    expect(aliasSchema.safeParse(read('releases/20260711-001/tag-alias-index.json')).error?.issues).toBeUndefined();
    expect(videoDetailSchema.safeParse(read('releases/20260711-001/videos/rY4A7Lxk12Q.json')).error?.issues).toBeUndefined();
  });
  it('distinguishes not found from valid empty data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 404 })));
    await expect(getJson('/missing', z.object({}).strict())).rejects.toMatchObject({ kind: 'not_found' });

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"items":[]}', { status: 200 })));
    await expect(getJson('/empty', z.object({ items: z.array(z.string()) }).strict())).resolves.toEqual({ items: [] });
  });

  it('rejects schema drift instead of returning typed invalid data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"count":"wrong"}', { status: 200 })));
    await expect(getJson('/schema', z.object({ count: z.number() }).strict())).rejects.toMatchObject({ kind: 'schema' });
  });

  it('classifies server errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })));
    await expect(getJson('/server', z.object({}))).rejects.toMatchObject({ kind: 'server', status: 503 });
  });

  it('accepts a containment release without tag contracts', () => {
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

    expect(latestReleaseSchema.safeParse(latest).success).toBe(true);
    expect(releaseIndexSchema.safeParse(index).success).toBe(true);
  });
});
