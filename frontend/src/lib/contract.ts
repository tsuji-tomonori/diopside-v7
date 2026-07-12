import {
  ArtifactType,
  LatestRelease,
  ReleaseIndex,
  TagIndex,
  SearchIndex,
  TagAliasIndex,
  TagTaxonomy,
  VideoDetail,
} from '@/types';

const base = '/data';

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`failed to load ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function loadLatest(): Promise<LatestRelease> {
  return getJson<LatestRelease>(`${base}/latest.json`);
}

export async function loadReleaseIndex(releaseId: string): Promise<ReleaseIndex> {
  return getJson<ReleaseIndex>(`${base}/releases/${releaseId}/index.json`);
}

export async function loadSearchIndex(releaseId: string): Promise<SearchIndex> {
  return getJson<SearchIndex>(`${base}/releases/${releaseId}/search-index.json`);
}

export async function loadTags(releaseId: string): Promise<{
  taxonomy: TagTaxonomy;
  index: TagIndex;
  alias: TagAliasIndex;
}> {
  return getJson<TagTaxonomy>(
    `${base}/releases/${releaseId}/tag-taxonomy.json`,
  )
    .then(async (taxonomy: TagTaxonomy) => {
      const index = await getJson<TagIndex>(`${base}/releases/${releaseId}/tag-index.json`);
      const alias = await getJson<TagAliasIndex>(`${base}/releases/${releaseId}/tag-alias-index.json`);
      return { taxonomy, index, alias };
    });
}

export function makeVideoPath(releaseId: string, videoId: string): string {
  return `${base}/releases/${releaseId}/videos/${videoId}.json`;
}

export async function loadVideoDetail(releaseId: string, videoId: string): Promise<VideoDetail> {
  return getJson<VideoDetail>(makeVideoPath(releaseId, videoId));
}

export function includesArtifactType(flags: {
  chat: boolean;
  comments: boolean;
  timestamps: boolean;
  wordcloud: boolean;
}, active: ArtifactType[]): boolean {
  return active.some((item) => {
    if (item === 'chat') {
      return flags.chat;
    }
    if (item === 'comments') {
      return flags.comments;
    }
    if (item === 'timestamps') {
      return flags.timestamps;
    }
    if (item === 'wordcloud') {
      return flags.wordcloud;
    }
    return false;
  });
}
