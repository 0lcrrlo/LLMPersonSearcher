from typing import Protocol

from person_searcher.domain.models import PersonSearchCondition


class QueryParser(Protocol):
    def parse(self, query: str) -> PersonSearchCondition:
        """Parse a user query into validated search conditions."""
