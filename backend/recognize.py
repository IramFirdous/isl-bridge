
"""Local ISL demo-subset recognizer.

VerbX is never called here. Input is MediaPipe Hands landmarks from the browser.
Unknown or low-confidence poses return state=UNRECOGNIZED.
"""

from __future__ import annotations

from collections import Counter
from catalog import load_catalog

# MediaPipe Hands indices.
TIP = [4, 8, 12, 16, 20]
PIP = [3, 6, 10, 14, 18]  # thumb uses IP (3)
MCP = [2, 5, 9, 13, 17]


def _pt(hand: list, idx: int) -> dict:
    return hand[idx]


def _dist(a: dict, b: dict) -> float:
    return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5


def _dot_unit(ax: float, ay: float, bx: float, by: float) -> float:
    na = (ax * ax + ay * ay) ** 0.5
    nb = (bx * bx + by * by) ** 0.5
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return (ax * bx + ay * by) / (na * nb)


def _finger_up(hand: list, finger: int) -> bool:
    """True when a finger is extended, independent of palm rotation.

    Image-Y comparisons fail when the hand is sideways or pointing at the
    camera. Joint direction plus tip-to-MCP distance is more stable.
    """
    tip = _pt(hand, TIP[finger])
    pip = _pt(hand, PIP[finger])
    mcp = _pt(hand, MCP[finger])
    wrist = _pt(hand, 0)

    v1x, v1y = pip["x"] - mcp["x"], pip["y"] - mcp["y"]
    v2x, v2y = tip["x"] - pip["x"], tip["y"] - pip["y"]
    aligned = _dot_unit(v1x, v1y, v2x, v2y) > 0.45

    tip_mcp = _dist(tip, mcp)
    pip_mcp = _dist(pip, mcp)
    stretched = tip_mcp > pip_mcp * 1.15

    if finger == 0:
        # Thumb: compare reach away from the palm, not image-up.
        index_mcp = _pt(hand, 5)
        pinky_mcp = _pt(hand, 17)
        palm = {
            "x": (index_mcp["x"] + pinky_mcp["x"]) / 2,
            "y": (index_mcp["y"] + pinky_mcp["y"]) / 2,
        }
        away_from_palm = _dist(tip, palm) > _dist(pip, palm) * 1.08
        away_from_wrist = _dist(tip, wrist) > _dist(mcp, wrist) * 1.05
        return (aligned or stretched) and away_from_palm and away_from_wrist

    farther_than_mcp = _dist(tip, wrist) > _dist(mcp, wrist) * 1.05
    return aligned and stretched and farther_than_mcp


def _pattern(hand: list) -> tuple[bool, bool, bool, bool, bool]:
    return tuple(_finger_up(hand, i) for i in range(5))


def _wrist(hand: list) -> dict:
    return _pt(hand, 0)


def _std(values: list[float]) -> float:
    if not values:
        return 0.0

    mean = sum(values) / len(values)
    return (
        sum((v - mean) ** 2 for v in values) / len(values)
    ) ** 0.5


def _trajectory_features(xs: list[float], ys: list[float]) -> dict:
    """Describe the order and direction of wrist movement."""
    points = list(zip(xs, ys))

    if len(points) < 3:
        return {
            "x_range": 0.0,
            "y_range": 0.0,
            "path_x": 0.0,
            "path_y": 0.0,
            "x_reversals": 0,
            "y_reversals": 0,
            "loop_area_ratio": 0.0,
        }

    dx = [
        points[i][0] - points[i - 1][0]
        for i in range(1, len(points))
    ]
    dy = [
        points[i][1] - points[i - 1][1]
        for i in range(1, len(points))
    ]

    def reversals(values):
        # Ignore tiny coordinate changes caused by tracking noise.
        directions = [
            1 if value > 0.003 else -1 if value < -0.003 else 0
            for value in values
        ]
        directions = [
            value for value in directions if value != 0
        ]

        return sum(
            directions[i] != directions[i - 1]
            for i in range(1, len(directions))
        )

    x_range = max(xs) - min(xs)
    y_range = max(ys) - min(ys)

    # Shoelace area measures how much the path encloses a loop.
    area = abs(
        sum(
            points[i][0] * points[(i + 1) % len(points)][1]
            - points[(i + 1) % len(points)][0] * points[i][1]
            for i in range(len(points))
        )
    ) / 2

    loop_area_ratio = area / (x_range * y_range + 1e-6)

    return {
        "x_range": x_range,
        "y_range": y_range,
        "path_x": sum(abs(value) for value in dx),
        "path_y": sum(abs(value) for value in dy),
        "x_reversals": reversals(dx),
        "y_reversals": reversals(dy),
        "loop_area_ratio": loop_area_ratio,
    }


