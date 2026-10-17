import os
import shutil
import json
import logging
from typing import List, Optional, Dict
from datetime import datetime
from app.models.job import ApplicationTrackerItem
from app.storage.file_utils import file_lock, atomic_write_json

logger = logging.getLogger("TrackerStore")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "tracker_applications.json")

LEGACY_UNASSIGNED_ID = "legacy_unassigned"

class TrackerStore:
    def __init__(self, filepath: Optional[str] = None):
        self.storage_file = filepath or STORAGE_FILE
        self.data_dir = os.path.dirname(self.storage_file)
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.storage_file):
            with file_lock(self.storage_file):
                atomic_write_json(self.storage_file, {})
        else:
            self._migrate_legacy_records_if_needed()

    def _migrate_legacy_records_if_needed(self):
        """
        Inspects stored tracker records. If any record lacks a valid candidate_id,
        safely creates a timestamped backup before marking them as 'legacy_unassigned'
        for explicit review, rather than silently assigning them to any candidate.
        """
        with file_lock(self.storage_file, shared=False):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    raw_dict = json.load(f)
            except Exception as e:
                logger.error(f"Error checking tracker storage for legacy records: {e}")
                return

            needs_migration = False
            for v in raw_dict.values():
                if isinstance(v, dict) and not v.get("candidate_id"):
                    needs_migration = True
                    break

            if needs_migration:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{self.storage_file}.bak.{timestamp}"
                try:
                    shutil.copy2(self.storage_file, backup_file)
                    logger.info(f"Backed up legacy tracker file to {backup_file}")
                except Exception as b_err:
                    logger.error(f"Failed to create tracker backup: {b_err}")
                    return

                migrated_count = 0
                for item_id, v in raw_dict.items():
                    if isinstance(v, dict) and not v.get("candidate_id"):
                        v["candidate_id"] = LEGACY_UNASSIGNED_ID
                        existing_notes = v.get("notes") or ""
                        migration_notice = "[Notice: Legacy unassigned record migrated for explicit candidate assignment]"
                        if migration_notice not in existing_notes:
                            v["notes"] = f"{existing_notes} {migration_notice}".strip()
                        v["updated_at"] = datetime.utcnow().isoformat()
                        migrated_count += 1

                atomic_write_json(self.storage_file, raw_dict)
                logger.info(f"Safely migrated {migrated_count} legacy tracker records with backup.")

    def _read_data(self) -> Dict[str, dict]:
        with file_lock(self.storage_file, shared=True):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading tracker storage: {e}")
                return {}

    def _write_data(self, data: Dict[str, dict]):
        with file_lock(self.storage_file, shared=False):
            atomic_write_json(self.storage_file, data)

    def list_applications(
        self,
        candidate_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ApplicationTrackerItem]:
        """
        Returns tracked applications.
        If candidate_id is specified, strictly scopes results to that candidate.
        Legacy unassigned records are excluded from standard candidate listings.
        """
        raw_dict = self._read_data()
        items: List[ApplicationTrackerItem] = []
        for v in raw_dict.values():
            try:
                item = ApplicationTrackerItem(**v)
                # Strict candidate scoping
                if candidate_id is not None and item.candidate_id != candidate_id:
                    continue
                # Exclude unassigned legacy items if candidate_id is not provided
                if candidate_id is None and item.candidate_id == LEGACY_UNASSIGNED_ID:
                    continue
                if not status or item.status == status:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Error parsing tracker item: {e}")

        # Sort by updated_at descending
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    def list_legacy_unassigned(self) -> List[ApplicationTrackerItem]:
        """Returns all legacy records requiring candidate assignment review."""
        raw_dict = self._read_data()
        items: List[ApplicationTrackerItem] = []
        for v in raw_dict.values():
            try:
                item = ApplicationTrackerItem(**v)
                if item.candidate_id == LEGACY_UNASSIGNED_ID:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Error parsing legacy tracker item: {e}")
        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    def assign_legacy_record(self, tracker_id: str, target_candidate_id: str) -> Optional[ApplicationTrackerItem]:
        """Explicit review workflow: safely assigns a legacy unassigned record to a candidate."""
        clean_target = (target_candidate_id or "").strip()
        if not clean_target or clean_target == LEGACY_UNASSIGNED_ID:
            raise ValueError("Target candidate ID must be a valid, existing candidate.")

        with file_lock(self.storage_file, shared=False):
            raw_dict = self._read_data()
            if tracker_id not in raw_dict:
                return None
            record = raw_dict[tracker_id]
            if record.get("candidate_id") != LEGACY_UNASSIGNED_ID:
                raise ValueError("Record is not in legacy unassigned status.")
            
            record["candidate_id"] = clean_target
            record["updated_at"] = datetime.utcnow().isoformat()
            self._write_data(raw_dict)
            return ApplicationTrackerItem(**record)

    def get_application(
        self,
        tracker_id: str,
        candidate_id: Optional[str] = None
    ) -> Optional[ApplicationTrackerItem]:
        """
        Retrieves a specific tracked job application.
        If candidate_id is provided, returns None if the item belongs to another candidate (non-disclosing).
        """
        raw_dict = self._read_data()
        data = raw_dict.get(tracker_id)
        if not data:
            return None
        try:
            item = ApplicationTrackerItem(**data)
            if candidate_id is not None and item.candidate_id != candidate_id:
                return None  # Non-disclosing not-found
            return item
        except Exception as e:
            logger.error(f"Error parsing tracker item {tracker_id}: {e}")
            return None

    def get_application_by_job_id(
        self,
        job_id: str,
        candidate_id: Optional[str] = None
    ) -> Optional[ApplicationTrackerItem]:
        """Finds application by job ID scoped strictly to candidate_id."""
        raw_dict = self._read_data()
        for v in raw_dict.values():
            if candidate_id is not None and v.get("candidate_id") != candidate_id:
                continue
            if v.get("job", {}).get("id") == job_id or v.get("job_id") == job_id:
                try:
                    return ApplicationTrackerItem(**v)
                except Exception:
                    continue
        return None

    def save_or_update(
        self,
        item: ApplicationTrackerItem,
        expected_candidate_id: Optional[str] = None
    ) -> ApplicationTrackerItem:
        """
        Saves or updates a tracker record with candidate validation and cross-candidate collision guards.
        """
        if expected_candidate_id is not None and item.candidate_id != expected_candidate_id:
            raise PermissionError("Application candidate_id does not match the authorized candidate context.")

        with file_lock(self.storage_file, shared=False):
            raw_dict = self._read_data()
            if item.id in raw_dict:
                existing = raw_dict[item.id]
                existing_candidate = existing.get("candidate_id")
                if existing_candidate and existing_candidate != item.candidate_id:
                    raise PermissionError("Cannot modify or overwrite a tracker record owned by another candidate.")

            item.updated_at = datetime.utcnow().isoformat()
            raw_dict[item.id] = item.model_dump()
            self._write_data(raw_dict)
            return item

    def update_status(
        self,
        tracker_id: str,
        new_status: str,
        candidate_id: Optional[str] = None
    ) -> Optional[ApplicationTrackerItem]:
        """
        Updates the status of an application scoped to candidate_id.
        Returns None if not found or owned by another candidate.
        """
        with file_lock(self.storage_file, shared=False):
            raw_dict = self._read_data()
            if tracker_id not in raw_dict:
                return None
            
            existing = raw_dict[tracker_id]
            if candidate_id is not None and existing.get("candidate_id") != candidate_id:
                return None  # Non-disclosing not-found

            existing["status"] = new_status
            existing["updated_at"] = datetime.utcnow().isoformat()
            if "job" in existing and isinstance(existing["job"], dict):
                existing["job"]["application_status"] = new_status
            self._write_data(raw_dict)
            return ApplicationTrackerItem(**existing)

    def delete(
        self,
        tracker_id: str,
        candidate_id: Optional[str] = None
    ) -> bool:
        """
        Deletes an application from the tracker scoped to candidate_id.
        Returns False if not found or owned by another candidate.
        """
        with file_lock(self.storage_file, shared=False):
            raw_dict = self._read_data()
            if tracker_id not in raw_dict:
                return False
            
            existing = raw_dict[tracker_id]
            if candidate_id is not None and existing.get("candidate_id") != candidate_id:
                return False  # Non-disclosing not-found

            del raw_dict[tracker_id]
            self._write_data(raw_dict)
            return True

TRACKER_STORE = TrackerStore()
