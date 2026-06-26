from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionState:
    ask_mode: str = "search"
    search_mode: str = "hybrid"
    limit: int = 10
    filters: dict[str, str] = field(default_factory=dict)

    def api_filters(self) -> dict[str, dict[str, str]]:
        return {key: {"eq": value} for key, value in self.filters.items()}
