from random import random

from starlette.responses import StreamingResponse

from dsx_connect.utils import file_ops
from dsx_connect.models.connector_models import ScanRequestModel
from dsx_connect.utils.logging import dsx_logging
from dsx_connect.models.responses import StatusResponse, StatusResponseEnum
from connectors.filesystem.config import config
from connectors.filesystem.version import CONNECTOR_VERSION

random_number_id = random.randint(0, 9999)
connector_id = f'filesystem-connector-{random_number_id:04d}'

# Initialize DSXA Connector instance
connector = DSXAConnector(connector_name=config.name,
                          connector_id=connector_id,
                          base_connector_url=config.connector_url,
                          dsxa_connect_url=config.dsx_connect_url,
                          test_mode=True)


async def startup():
    """
    Create any resources necessary for this connector's operations
    """


@connector.startup
async def startup_event():
    """
    Startup handler for the DSX Connector.

    This function is invoked by dsx-connector during the startup phase of the connector.
    It should be used to initialize any required resources, such as setting up connections,
    starting background tasks, or performing initial configuration checks.

    Returns:
        bool: True if startup completes successfully. Otherwise, implement proper error handling.
    """
    dsx_logging.info(f"Starting up connector {connector.connector_id}")
    await startup()
    dsx_logging.info(f"{connector.connector_id} version: {CONNECTOR_VERSION}.")
    dsx_logging.info(f"{connector.connector_id} configuration: {config}.")
    dsx_logging.info(f"{connector.connector_name}:{connector.connector_id} startup completed.")

    return True


@connector.shutdown
def shutdown_event():
    """
    Shutdown handler for the DSX Connector.

    This function is called by dsx-connect when the connector is shutting down.
    Use this handler to clean up resources such as closing connections or stopping background tasks.

    Returns:
        None
    """
    dsx_logging.info(f"Shutting down connector {connector.connector_id}")


@connector.full_scan
async def full_scan_handler() -> StatusResponse:
    """
    Full Scan handler for the DSXA Connector.

    This function is invoked by DSXA Connect when a full scan of the connector's repository is requested.
    If your connector supports scanning all files (e.g., a filesystem or cloud storage connector), implement
    the logic to enumerate all files and trigger individual scan requests, using the base
    connector scan_file_request function.

    Example:
        iterate through files in a repository, and send a scan_file_request to dsx-connect for each file

        ```python
        async for file_path in file_ops.get_filepaths_async('F:/FileShare', True):
            await connector.scan_file_request(ScanRequestModel(location=str(file_path), metainfo=file_path.name))
        ```

        You can choose whatever location makes sense, as long as this connector can use it
        in read_file to read the file, whereever it is located.  The flow works like this:
        full_scan is invoked by dsx_connect, as it wants a full scan on whatever respository this
        connector is assigned to.  This connector in turn, enumerates through all files and
        sends a ScanEventQueueModel for each to dsx-connect, and more specifically, a queue
        of scan requests that dsx-connect will process.  dsx-connect then processes each
        queue item, calling read_file for each file that needs to be read.

    Args:
        scan_event_queue_info (ScanRequestModel): Contains metadata and location information necessary
            to perform a full scan.

    Returns:
        SimpleResponse: A response indicating success if the full scan is initiated, or an error if the
            functionality is not supported. (For connectors without full scan support, return an error response.)
    """
    dsx_logging.debug(f'Scanning files at: {config.location}')

    # ****  Example code  ****
    async for file_path in file_ops.get_filepaths_async('F:/FileShare', True):
        await connector.scan_file_request(ScanRequestModel(location=str(file_path), metainfo=file_path.name))

    return StatusResponse(
        status=StatusResponseEnum.NOTHING,
        message="Full scan not implemented",
        description=""
    )


@connector.item_action
def item_action_handler(scan_event_queue_info: ScanRequestModel) -> StatusResponse:
    """
    Item Action handler for the DSX Connector.

    This function is called by DSX Connect when a file is determined to be malicious
    (or some other condition which DSX Connect thinks of a need to take action on a
    file)
    The connector should implement the appropriate remediation action here (e.g., delete, move, or tag the file)
    based on the provided quarantine configuration.

    Args:
        scan_event_queue_info (ScanRequestModel): Contains the location and metadata of the item that requires action.

    Returns:
        SimpleResponse: A response indicating that the remediation action was performed successfully,
            or an error if the action is not implemented.
    """
    return StatusResponse(status=StatusResponseEnum.NOTHING,
                          message=f"Item action not implemented.")


@connector.read_file
def read_file_handler(scan_event_queue_info: ScanRequestModel) -> StatusResponse | StreamingResponse:
    """
    Read File handler for the DSX Connector.

    This function is invoked by DSX Connect when it needs to retrieve the content of a file.
    The connector should implement logic here to read the file from its repository (e.g., file system,
    S3 bucket, etc.) and return its contents wrapped in a FileContentResponse.

    Example:
    ```python
        @connector.read_file
        def read_file_handler(scan_event_queue_info: ScanEventQueueModel):
            file_path = pathlib.Path(scan_event_queue_info.location)

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
    ```

    Args:
        scan_event_queue_info (ScanRequestModel): Contains the location and metadata needed to locate and read the file.

    Returns:
        FileContentResponse or SimpleResponse: A successful FileContentResponse containing the file's content,
            or a SimpleResponse with an error message if file reading is not supported.
    """
    # Implement file read (if applicable)
    return StatusResponse(
        status=StatusResponseEnum.NOTHING,
        message="Read file not implemented",
        description=""
    )


@connector.repo_check
def repo_check_handler():
    """
    Repository connectivity check handler.

    This handler verifies that the configured repository location exists and this DSX Connector can connect to it.

    Returns:
        bool: True if the repository connectivity OK, False otherwise.
    """
    return True


@connector.webhook_event
def webhook_handler(event: dict):
    """
    Webhook Event handler for the DSX Connector.

    This function is invoked by external systems (e.g., third-party file repositories or notification services)
    when a new file event occurs. The connector should extract the necessary file details from the event payload
    (for example, a file ID or name) and trigger a scan request via DSX Connect using the connector.scan_file_request method.

    Args:
        event (dict): The JSON payload sent by the external system containing file event details.

    Returns:
        SimpleResponse: A response indicating that the webhook was processed and the file scan request has been initiated,
            or an error if processing fails.
    """
    dsx_logging.info("Processing webhook event")
    # Example: Extract a file ID from the event and trigger a scan
    file_id = event.get("file_id", "unknown")
    connector.scan_file_request(ScanRequestModel(
        location=f"custom://{file_id}",
        metainfo=event
    ))
    return StatusResponse(
        status=StatusResponseEnum.SUCCESS,
        message="Webhook processed",
        description=""
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("connectors.framework.dsxa_connector:connector_api", host="0.0.0.0",
                port="{{ cookiecutter.connector_port }}", reload=True)
