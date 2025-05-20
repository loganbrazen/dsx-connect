from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import uvicorn
import pathlib
from starlette.responses import FileResponse
from dsx_connect.config import ConfigManager

from dsx_connect.models.constants import DSXConnectAPIEndpoints
from dsx_connect.dsxa_client.dsxa_client import DSXAClient
from dsx_connect.models.responses import StatusResponse, StatusResponseEnum
from dsx_connect.utils.logging import dsx_logging

from dsx_connect.app.dependencies import static_path

from dsx_connect.app.routers import scan_request, scan_request_test, scan_results

from dsx_connect import version


@asynccontextmanager
async def lifespan(app: FastAPI):

    dsx_logging.info(f"dsx-connect version: {version.DSX_CONNECT_VERSION}")
    dsx_logging.info(f"dsx-connect configuration: {config}")
    dsx_logging.info("dsx-connect startup completed.")

    yield

    dsx_logging.info("dsx-connect shutdown completed.")


app = FastAPI(title='dsx-connect API',
              description='Deep Instinct Data Security X Connect for Applications API',
              version=version.DSX_CONNECT_VERSION,
              docs_url='/docs',
              lifespan=lifespan)


# Reload config to pick up environment variables
config = ConfigManager.reload_config()

app.mount("/static", StaticFiles(directory=static_path, html=True), name='static')


app.include_router(scan_request_test.router, tags=["test"])
app.include_router(scan_request.router, tags=["scan"])
app.include_router(scan_results.router, tags=["results"])



# @app.on_event("startup")
# async def startup_event():
#     dpx_logging.info(f"dsx-connect version: {version.DSX_CONNECT_VERSION}")
#     dpx_logging.info(f"dsx-connect configuration: {get_config()}")
#     dpx_logging.info("dsx-connect startup completed.")
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     dpx_logging.info("dsx-connect shutdown completed.")


@app.get("/")
def home(request: Request):
    home_path = pathlib.Path(static_path / 'html/dsx_connect.html')
    return FileResponse(home_path)


@app.get(DSXConnectAPIEndpoints.CONFIG, description='Get all configuration')
def get_get_config():
    return config


@app.get(DSXConnectAPIEndpoints.CONNECTION_TEST, description="Test connection to dsx-connect.", tags=["test"])
async def get_test_connection():
    return StatusResponse(
        status=StatusResponseEnum.SUCCESS,
        description="",
        message="Successfully connected to dsx-connect"
    )

@app.get(DSXConnectAPIEndpoints.DSXA_CONNECTION_TEST, description="Test connection to dsxa.", tags=["test"])
async def get_dsxa_test_connection():
    dsxa_client = DSXAClient(config.scanner.scan_binary_url)
    response = await dsxa_client.test_connection_async()
    return response

# Main entry point to start the FastAPI app
if __name__ == "__main__":
    # Uvicorn will serve the FastAPI app and keep it running
    uvicorn.run("dsx_connect_app:app", host="0.0.0.0", port=8586, reload=True, workers=1)
