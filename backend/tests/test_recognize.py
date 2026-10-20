import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recognize import recognize_frames  # noqa: E402


def _hand(pattern_up: list[bool], wrist=(0.5, 0.55)):
    pts = [{"x": wrist[0], "y": wrist[1], "z": 0.0} for _ in range(21)]
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    for i, up in enumerate(pattern_up):
        if i == 0:
            pts[tips[i]]["x"] = wrist[0] + (0.18 if up else 0.01)
            pts[pips[i]]["x"] = wrist[0] + 0.04
        else:
            pts[tips[i]]["y"] = wrist[1] - (0.25 if up else -0.05)
            pts[pips[i]]["y"] = wrist[1] - 0.05
    return pts


def _seq(hand, n=16, dx=0.0, dy=0.0):
    frames = []
    for i in range(n):
        t = i / max(n - 1, 1)
        shifted = []
        for p in hand:
            shifted.append({"x": p["x"] + dx * t, "y": p["y"] + dy * t, "z": p["z"]})
        frames.append({"hands": [shifted]})
    return frames


def test_thumbs_up_is_good():
    result = recognize_frames(_seq(_hand([True, False, False, False, False]), n=14))
    assert result["state"] == "recognized"
    assert result["sign_id"] == "GOOD"


def test_unknown_is_unrecognized():
    # Random mid-curl-ish fingers, no motion
    result = recognize_frames(_seq(_hand([True, True, False, True, False]), n=12))
    assert result["state"] == "UNRECOGNIZED"


def test_empty_unrecognized():
    result = recognize_frames([])
    assert result["state"] == "UNRECOGNIZED"
    assert result["code"] == "no_frames"


if __name__ == "__main__":
    test_thumbs_up_is_good()
    test_unknown_is_unrecognized()
    test_empty_unrecognized()
    print("ok")
