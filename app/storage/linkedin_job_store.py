import os
import json
import logging
from typing import List, Optional, Tuple, Dict
from app.models.job import JobPosting
from app.storage.file_utils import file_lock, atomic_write_json

logger = logging.getLogger("LinkedInJobStore")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "linkedin_jobs.json")

class LinkedInJobStore:
    def __init__(self, filepath: Optional[str] = None):
        self.storage_file = filepath or STORAGE_FILE
        self.data_dir = os.path.dirname(self.storage_file)
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.storage_file):
            with file_lock(self.storage_file):
                atomic_write_json(self.storage_file, {})

    def get_all_jobs(self) -> List[JobPosting]:
        """Returns all persisted LinkedIn Job Alert postings."""
        with file_lock(self.storage_file, shared=True):
            if not os.path.exists(self.storage_file):
                return []
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                return [JobPosting(**item) for item in raw_data.values() if isinstance(item, dict)]
            except Exception as e:
                logger.error(f"Error reading LinkedIn jobs store: {e}")
                return []

    def save_jobs(self, jobs: List[JobPosting]) -> Tuple[int, int]:
        """
        Persists a list of ingested LinkedIn Job postings.
        Returns a tuple of (newly_added_count, duplicates_skipped_count).
        """
        if not jobs:
            return 0, 0

        with file_lock(self.storage_file, shared=False):
            raw_data: Dict[str, dict] = {}
            if os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load existing LinkedIn store; initializing new: {e}")
                    raw_data = {}

            added_count = 0
            duplicate_count = 0

            for job in jobs:
                key = job.id or job.url
                if key in raw_data:
                    duplicate_count += 1
                else:
                    raw_data[key] = job.model_dump() if hasattr(job, "model_dump") else job.dict()
                    added_count += 1

            if added_count > 0:
                atomic_write_json(self.storage_file, raw_data)
                logger.info(f"LinkedInJobStore: Saved {added_count} new jobs ({duplicate_count} duplicates skipped).")

            return added_count, duplicate_count

    def clear(self) -> None:
        """Clears all stored LinkedIn postings (primarily for test isolation)."""
        with file_lock(self.storage_file, shared=False):
            atomic_write_json(self.storage_file, {})

LINKEDIN_JOB_STORE = LinkedInJobStore()
