import { z } from 'zod';

const releaseMode = z.enum(['normal', 'compliance_purge']);
const timestamp = z.iso.datetime({ offset: true });
const artifactFlags = z.object({
  chat: z.boolean(),
  comments: z.boolean(),
  timestamps: z.boolean(),
  wordcloudChat: z.boolean(),
  wordcloudComments: z.boolean(),
  wordcloudBoth: z.boolean(),
}).strict();
const thumbnail = z.object({ url: z.string().url(), width: z.number().int().positive(), height: z.number().int().positive() }).strict();
const coverage = z.object({
  coverageStart: timestamp,
  coverageEnd: timestamp,
  completeFromStart: z.boolean(),
  sourceUpdatedAt: timestamp,
}).strict();
const provenance = z.object({
  source: z.string().optional(),
  titleSource: z.string().optional(),
  publishedSource: z.string().optional(),
  generatedBy: z.string().optional(),
}).strict();

export const latestReleaseSchema = z.object({
  schemaVersion: z.string().min(1),
  releaseId: z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/),
  generatedAt: timestamp,
  releaseMode,
  normalizationVersion: z.string().min(1),
  indexPath: z.string().min(1),
  searchIndexPath: z.string().min(1),
  tagTaxonomyPath: z.string().min(1),
  tagIndexPath: z.string().min(1),
  tagAliasIndexPath: z.string().min(1),
  artifactHashes: z.record(z.string(), z.string()).optional(),
}).strict();

export const videoIndexSchema = z.object({
  videoId: z.string().min(1),
  title: z.string().min(1),
  publishedAt: timestamp,
  duration: z.string().startsWith('PT'),
  durationSec: z.number().int().nonnegative(),
  thumbnail,
  sourceKind: z.string().min(1),
  metadataStatus: z.string().min(1),
  sourceUpdatedAt: timestamp,
  artifactFlags,
  tagIds: z.array(z.string()),
  provenance,
  chat: z.object({ totalCount: z.number().int().nonnegative() }).strict().optional(),
  comments: z.object({ totalCount: z.number().int().nonnegative() }).strict().optional(),
  coverage: coverage.optional(),
}).strict();

export const releaseIndexSchema = z.object({
  schemaVersion: z.string(), releaseId: z.string(), releaseMode, generatedAt: timestamp,
  layout: z.string(), normalizationVersion: z.string(), taxonomyVersion: z.string(), aliasVersion: z.string(),
  videos: z.array(videoIndexSchema),
}).strict();

const searchVideoSchema = z.object({
  videoId: z.string(), titleTokens: z.array(z.string()), sourceKind: z.string(), metadataStatus: z.string(),
  publishedAt: timestamp, publishedDate: z.string(), durationSec: z.number().int().nonnegative().nullable(),
  artifactFlags, tagIds: z.array(z.string()),
}).strict();
export const searchIndexSchema = z.object({
  schemaVersion: z.string(), releaseId: z.string(), releaseMode, generatedAt: timestamp,
  layout: z.string(), normalizationVersion: z.string(), videos: z.array(searchVideoSchema),
}).strict();

const tagInfoSchema = z.object({
  tagId: z.string(), categoryId: z.string(), subcategoryId: z.string(), displayName: z.string(),
  count: z.number().int().nonnegative(), videoIds: z.array(z.string()),
}).strict();
export const tagIndexSchema = z.object({
  schemaVersion: z.string(), releaseId: z.string(), generatedAt: timestamp, tags: z.array(tagInfoSchema),
}).strict();
export const taxonomySchema = z.object({
  schemaVersion: z.string(), releaseId: z.string(), generatedAt: timestamp,
  categories: z.array(z.object({
    categoryId: z.string(), label: z.string(),
    subcategories: z.array(z.object({ subcategoryId: z.string(), label: z.string(), tagIds: z.array(z.string()) }).strict()),
  }).strict()),
}).strict();
export const aliasSchema = z.object({
  schemaVersion: z.string(), releaseId: z.string(), generatedAt: timestamp,
  aliases: z.record(z.string(), z.string()),
}).strict();

const artifactBase = z.object({
  status: z.string(), source: z.string(), generatedAt: timestamp, coverage: coverage.optional(),
});
export const videoDetailSchema = videoIndexSchema.extend({
  chat: artifactBase.extend({ totalCount: z.number().int().nonnegative() }).strict().optional(),
  comments: artifactBase.extend({ totalCount: z.number().int().nonnegative() }).strict().optional(),
  timestamps: artifactBase.extend({
    items: z.array(z.object({ atSec: z.number().nonnegative(), label: z.string(), confidence: z.number().optional() }).strict()),
  }).strict().optional(),
  wordcloud: artifactBase.extend({
    topTerms: z.array(z.object({ term: z.string(), count: z.number().int().positive() }).strict()).optional(),
    svgPath: z.string(), jsonPath: z.string(),
  }).strict().optional(),
}).strict();
