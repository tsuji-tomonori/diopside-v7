import { z } from 'zod';

import {
  aliasSchema,
  latestReleaseSchema,
  releaseIndexSchema,
  searchIndexSchema,
  tagIndexSchema,
  taxonomySchema,
  videoDetailSchema,
} from '@/lib/schemas';
import type {
  ArtifactType,
  LatestRelease,
  ReleaseIndex,
  SearchIndex,
  TagAliasIndex,
  TagIndex,
  TagTaxonomy,
  VideoDetail,
} from '@/types';

const base = '/data';

export type ContractErrorKind = 'not_found' | 'timeout' | 'server' | 'network' | 'schema' | 'release_mismatch';

export class ContractError extends Error {
  constructor(
    public readonly kind: ContractErrorKind,
    message: string,
    public readonly path: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ContractError';
  }
}

export async function getJson<T>(path: string, schema: z.ZodType<T>, timeoutMs = 10_000): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, { signal: controller.signal });
    if (!response.ok) {
      const kind = response.status === 404 ? 'not_found' : response.status >= 500 ? 'server' : 'network';
      throw new ContractError(kind, `failed to load ${path}: HTTP ${response.status}`, path, response.status);
    }
    const value: unknown = await response.json();
    const parsed = schema.safeParse(value);
    if (!parsed.success) {
      throw new ContractError('schema', `invalid contract schema: ${path}`, path);
    }
    return parsed.data;
  } catch (error) {
    if (error instanceof ContractError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ContractError('timeout', `contract request timed out: ${path}`, path);
    }
    throw new ContractError('network', `contract request failed: ${path}`, path);
  } finally {
    window.clearTimeout(timeout);
  }
}

export function loadLatest(): Promise<LatestRelease> {
  return getJson(`${base}/latest.json`, latestReleaseSchema) as Promise<LatestRelease>;
}

export function loadReleaseIndex(releaseId: string): Promise<ReleaseIndex> {
  return loadJoined(`${base}/releases/${releaseId}/index.json`, releaseIndexSchema, releaseId) as Promise<ReleaseIndex>;
}

export function loadSearchIndex(releaseId: string): Promise<SearchIndex> {
  return loadJoined(`${base}/releases/${releaseId}/search-index.json`, searchIndexSchema, releaseId) as Promise<SearchIndex>;
}

export async function loadTags(releaseId: string): Promise<{ taxonomy: TagTaxonomy; index: TagIndex; alias: TagAliasIndex }> {
  const [taxonomy, index, alias] = await Promise.all([
    loadJoined(`${base}/releases/${releaseId}/tag-taxonomy.json`, taxonomySchema, releaseId),
    loadJoined(`${base}/releases/${releaseId}/tag-index.json`, tagIndexSchema, releaseId),
    loadJoined(`${base}/releases/${releaseId}/tag-alias-index.json`, aliasSchema, releaseId),
  ]);
  return { taxonomy: taxonomy as TagTaxonomy, index: index as TagIndex, alias: alias as TagAliasIndex };
}

async function loadJoined<T extends { releaseId: string }>(path: string, schema: z.ZodType<T>, releaseId: string): Promise<T> {
  const value = await getJson(path, schema);
  if (value.releaseId !== releaseId) {
    throw new ContractError('release_mismatch', `releaseId mismatch: ${path}`, path);
  }
  return value;
}

export function makeVideoPath(releaseId: string, videoId: string): string {
  return `${base}/releases/${releaseId}/videos/${videoId}.json`;
}

export function loadVideoDetail(releaseId: string, videoId: string): Promise<VideoDetail> {
  return getJson(makeVideoPath(releaseId, videoId), videoDetailSchema) as Promise<VideoDetail>;
}

export function includesArtifactType(flags: { chat: boolean; comments: boolean; timestamps: boolean; wordcloud: boolean }, active: ArtifactType[]): boolean {
  return active.some((item) => flags[item]);
}
