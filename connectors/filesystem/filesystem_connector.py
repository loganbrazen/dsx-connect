import pathlib
import random

import uvicorn
import os

from starlette.responses import StreamingResponse

from dsx_connect.utils import file_ops
from connectors.framework.dsx_connector import DSXConnector
from dsx_connect.models.connector_models import ScanRequestModel, ItemActionEnum
from dsx_connect.utils.logging import dsx_logging
from dsx_connect.models.responses import StatusResponse, StatusResponseEnum
from filesystem_monitor import FilesystemMonitor, FilesystemMonitorCallback, ScanFolderModel
from dsx_connect.utils.async_ops import run_async
from connectors.filesystem.config import config
from connectors.filesystem.version import CONNECTOR_VERSION

# config = FilesystemConnectorConfig()

random_number_id = random.randint(0, 9999)
connector_id = f'filesystem-connector-{random_number_id:04d}'

connector = DSXConnector(connector_name=config.name,
                         connector_id=connector_id,
                         base_connector_url=config.connector_url,
                         dsx_connect_url=config.dsx_connect_url,
                         test_mode=config.test_mode)


# given that this could potentially be a lengthy file iteration, make the iteration asynchronous...
# TODO possibly should allow startup of FAstAPI to complete, and schedule full scans in the background
async def startup():
    """
    Create a filesystem monitor and capture the file information to send to the webhook/event.
    """
    class MonitorCallback(FilesystemMonitorCallback):
        def __init__(self):
            super().__init__()

        def file_modified_callback(self, file_path: pathlib.Path):
            dsx_logging.debug(f'Sending scan request for {file_path}')
            run_async(connector.scan_file_request(ScanRequestModel(location=str(file_path), metainfo=file_path.name)))

    monitor_callback = MonitorCallback()

    connector.filesystem_monitor = FilesystemMonitor(
        monitor_folder=ScanFolderModel(folder=config.location, recursive=config.recursive, scan_existing=False),
        callback=monitor_callback)
    connector.filesystem_monitor.start()


@connector.startup
async def startup_event():
    await startup()
    dsx_logging.info(f"{connector.connector_id} version: {CONNECTOR_VERSION}.")
    dsx_logging.info(f"{connector.connector_id} configuration: {config}.")
    dsx_logging.info(f"{connector.connector_name}:{connector.connector_id} startup completed.")


@connector.shutdown
def shutdown_event():
    dsx_logging.info(f"{connector.connector_name}:{connector.connector_id}  shutdown completed.")


@connector.full_scan
async def full_scan_handler() -> StatusResponse:
    dsx_logging.debug(f'Scanning files at: {config.location}')

    async for file_path in file_ops.get_filepaths_async(config.location, config.recursive):
        status_response = await connector.scan_file_request(ScanRequestModel(location=str(file_path), metainfo=file_path.name))
        dsx_logging.debug(f'Sent scan request for {file_path}, result: {status_response}')

    return StatusResponse(status=StatusResponseEnum.SUCCESS, message='Full scan invoked and scan requests sent.')


@connector.item_action
def item_action_handler(scan_event_queue_info: ScanRequestModel) -> StatusResponse:
    file_path = scan_event_queue_info.location
    path_obj = pathlib.Path(file_path)

    if config.item_action == ItemActionEnum.NOTHING:
        dsx_logging.debug(f'Item action {ItemActionEnum.NOTHING} on {file_path} invoked.')
        return StatusResponse(status=StatusResponseEnum.SUCCESS, message=f'Item action {config.item_action} was invoked.')
    elif config.item_action == ItemActionEnum.DELETE:
        dsx_logging.debug(f'Item action {ItemActionEnum.DELETE} on {file_path} invoked.')
        # Check if the file exists
        if not path_obj.is_file():
            return StatusResponse(
                status=StatusResponseEnum.ERROR,
                message=f'File {file_path} not found for deletion.',
                description=''
            )
        path_obj.unlink()
        return StatusResponse(status=StatusResponseEnum.SUCCESS,
                              message=f'Item action {config.item_action} was invoked. File {file_path} successfully deleted.')
    elif config.item_action == ItemActionEnum.MOVE:
        dsx_logging.debug(f'Item action {ItemActionEnum.MOVE} on {file_path} invoked.')
        # Ensure the destination directory exists
        move_dir = pathlib.Path(config.item_action_move_dir)
        move_dir.mkdir(parents=True, exist_ok=True)
        # Construct the destination file path (same file name)
        new_path = move_dir / path_obj.name
        try:
            path_obj.rename(new_path)
            return StatusResponse(
                status=StatusResponseEnum.SUCCESS,
                message=f'Item action {config.item_action} was invoked. File {file_path} successfully moved to {new_path}.'
            )
        except Exception as e:
            error_msg = f'Failed to move file {file_path}: {e}'
            dsx_logging.error(error_msg)
            return StatusResponse(
                status=StatusResponseEnum.ERROR,
                message=error_msg
            )

    return StatusResponse(status=StatusResponseEnum.NOTHING,
                          message=f"Item action {config.item_action} not implemented.")


@connector.read_file
def read_file_handler(scan_request_info: ScanRequestModel) -> StreamingResponse | StatusResponse:
    file_path = pathlib.Path(scan_request_info.location)

    # Check if the file exists
    if not os.path.isfile(file_path):
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message=f"File {file_path} not found")

    # Read the file content
    try:
        file_like = file_path.open("rb")  # Open file in binary mode
        return StreamingResponse(file_like, media_type="application/octet-stream")  # Stream file
    except Exception as e:
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message=f"Failed to read file: {str(e)}")


@connector.repo_check
def repo_check_handler():
    return os.path.exists(config.location)

# Add the distribution root (directory containing this script) to sys.path
# dist_root = pathlib.Path(__file__).resolve().parent.parent
# sys.path.insert(0, str(dist_root))

# Main entry point to start the FastAPI app
if __name__ == "__main__":
    # Uvicorn will serve the FastAPI app and keep it running
    uvicorn.run("connectors.framework.dsx_connector:connector_api", host="0.0.0.0", port=8590, reload=False, workers=1)
