from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile


def read_object(archive: ZipFile, name: str) -> dict[str, Any]:
    raw: object = json.loads(archive.read(name))
    if not isinstance(raw, dict):
        raise ValueError(f"{name} must contain an object")
    return cast(dict[str, Any], raw)


def rows(document: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = document.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    items = cast(list[object], value)
    if not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{key} items must be objects")
    return cast(list[dict[str, Any]], items)


def assignment_keys(videos: list[dict[str, Any]], field: str) -> set[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for video in videos:
        video_id = str(video.get("videoId", ""))
        for item in rows(video, field):
            result.add((video_id, str(item.get("field", "")), str(item.get("tag", ""))))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="受領した意味review投影を検証する")
    parser.add_argument("--tags-zip", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    source_names = [
        "tags/spoken_references_v2.json",
        "tags/collaborator_archive_review_v2.json",
        "tags/group_alias_archive_review_v2.json",
        "tags/video_tags_v2.json",
        "tags/collaboration_video_tags_v2.json",
    ]
    with ZipFile(args.tags_zip) as archive:
        documents = {name: read_object(archive, name) for name in source_names}
        source_hashes = {
            name: hashlib.sha256(archive.read(name)).hexdigest() for name in source_names
        }

    spoken = documents["tags/spoken_references_v2.json"]
    spoken_videos = rows(spoken, "videos")
    accepted = [item for video in spoken_videos for item in rows(video, "acceptedAssignments")]
    review = [item for video in spoken_videos for item in rows(video, "reviewCandidates")]
    if len(accepted) != spoken.get("acceptedAssignmentCount"):
        raise ValueError("spoken accepted count mismatch")
    if len(review) != spoken.get("reviewCandidateCount"):
        raise ValueError("spoken review count mismatch")
    if any(item.get("status") != "accepted" for item in accepted):
        raise ValueError("spoken accepted assignment has invalid status")
    if any(item.get("status") != "review" for item in review):
        raise ValueError("spoken review candidate has invalid status")
    if any(not item.get("evidenceItems") for item in [*accepted, *review]):
        raise ValueError("spoken semantic item lacks evidence")
    overlap = assignment_keys(spoken_videos, "acceptedAssignments") & assignment_keys(
        spoken_videos, "reviewCandidates"
    )
    if overlap:
        raise ValueError(f"spoken accepted/review overlap: {len(overlap)}")

    own = rows(documents["tags/video_tags_v2.json"], "videos")
    external = rows(documents["tags/collaboration_video_tags_v2.json"], "videos")
    public_videos = {str(video.get("videoId")): video for video in [*own, *external]}

    collaborator = documents["tags/collaborator_archive_review_v2.json"]
    collaborator_decisions = rows(collaborator, "decisions")
    collaborator_accepted = [
        item for item in collaborator_decisions if item.get("status") == "accepted"
    ]
    collaborator_rejected = [
        item for item in collaborator_decisions if item.get("status") == "rejected"
    ]
    if len(collaborator_accepted) != collaborator.get("acceptedCount"):
        raise ValueError("collaborator accepted count mismatch")
    if len(collaborator_rejected) != collaborator.get("rejectedCount"):
        raise ValueError("collaborator rejected count mismatch")
    missing_accepted = [
        item["videoId"]
        for item in collaborator_accepted
        if str(item["videoId"]) not in public_videos
    ]
    leaked_rejected = [
        item["videoId"] for item in collaborator_rejected if str(item["videoId"]) in public_videos
    ]
    if missing_accepted or leaked_rejected:
        raise ValueError("collaborator projection mismatch")

    groups = documents["tags/group_alias_archive_review_v2.json"]
    group_decisions = rows(groups, "decisions")
    group_accepted = [item for item in group_decisions if item.get("status") == "accepted"]
    group_rejected = [item for item in group_decisions if item.get("status") == "rejected"]
    if len(group_accepted) != groups.get("acceptedCount"):
        raise ValueError("group accepted count mismatch")
    if len(group_rejected) != groups.get("rejectedCount"):
        raise ValueError("group rejected count mismatch")
    for decision in group_accepted:
        video = public_videos.get(str(decision["videoId"]))
        if video is None:
            raise ValueError("accepted group video missing from public tags")
        public_units = {
            str(item.get("tag"))
            for item in rows(video, "tags")
            if item.get("subcategoryId") == "unit"
        }
        expected_units = {str(item.get("group")) for item in rows(decision, "matchedGroups")}
        if not public_units.intersection(expected_units):
            raise ValueError("accepted group lacks matching public unit")
    if any(str(item["videoId"]) in public_videos for item in group_rejected):
        raise ValueError("rejected group candidate leaked into public tags")

    report: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "generatedAt": "2026-07-13T00:00:00Z",
        "sourceHashes": source_hashes,
        "spoken": {
            "videoCount": len(spoken_videos),
            "acceptedAssignmentCount": len(accepted),
            "reviewCandidateCount": len(review),
            "acceptedReviewOverlapCount": len(overlap),
        },
        "externalCollaborators": {
            "acceptedCount": len(collaborator_accepted),
            "rejectedCount": len(collaborator_rejected),
            "missingAcceptedCount": len(missing_accepted),
            "leakedRejectedCount": len(leaked_rejected),
        },
        "groupAliases": {
            "acceptedCount": len(group_accepted),
            "rejectedCount": len(group_rejected),
            "acceptedProjectionCount": len(group_accepted),
            "leakedRejectedCount": 0,
        },
    }
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    report["semanticFingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
