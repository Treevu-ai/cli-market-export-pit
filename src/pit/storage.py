"""Dual-backend persistence for research runs (SQLite / PostgreSQL)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
try:
    import psycopg2  # noqa: F401
except ImportError:
    psycopg2 = None  # type: ignore[assignment]
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_SENSITIVE_PARAM_KEYS = {
    "api_key",
    "apikey",
    "key",
    "token",
    "access_token",
    "client_secret",
    "secret",
    "password",
}
_REDACTED = "***REDACTED***"


def _redact_sensitive_params(request_params: dict[str, Any]) -> dict[str, Any]:
    """Defense in depth: strip known-sensitive query params before persisting.

    Connectors are expected to keep secrets out of request_url/request_params
    entirely (they belong in headers), but this backstop protects stored
    evidence and API responses even if a connector gets that wrong.
    """
    return {
        key: (_REDACTED if key.lower() in _SENSITIVE_PARAM_KEYS else value)
        for key, value in request_params.items()
    }


def _redact_sensitive_query_string(url: str) -> str:
    for sensitive_key in _SENSITIVE_PARAM_KEYS:
        url = re.sub(
            rf"([?&]{re.escape(sensitive_key)}=)[^&]*",
            rf"\g<1>{_REDACTED}",
            url,
            flags=re.IGNORECASE,
        )
    return url


class ResearchStore:
    """Owns PIT metadata and content-addressed source responses."""

    def __init__(self, database_path: Path, raw_directory: Path, database_url: str | None = None) -> None:
        self.database_url: str = database_url if database_url else os.getenv("DATABASE_URL", "")
        self.raw_directory = raw_directory
        if self.database_url.startswith("postgresql://"):
            if psycopg2 is None:
                raise RuntimeError("psycopg2-binary is required for PostgreSQL. Install it with: pip install psycopg2-binary")
            self._backend = "postgresql"
            self._conn: Any = None
        else:
            self._backend = "sqlite"
            self.database_path = database_path
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_directory.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> Any:
        if self._backend == "postgresql":
            if self._conn is None:
                self._conn = psycopg2.connect(self.database_url)
                self._conn.autocommit = False
            return self._conn
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _execute(self, connection: Any, query: str, params: tuple[Any, ...] = ()) -> Any:
        placeholder = self._placeholder()
        if placeholder == "%s":
            query = query.replace("?", "%s")
        else:
            query = query.replace("_ph()", "?")
        cursor = connection.cursor()
        cursor.execute(query, params)
        return cursor

    @contextmanager
    def _transaction(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            if self._backend == "sqlite":
                connection.close()

    def _placeholder(self) -> str:
        return "%s" if self._backend == "postgresql" else "?"

    def _insert_ignore(self) -> str:
        return "ON CONFLICT DO NOTHING" if self._backend == "postgresql" else "OR IGNORE"

    def initialize(self) -> None:
        with self._transaction() as db:
            if self._backend == "postgresql":
                statements = [
                    "CREATE TABLE IF NOT EXISTS research_runs (id TEXT PRIMARY KEY, query_original TEXT NOT NULL, query_normalized TEXT NOT NULL, taxonomy_version TEXT NOT NULL, target_market TEXT NOT NULL, application TEXT NOT NULL, from_publication_date TEXT NOT NULL DEFAULT '2021-01-01', cutoff_at TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT, error TEXT)",
                    "CREATE TABLE IF NOT EXISTS source_requests (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, source TEXT NOT NULL, request_url TEXT NOT NULL, request_params TEXT NOT NULL, fetched_at TEXT, http_status INTEGER, checksum TEXT, raw_object_key TEXT, license TEXT NOT NULL, status TEXT NOT NULL, error TEXT)",
                    "CREATE TABLE IF NOT EXISTS evidence_records (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, source_request_id TEXT NOT NULL REFERENCES source_requests(id) ON DELETE RESTRICT, source TEXT NOT NULL, domain TEXT NOT NULL, external_id TEXT NOT NULL, title TEXT NOT NULL, published_at TEXT, geography TEXT, normalized_payload TEXT NOT NULL, dedupe_key TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(research_run_id, source, dedupe_key))",
                    "CREATE TABLE IF NOT EXISTS evidence_source_links (id TEXT PRIMARY KEY, evidence_record_id TEXT NOT NULL REFERENCES evidence_records(id) ON DELETE CASCADE, source_request_id TEXT NOT NULL REFERENCES source_requests(id) ON DELETE RESTRICT, source TEXT NOT NULL, external_id TEXT NOT NULL, normalized_payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(source_request_id, external_id))",
                    "CREATE INDEX IF NOT EXISTS idx_source_requests_run ON source_requests(research_run_id)",
                    "CREATE INDEX IF NOT EXISTS idx_evidence_records_run ON evidence_records(research_run_id)",
                    "CREATE INDEX IF NOT EXISTS idx_evidence_source_links_record ON evidence_source_links(evidence_record_id)",
                    "CREATE TABLE IF NOT EXISTS taxonomies (id TEXT PRIMARY KEY, name TEXT NOT NULL, version TEXT NOT NULL, created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS synonyms (id TEXT PRIMARY KEY, taxonomy_id TEXT NOT NULL REFERENCES taxonomies(id), term TEXT NOT NULL, normalized TEXT NOT NULL, created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS hs_mappings (id TEXT PRIMARY KEY, taxonomy_id TEXT NOT NULL REFERENCES taxonomies(id), product_term TEXT NOT NULL, hs_code TEXT NOT NULL, description TEXT, created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS domain_summaries (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, domain TEXT NOT NULL, summary_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(research_run_id, domain, summary_type))",
                    "CREATE TABLE IF NOT EXISTS claims (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, domain TEXT NOT NULL, statement TEXT NOT NULL, value REAL, unit TEXT, method TEXT, period_from TEXT, period_to TEXT, geography TEXT, confidence TEXT NOT NULL, limitations TEXT, source_refs TEXT NOT NULL, created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS domain_scores (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, domain TEXT NOT NULL, score INTEGER NOT NULL, confidence TEXT NOT NULL, weight REAL NOT NULL, coverage REAL NOT NULL, created_at TEXT NOT NULL, UNIQUE(research_run_id, domain))",
                    "CREATE TABLE IF NOT EXISTS opportunity_scores (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, score_version TEXT NOT NULL, opportunity_score REAL NOT NULL, coverage_factor REAL NOT NULL, recommendation TEXT NOT NULL, alerts TEXT NOT NULL, exclusions TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(research_run_id))",
                    "CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE, format TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, tier TEXT NOT NULL DEFAULT 'free', created_at TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS usage_counters (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, period TEXT NOT NULL, run_count INTEGER NOT NULL DEFAULT 0, UNIQUE(user_id, period))",
                ]
                for stmt in statements:
                    self._execute(db, stmt)
                self._execute(db, "ALTER TABLE research_runs ADD COLUMN IF NOT EXISTS from_publication_date TEXT NOT NULL DEFAULT '2021-01-01'")
                self._execute(db, "INSERT INTO evidence_source_links (id, evidence_record_id, source_request_id, source, external_id, normalized_payload, created_at) SELECT 'legacy_' || id, id, source_request_id, source, external_id, normalized_payload, created_at FROM evidence_records ON CONFLICT DO NOTHING")
            else:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS research_runs (
                        id TEXT PRIMARY KEY,
                        query_original TEXT NOT NULL,
                        query_normalized TEXT NOT NULL,
                        taxonomy_version TEXT NOT NULL,
                        target_market TEXT NOT NULL,
                        application TEXT NOT NULL,
                        from_publication_date TEXT NOT NULL DEFAULT '2021-01-01',
                        cutoff_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        error TEXT
                    );

                    CREATE TABLE IF NOT EXISTS source_requests (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        source TEXT NOT NULL,
                        request_url TEXT NOT NULL,
                        request_params TEXT NOT NULL,
                        fetched_at TEXT,
                        http_status INTEGER,
                        checksum TEXT,
                        raw_object_key TEXT,
                        license TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error TEXT
                    );

                    CREATE TABLE IF NOT EXISTS evidence_records (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        source_request_id TEXT NOT NULL REFERENCES source_requests(id) ON DELETE RESTRICT,
                        source TEXT NOT NULL,
                        domain TEXT NOT NULL,
                        external_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        published_at TEXT,
                        geography TEXT,
                        normalized_payload TEXT NOT NULL,
                        dedupe_key TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(research_run_id, source, dedupe_key)
                    );

                    CREATE TABLE IF NOT EXISTS evidence_source_links (
                        id TEXT PRIMARY KEY,
                        evidence_record_id TEXT NOT NULL REFERENCES evidence_records(id) ON DELETE CASCADE,
                        source_request_id TEXT NOT NULL REFERENCES source_requests(id) ON DELETE RESTRICT,
                        source TEXT NOT NULL,
                        external_id TEXT NOT NULL,
                        normalized_payload TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(source_request_id, external_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_source_requests_run
                        ON source_requests(research_run_id);
                    CREATE INDEX IF NOT EXISTS idx_evidence_records_run
                        ON evidence_records(research_run_id);
                    CREATE INDEX IF NOT EXISTS idx_evidence_source_links_record
                        ON evidence_source_links(evidence_record_id);

                    CREATE TABLE IF NOT EXISTS taxonomies (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS synonyms (
                        id TEXT PRIMARY KEY,
                        taxonomy_id TEXT NOT NULL REFERENCES taxonomies(id),
                        term TEXT NOT NULL,
                        normalized TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS hs_mappings (
                        id TEXT PRIMARY KEY,
                        taxonomy_id TEXT NOT NULL REFERENCES taxonomies(id),
                        product_term TEXT NOT NULL,
                        hs_code TEXT NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS domain_summaries (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        domain TEXT NOT NULL,
                        summary_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(research_run_id, domain, summary_type)
                    );

                    CREATE TABLE IF NOT EXISTS claims (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        domain TEXT NOT NULL,
                        statement TEXT NOT NULL,
                        value REAL,
                        unit TEXT,
                        method TEXT,
                        period_from TEXT,
                        period_to TEXT,
                        geography TEXT,
                        confidence TEXT NOT NULL,
                        limitations TEXT,
                        source_refs TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS domain_scores (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        domain TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        confidence TEXT NOT NULL,
                        weight REAL NOT NULL,
                        coverage REAL NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(research_run_id, domain)
                    );

                    CREATE TABLE IF NOT EXISTS opportunity_scores (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        score_version TEXT NOT NULL,
                        opportunity_score REAL NOT NULL,
                        coverage_factor REAL NOT NULL,
                        recommendation TEXT NOT NULL,
                        alerts TEXT NOT NULL,
                        exclusions TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(research_run_id)
                    );

                    CREATE TABLE IF NOT EXISTS reports (
                        id TEXT PRIMARY KEY,
                        research_run_id TEXT NOT NULL REFERENCES research_runs(id) ON DELETE CASCADE,
                        format TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        tier TEXT NOT NULL DEFAULT 'free',
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS usage_counters (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        period TEXT NOT NULL,
                        run_count INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(user_id, period)
                    );
                    """
                )
                try:
                    db.execute("ALTER TABLE research_runs ADD COLUMN from_publication_date TEXT NOT NULL DEFAULT '2021-01-01'")
                except sqlite3.OperationalError:
                    pass
                db.execute(
                    """
                    INSERT OR IGNORE INTO evidence_source_links (
                        id, evidence_record_id, source_request_id, source, external_id,
                        normalized_payload, created_at
                    )
                    SELECT
                        'legacy_' || id, id, source_request_id, source, external_id,
                        normalized_payload, created_at
                    FROM evidence_records
                    """
                )

    def create_run(
        self,
        *,
        query_original: str,
        query_normalized: str,
        target_market: str,
        application: str,
        cutoff_at: str,
        from_publication_date: str = "2021-01-01",
        taxonomy_version: str = "cacao-functional-v1",
    ) -> dict[str, Any]:
        run_id = f"rr_{uuid.uuid4().hex}"
        created_at = _now()
        with self._transaction() as db:
            self._execute(db,
                """
                INSERT INTO research_runs (
                    id, query_original, query_normalized, taxonomy_version, target_market,
                    application, from_publication_date, cutoff_at, status, created_at
                ) VALUES (_ph(), _ph(), _ph(), _ph(), _ph(), _ph(), _ph(), _ph(), 'running', _ph())
                """,
                (
                    run_id,
                    query_original,
                    query_normalized,
                    taxonomy_version,
                    target_market,
                    application,
                    from_publication_date,
                    cutoff_at,
                    created_at,
                ),
            )
        return self.get_run(run_id)

    def start_source_request(
        self,
        *,
        research_run_id: str,
        source: str,
        request_url: str,
        request_params: dict[str, Any],
        license_name: str,
    ) -> str:
        request_id = f"sr_{uuid.uuid4().hex}"
        safe_request_url = _redact_sensitive_query_string(request_url)
        safe_request_params = _redact_sensitive_params(request_params)
        with self._transaction() as db:
            self._execute(db,
                """
                INSERT INTO source_requests (
                    id, research_run_id, source, request_url, request_params, license, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'running')
                """,
                (
                    request_id,
                    research_run_id,
                    source,
                    safe_request_url,
                    json.dumps(safe_request_params, sort_keys=True),
                    license_name,
                ),
            )
        return request_id

    def store_raw(self, content: bytes) -> tuple[str, str]:
        """Persist source content by digest and never mutate an existing object."""
        checksum = hashlib.sha256(content).hexdigest()
        object_key = f"{checksum}.json"
        object_path = self.raw_directory / object_key
        try:
            with object_path.open("xb") as raw_file:
                raw_file.write(content)
        except FileExistsError:
            pass
        return checksum, object_key

    def finish_source_request(
        self,
        *,
        request_id: str,
        http_status: int,
        raw_content: bytes,
    ) -> None:
        checksum, object_key = self.store_raw(raw_content)
        with self._transaction() as db:
            self._execute(db, 
                """
                UPDATE source_requests
                SET fetched_at=?, http_status=?, checksum=?, raw_object_key=?, status='completed', error=NULL
                WHERE id=?
                """,
                (_now(), http_status, checksum, object_key, request_id),
            )

    def fail_source_request(
        self,
        *,
        request_id: str,
        http_status: int | None,
        error: str,
        raw_content: bytes | None = None,
    ) -> None:
        checksum: str | None = None
        object_key: str | None = None
        if raw_content:
            checksum, object_key = self.store_raw(raw_content)
        with self._transaction() as db:
            self._execute(db, 
                """
                UPDATE source_requests
                SET fetched_at=?, http_status=?, checksum=?, raw_object_key=?, status='failed', error=?
                WHERE id=?
                """,
                (_now(), http_status, checksum, object_key, error, request_id),
            )

    def add_evidence(
        self,
        *,
        research_run_id: str,
        source_request_id: str,
        source: str,
        domain: str,
        external_id: str,
        title: str,
        published_at: str | None,
        geography: str | None,
        payload: dict[str, Any],
        dedupe_key: str,
    ) -> bool:
        with self._transaction() as db:
            existing = self._execute(db, 
                """
                SELECT id FROM evidence_records
                WHERE research_run_id=? AND dedupe_key=?
                """,
                (research_run_id, dedupe_key),
            ).fetchone()
            if existing is None:
                evidence_record_id = f"ev_{uuid.uuid4().hex}"
                self._execute(db, 
                    """
                    INSERT INTO evidence_records (
                        id, research_run_id, source_request_id, source, domain, external_id, title,
                        published_at, geography, normalized_payload, dedupe_key, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evidence_record_id,
                        research_run_id,
                        source_request_id,
                        source,
                        domain,
                        external_id,
                        title,
                        published_at,
                        geography,
                        json.dumps(payload, sort_keys=True),
                        dedupe_key,
                        _now(),
                    ),
                )
                inserted = True
            else:
                evidence_record_id = existing["id"]
                inserted = False
            self._execute(db, 
                """
                INSERT INTO evidence_source_links (
                    id, evidence_record_id, source_request_id, source, external_id,
                    normalized_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_request_id, external_id) DO NOTHING
                """,
                (
                    f"esl_{uuid.uuid4().hex}",
                    evidence_record_id,
                    source_request_id,
                    source,
                    external_id,
                    json.dumps(payload, sort_keys=True),
                    _now(),
                ),
            )
        return inserted

    def complete_run(self, run_id: str) -> None:
        with self._transaction() as db:
            self._execute(db, 
                "UPDATE research_runs SET status='completed', completed_at=?, error=NULL WHERE id=?",
                (_now(), run_id),
            )

    def fail_run(self, run_id: str, error: str) -> None:
        with self._transaction() as db:
            self._execute(db, 
                "UPDATE research_runs SET status='failed', completed_at=?, error=? WHERE id=?",
                (_now(), error, run_id),
            )

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._transaction() as db:
            row = self._execute(db, "SELECT * FROM research_runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return dict(row)

    def get_run_detail(self, run_id: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        with self._transaction() as db:
            sources = self._execute(db, 
                """
                SELECT id, source, request_url, request_params, fetched_at, http_status, checksum,
                       raw_object_key, license, status, error
                FROM source_requests WHERE research_run_id=? ORDER BY rowid
                """,
                (run_id,),
            ).fetchall()
            evidence = self._execute(db, 
                """
                SELECT id, source_request_id, source, domain, external_id, title, published_at,
                       geography, normalized_payload, dedupe_key, created_at
                FROM evidence_records WHERE research_run_id=? ORDER BY published_at DESC, id
                """,
                (run_id,),
            ).fetchall()
            source_links = self._execute(db, 
                """
                SELECT evidence_record_id, source_request_id, source, external_id, normalized_payload
                FROM evidence_source_links
                WHERE evidence_record_id IN (
                    SELECT id FROM evidence_records WHERE research_run_id=?
                )
                ORDER BY source, external_id
                """,
                (run_id,),
            ).fetchall()
            summaries = self._execute(db, 
                """
                SELECT domain, summary_type, payload
                FROM domain_summaries WHERE research_run_id=?
                """,
                (run_id,),
            ).fetchall()
        run["sources"] = [
            {**dict(row), "request_params": json.loads(row["request_params"])} for row in sources
        ]
        links_by_evidence: dict[str, list[dict[str, Any]]] = {}
        for row in source_links:
            link = dict(row)
            evidence_record_id = link.pop("evidence_record_id")
            link["normalized_payload"] = json.loads(link["normalized_payload"])
            links_by_evidence.setdefault(evidence_record_id, []).append(link)
        run["evidence"] = []
        for row in evidence:
            item = {**dict(row), "normalized_payload": json.loads(row["normalized_payload"])}
            item["source_links"] = links_by_evidence.get(item["id"], [])
            run["evidence"].append(item)
        run["summaries"] = {
            row["summary_type"]: json.loads(row["payload"]) for row in summaries
        }
        return run

    def get_raw_by_checksum(self, checksum: str) -> bytes | None:
        object_path = self.raw_directory / f"{checksum}.json"
        if object_path.exists():
            return object_path.read_bytes()
        return None

    def get_completed_request(self, request_url: str, request_params: dict[str, Any]) -> dict[str, Any] | None:
        params_json = json.dumps(request_params, sort_keys=True)
        with self._transaction() as db:
            row = self._execute(db, 
                """
                SELECT id, request_url, request_params, checksum, status, fetched_at
                FROM source_requests
                WHERE request_url=? AND request_params=? AND status='completed'
                LIMIT 1
                """,
                (request_url, params_json),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def create_taxonomy(self, *, name: str, version: str) -> dict[str, Any]:
        taxonomy_id = f"tx_{uuid.uuid4().hex}"
        created_at = _now()
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO taxonomies (id, name, version, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (taxonomy_id, name, version, created_at),
            )
        return {"id": taxonomy_id, "name": name, "version": version, "created_at": created_at}

    def get_taxonomy(self, name: str, version: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            row = self._execute(db, 
                "SELECT id, name, version, created_at FROM taxonomies WHERE name=? AND version=?",
                (name, version),
            ).fetchone()
        return dict(row) if row else None

    def add_synonym(self, *, taxonomy_id: str, term: str, normalized: str) -> None:
        synonym_id = f"sy_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO synonyms (id, taxonomy_id, term, normalized, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (synonym_id, taxonomy_id, term, normalized, _now()),
            )

    def get_synonyms(self, taxonomy_id: str) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                "SELECT term, normalized FROM synonyms WHERE taxonomy_id=?",
                (taxonomy_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_hs_mapping(self, *, taxonomy_id: str, product_term: str, hs_code: str, description: str | None = None) -> None:
        mapping_id = f"hs_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO hs_mappings (id, taxonomy_id, product_term, hs_code, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (mapping_id, taxonomy_id, product_term, hs_code, description, _now()),
            )

    def get_hs_mappings(self, taxonomy_id: str) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                "SELECT product_term, hs_code, description FROM hs_mappings WHERE taxonomy_id=?",
                (taxonomy_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_domain_summary(self, *, research_run_id: str, domain: str, summary_type: str, payload: dict[str, Any]) -> None:
        summary_id = f"dsm_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db,
                """
                INSERT INTO domain_summaries (id, research_run_id, domain, summary_type, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_run_id, domain, summary_type) DO UPDATE SET payload=excluded.payload
                """,
                (summary_id, research_run_id, domain, summary_type, json.dumps(payload, sort_keys=True), _now()),
            )

    def get_domain_summaries(self, research_run_id: str) -> dict[str, dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                "SELECT domain, summary_type, payload FROM domain_summaries WHERE research_run_id=?",
                (research_run_id,),
            ).fetchall()
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            result.setdefault(row["domain"], {})[row["summary_type"]] = json.loads(row["payload"])
        return result

    def save_claim(self, *, research_run_id: str, domain: str, statement: str, value: float | None, unit: str | None, method: str | None, period_from: str | None, period_to: str | None, geography: str | None, confidence: str, limitations: str | None, source_refs: list[str]) -> None:
        claim_id = f"clm_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO claims (id, research_run_id, domain, statement, value, unit, method, period_from, period_to, geography, confidence, limitations, source_refs, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (claim_id, research_run_id, domain, statement, value, unit, method, period_from, period_to, geography, confidence, limitations, json.dumps(source_refs), _now()),
            )

    def get_claims(self, research_run_id: str) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                "SELECT id, domain, statement, value, unit, method, period_from, period_to, geography, confidence, limitations, source_refs FROM claims WHERE research_run_id=?",
                (research_run_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "domain": row["domain"],
                "statement": row["statement"],
                "value": row["value"],
                "unit": row["unit"],
                "method": row["method"],
                "period": {"from": row["period_from"], "to": row["period_to"]} if row["period_from"] or row["period_to"] else None,
                "geography": row["geography"],
                "confidence": row["confidence"],
                "limitations": row["limitations"],
                "source_refs": json.loads(row["source_refs"]),
            }
            for row in rows
        ]

    def save_domain_score(self, *, research_run_id: str, domain: str, score: int, confidence: str, weight: float, coverage: float) -> None:
        score_id = f"ds_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO domain_scores (id, research_run_id, domain, score, confidence, weight, coverage, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_run_id, domain) DO UPDATE SET score=excluded.score, confidence=excluded.confidence, weight=excluded.weight, coverage=excluded.coverage
                """,
                (score_id, research_run_id, domain, score, confidence, weight, coverage, _now()),
            )

    def get_domain_scores(self, research_run_id: str) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                "SELECT domain, score, confidence, weight, coverage FROM domain_scores WHERE research_run_id=?",
                (research_run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_opportunity_score(self, *, research_run_id: str, score_version: str, opportunity_score: float, coverage_factor: float, recommendation: str, alerts: list[str], exclusions: list[str], dimensions: list[dict[str, Any]] | None = None) -> None:
        score_id = f"os_{uuid.uuid4().hex}"
        payload = {
            "score_version": score_version,
            "opportunity_score": opportunity_score,
            "coverage_factor": coverage_factor,
            "recommendation": recommendation,
            "alerts": alerts,
            "exclusions": exclusions,
            "dimensions": dimensions or [],
        }
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO opportunity_scores (id, research_run_id, score_version, opportunity_score, coverage_factor, recommendation, alerts, exclusions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_run_id) DO UPDATE SET score_version=excluded.score_version, opportunity_score=excluded.opportunity_score, coverage_factor=excluded.coverage_factor, recommendation=excluded.recommendation, alerts=excluded.alerts, exclusions=excluded.exclusions
                """,
                (score_id, research_run_id, score_version, opportunity_score, coverage_factor, recommendation, json.dumps(alerts), json.dumps(exclusions), _now()),
            )
            self._execute(db, 
                """
                INSERT OR REPLACE INTO reports (id, research_run_id, format, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"os_{research_run_id}", research_run_id, "opportunity_score", json.dumps(payload, sort_keys=True), _now()),
            )

    def get_opportunity_score(self, research_run_id: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            row = self._execute(db, 
                "SELECT score_version, opportunity_score, coverage_factor, recommendation, alerts, exclusions FROM opportunity_scores WHERE research_run_id=?",
                (research_run_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "score_version": row["score_version"],
            "opportunity_score": row["opportunity_score"],
            "coverage_factor": row["coverage_factor"],
            "recommendation": row["recommendation"],
            "alerts": json.loads(row["alerts"]),
            "exclusions": json.loads(row["exclusions"]),
        }

    def save_report(self, *, research_run_id: str, format: str, payload: dict[str, Any]) -> None:
        report_id = f"rp_{uuid.uuid4().hex}"
        with self._transaction() as db:
            self._execute(db, 
                """
                INSERT INTO reports (id, research_run_id, format, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (report_id, research_run_id, format, json.dumps(payload, sort_keys=True), _now()),
            )

    def get_report(self, research_run_id: str, format: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            row = self._execute(db, 
                "SELECT payload FROM reports WHERE research_run_id=? AND format=? ORDER BY created_at DESC LIMIT 1",
                (research_run_id, format),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def count_evidence_by_source(self, research_run_id: str, domain: str) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db,
                """
                SELECT source, COUNT(*) as count
                FROM evidence_records
                WHERE research_run_id=? AND domain=?
                GROUP BY source
                """,
                (research_run_id, domain),
            ).fetchall()
        return [{"source": row["source"], "count": row["count"]} for row in rows]

    def get_connector_stats(self) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                """
                SELECT source, COUNT(*) as total_requests, SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed, MAX(fetched_at) as last_fetched, AVG(CASE WHEN status='completed' THEN 1.0 ELSE 0.0 END) as success_rate
                FROM source_requests
                GROUP BY source
                ORDER BY source
                """,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_freshness(self) -> list[dict[str, Any]]:
        with self._transaction() as db:
            rows = self._execute(db, 
                """
                SELECT source, MAX(fetched_at) as last_fetched, COUNT(*) as total
                FROM source_requests
                WHERE status='completed'
                GROUP BY source
                ORDER BY source
                """,
            ).fetchall()
        return [dict(row) for row in rows]

    def create_user(self, *, email: str, password_hash: str, tier: str = "free") -> dict[str, Any]:
        user_id = f"usr_{uuid.uuid4().hex}"
        created_at = _now()
        with self._transaction() as db:
            self._execute(db,
                "INSERT INTO users (id, email, password_hash, tier, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, password_hash, tier, created_at),
            )
        return self.get_user_by_id(user_id)  # type: ignore[return-value]

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            row = self._execute(db, "SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            row = self._execute(db, "SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def set_user_tier(self, user_id: str, tier: str) -> dict[str, Any] | None:
        with self._transaction() as db:
            self._execute(db, "UPDATE users SET tier=? WHERE id=?", (tier, user_id))
        return self.get_user_by_id(user_id)

    def get_and_increment_usage(self, *, user_id: str, period: str, limit: int | None) -> int | None:
        """Atomically increments and returns the new run_count, or returns None
        (without incrementing) if the increment would exceed `limit`. The
        increment is a single conditional UPDATE (not read-then-write in
        Python) so concurrent requests near the limit can't both slip through."""
        counter_id = f"uc_{uuid.uuid4().hex}"
        with self._transaction() as db:
            if self._backend == "postgresql":
                self._execute(db,
                    "INSERT INTO usage_counters (id, user_id, period, run_count) VALUES (?, ?, ?, 0) "
                    "ON CONFLICT (user_id, period) DO NOTHING",
                    (counter_id, user_id, period),
                )
            else:
                self._execute(db,
                    "INSERT OR IGNORE INTO usage_counters (id, user_id, period, run_count) VALUES (?, ?, ?, 0)",
                    (counter_id, user_id, period),
                )
            if limit is None:
                cursor = self._execute(db,
                    "UPDATE usage_counters SET run_count = run_count + 1 WHERE user_id=? AND period=?",
                    (user_id, period),
                )
            else:
                cursor = self._execute(db,
                    "UPDATE usage_counters SET run_count = run_count + 1 WHERE user_id=? AND period=? AND run_count < ?",
                    (user_id, period, limit),
                )
            if cursor.rowcount != 1:
                return None
            row = self._execute(
                db, "SELECT run_count FROM usage_counters WHERE user_id=? AND period=?", (user_id, period)
            ).fetchone()
        return row["run_count"]

    def get_usage(self, *, user_id: str, period: str) -> int:
        with self._transaction() as db:
            row = self._execute(
                db, "SELECT run_count FROM usage_counters WHERE user_id=? AND period=?", (user_id, period)
            ).fetchone()
        return row["run_count"] if row else 0

    def get_quota_usage(self) -> list[dict[str, Any]]:
        with self._transaction() as db:
            if self._backend == "postgresql":
                rows = self._execute(db,
                    """
                    SELECT source, COUNT(*) as request_count, SUM(CASE WHEN http_status=429 THEN 1 ELSE 0 END) as rate_limited
                    FROM source_requests
                    WHERE fetched_at >= NOW() - INTERVAL '1 day'
                    GROUP BY source
                    ORDER BY source
                    """,
                ).fetchall()
            else:
                rows = self._execute(db,
                    """
                    SELECT source, COUNT(*) as request_count, SUM(CASE WHEN http_status=429 THEN 1 ELSE 0 END) as rate_limited
                    FROM source_requests
                    WHERE fetched_at >= datetime('now', '-1 day')
                    GROUP BY source
                    ORDER BY source
                    """,
                ).fetchall()
        return [dict(row) for row in rows]
