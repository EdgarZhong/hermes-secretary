"""Read-only, single-query candidate stream over Hermes' existing search indexes.

This internal adapter deliberately does not call search_messages(offset=...): that
public API may repeat the rebuild gap and change routes on a later empty page.
The caller supplies one read transaction and closes the stream before leaving it.
No FTS repair, index creation, Session binding or transcript write happens here.
"""

from collections import deque
from dataclasses import dataclass
import re
import sqlite3

from hermes_state_common import FTS_CJK_STALE_KEY, FTS_STALE_KEY, MAX_FTS5_QUERY_CHARS
from hermes_state_search import SessionSearchMixin


class CandidateQueryError(ValueError):
    """The requested query is not in the supported FTS expression subset."""


class CandidateUnavailableError(RuntimeError):
    """A search route or its completeness evidence could not be read."""


_TOKEN = re.compile(r'"(?:[^"]|"")*"\*?|[^\s"]+')
_OPERATORS = {"AND", "OR", "NOT"}


def prepare_query(query):
    """Validate before native sanitizing, which otherwise repairs invalid queries."""
    if not isinstance(query, str) or not query.strip():
        raise CandidateQueryError("Search requires a nonempty query.")
    if len(query) > MAX_FTS5_QUERY_CHARS:
        raise CandidateQueryError("The query exceeds the native FTS query length limit.")
    tokens, end, need_term = [], 0, True
    for match in _TOKEN.finditer(query):
        if query[end:match.start()].strip():
            raise CandidateQueryError("Use balanced quoted phrases and supported FTS operators.")
        token = match.group()
        if token.upper() in _OPERATORS:
            token = token.upper()
            if need_term:
                raise CandidateQueryError("An FTS operator must follow a search term.")
            need_term = True
        else:
            if token == "NEAR" or any(c in token for c in "\x00\r\n"):
                raise CandidateQueryError("Use words, quoted phrases, AND/OR/NOT or prefix*.")
            literal = token.rstrip("*")
            if literal.startswith('"'):
                literal = literal[1:-1].replace('""', '"')
            elif '"' in literal or "*" in literal or not any(char.isalnum() for char in literal):
                raise CandidateQueryError("A prefix wildcard is allowed only at the end of a term.")
            if not literal.strip():
                raise CandidateQueryError("A search term cannot be empty.")
            need_term = False
        tokens.append(token)
        end = match.end()
    if query[end:].strip() or need_term:
        raise CandidateQueryError("The query has an unmatched quote or a trailing operator.")
    sanitized = SessionSearchMixin._sanitize_fts5_query(" ".join(tokens))
    if not sanitized:
        raise CandidateQueryError("The query contains no searchable terms.")
    return sanitized


def positive_terms(query):
    """Literal positive units for excerpts, never terms following NOT."""
    result, negated = [], False
    for token in _TOKEN.findall(query):
        if token in _OPERATORS:
            negated = token == "NOT"
            continue
        term = token.rstrip("*")
        if term.startswith('"') and term.endswith('"'):
            term = term[1:-1].replace('""', '"')
        if not negated and term and term not in result:
            result.append(term)
        negated = False
    return result


@dataclass(frozen=True)
class _Route:
    name: str
    query: str
    table: str | None = None


