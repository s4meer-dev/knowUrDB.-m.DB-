from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ScopeType(str, Enum):
    ALL_SOURCES = "ALL_SOURCES"
    DATASET = "DATASET"
    COLLECTION = "COLLECTION"
    DATABASE = "DATABASE"


class QueryScopeModel(BaseModel):
    """
    Formal representation of the user's active analytical scope.
    Guarantees frontend and backend share an identical source-of-truth scope.
    """
    scope_type: ScopeType = Field(
        default=ScopeType.ALL_SOURCES,
        description="Active scope type: ALL_SOURCES, DATASET, COLLECTION, or DATABASE"
    )
    dataset_id: str | None = Field(
        default=None,
        description="Selected dataset identifier (e.g. demo_banking_0cc3 or mongodb_demo_banking_0cc3)"
    )
    dataset_name: str | None = Field(
        default=None,
        description="Human-readable title of the selected dataset"
    )
    collection_name: str | None = Field(
        default=None,
        description="Selected MongoDB collection name (e.g. customers, orders, students)"
    )
    database_name: str | None = Field(
        default=None,
        description="Physical MongoDB database name if applicable (e.g. demo_database)"
    )

    def is_all_sources(self) -> bool:
        return self.scope_type == ScopeType.ALL_SOURCES or (not self.dataset_id and not self.collection_name)

    def is_dataset_scoped(self) -> bool:
        return self.scope_type == ScopeType.DATASET and bool(self.dataset_id) and not self.collection_name

    def is_collection_scoped(self) -> bool:
        return bool(self.collection_name) or self.scope_type == ScopeType.COLLECTION

    @classmethod
    def all_sources(cls) -> "QueryScopeModel":
        return cls(scope_type=ScopeType.ALL_SOURCES)

    @classmethod
    def for_dataset(cls, dataset_id: str, dataset_name: str | None = None) -> "QueryScopeModel":
        return cls(
            scope_type=ScopeType.DATASET,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

    @classmethod
    def for_collection(
        cls,
        dataset_id: str,
        collection_name: str,
        dataset_name: str | None = None,
    ) -> "QueryScopeModel":
        return cls(
            scope_type=ScopeType.COLLECTION,
            dataset_id=dataset_id,
            collection_name=collection_name,
            dataset_name=dataset_name,
        )
