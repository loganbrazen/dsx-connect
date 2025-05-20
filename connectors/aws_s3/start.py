import uvicorn
from dsx_connect.utils.logging import dsx_logging
import socket
import os

def get_random_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        s.listen()
        _, port = s.getsockname()
        return port

if __name__ == "__main__":
    # Import aws_s3 to register decorators
    import connectors.aws_s3.aws_s3_connector  # noqa: F401

    # Now import connector_api, which includes filesystem_connector's handlers
    from connectors.framework.dsx_connector import connector_api

    # port = get_random_port()
    port = 8591
    # os.environ["PORT"] = str(port)
    dsx_logging.info(f"Starting AWS S3 Connector FastAPI app on port {port}")

    uvicorn.run(connector_api, host="0.0.0.0", port=port, reload=False, workers=1)
