from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, cast


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> int:
    path = Path("docs/evidence/cost-estimate-20260713.json")
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("cost estimate root must be an object")
    document = cast(dict[str, Any], raw)
    lines = document.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("cost estimate requires line items")
    subtotal = money(
        sum(Decimal(str(cast(dict[str, Any], line)["monthlyUsd"])) for line in lines)
    )
    declared_subtotal = Decimal(str(document["subtotalUsd"]))
    if subtotal != declared_subtotal:
        raise ValueError(f"subtotal mismatch: {subtotal} != {declared_subtotal}")
    contingency = money(subtotal * Decimal(str(document["contingencyRate"])))
    if contingency != Decimal(str(document["contingencyUsd"])):
        raise ValueError("contingency mismatch")
    total = money(subtotal + contingency)
    if total != Decimal(str(document["totalUsd"])):
        raise ValueError("total mismatch")
    if total > Decimal(str(document["monthlyTargetUsd"])):
        raise ValueError("monthly target exceeded")
    fx = cast(dict[str, Any], document["fx"])
    total_jpy = int(
        (total * Decimal(str(fx["planningJpyPerUsd"]))).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    if total_jpy != document["totalJpy"]:
        raise ValueError("JPY total mismatch")
    if document.get("approvalStatus") not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid approvalStatus")
    print(f"ok: {document['estimateId']} ${total}/month JPY {total_jpy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
