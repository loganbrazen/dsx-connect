from pymongo import MongoClient
import json

from scan_results_base_db import ScanResultsBaseDB
from dsx_connect.models.scan_models import ScanResultModel


class ScanResultsMongoDB(ScanResultsBaseDB):
    def __init__(self, db_uri: str, db_name: str, collection_name: str = 'scan_results', retain: int = -1):
        super().__init__(retain)
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def __str__(self):
        return f'db: {self.db.name}   collection: {self.collection.name}'

    def insert(self, model: ScanResultModel) -> int:
        if self._retain == 0:
            return -1  # Do nothing if retain is 0 (store nothing)

    # Generate the next available integer id by checking the highest current id
        last_record = self.collection.find_one(sort=[("id", -1)])  # Sort by id descending
        next_id = (last_record["id"] + 1) if last_record else 1

        model_dict = json.loads(model.json(exclude={"id"}))
        model_dict["id"] = next_id  # Add the custom integer id
        self.collection.insert_one(model_dict)

        model.id = next_id  # Set the model id to the newly generated one

        self._check_retain_limit()

        return model.id

    def delete(self, key: str, value: str) -> bool:
        if key == 'id':
            result = self.collection.delete_one({'id': int(value)})
        else:
            result = self.collection.delete_many({key: value})

        return result.deleted_count > 0

    def delete_oldest(self):
        oldest_record = self.collection.find_one(sort=[('_id', 1)])
        if oldest_record:
            self.collection.delete_one({"_id": oldest_record['_id']})

    def read_all(self) -> list[ScanResultModel]:
        # Fetch all records and map them to ScanResultModel objects using the integer id
        records = self.collection.find()
        return [ScanResultModel(id=record['id'], **{k: v for k, v in record.items() if k != 'id'}) for record in records]

    def find(self, key: str, value: str) -> list[ScanResultModel] | None:
        # Search by integer id if key is 'id', otherwise search by other fields
        if key == 'id':
            result = self.collection.find_one({'id': int(value)})
            results = [result] if result else []
        else:
            results = self.collection.find({key: value})

        return [ScanResultModel(id=result['id'], **{k: v for k, v in result.items() if k != 'id'}) for result in results]

    def __len__(self):
        return self.collection.count_documents({})


if __name__ == "__main__":
    # Replace 'mongodb://localhost:27017' with your actual MongoDB connection URI
    service = ScanResultsMongoDB('mongodb://localhost:27017', 'dpx-db')

    # Insert sample records
    service.insert(ScanResultModel(dpa_proxy_scan_id='A'))
    service.insert(ScanResultModel(dpa_proxy_scan_id='B'))
    service.insert(ScanResultModel(dpa_proxy_scan_id='B'))
    service.insert(ScanResultModel(dpa_proxy_scan_id='B'))
    service.insert(ScanResultModel(dpa_proxy_scan_id='C'))

    # Read all records
    print("All records:")
    print(service.read_all())

    # Find records matching a key-value pair
    print("\nRecords matching 'dpa_proxy_scan_id=B':")
    matching_records = service.find("dpa_proxy_scan_id", "B")
    print(matching_records)

    service.insert(ScanResultModel(dpa_proxy_scan_id='B'))
    service.insert(ScanResultModel(dpa_proxy_scan_id='C'))
    print("\nRecords matching 'dpa_proxy_scan_id=B':")
    matching_records = service.find("dpa_proxy_scan_id", "B")
    print(matching_records)

    print("\nRecords matching 'id=2':")
    matching_records = service.find("id", '2')
    print(matching_records)

    print("\nDeleting 'id=2':")
    service.delete('id', '2')
    print(service.read_all())

    print("\nDeleting 'dpa_proxy_scan_id=B':")
    service.delete('dpa_proxy_scan_id', 'B')
    print(service.read_all())
