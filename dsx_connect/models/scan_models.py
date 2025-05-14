from enum import Enum

from pydantic import BaseModel
from dsx_connect.dsxa_client.verdict_models import DPAVerdictModel2


class ScanResultStatusEnum(str, Enum):
    NOT_SCANNED = "not scanned"
    SCANNED = "scanned"
    ACTION_FAILED = "action attempted, but failed"
    ACTION_SUCCEEDED = "action succeeded"


class ScanResultModel(BaseModel):
    id: int = -1
    scan_request_task_id: str
    metadata_tag: str | None = None
    dpa_verdict: DPAVerdictModel2 | None = None
    status: str = ScanResultStatusEnum.NOT_SCANNED


class ScanStatsModel(BaseModel):
    files_scanned: int = 0
    total_scan_time_in_microseconds: int = -1
    total_scan_time_in_seconds: float = -1
    total_file_size: int = -1
    avg_file_size: int = -1
    avg_scan_time_in_microseconds: int = -1
    avg_scan_time_in_milliseconds: float = -1
    avg_scan_time_in_seconds: float = -1
    median_file_size_in_bytes: int = -1
    median_scan_time_in_microseconds: int = -1
    longest_scan_time_file: str = ''
    longest_scan_time_file_size_in_bytes: int = -1
    longest_scan_time_in_microseconds: int = -1
    longest_scan_time_in_milliseconds: float = -1
    longest_scan_time_in_seconds: float = -1
