import pathlib
import json
from tinydb import TinyDB, Query
from dsx_connect.models.scan_models import ScanStatsModel
from .scan_stats_base_db import ScanStatsBaseDB


class ScanStatsTinyDB(ScanStatsBaseDB):
    def __init__(self, db_path: str, collection_name: str = 'scan_stats', retain: int = -1):
        super().__init__(retain)
        self.db_path = db_path
        pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = TinyDB(db_path)
        self.collection = self.db.table(collection_name)

        if not self.find_by_scan_id("global_stats"):
            self.insert(ScanStatsModel(), scan_id="global_stats")

    def insert(self, stats: ScanStatsModel, scan_id: str = None) -> int:
        stats_dict = json.loads(stats.json())
        if scan_id:
            stats_dict['dpa_proxy_scan_id'] = scan_id
        inserted_id = self.collection.insert(stats_dict)
        self._check_retain_limit()
        return inserted_id

    def update(self, stats: ScanStatsModel, scan_id: str = None):
        query = Query()
        stats_dict = json.loads(stats.json())
        stats_dict['dpa_proxy_scan_id'] = scan_id or "global_stats"
        self.collection.upsert(stats_dict, query.dpa_proxy_scan_id == stats_dict['dpa_proxy_scan_id'])

    def delete(self, scan_id: str):
        query = Query()
        self.collection.remove(query.dpa_proxy_scan_id == scan_id)

    def delete_oldest(self):
        if self.collection:
            oldest = self.collection.all()[0]
            self.collection.remove(doc_ids=[oldest.doc_id])

    def read_all(self) -> list[dict]:
        return [{'dpa_proxy_scan_id': item.get('dpa_proxy_scan_id', 'global_stats'), 'stats': ScanStatsModel(**item)}
                for item in self.collection.all()]

    def find_by_scan_id(self, scan_id: str) -> ScanStatsModel | None:
        query = Query()
        result = self.collection.get(query.dpa_proxy_scan_id == scan_id)
        return ScanStatsModel(**result) if result else None

    def __len__(self):
        return len(self.collection)
