import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from 'zod';

import { getJson } from './contract';

afterEach(() => vi.unstubAllGlobals());

describe('contract loading', () => {
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
});
