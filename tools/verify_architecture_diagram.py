#!/usr/bin/env python3
"""編集可能なAWS物理構成SVGの構造、内容、接続線を検証する。"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SERVICES = {
    "Amazon CloudFront",
    "Amazon Simple Storage Service (Amazon S3)",
    "Amazon EventBridge",
    "AWS Lambda",
    "Amazon Simple Queue Service (Amazon SQS)",
    "Amazon DynamoDB",
    "AWS Secrets Manager",
    "Amazon CloudWatch",
    "AWS X-Ray",
    "Amazon Simple Notification Service (Amazon SNS)",
    "AWS Budgets",
    "AWS Cost Explorer",
    "AWS Identity and Access Management (IAM)",
    "AWS Security Token Service (AWS STS)",
    "AWS Command Line Interface (AWS CLI)",
}

REQUIRED_RESOURCES = {
    "Distribution",
    "PublicData",
    "Raw",
    "Processed",
    "Configuration",
    "AccessLogs",
    "ControlTable",
    "YouTubeApiKey",
    "PseudonymSecret",
    "JobQueue",
    "ExportQueue",
    "JobDeadLetterQueue",
    "Collector",
    "Processor",
    "Exporter",
    "OperationsDashboard",
    "OperationsAlerts",
    "MonthlyCostBudget",
    "AdminRole",
}

FORBIDDEN_TERMS = {
    "Nuxt",
    "API Gateway",
    "FastAPI",
    "Aurora",
    "DSQL",
    "CloudFront Functions",
    "EventBridge Scheduler",
}


@dataclass(frozen=True)
class Box:
    node_id: str
    x: float
    y: float
    width: float
    height: float

    def contains(self, point: tuple[float, float]) -> bool:
        x, y = point
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


@dataclass(frozen=True)
class Connector:
    edge_id: str
    source: str
    target: str
    points: tuple[tuple[float, float], ...]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_box(element: ET.Element) -> Box:
    values = [float(value) for value in element.attrib["data-bounds"].split(",")]
    if len(values) != 4:
        raise ValueError(f"invalid bounds for {element.attrib.get('data-node')}")
    return Box(element.attrib["data-node"], *values)


def parse_connector(element: ET.Element) -> Connector:
    points: list[tuple[float, float]] = []
    for token in element.attrib["points"].split():
        values = token.split(",")
        if len(values) != 2:
            raise ValueError(f"invalid point for {element.attrib.get('data-edge')}: {token}")
        points.append((float(values[0]), float(values[1])))
    if len(points) < 2:
        raise ValueError(f"connector has fewer than two points: {element.attrib.get('data-edge')}")
    return Connector(
        element.attrib["data-edge"],
        element.attrib["data-source"],
        element.attrib["data-target"],
        tuple(points),
    )


def segments(connector: Connector) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    return list(zip(connector.points, connector.points[1:], strict=False))


def segment_hits_box(segment: tuple[tuple[float, float], tuple[float, float]], box: Box) -> bool:
    (x1, y1), (x2, y2) = segment
    if x1 == x2:
        lo, hi = sorted((y1, y2))
        return box.x < x1 < box.x + box.width and max(lo, box.y) < min(hi, box.y + box.height)
    if y1 == y2:
        lo, hi = sorted((x1, x2))
        return box.y < y1 < box.y + box.height and max(lo, box.x) < min(hi, box.x + box.width)
    raise ValueError(f"connector segment is not orthogonal: {segment}")


def segment_intersection(
    first: tuple[tuple[float, float], tuple[float, float]],
    second: tuple[tuple[float, float], tuple[float, float]],
) -> str | None:
    first_vertical = first[0][0] == first[1][0]
    second_vertical = second[0][0] == second[1][0]
    if first_vertical == second_vertical:
        return parallel_intersection(first, second, first_vertical)
    vertical, horizontal = (first, second) if first_vertical else (second, first)
    vx, vy1, vy2 = vertical[0][0], *sorted((vertical[0][1], vertical[1][1]))
    hy, hx1, hx2 = horizontal[0][1], *sorted((horizontal[0][0], horizontal[1][0]))
    return "cross" if hx1 <= vx <= hx2 and vy1 <= hy <= vy2 else None


def parallel_intersection(
    first: tuple[tuple[float, float], tuple[float, float]],
    second: tuple[tuple[float, float], tuple[float, float]],
    vertical: bool,
) -> str | None:
    fixed = 0 if vertical else 1
    varying = 1 - fixed
    if first[0][fixed] != second[0][fixed]:
        return None
    first_range = sorted((first[0][varying], first[1][varying]))
    second_range = sorted((second[0][varying], second[1][varying]))
    overlap = min(first_range[1], second_range[1]) - max(first_range[0], second_range[0])
    return "overlap" if overlap > 0 else ("touch" if overlap == 0 else None)


def verify_geometry(root: ET.Element) -> list[str]:
    boxes = {
        element.attrib["data-node"]: parse_box(element)
        for element in root.iter()
        if element.attrib.get("data-obstacle") == "true"
    }
    connectors = [
        parse_connector(element)
        for element in root.iter()
        if element.attrib.get("data-connector") == "true"
    ]
    errors = verify_connector_obstacles(connectors, boxes)
    errors.extend(verify_connector_endpoints(connectors, boxes))
    errors.extend(verify_connector_intersections(connectors))
    errors.extend(verify_canvas_bounds(root, boxes, connectors))
    print(f"geometry: {len(connectors)} connectors, {len(boxes)} obstacles")
    return errors


def verify_connector_endpoints(connectors: list[Connector], boxes: dict[str, Box]) -> list[str]:
    errors: list[str] = []
    for connector in connectors:
        source = boxes.get(connector.source)
        target = boxes.get(connector.target)
        if source is not None and not source.contains(connector.points[0]):
            errors.append(f"{connector.edge_id}: first point is outside source {source.node_id}")
        if target is not None and not target.contains(connector.points[-1]):
            errors.append(f"{connector.edge_id}: last point is outside target {target.node_id}")
    return errors


def verify_canvas_bounds(
    root: ET.Element, boxes: dict[str, Box], connectors: list[Connector]
) -> list[str]:
    view_box = [float(value) for value in root.attrib.get("viewBox", "").split()]
    if len(view_box) != 4:
        return ["SVG viewBox must contain four numbers"]
    left, top, width, height = view_box
    right, bottom = left + width, top + height
    errors: list[str] = []
    for box in boxes.values():
        if box.x < left or box.y < top or box.x + box.width > right or box.y + box.height > bottom:
            errors.append(f"{box.node_id}: obstacle exceeds SVG viewBox")
    for connector in connectors:
        if any(not (left <= x <= right and top <= y <= bottom) for x, y in connector.points):
            errors.append(f"{connector.edge_id}: connector point exceeds SVG viewBox")
    return errors


def verify_connector_obstacles(connectors: list[Connector], boxes: dict[str, Box]) -> list[str]:
    errors: list[str] = []
    for connector in connectors:
        if connector.source not in boxes or connector.target not in boxes:
            errors.append(f"{connector.edge_id}: unknown source or target")
            continue
        for box in boxes.values():
            if box.node_id in {connector.source, connector.target}:
                continue
            if any(segment_hits_box(segment, box) for segment in segments(connector)):
                errors.append(f"{connector.edge_id}: crosses obstacle {box.node_id}")
    return errors


def verify_connector_intersections(connectors: list[Connector]) -> list[str]:
    errors: list[str] = []
    for index, first in enumerate(connectors):
        for second in connectors[index + 1 :]:
            intersections = {
                result
                for a in segments(first)
                for b in segments(second)
                if (result := segment_intersection(a, b)) is not None
            }
            if intersections:
                errors.append(
                    f"{first.edge_id}/{second.edge_id}: connector intersection "
                    f"{sorted(intersections)}"
                )
    return errors


def verify_drawio(root: ET.Element) -> list[str]:
    content = root.attrib.get("content", "")
    if not content:
        return ["missing embedded draw.io content attribute"]
    try:
        model = ET.fromstring(content)  # noqa: S314
    except ET.ParseError as error:
        return [f"embedded draw.io XML parse error: {error}"]
    errors = []
    if model.tag != "mxfile" or model.attrib.get("compressed") != "false":
        errors.append("embedded model must be an uncompressed mxfile")
    if not any(element.tag == "mxGraphModel" for element in model.iter()):
        errors.append("embedded model has no mxGraphModel")
    if content.count("mxgraph.aws4") < 12:
        errors.append("embedded model does not use enough AWS4 icon shapes")
    print(f"draw.io: {sum(1 for _ in model.iter())} XML elements")
    return errors


def verify_inventory(root: ET.Element, raw: str) -> list[str]:
    services = {
        element.attrib["data-service"]
        for element in root.iter()
        if "data-service" in element.attrib
    }
    text = " ".join("".join(root.itertext()).split())
    errors = [f"missing service: {name}" for name in sorted(REQUIRED_SERVICES - services)]
    errors.extend(
        f"missing resource label: {name}" for name in sorted(REQUIRED_RESOURCES) if name not in text
    )
    errors.extend(
        f"forbidden legacy term: {term}" for term in sorted(FORBIDDEN_TERMS) if term in raw
    )
    print(f"inventory: {len(services)} services, {len(REQUIRED_RESOURCES)} required resources")
    return errors


def verify_vector_only(root: ET.Element) -> list[str]:
    errors: list[str] = []
    for element in root.iter():
        if local_name(element.tag) == "image":
            errors.append("raster/image element is not allowed")
        href = element.attrib.get("href") or element.attrib.get(
            "{http://www.w3.org/1999/xlink}href"
        )
        if href and not href.startswith("#"):
            errors.append(f"external reference is not allowed: {href[:80]}")
    if root.attrib.get("data-icon-license") != "AWS Architecture Icons via aws-icons MIT":
        errors.append("icon source/license metadata is missing")
    if root.attrib.get("data-icon-source") != "aws-icons@3.3.0":
        errors.append("icon package/version metadata is missing")
    if root.attrib.get("data-icon-license-file") != "THIRD_PARTY_NOTICES.md":
        errors.append("icon license notice reference is missing")
    return errors


def verify(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(raw)  # noqa: S314
    except ET.ParseError as error:
        return [f"SVG XML parse error: {error}"]
    errors = verify_drawio(root)
    errors.extend(verify_inventory(root, raw))
    errors.extend(verify_vector_only(root))
    errors.extend(verify_geometry(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("docs/design/architecture.drawio.svg"),
    )
    args = parser.parse_args()
    errors = verify(args.path)
    if errors:
        print("architecture diagram verification: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("architecture diagram verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
