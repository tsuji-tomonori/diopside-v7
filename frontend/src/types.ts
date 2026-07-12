export type ReleaseMode = 'normal' | 'purge' | 'staging' | 'blocked' | string;
export type ArtifactType = 'chat' | 'comments' | 'timestamps' | 'wordcloud';

export interface Thumbnail {
  url: string;
  width: number;
  height: number;
}

export interface ArtifactFlags {
  chat: boolean;
  comments: boolean;
  timestamps: boolean;
  wordcloud: boolean;
}

export interface VideoIndex {
  videoId: string;
  title: string;
  publishedAt: string;
  duration: string;
  durationSec: number;
  thumbnail: Thumbnail;
  sourceKind: string;
  metadataStatus: string;
  sourceUpdatedAt: string;
  artifactFlags: ArtifactFlags;
  tagIds: string[];
  provenance: {
    source?: string;
    titleSource?: string;
    publishedSource?: string;
    generatedBy?: string;
  };
  chat?: { totalCount: number };
  comments?: { totalCount: number };
  coverage?: {
    coverageStart: string;
    coverageEnd: string;
    completeFromStart: boolean;
    sourceUpdatedAt: string;
  };
}

export interface SearchVideoIndex {
  videoId: string;
  titleTokens: string[];
  sourceKind: string;
  metadataStatus: string;
  publishedAt: string;
  publishedDate: string;
  durationSec: number | null;
  artifactFlags: ArtifactFlags;
  tagIds: string[];
}

export interface TagInfo {
  tagId: string;
  categoryId: string;
  subcategoryId: string;
  displayName: string;
  count: number;
  videoIds: string[];
}

export interface TagIndex {
  schemaVersion: string;
  releaseId: string;
  generatedAt: string;
  tags: TagInfo[];
}

export interface TagTaxonomy {
  schemaVersion: string;
  releaseId: string;
  generatedAt: string;
  categories: {
    categoryId: string;
    label: string;
    subcategories: {
      subcategoryId: string;
      label: string;
      tagIds: string[];
    }[];
  }[];
}

export interface TagAliasIndex {
  schemaVersion: string;
  releaseId: string;
  generatedAt: string;
  aliases: Record<string, string>;
}

export interface LatestRelease {
  schemaVersion: string;
  releaseId: string;
  generatedAt: string;
  releaseMode: ReleaseMode;
  normalizationVersion: string;
  indexPath: string;
  searchIndexPath: string;
  tagTaxonomyPath: string;
  tagIndexPath: string;
  tagAliasIndexPath: string;
  artifactHashes?: Record<string, string>;
}

export interface ReleaseIndex {
  schemaVersion: string;
  releaseId: string;
  releaseMode: ReleaseMode;
  generatedAt: string;
  layout: string;
  normalizationVersion: string;
  taxonomyVersion: string;
  aliasVersion: string;
  videos: VideoIndex[];
}

export interface SearchIndex {
  schemaVersion: string;
  releaseId: string;
  releaseMode: string;
  generatedAt: string;
  layout: string;
  normalizationVersion: string;
  videos: SearchVideoIndex[];
}

export interface VideoDetailTimestampItem {
  atSec: number;
  label: string;
  confidence?: number;
}

export interface VideoDetailArtifact {
  status: string;
  source: string;
  generatedAt: string;
  coverage?: {
    coverageStart: string;
    coverageEnd: string;
    completeFromStart: boolean;
    sourceUpdatedAt: string;
  };
}

export interface VideoDetailChat extends VideoDetailArtifact {
  totalCount: number;
}

export interface VideoDetailComments extends VideoDetailArtifact {
  totalCount: number;
}

export interface VideoDetailTimestamps extends VideoDetailArtifact {
  items: VideoDetailTimestampItem[];
}

export interface VideoDetailWordcloud extends VideoDetailArtifact {
  topTerms?: { term: string; count: number }[];
  svgPath: string;
  jsonPath: string;
}

export interface VideoDetail extends VideoIndex {
  chat?: VideoDetailChat;
  comments?: VideoDetailComments;
  timestamps?: VideoDetailTimestamps;
  wordcloud?: VideoDetailWordcloud;
}

export interface SearchCondition {
  q: string;
  tags: string[];
  lmin?: number;
  lmax?: number;
  from?: string;
  to?: string;
  artifacts: ArtifactType[];
  sort: 'newest' | 'oldest' | 'longest' | 'mostChat';
}

export interface LocalLibrary {
  schemaVersion: number;
  updatedAt: string;
  items: string[];
}

export interface RecentSearchItem {
  schemaVersion: number;
  createdAt: string;
  condition: SearchCondition;
}