def _open_palm(p: tuple) -> bool:
    return all(p[1:])


def _fist(p: tuple) -> bool:
    return not any(p[1:]) and not p[0]


def _thumbs_up(p: tuple) -> bool:
    return p[0] and not any(p[1:])


def _index_only(p: tuple) -> bool:
    return not p[0] and p[1] and not any(p[2:])


def _index_with_thumb(p: tuple) -> bool:
    return p[0] and p[1] and not any(p[2:])


def _two_fingers(p: tuple) -> bool:
    return p[1] and p[2] and not p[3] and not p[4]


def _three_fingers(p: tuple) -> bool:
    return p[1] and p[2] and p[3] and not p[4]


def _unrecognized(
    code: str,
    reason: str,
    threshold: float,
    supported: list,
    scores=None,
    debug=None,
) -> dict:
    scores = scores or {}

    return {
        "state": "UNRECOGNIZED",
        "code": code,
        "reason": reason,
        "sign_language": "Indian Sign Language (ISL)",
        "gloss": None,
        "sign_id": None,
        "confidence": round(
            max(scores.values()) if scores else 0.0, 3
        ),
        "threshold": threshold,
        "scores": {
            k: round(v, 3)
            for k, v in scores.items()
            if v > 0
        },
        "supported_ids": supported,
        "verbx_used": False,
        "recognizer": "mediapipe_hands_plus_local_geometry",
        "debug": debug,
        "sign": None,
    }


def _debug(
    pattern, std_x, std_y, avg_y, motion, two_hand: bool
) -> dict:
    names = ["thumb", "index", "middle", "ring", "pinky"]

    return {
        "fingers_up": {
            names[i]: bool(pattern[i]) for i in range(5)
        },
        "std_x": round(std_x, 4),
        "std_y": round(std_y, 4),
        "avg_wrist_y": round(avg_y, 4),
        "motion": round(motion, 4),
        "two_hand": two_hand,
    }


