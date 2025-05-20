from fastapi import APIRouter

from dsx_connect.models.scan_models import ScanResultModel, ScanStatsModel
from dsx_connect.utils.logging import dsx_logging
from dsx_connect.models.connector_models import ScanRequestModel
from dsx_connect.config import ConfigManager
from dsx_connect.models.constants import DSXConnectAPIEndpoints
from dsx_connect.taskqueue.celery_app import celery_app
from dsx_connect.models.responses import StatusResponse, StatusResponseEnum
from dsx_connect.database.database_factory import database_scan_stats_factory, database_scan_results_factory

router = APIRouter()

config = ConfigManager().reload_config()
_results_database = database_scan_results_factory(config.results_database.type,
                                                  database_loc=config.results_database.loc,
                                                  retain=config.results_database.retain)

_stats_database = database_scan_stats_factory(database_loc=config.results_database.scan_stats_db)


@router.get(DSXConnectAPIEndpoints.SCAN_RESULTS, description="Review scan results.")
async def get_scan_result() -> list[ScanResultModel]:
    return _results_database.read_all()


@router.get(DSXConnectAPIEndpoints.SCAN_STATS, description="Retrieve scan statistics.")
async def get_scan_result() -> ScanStatsModel:
    return _stats_database.get()
