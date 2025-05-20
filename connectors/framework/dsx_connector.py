import httpx
from httpx import HTTPStatusError
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError

from fastapi import FastAPI, APIRouter, Request, BackgroundTasks
from typing import Callable, Awaitable

from starlette.responses import StreamingResponse

from dsx_connect.models.connector_models import ScanRequestModel
from dsx_connect.models.constants import DSXConnectAPIEndpoints, ConnectorEndpoints
from dsx_connect.models.responses import StatusResponse, StatusResponseEnum
from dsx_connect.utils.logging import dsx_logging

connector_api = None


class DSXConnector:
    def __init__(self, connector_name: str, connector_id: str, base_connector_url: str, dsx_connect_url: str,
                 test_mode: bool = False):
        self.test_mode = test_mode
        self.connector_name = connector_name
        self.connector_id = connector_id

        self.connector_url = f'{str(base_connector_url).rstrip('/')}/{connector_id}'
        self.scan_request_count = 0

        self.dsx_connect_url = str(dsx_connect_url).rstrip('/')

        # TODO would rather this not be a global, rather instantiated within the base connector... although ont sure that's possible since
        # this is what uvicorn uses to start the app

        global connector_api
        connector_api = FastAPI(
            title=f"{connector_name} [dsx-connector] - {connector_id}",
            description=f"API for dsx-connector: {connector_name} (ID: {connector_id})"
        )
        connector_api.include_router(DSXAConnectorRouter(self))

        self.startup_handler: Callable[[], Awaitable[None]] = None
        self.shutdown_handler: Callable[[], Awaitable[None]] = None

        self.full_scan_handler: Callable[[ScanRequestModel], StatusResponse] = None
        self.item_action_handler: Callable[[ScanRequestModel], StatusResponse] = None
        self.read_file_handler: Callable[[ScanRequestModel], StreamingResponse | StatusResponse] = None
        self.webhook_handler: Callable[[ScanRequestModel], StatusResponse] = None
        self.repo_check_connection_handler: Callable[[], StatusResponse] = None

    # Register handlers for startup and shutdown events
    def startup(self, func: Callable[[], bool]):
        self.startup_handler = func
        return func

    def shutdown(self, func: Callable[[], bool]):
        self.shutdown_handler = func
        return func

    # Register handler for the /full_scan event
    def full_scan(self, func: Callable[[], dict]):
        self.full_scan_handler = func
        return func

    # Register handler for the /quarantine_action event
    def item_action(self, func: Callable[[ScanRequestModel], dict]):
        self.item_action_handler = func
        return func

    # Register handler for the /read_file event
    def read_file(self, func: Callable[[ScanRequestModel], StreamingResponse | StatusResponse]):
        self.read_file_handler = func
        return func

    def repo_check(self, func: Callable[[], bool]):
        """Register a function to check repository connectivity."""
        self.repo_check_connection_handler = func
        return func  # ✅ Return func so it works as a decorator

    # Register handler for the /webhook event
    def webhook_event(self, func: Callable[[ScanRequestModel], StreamingResponse | StatusResponse]):
        self.webhook_handler = func
        return func

    async def scan_file_request(self, scan_request: ScanRequestModel) -> StatusResponse:
        scan_request.connector_url = self.connector_url
        try:
            async with httpx.AsyncClient(verify=False) as client:
                if not self.test_mode:
                    response = await client.post(
                        f'{self.dsx_connect_url}{DSXConnectAPIEndpoints.SCAN_REQUEST}',
                        json=scan_request.dict()
                    )
                    dsx_logging.debug(f'Scan request returned')

                else:
                    response = await client.post(
                        f'{self.dsx_connect_url}{DSXConnectAPIEndpoints.SCAN_REQUEST_TEST}',
                        json=scan_request.dict()
                    )
                    dsx_logging.debug(f'Scan request test returned')

        # Raise an exception for bad responses (4xx and 5xx status codes)
            response.raise_for_status()

            self.scan_request_count += 1  # for reporting purposes
            # Return the response JSON if the request was successful
            return StatusResponse(**response.json())

        except httpx.HTTPStatusError as http_error:
            dsx_logging.error(f"HTTP error during scan request: {http_error}", exc_info=True)
            return StatusResponse(
                status=StatusResponseEnum.ERROR,
                description="Failed to send scan request",
                message=str(http_error)
            )
        except Exception as e:
            dsx_logging.error(f"Unexpected error during scan request: {e}", exc_info=True)
            return StatusResponse(
                status=StatusResponseEnum.ERROR,
                description="Unexpected error in scan request",
                message=str(e)
            )

    async def get_status(self):
        dsxa_status = await self.test_dsx_connect()
        repo_status = self.repo_check_connection_handler() if self.repo_check_connection_handler else False

        return {
            "connector_status": "Active",
            "dsxa_connectivity": "success" if dsxa_status else "failed",
            "repo_connectivity": "success" if repo_status else "failed",
            "scan_requests_since_active_count": self.scan_request_count,
        }

    async def test_dsx_connect(self) -> StatusResponse:
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(f'{self.dsx_connect_url}{DSXConnectAPIEndpoints.CONNECTION_TEST}')
            # Raise an exception for bad responses (4xx and 5xx status codes)
            response.raise_for_status()

            # Return the response JSON if the request was successful
            return response.json()
        except HTTPError as http_err:
            dsx_logging.warn(f"HTTP error occurred: {http_err}")  # Handle HTTP errors (4xx, 5xx)
        except HTTPStatusError as http_err:
            dsx_logging.warn(f"HTTP error occurred: {http_err}")  # Handle HTTP errors (4xx, 5xx)
        except ConnectionError as conn_err:
            dsx_logging.warn(f"Connection error occurred: {conn_err}")  # Handle network problems (e.g., DNS failure)
        except Timeout as timeout_err:
            dsx_logging.warn(f"Timeout error occurred: {timeout_err}")  # Handle request timeout
        except RequestException as req_err:
            dsx_logging.warn(f"An error occurred: {req_err}")  # Catch all other request exceptions
        except Exception as e:
            dsx_logging.warn(f"An unexpected error occurred: {e}")
        return None  # Return None if an exception occurred