def recognize_frames(
    frames: list, threshold: float | None = None
) -> dict:
    catalog = load_catalog()

    threshold = (
        threshold
        if threshold is not None
        else float(catalog["confidence_threshold"])
    )

    supported = [s["id"] for s in catalog["signs"]]

    if not frames:
        return _unrecognized(
            "no_frames",
            "No landmark frames were sent.",
            threshold,
            supported,
        )

    parsed = []

    for frame in frames:
        hands = frame.get("hands") or []
        cleaned = []

        for hand in hands:
            if isinstance(hand, dict):
                hand = hand.get("landmarks", [])

            if isinstance(hand, list) and len(hand) >= 21:
                cleaned.append(hand[:21])

        if cleaned:
            parsed.append(cleaned)

    if not parsed:
        return _unrecognized(
            "no_hand",
            "No hand landmarks detected.",
            threshold,
            supported,
        )

    # Use the most consistently observed hand pattern.
    # Keep movement calculation based on the primary hand.
    primary = [hands[0] for hands in parsed]
    patterns = [_pattern(hand) for hand in primary]
    wrists = [_wrist(hand) for hand in primary]

    xs = [w["x"] for w in wrists]
    ys = [w["y"] for w in wrists]

    std_x = _std(xs)
    std_y = _std(ys)
    motion = (std_x ** 2 + std_y ** 2) ** 0.5

    trajectory = _trajectory_features(xs, ys)

    avg_y = sum(ys) / len(ys)

    # Stationary palms can have small tracking fluctuations.
    still = motion < 0.050

    # Require meaningful movement before considering dynamic signs.
    moving = motion > 0.050

    # HELLO: predominantly horizontal movement, ideally with a wave reversal.
    horizontal = (
        moving
        and std_x > std_y * 1.10
        and trajectory["x_range"] > 0.05
        and (
            trajectory["x_reversals"] >= 1
            or trajectory["path_x"] > 0.12
        )
    )

    vertical = (
        moving
        and std_y > std_x * 1.25
        and trajectory["y_range"] > 0.04
    )

    # PLEASE: movement in both axes with evidence of a loop.
    circular = (
        moving
        and trajectory["x_range"] > 0.04
        and trajectory["y_range"] > 0.04
        and trajectory["loop_area_ratio"] > 0.12
        and not (std_x > std_y * 1.6)
        and not (std_y > std_x * 1.6)
    )

    # Find the most common hand shape across the frames.
    maj_pattern, maj_count = Counter(patterns).most_common(1)[0]
    maj_ratio = maj_count / len(patterns)

    # Require a reasonably consistent hand shape.
    if maj_ratio < 0.45:
        return _unrecognized(
            "unstable_pose",
            "Hand shape was inconsistent across frames. "
            "Keep your hand clearly visible and try again.",
            threshold,
            supported,
            debug={
                **_debug(
                    maj_pattern,
                    std_x,
                    std_y,
                    avg_y,
                    motion,
                    two_hand=(
                        sum(
                            len(hands) >= 2 for hands in parsed
                        ) / len(parsed)
                    ) >= 0.65,
                ),
                "stable_pattern_ratio": round(maj_ratio, 3),
                "parsed_frames": len(parsed),
            },
        )

    # Check whether two hands are consistently present.
    two_hand_frames = [
        hands for hands in parsed if len(hands) >= 2
    ]
    two_hand_ratio = len(two_hand_frames) / len(parsed)

    scores = {sid: 0.0 for sid in supported}

    # HELP requires two hands; don't infer it from a single hand.
    if two_hand_ratio >= 0.65:
        last_two = two_hand_frames[-1]

        p0 = _pattern(last_two[0])
        p1 = _pattern(last_two[1])

        w0 = _wrist(last_two[0])
        w1 = _wrist(last_two[1])

        dist = (
            (w0["x"] - w1["x"]) ** 2
            + (w0["y"] - w1["y"]) ** 2
        ) ** 0.5

        combo = (
            (_fist(p0) and _open_palm(p1))
            or (_fist(p1) and _open_palm(p0))
            or (_thumbs_up(p0) and _open_palm(p1))
            or (_thumbs_up(p1) and _open_palm(p0))
        )

        if combo and dist < 0.38:
            scores["HELP"] = 0.88

    # Open-palm signs.
    if _open_palm(maj_pattern):
        if horizontal:
            scores["HELLO"] = 0.88

        elif circular:
            scores["PLEASE"] = 0.84

        elif vertical and avg_y < 0.62:
            scores["THANK_YOU"] = 0.82

        elif still and trajectory["x_range"] < 0.08:
            scores["STOP"] = 0.88

    # Closed fingers nodding counts as YES even if the thumb is wrapped/out.
    if (not any(maj_pattern[1:])) and vertical:
        scores["YES"] = 0.86

    # NO: index finger (thumb optional) waving side to side — not a still pose.
    if _index_only(maj_pattern) or _index_with_thumb(maj_pattern):
        if horizontal:
            scores["NO"] = 0.86 if _index_only(maj_pattern) else 0.80

    if _two_fingers(maj_pattern) and not horizontal:
        scores["NAME"] = 0.84 if (still or vertical) else 0.76

    if _three_fingers(maj_pattern) and not horizontal:
        scores["WATER"] = 0.86

    if _thumbs_up(maj_pattern) and not horizontal and not vertical:
        scores["GOOD"] = 0.88 if still else 0.78

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    best_id, best_score = ranked[0]
    second_score = ranked[1][1]

    debug = _debug(
        maj_pattern,
        std_x,
        std_y,
        avg_y,
        motion,
        two_hand=two_hand_ratio >= 0.65,
    )
    debug.update({
        "x_range": round(trajectory["x_range"], 4),
        "y_range": round(trajectory["y_range"], 4),
        "x_reversals": trajectory["x_reversals"],
        "loop_area_ratio": round(
            trajectory["loop_area_ratio"], 4
        ),
        "stable_pattern_ratio": round(maj_ratio, 3),
        "two_hand_ratio": round(two_hand_ratio, 3),
    })

    # Confidence is a rule score, not a calibrated probability.
    if best_score < threshold:
        return _unrecognized(
            "unknown_sign",
            "Pose did not match a documented ISL demo sign "
            "with enough confidence.",
            threshold,
            supported,
            scores=scores,
            debug=debug,
        )

    if best_score - second_score < 0.06:
        return _unrecognized(
            "ambiguous_sign",
            "More than one sign rule matched. "
            "Try again with a clearer, steadier gesture.",
            threshold,
            supported,
            scores=scores,
            debug=debug,
        )

    sign = next(
        s for s in catalog["signs"] if s["id"] == best_id
    )

    return {
        "state": "recognized",
        "sign_language": catalog["sign_language"],
        "gloss": sign["gloss"],
        "sign_id": sign["id"],
        "en": sign["en"],
        "hi": sign["hi"],
        "confidence": round(best_score, 3),
        "threshold": threshold,
        "scores": {
            k: round(v, 3)
            for k, v in scores.items()
            if v > 0
        },
        "verbx_used": False,
        "recognizer": "mediapipe_hands_plus_local_geometry",
        "debug": debug,
        "sign": sign,
    }
