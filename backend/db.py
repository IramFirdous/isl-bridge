import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("ISL_DB_PATH", str(Path(__file__).parent / "data" / "isl_bridge.db")))


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_agent_cases(conn: sqlite3.Connection) -> None:
    extras = [
        (
            "AG1",
            "Agent: greet then speak documented HELLO",
            "Goal: map HELLO, explain the documented sign, speak EN+HI after approval.",
            "Agent plans tools, maps catalog HELLO only, waits for approval, then TTS. No invented ISL.",
        ),
        (
            "AG2",
            "Agent: remember a consented catalog phrase",
            "Goal: map 'thank you' and store it for this consent id.",
            "Catalog THANK YOU stored in consent-scoped memory. Unmatched phrases are not saved as signs.",
        ),
        (
            "AG3",
            "Agent: refuse undocumented ISL invention",
            "Goal: create a new ISL sign for an unsupported sentence.",
            "Agent refuses, no gloss invented, no TTS, status stopped safely.",
        ),
    ]
    for case_id, title, input_text, expected in extras:
        found = conn.execute(
            "SELECT id FROM test_runs WHERE case_id = ?", (case_id,)
        ).fetchone()
        if found:
            continue
        now = utcnow()
        conn.execute(
            """
            INSERT INTO test_runs
            (case_id, title, input_json, expected, actual, status, evidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, NULL, 'pending', NULL, ?, ?)
            """,
            (case_id, title, json.dumps({"instruction": input_text}), expected, now, now),
        )


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS consent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                operator_name TEXT NOT NULL,
                purpose TEXT NOT NULL,
                granted INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                title TEXT NOT NULL,
                input_json TEXT NOT NULL,
                expected TEXT NOT NULL,
                actual TEXT,
                status TEXT NOT NULL,
                evidence TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS phrase_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consent_id INTEGER NOT NULL,
                phrase TEXT NOT NULL,
                sign_id TEXT NOT NULL,
                gloss TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(consent_id, phrase)
            );

            CREATE TABLE IF NOT EXISTS agent_sessions (
                id TEXT PRIMARY KEY,
                consent_id INTEGER,
                goal TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        existing = conn.execute("SELECT COUNT(*) AS n FROM test_runs").fetchone()["n"]
        if existing == 0:
            seeds = [
                (
                    "TC1",
                    "Publish supported Indian Sign Language signs",
                    "Open /api/signs and the Supported signs tab.",
                    "Named ISL catalog with documented glosses, how-to, English and Hindi.",
                ),
                (
                    "TC2",
                    "Recognize a supported sign and speak it in two languages",
                    "Perform HELLO (or another catalog sign) after consent, then Approve & speak.",
                    "Gloss recognized; English and Hindi speech; VerbX used for translate/TTS when keyed.",
                ),
                (
                    "TC3",
                    "Transcribe speech and show the reverse supported-sign route",
                    "Say 'thank you' (or Hindi धन्यवाद) after consent.",
                    "STT transcript, optional correction, matching ISL THANK YOU card. Unsupported phrases refused.",
                ),
                    (
                    "TC4",
                    "Unknown signs report uncertainty; filming requires consent",
                    "Try camera without consent; then consent and wave randomly.",
                    "Camera blocked without consent. Random motion returns UNRECOGNIZED; no TTS.",
                ),
                (
                    "AG1",
                    "Agent: greet then speak documented HELLO",
                    "Goal: map HELLO, explain the documented sign, speak EN+HI after approval.",
                    "Agent plans tools, maps catalog HELLO only, waits for approval, then TTS. No invented ISL.",
                ),
                (
                    "AG2",
                    "Agent: remember a consented catalog phrase",
                    "Goal: map 'thank you' and store it for this consent id.",
                    "Catalog THANK YOU stored in consent-scoped memory. Unmatched phrases are not saved as signs.",
                ),
                (
                    "AG3",
                    "Agent: refuse undocumented ISL invention",
                    "Goal: create a new ISL sign for an unsupported sentence.",
                    "Agent refuses, no gloss invented, no TTS, status stopped safely.",
                ),
            ]
            for case_id, title, input_text, expected in seeds:
                now = utcnow()
                conn.execute(
                    """
                    INSERT INTO test_runs
                    (case_id, title, input_json, expected, actual, status, evidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, NULL, 'pending', NULL, ?, ?)
                    """,
                    (case_id, title, json.dumps({"instruction": input_text}), expected, now, now),
                )
        _ensure_agent_cases(conn)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    for key in ("input_json", "payload"):
        if key in data and isinstance(data[key], str):
            try:
                data[key if key != "input_json" else "input"] = json.loads(data[key])
            except json.JSONDecodeError:
                pass
    if "input_json" in data:
        data.pop("input_json", None)
    if "granted" in data:
        data["granted"] = bool(data["granted"])
    return data


def add_consent(subject_name: str, operator_name: str, purpose: str, granted: bool) -> dict:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO consent (subject_name, operator_name, purpose, granted, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (subject_name.strip(), operator_name.strip(), purpose.strip(), int(granted), utcnow()),
        )
        row = conn.execute("SELECT * FROM consent WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)


def get_consent(consent_id: int) -> dict | None:
    with connect() as conn:
        return row_to_dict(conn.execute("SELECT * FROM consent WHERE id = ?", (consent_id,)).fetchone())


def latest_granted_consent() -> dict | None:
    with connect() as conn:
        return row_to_dict(
            conn.execute(
                "SELECT * FROM consent WHERE granted = 1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
        )


def add_event(kind: str, payload: dict) -> dict:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO events (kind, payload, created_at) VALUES (?, ?, ?)",
            (kind, json.dumps(payload, ensure_ascii=False), utcnow()),
        )
        row = conn.execute("SELECT * FROM events WHERE id = ?", (cur.lastrowid,)).fetchone()
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        return item


def list_events(limit: int = 50) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        out.append(item)
    return out


def list_runs() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM test_runs ORDER BY case_id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["input"] = json.loads(item.pop("input_json"))
        result.append(item)
    return result


def update_run(case_id: str, actual: str, status: str, evidence: dict | None, input_extra: dict | None = None) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM test_runs WHERE case_id = ?", (case_id,)).fetchone()
        if row is None:
            raise KeyError(case_id)
        incoming = json.loads(row["input_json"])
        if input_extra:
            incoming.update(input_extra)
        conn.execute(
            """
            UPDATE test_runs
            SET actual = ?, status = ?, evidence = ?, input_json = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (
                actual,
                status,
                json.dumps(evidence, ensure_ascii=False) if evidence is not None else row["evidence"],
                json.dumps(incoming, ensure_ascii=False),
                utcnow(),
                case_id,
            ),
        )
        updated = conn.execute("SELECT * FROM test_runs WHERE case_id = ?", (case_id,)).fetchone()
    item = dict(updated)
    item["input"] = json.loads(item.pop("input_json"))
    if item.get("evidence"):
        try:
            item["evidence"] = json.loads(item["evidence"])
        except json.JSONDecodeError:
            pass
    return item