class HistoryCandidateStream:
    """Internal bounded physical candidates; no model-facing cursor or scroll API.

    next_batch() -> list[{id, session_id, message_uid, role, timestamp}].
    diagnostics() reports the actual pinned route, query, degradation, exhaustion
    and candidate budget. A fresh call creates a fresh stream; this object never
    outlives its caller-owned read transaction.
    """

    def __init__(self, db, conn, query, *, limit=20, roles=None, start_time=None, end_time=None):
        self.db, self.conn = db, conn
        self.query = prepare_query(query)
        self.budget = min(10000, max(1000, 20 * limit))
        self.batch_size = 200
        self.roles, self.start_time, self.end_time = roles, start_time, end_time
        self._cursors, self._queue = [], deque()
        self._seen, self._peek = set(), None
        self.examined = 0
        self.warnings = []
        self.gaps = []
        self.route = None
        try:
            self._base_gap = self._gap("fts_rebuild")
            self._cjk_gap = self._gap("fts_cjk_rebuild")
            self._select_route()
            self._peek = self._next_unique()
        except sqlite3.Error as exc:
            self.close()
            raise CandidateUnavailableError("The native search route could not be read.") from exc
        except BaseException:
            self.close()
            raise

    def _meta(self, key):
        row = self.conn.execute("SELECT value FROM state_meta WHERE key=?", (key,)).fetchone()
        return None if row is None else row[0]

    def _gap(self, prefix):
        high, progress = self._meta(prefix + "_high_water"), self._meta(prefix + "_progress")
        if high is None:
            return None
        try:
            high, progress = int(high), int(progress or 0)
        except (TypeError, ValueError) as exc:
            raise CandidateUnavailableError("Native index backfill progress is unavailable.") from exc
        if high <= 0:
            return None  # Same sentinel as the native deferred-rebuild reader.
        if not 0 <= progress <= high:
            raise CandidateUnavailableError("Native index backfill progress is inconsistent.")
        return (progress, high) if progress < high else None

    def _filters(self):
        # Do not apply native default inactive filtering: a live fork may still
        # reference an inactive source. Logical visibility is checked afterwards.
        clauses, params = ["COALESCE(m.display_kind, '') <> 'hidden'"], []
        if self.roles is not None:
            if not self.roles:
                clauses.append("0")
            else:
                clauses.append("m.role IN (" + ",".join("?" for _ in self.roles) + ")")
                params.extend(self.roles)
        if self.start_time is not None:
            clauses.append("m.timestamp >= ?")
            params.append(self.start_time)
        if self.end_time is not None:
            clauses.append("m.timestamp <= ?")
            params.append(self.end_time)
        return clauses, params

    def _sql(self, route, *, gaps=(), row_id=None):
        clauses, params = self._filters()
        if route.table:
            source = f"{route.table} JOIN messages m ON m.id={route.table}.rowid"
            clauses.insert(0, f"{route.table} MATCH ?")
            params.insert(0, route.query)
            order = "rank, m.id"
        else:
            source = "messages m"
            predicate, like_params, anchor = self.db._compile_like_boolean_query(route.query)
            if not predicate or anchor is None:
                raise CandidateQueryError("The query contains no searchable positive terms.")
            clauses.insert(0, "(" + predicate + ")")
            params = [*like_params, *params]
            order = "m.timestamp DESC, m.id DESC"
        if gaps:
            clauses.append("(" + " OR ".join("(m.id > ? AND m.id <= ?)" for _ in gaps) + ")")
            params.extend(value for gap in gaps for value in gap)
        if row_id is not None:
            clauses.append("m.id=?")
            params.append(row_id)
        sql = ("SELECT m.id, m.session_id, m.message_uid, m.role, m.timestamp FROM " + source
               + " WHERE " + " AND ".join(clauses) + " ORDER BY " + order + " LIMIT ?")
        params.append(1 if row_id is not None else self.budget + 1)
        return sql, params

    def _open(self, route, *, gaps=()):
        cursor = self.conn.execute(*self._sql(route, gaps=gaps))
        self._cursors.append(cursor)
        first = cursor.fetchone()
        return cursor, first

    def _try(self, route, *, optional=False):
        gaps = [] if not route.table else [g for g in (self._base_gap,
                self._cjk_gap if route.table == "messages_fts_cjk" else None) if g]
        opened = []
        try:
            opened.append(self._open(route))
            if gaps:
                opened.append(self._open(_Route("gap_like", route.query), gaps=gaps))
        except sqlite3.OperationalError as exc:
            text = str(exc).lower()
            if "syntax error" in text or "unterminated string" in text or "fts5: phrase" in text:
                raise CandidateQueryError("The native FTS parser rejected this query.") from exc
            if not optional or not any(part in text for part in ("no such table", "no such tokenizer", "no such module")):
                raise
            self.warnings.append("An optional native substring index was unavailable.")
            for cursor, _ in opened:
                cursor.close()
            return False
        if not any(first is not None for _, first in opened):
            for cursor, _ in opened:
                cursor.close()
            return False
        self.route, self.gaps = route, gaps
        for cursor, first in opened:
            if first is not None:
                self._queue.append((cursor, first))
        if gaps:
            self.warnings.append("Native index backfill is incomplete; its gap was searched with literal predicates.")
        return True

    def _select_route(self):
        stale = bool(getattr(self.db, "_fts_stale", False)) or self._meta(FTS_STALE_KEY) is not None
        if stale or (self.roles is not None and "tool" in self.roles):
            route = _Route("like_stale" if stale else "like_tool_body", self.query)
            self.warnings.append("Native literal substring fallback was used instead of token-exact FTS.")
            self._try(route)
            self.route = self.route or route
            return
        if not getattr(self.db, "_fts_enabled", False):
            raise CandidateUnavailableError("Native search indexes are unavailable.")
        cjk = self.db._contains_cjk(self.query)
        cjk_available = (getattr(self.db, "_fts_cjk_available", False)
                         and self._meta(FTS_CJK_STALE_KEY) is None)
        if cjk:
            # Keep the native query's phrases and Boolean syntax intact. Quoting
            # whitespace-separated tokens here would break a multiword phrase.
            if cjk_available and not self.db._has_lone_cjk_run(self.query):
                route = _Route("fts_cjk", self.query, "messages_fts_cjk")
                if self._try(route, optional=True):
                    return
                # A successfully queried empty CJK index is not an excuse to OR
                # the query. The same-expression LIKE route remains a native fallback.
            if self.db._trigram_route_ok(self.query):
                if self._try(_Route("trigram", self.query, "messages_fts_trigram"), optional=True):
                    return
            route = _Route("like_cjk", self.query)
            self.warnings.append("Native literal CJK substring fallback was used.")
            self._try(route)
            self.route = self.route or route
            return
        exact = _Route("fts5", self.query, "messages_fts")
        if self._try(exact):
            return
        if cjk_available and self._try(_Route("fts_cjk_substring", self.query, "messages_fts_cjk"), optional=True):
            self.warnings.append("The empty native token query used the CJK substring index.")
            return
        if getattr(self.db, "_trigram_available", False) and self.db._trigram_eligible_tokens(self.query):
            if self._try(_Route("trigram_substring", self.query, "messages_fts_trigram"), optional=True):
                self.warnings.append("The empty native token query used the trigram substring index.")
                return
        relaxed = self.db._or_relaxed_query(self.query)
        if relaxed and self._try(_Route("fts5_or_relaxed", relaxed, "messages_fts")):
            self.warnings.append("The initial native query had no candidates; native OR relaxation was used.")
            return
        # All initial routes were actually read and empty. Later empty batches
        # cannot trigger any further fallback or OR query.
        self.route = exact

    def _next_unique(self):
        while self._queue:
            cursor, row = self._queue.popleft()
            following = cursor.fetchone()
            if following is not None:
                self._queue.append((cursor, following))
            if row["id"] not in self._seen:
                self._seen.add(row["id"])
                return dict(row)
        return None

    def next_batch(self):
        rows = []
        try:
            while self._peek is not None and len(rows) < self.batch_size and self.examined < self.budget:
                rows.append(self._peek)
                self.examined += 1
                self._peek = self._next_unique()
        except sqlite3.Error as exc:
            raise CandidateUnavailableError("The pinned native candidate stream failed during reading.") from exc
        return rows

    def matches_row_id(self, row_id):
        """Recheck a canonical winner, not just a copied UID, on the pinned route."""
        try:
            if self.conn.execute(*self._sql(self.route, row_id=row_id)).fetchone() is not None:
                return True
            if self.gaps:
                return self.conn.execute(*self._sql(_Route("gap_like", self.route.query),
                                                    gaps=self.gaps, row_id=row_id)).fetchone() is not None
            return False
        except sqlite3.Error as exc:
            raise CandidateUnavailableError("The current source could not be checked against the native query.") from exc

    def matches_projection(self, content, tool_name, tool_calls):
        """Native literal predicate for a compaction carrier's original-user slice.

        Physical MATCH can hit a removed handoff. It is never sufficient evidence
        for that slice. This check uses the existing canonical fallback predicate;
        the caller marks the changed projection as a degraded, partial result.
        """
        predicate, params, _ = self.db._compile_like_boolean_query(self.route.query)
        sql = ("SELECT 1 FROM (SELECT ? AS content, ? AS tool_name, ? AS tool_calls) m WHERE " + predicate)
        try:
            return self.conn.execute(sql, [content, tool_name, tool_calls, *params]).fetchone() is not None
        except sqlite3.Error as exc:
            raise CandidateUnavailableError("The visible original content could not be checked.") from exc

    def diagnostics(self):
        exhausted = self._peek is None
        return {"route": self.route.name, "actual_query": self.route.query,
                "degraded": bool(self.warnings), "warnings": list(dict.fromkeys(self.warnings)),
                "examined": self.examined, "budget": self.budget, "exhausted": exhausted,
                "budget_exhausted": self.examined >= self.budget and not exhausted}

    def close(self):
        for cursor in self._cursors:
            cursor.close()
        self._cursors.clear()
        self._queue.clear()
