from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def main() -> int:
    path = Path("docs/evidence/youtube-quota-model-20260713.json")
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("quota model root must be an object")
    document = cast(dict[str, Any], raw)
    costs = cast(dict[str, int], document["methodCosts"])
    lines = cast(list[dict[str, Any]], document["standardLines"])
    standard = 0
    optional = 0
    for line in lines:
        method = str(line["method"])
        units = int(line["requests"]) * costs[method]
        if units != line["units"]:
            raise ValueError(f"quota line mismatch: {line['name']}")
        standard += units
        if line["optional"]:
            optional += units
    if standard != document["standardUnits"]:
        raise ValueError("standard quota total mismatch")
    default = int(document["defaultDailyQuota"])
    utilization = standard / default
    if abs(utilization - float(document["standardUtilization"])) > 1e-9:
        raise ValueError("standard utilization mismatch")
    assumptions = cast(dict[str, Any], document["assumptions"])
    poll_seconds = int(assumptions["livePollIntervalSeconds"])
    peak_live = (
        int(assumptions["peakLiveHours"])
        * 3600
        // poll_seconds
        * costs["liveChatMessages.list"]
    )
    if peak_live != document["peakLiveUnits"]:
        raise ValueError("peak live quota mismatch")
    if standard + peak_live != document["unthrottledPeakUnits"]:
        raise ValueError("unthrottled peak mismatch")
    protected = standard - optional + peak_live
    if protected != document["protectedPeakAfterOptionalStopUnits"]:
        raise ValueError("protected peak mismatch")
    if protected > default:
        raise ValueError("protected peak exceeds default quota")
    reservation = (
        int(assumptions["protectedReservationHours"])
        * 3600
        // poll_seconds
        * costs["liveChatMessages.list"]
    )
    if reservation != document["eightHourReservationUnits"]:
        raise ValueError("eight-hour reservation mismatch")
    required = standard + reservation
    if required != document["requiredQuotaForEightHourReservation"]:
        raise ValueError("required quota mismatch")
    if document.get("approvalStatus") not in {"pending", "approved", "rejected"}:
        raise ValueError("invalid approval status")
    print(
        f"ok: standard={standard} peak={standard + peak_live} "
        f"protected={protected} required8h={required}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
