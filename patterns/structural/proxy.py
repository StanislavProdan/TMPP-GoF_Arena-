# DESIGN PATTERN: Proxy
# In this program, Proxy lazily loads and caches match history files before exposing them to the user.

from __future__ import annotations

from pathlib import Path


class MatchHistoryReader:
    """Real subject that performs filesystem access for match history."""

    def __init__(self, history_dir: Path):
        self.history_dir = history_dir

    def list_matches(self) -> list[Path]:
        if not self.history_dir.exists():
            return []
        return sorted(self.history_dir.glob("match_*.txt"), reverse=True)

    def read_match(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")


class MatchHistoryProxy:
    """Lazy-loading proxy that instantiates the real reader only when needed."""

    def __init__(self, history_dir: str | Path = "match_history"):
        self.history_dir = Path(history_dir)
        self._reader: MatchHistoryReader | None = None
        self._match_cache: list[Path] | None = None

    def _get_reader(self) -> MatchHistoryReader:
        if self._reader is None:
            self._reader = MatchHistoryReader(self.history_dir)
        return self._reader

    def list_matches(self) -> list[Path]:
        if self._match_cache is None:
            self._match_cache = self._get_reader().list_matches()
        return list(self._match_cache)

    def latest_matches(self, limit: int = 3) -> list[Path]:
        return self.list_matches()[:limit]

    def preview(self, path: Path, line_count: int = 6) -> str:
        lines = self._get_reader().read_match(path).splitlines()
        return "\n".join(lines[:line_count])

    @property
    def cache_loaded(self) -> bool:
        return self._match_cache is not None
