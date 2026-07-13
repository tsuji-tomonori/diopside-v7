from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LatestRelease(StrictModel):
    schemaVersion: str
    releaseId: str = Field(pattern=r"^[A-Za-z0-9._-]+$")
    generatedAt: datetime
    releaseMode: Literal["normal", "compliance_purge"]
    normalizationVersion: str
    indexPath: str
    searchIndexPath: str
    tagTaxonomyPath: str | None = None
    tagIndexPath: str | None = None
    tagAliasIndexPath: str | None = None
    purgeBaseReleaseId: str | None = None
    purgeBaseManifestSha256: str | None = None
    purgeTrigger: str | None = None
    artifactHashes: dict[str, str]


class Thumbnail(StrictModel):
    url: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ArtifactFlags(StrictModel):
    chat: bool
    comments: bool
    timestamps: bool
    wordcloudChat: bool
    wordcloudComments: bool
    wordcloudBoth: bool


class Provenance(StrictModel):
    titleSource: str
    publishedSource: str


class Coverage(StrictModel):
    coverageStart: datetime
    coverageEnd: datetime
    completeFromStart: bool
    sourceUpdatedAt: datetime


class VideoIndexItem(StrictModel):
    videoId: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publishedAt: datetime
    durationSec: int = Field(ge=0)
    duration: str = Field(pattern=r"^PT")
    thumbnail: Thumbnail
    sourceKind: str
    metadataStatus: str
    sourceUpdatedAt: datetime
    artifactFlags: ArtifactFlags
    tagIds: list[str] | None = None
    provenance: Provenance
    coverage: Coverage

    @model_validator(mode="after")
    def tag_ids_are_unique(self) -> VideoIndexItem:
        if self.tagIds is not None and len(self.tagIds) != len(set(self.tagIds)):
            raise ValueError("tagIds must be unique per video")
        return self


class ReleaseIndex(StrictModel):
    schemaVersion: str
    releaseId: str
    releaseMode: Literal["normal", "compliance_purge"]
    generatedAt: datetime
    layout: Literal["monolithic"]
    normalizationVersion: str
    taxonomyVersion: str | None = None
    aliasVersion: str | None = None
    purgeBaseReleaseId: str | None = None
    purgeBaseManifestSha256: str | None = None
    purgeTrigger: str | None = None
    videos: list[VideoIndexItem]

    @model_validator(mode="after")
    def video_ids_are_unique(self) -> ReleaseIndex:
        ids = [video.videoId for video in self.videos]
        if len(ids) != len(set(ids)):
            raise ValueError("videoId must be unique in a release")
        if self.releaseMode == "normal":
            if not self.taxonomyVersion or not self.aliasVersion:
                raise ValueError("normal release requires taxonomy and alias versions")
            if any(video.tagIds is None for video in self.videos):
                raise ValueError("normal release requires tagIds")
        elif (
            self.taxonomyVersion
            or self.aliasVersion
            or any(video.tagIds is not None for video in self.videos)
        ):
            raise ValueError("compliance purge forbids tags")
        if self.releaseMode == "compliance_purge" and not all(
            (self.purgeBaseReleaseId, self.purgeBaseManifestSha256, self.purgeTrigger)
        ):
            raise ValueError("compliance purge requires base and trigger")
        return self