class DSXAConnectorRouter(APIRouter):
    def __init__(self, connector: DSXConnector):
        super().__init__()
        self._connector = connector

        (self.get('/', description='Test for connector availability',
                  response_model=None)
         (self.home))
        self.post(f'/{self._connector.connector_id}{ConnectorEndpoints.ITEM_ACTION}',
                  description='Request that the connector perform and action on an item',
                  response_model=StatusResponse,
                  response_description='')(self.post_item_action)
        self.post(f'/{self._connector.connector_id}{ConnectorEndpoints.FULL_SCAN}',
                  description='Request that the connector initiate a full scan.',
                  response_model=StatusResponse,
                  response_description='')(self.post_full_scan)
        self.post(f'/{self._connector.connector_id}{ConnectorEndpoints.READ_FILE}',
                  description='Request a file from the connector',
                  response_description='',
                  response_model=None)(self.post_read_file)

        self.post(f'/{self._connector.connector_id}{ConnectorEndpoints.REPO_CHECK}',
                  description='Check connectivity to repository',
                  response_description='',
                  response_model=None)(self.post_repo_check)

        self.post(f'/{self._connector.connector_id}{ConnectorEndpoints.WEBHOOK_EVENT}')(self.post_handle_webhook_event)

        # Register FastAPI events
        self.on_event("startup")(self.on_startup_event)
        self.on_event("shutdown")(self.on_shutdown_event)

    async def home(self):
        return await self._connector.get_status()

    async def post_item_action(self, scan_request_info: ScanRequestModel) -> StatusResponse:
        if self._connector.item_action_handler:
            return self._connector.item_action_handler(scan_request_info)
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message="No handler registered for quarantine_action",
                              description="Add a decorator (ex: @connector.item_action) to handle item_action requests")

    async def post_full_scan(self, background_tasks: BackgroundTasks) -> StatusResponse:
        if self._connector.full_scan_handler:
            background_tasks.add_task(self._connector.full_scan_handler)
            return StatusResponse(
                status=StatusResponseEnum.SUCCESS,
                message="Full scan initiated",
                description="The scan is running in the background."
            )
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message="No handler registered for full_scan",
                              description="Add a decorator (ex: @connector.full_scan) to handle full scan requests")

    async def post_read_file(self, scan_request_info: ScanRequestModel) -> StreamingResponse | StatusResponse:
        dsx_logging.info(f'Receive read_file request for {scan_request_info}')
        if self._connector.read_file_handler:
            return self._connector.read_file_handler(scan_request_info)
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message="No event handler registered for read_file",
                              description="Add a decorator (ex: @connector.read_file) to handle read file requests")

    async def post_repo_check(self) -> StatusResponse:
        if self._connector.repo_check_connection_handler:
            return self._connector.repo_check_connection_handler()
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message="No event handler registered for repo_check",
                              description="Add a decorator (ex: @connector.repo_check) to handle repo check requests")

    async def post_handle_webhook_event(self, request: Request):
        if self._connector.webhook_handler:
            # Parse the JSON payload from the request body
            event = await request.json()
            dsx_logging.info(f"Received webhook for artifact path: {event}")
            return await self._connector.webhook_handler(event)
        # dpx_logging.info(f"Received webhook for file: {event.name} at {event.repo_key}/{event.path}")
        # Trigger a scan or other processing as required
        # await connector.scan_file_request(ScanEventQueueModel(location=event.path, metainfo=event.name))
        return StatusResponse(status=StatusResponseEnum.ERROR,
                              message="No handler registered for webhook_event",
                              description="Add a decorator (ex: @connector.webhook_event) to handle webhook events")
        # Startup event

    async def on_startup_event(self):
        # Default DSXA Connect connectivity test for all connectors
        test_response = await self._connector.test_dsx_connect()
        if not test_response:
            dsx_logging.warn(
                f"Connection to dsx-connect at {self._connector.dsx_connect_url} failed. "
                f"Operations will not allow scanning of files until connectivity is established.")
        else:
            dsx_logging.info(
                f"Connection to dsx-connect at {self._connector.dsx_connect_url} success.")
        if self._connector.startup_handler:
            await self._connector.startup_handler()

    # Shutdown event
    async def on_shutdown_event(self):
        if self._connector.shutdown_handler:
            await self._connector.shutdown_handler()
