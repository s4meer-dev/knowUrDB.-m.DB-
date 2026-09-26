import logging
from typing import Any

from app.core.mongodb import MongoDBManager
from app.models.source import SourceStatus

logger = logging.getLogger("knowurdb.registry")


class RegistryService:
    """
    Deterministic Platform Registry Service for KnowUrDB.
    Provides authoritative access to the central KnowUrDB source and dataset catalogs
    (backed by `knowurdb.datasets`, `knowurdb.sources`, and `knowurdb.generations` on port 27018)
    without performing unnecessary document scans or LLM calls.
    """

    def __init__(self):
        pass

    def _get_db(self):
        return MongoDBManager.get_db()

    def count_datasets(self) -> int:
        """Returns total active datasets registered in KnowUrDB."""
        db = self._get_db()
        cnt = db[MongoDBManager.SYS_DATASETS].count_documents({"status": {"$ne": "deleted"}})
        if cnt == 0:
            # Fallback to counting managed sources in SYS_SOURCES
            cnt = db[MongoDBManager.SYS_SOURCES].count_documents(
                {"status": {"$ne": SourceStatus.DELETED.value}}
            )
        return cnt

    def list_datasets(self) -> list[dict[str, Any]]:
        """Returns all registered datasets with metadata, collection counts, and document counts."""
        db = self._get_db()
        ds_cursor = list(
            db[MongoDBManager.SYS_DATASETS].find(
                {"status": {"$ne": "deleted"}},
                {"_id": 0},
            ).sort("created_at", -1)
        )
        if ds_cursor:
            # Enrich with collection names and document counts if missing
            sources = {
                s.get("dataset_id") or s.get("source_id"): s
                for s in db[MongoDBManager.SYS_SOURCES].find({}, {"_id": 0})
            }
            results = []
            for d in ds_cursor:
                did = d.get("dataset_id")
                src = sources.get(did) or sources.get(d.get("source_id"))
                cols = d.get("collections") or (src.get("collections") if src else [])
                results.append(
                    {
                        "dataset_id": d.get("dataset_id") or (src.get("source_id") if src else "unknown"),
                        "source_id": d.get("source_id") or (src.get("source_id") if src else None),
                        "database_name": d.get("database_name") or (src.get("database_name") if src else None),
                        "display_name": d.get("display_name") or (src.get("display_name") if src else d.get("name")),
                        "domain": d.get("domain") or (src.get("domain") if src else "general"),
                        "description": d.get("description") or (src.get("description") if src else ""),
                        "collection_count": d.get("collection_count") or len(cols),
                        "document_count": d.get("document_count") or (src.get("record_count") if src else 0),
                        "collections": cols,
                        "status": d.get("status") or "ready",
                        "created_at": d.get("created_at"),
                    }
                )
            return results

        # Fallback: construct dataset entries from SYS_SOURCES
        sources = list(
            db[MongoDBManager.SYS_SOURCES].find(
                {"status": {"$ne": SourceStatus.DELETED.value}},
                {"_id": 0},
            ).sort("uploaded_at", -1)
        )
        results = []
        for s in sources:
            cols = s.get("collections", [])
            results.append(
                {
                    "dataset_id": s.get("dataset_id") or s.get("source_id"),
                    "source_id": s.get("source_id"),
                    "database_name": s.get("database_name"),
                    "display_name": s.get("display_name") or s.get("name"),
                    "domain": s.get("domain") or "general",
                    "description": s.get("description") or s.get("schema_summary") or "",
                    "collection_count": s.get("table_count") or len(cols),
                    "document_count": s.get("record_count") or 0,
                    "collections": cols,
                    "status": s.get("status") or "ready",
                    "created_at": s.get("uploaded_at"),
                }
            )
        return results

    def get_dataset(self, identifier: str) -> dict[str, Any] | None:
        """Finds a dataset by dataset_id, source_id, or database_name."""
        datasets = self.list_datasets()
        for d in datasets:
            if (
                d.get("dataset_id") == identifier
                or d.get("source_id") == identifier
                or d.get("database_name") == identifier
            ):
                return d
        return None

    def get_active_dataset(self) -> dict[str, Any] | None:
        """Returns the currently active dataset based on MongoDBManager active source."""
        active_sid = MongoDBManager.get_active_source_id()
        if not active_sid:
            return None
        return self.get_dataset(active_sid)

    ENTITY_SYNONYMS: dict[str, list[str]] = {
        "product": ["skus", "products", "items"],
        "products": ["skus", "products", "items"],
        "item": ["skus", "products", "items"],
        "items": ["skus", "products", "items"],
        "sku": ["skus"],
        "skus": ["skus"],
        "loan": ["loan_accounts", "loans"],
        "loans": ["loan_accounts", "loans"],
        "account": ["loan_accounts", "clients"],
        "accounts": ["loan_accounts", "clients"],
        "card": ["credit_cards", "cards"],
        "cards": ["credit_cards", "cards"],
        "credit_card": ["credit_cards"],
        "credit_cards": ["credit_cards"],
        "transfer": ["wire_transfers", "transfers"],
        "transfers": ["wire_transfers", "transfers"],
        "wire": ["wire_transfers"],
        "risk": ["risk_assessments"],
        "hotel": ["hotels"],
        "hotels": ["hotels"],
        "room": ["rooms"],
        "rooms": ["rooms"],
        "guest": ["guests"],
        "guests": ["guests"],
        "reservation": ["reservations"],
        "reservations": ["reservations"],
        "booking": ["reservations"],
        "bookings": ["reservations"],
        "concierge": ["concierge_services"],
        "service": ["concierge_services"],
        "services": ["concierge_services"],
        "store": ["stores"],
        "stores": ["stores"],
        "transaction": ["pos_transactions"],
        "transactions": ["pos_transactions"],
        "pos": ["pos_transactions"],
        "supplier": ["suppliers"],
        "suppliers": ["suppliers"],
        "loyalty": ["loyalty_members"],
        "member": ["loyalty_members"],
        "members": ["loyalty_members"],
        "client": ["clients"],
        "clients": ["clients"],
        "customer": ["clients", "loyalty_members", "customers"],
        "customers": ["clients", "loyalty_members", "customers"],
    }

    def find_datasets_matching_entity(self, entity_or_collection: str) -> list[dict[str, Any]]:
        """
        Scans all registered datasets to find which datasets contain the given collection or entity.
        Used when ALL SOURCES is active to resolve dataset ambiguity.
        """
        token = entity_or_collection.strip().lower()
        token_singular = token.rstrip("s")
        synonyms = set(self.ENTITY_SYNONYMS.get(token, []) + self.ENTITY_SYNONYMS.get(token_singular, []))
        synonyms.add(token)
        synonyms.add(token_singular)

        datasets = self.list_datasets()
        matched = []

        for ds in datasets:
            cols = [c.lower() for c in ds.get("collections", [])]
            # Exact, singular, or synonym collection match
            if any(syn in cols or syn in [c.rstrip("s") for c in cols] for syn in synonyms):
                matched.append(ds)
                continue
            # Substring match in collection name (e.g. "loan" in "loan_accounts")
            if any(token in c or token_singular in c for c in cols if len(token) > 2):
                matched.append(ds)
                continue
            # Domain or display name match
            ds_name = (ds.get("display_name") or "").lower()
            ds_domain = (ds.get("domain") or "").lower()
            if (
                token in ds_name
                or token in ds_domain
                or (len(token) > 3 and token_singular in ds_name)
            ):
                matched.append(ds)
                continue

        return matched

    def get_dataset_collections(self, identifier: str) -> list[str]:
        """Returns the list of collection names belonging to a dataset."""
        ds = self.get_dataset(identifier)
        if ds and ds.get("collections"):
            return ds["collections"]
        return []

    def count_generations(self) -> int:
        """Returns total generated database lifecycle events recorded."""
        db = self._get_db()
        return db[MongoDBManager.SYS_GENERATIONS].count_documents({})
