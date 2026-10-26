"""Bounded metadata-only time enumeration; keyword matching stays native."""


class TimeCandidateStream:
    """Enumerate existing message metadata, then let History validate membership."""

    def __init__(self, conn, *, roles, start_time, end_time, limit=200):
        self.budget = min(10000, max(1000, 20 * limit))
        self.examined = 0
        placeholders = ",".join("?" for _ in roles)
        self.cursor = conn.execute(
            "SELECT id,session_id,message_uid,role,timestamp FROM messages WHERE "
            "timestamp>=? AND timestamp<=? AND role IN (" + placeholders + ") "
            "AND COALESCE(display_kind,'')<>'hidden' ORDER BY timestamp,id LIMIT ?",
            (start_time, end_time, *roles, self.budget + 1))
        self.peek = self.cursor.fetchone()

    def next_batch(self):
        result = []
        while self.peek is not None and self.examined < self.budget and len(result) < 200:
            result.append(dict(self.peek))
            self.examined += 1
            self.peek = self.cursor.fetchone()
        return result

    def diagnostics(self):
        return {"budget_exhausted": self.peek is not None, "index_incomplete": False,
                "exhausted": self.peek is None, "route": "message_time", "order": "time",
                "degraded": False, "warnings": []}

    def matches_row_id(self, row_id):
        return True  # Winner timestamp and source are independently revalidated.

    def close(self):
        self.cursor.close()
