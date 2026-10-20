import json
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "signs.json"


def load_catalog() -> dict:
    with DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def signs_by_id(catalog: dict | None = None) -> dict:
    catalog = catalog or load_catalog()
    return {sign["id"]: sign for sign in catalog["signs"]}



def match_speech_to_sign(transcript: str, catalog: dict | None = None) -> dict:
    import re

    catalog = catalog or load_catalog()
    text = (transcript or "").strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = " ".join(text.split())

    if not text:
        return {
            "matched": False,
            "state": "empty_transcript",
            "sign": None,
            "reason": "No speech text to match.",
        }

    # First, prefer an exact match over a partial match.
    for sign in catalog["signs"]:
        aliases = [
            sign["en"],
            sign["hi"],
            sign["gloss"],
            sign["id"].replace("_", " "),
            *sign.get("aliases", []),
        ]

        for alias in aliases:
            alias = re.sub(r"[^\w\s]", " ", alias.lower())
            alias = " ".join(alias.split())

            if alias and text == alias:
                return {
                    "matched": True,
                    "state": "supported_sign",
                    "sign": sign,
                    "reason": f"Transcript exactly matched supported ISL gloss {sign['gloss']}.",
                }

    # Then allow a complete alias phrase inside a longer sentence.
    for sign in catalog["signs"]:
        aliases = [
            sign["en"],
            sign["hi"],
            sign["gloss"],
            sign["id"].replace("_", " "),
            *sign.get("aliases", []),
        ]

        for alias in aliases:
            alias = re.sub(r"[^\w\s]", " ", alias.lower())
            alias = " ".join(alias.split())

            if alias and re.search(rf"\b{re.escape(alias)}\b", text):
                return {
                    "matched": True,
                    "state": "supported_sign",
                    "sign": sign,
                    "reason": f"Transcript matched supported ISL gloss {sign['gloss']}.",
                }

    return {
        "matched": False,
        "state": "unsupported_phrase",
        "sign": None,
        "reason": (
            "Speech is not in the documented ISL demo set. "
            "Reverse route refused rather than inventing a sign."
        ),
    }

