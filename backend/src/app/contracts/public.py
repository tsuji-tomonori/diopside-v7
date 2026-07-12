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
    releaseMode: Literal["normal", "compliance_purge", "staging", "blocked"]
    normalizationVersion: str
    indexPath: str
    searchIndexPath: str
    tagTaxonomyPath: str
    tagIndexPath: str
    tagAliasIndexPath: str
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
    tagIds: list[str]
    provenance: Provenance
    coverage: Coverage

    @model_validator(mode="after")
    def tag_ids_are_unique(self) -> VideoIndexItem:
        if len(self.tagIds) != len(set(self.tagIds)):
            raise ValueError("tagIds must be unique per video")
        return self


class ReleaseIndex(StrictModel):
    schemaVersion: str
    releaseId: str
    releaseMode: Literal["normal", "compliance_purge", "staging", "blocked"]
    generatedAt: datetime
    layout: Literal["monolithic"]
    normalizationVersion: str
    taxonomyVersion: str
    aliasVersion: str
    videos: list[VideoIndexItem]

    @model_validator(mode="after")
    def video_ids_are_unique(self) -> ReleaseIndex:
        ids = [video.videoId for video in self.videos]
        if len(ids) != len(set(ids)):
            raise ValueError("videoId must be unique in a release")
        return self
