import json
from dsx_connect.models.scan_models import ScanStatsModel
from .scan_stats_base_db import ScanStatsBaseDB


class ScanStatsCollection(ScanStatsBaseDB):
    def __init__(self, retain: int = -1):
        super().__init__(retain)
        self.collection = []
        self.next_id = 1

        if not self.find_by_scan_id("global_stats"):
            self.insert(ScanStatsModel(), scan_id="global_stats")

    def insert(self, stats: ScanStatsModel, scan_id: str = None) -> int:
        stats_dict = json.loads(stats.json())
        stats_dict['dpa_proxy_scan_id'] = scan_id or self.next_id
        self.collection.append(stats_dict)
        self.next_id += 1
        self._check_retain_limit()
        return stats_dict['dpa_proxy_scan_id']

    def update(self, stats: ScanStatsModel, scan_id: str = None):
        for item in self.collection:
            if item.get('dpa_proxy_scan_id') == scan_id:
                updated_dict = json.loads(stats.json())
                updated_dict['dpa_proxy_scan_id'] = scan_id
                item.update(updated_dict)
                return

        # If scan_id is not found, insert the stats as a new entry
        self.insert(stats, scan_id=scan_id)
    def delete(self, scan_id: str):
        self.collection = [item for item in self.collection if item.get('dpa_proxy_scan_id') != scan_id]

    def delete_oldest(self):
        if self.collection:
            self.collection.pop(0)  # Removes the oldest record

    def read_all(self) -> list[dict]:
        return [{'dpa_proxy_scan_id': item.get('dpa_proxy_scan_id', 'global_stats'), 'stats': ScanStatsModel(**item)}
                for item in self.collection]

    def find_by_scan_id(self, scan_id: str) -> ScanStatsModel | None:
        for item in self.collection:
            if item.get('dpa_proxy_scan_id') == scan_id:
                return ScanStatsModel(**item)
        return None

    def __len__(self):
        return len(self.collection)
