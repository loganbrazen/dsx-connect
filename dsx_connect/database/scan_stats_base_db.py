from abc import ABC, abstractmethod
from dsx_connect.models.scan_models import ScanStatsModel


class ScanStatsBaseDB(ABC):
    def __init__(self, retain: int = -1):
        self._retain = retain

    @abstractmethod
    def insert(self, stats: ScanStatsModel, scan_id: str = None) -> int:
        """Insert a new record into the database."""
        pass

    @abstractmethod
    def update(self, stats: ScanStatsModel, scan_id: str = None):
        """Update an existing record in the database based on the scan_id."""
        pass

    @abstractmethod
    def delete(self, scan_id: str):
        """Delete a record from the database based on scan_id."""
        pass

    @abstractmethod
    def read_all(self) -> list[dict]:
        """Read all records from the database."""
        pass

    @abstractmethod
    def find_by_scan_id(self, scan_id: str) -> ScanStatsModel | None:
        """Find a record in the database based on the scan_id."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Return the number of records in the database."""
        pass

    def _check_retain_limit(self):
        """Check if the retain limit is exceeded and delete the oldest record if necessary."""
        if self._retain > 0 and len(self) > self._retain:
            self.delete_oldest()

    @abstractmethod
    def delete_oldest(self):
        """Delete the oldest record, used to maintain a specific record count."""
        pass