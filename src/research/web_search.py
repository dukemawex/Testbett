from dataclasses import dataclass
from typing import Protocol, List


@dataclass
class SearchResult:
    title: str
    snippet: str
    url: str


class WebSearchProtocol(Protocol):
    def search(self, query: str) -> List[SearchResult]: ...


class StubWebSearch:
    def search(self, query: str) -> List[SearchResult]:
        return []  # No results by default (offline safe)


def get_web_search(api_key: str = "") -> WebSearchProtocol:
    return StubWebSearch()
