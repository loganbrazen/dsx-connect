import logging
import logging.handlers
import json
from datetime import datetime
from typing import Optional
from dpa_client.dpa_models import DPAVerdictModel2
from dsx_connect.models import ScanRequestModel

dpx_logging = logging.getLogger(__name__)

# Syslog handler (initialized once per worker process)
_syslog_handler = None

def init_syslog_handler(syslog_host: str = "localhost", syslog_port: int = 514):
    """Initialize the syslog handler for the worker process."""
    global _syslog_handler
    try:
        _syslog_handler = logging.handlers.SysLogHandler(
            address=(syslog_host, syslog_port),
            facility=logging.handlers.SysLogHandler.LOG_LOCAL0,
            socktype=socket.SOCK_DGRAM  # UDP for syslog
        )
        _syslog_handler.setFormatter(logging.Formatter('%(message)s'))
        dpx_logging.info(f"Initialized syslog handler for {syslog_host}:{syslog_port}")
    except Exception as e:
        dpx_logging.error(f"Failed to initialize syslog handler: {e}")

def log_verdict_chain(
        scan_request: ScanRequestModel,
        verdict: DPAVerdictModel2,
        item_action_success: bool,
        original_task_id: str,
        current_task_id: Optional[str] = None
) -> None:
    """
    Log the complete chain (scan request, verdict, and item action) to syslog.

    Args:
        scan_request: The original scan request details.
        verdict: The scan verdict result.
        item_action_success: Whether the item_action (if triggered) was successful.
        original_task_id: The task ID of the initiating scan_request_task.
        current_task_id: The task ID of the verdict_task (optional).
    """
    global _syslog_handler
    if not _syslog_handler:
        dpx_logging.warning("Syslog handler not initialized, skipping log")
        return

    try:
        log_data = {
            "original_task_id": original_task_id,
            "current_task_id": current_task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scan_request": scan_request.model_dump(),
            "verdict": verdict.model_dump(),
            "item_action": {
                "triggered": verdict.verdict == DPAVerdictEnum.MALICIOUS and verdict.severity and verdict.severity >= SecurityConfig().action_severity_threshold,
                "success": item_action_success if verdict.verdict == DPAVerdictEnum.MALICIOUS and verdict.severity else None
            }
        }
        syslog_message = json.dumps(log_data)
        logger = logging.getLogger("verdict_chain")
        logger.setLevel(logging.INFO)
        logger.addHandler(_syslog_handler)
        logger.info(syslog_message)
        dpx_logging.debug(f"Sent verdict chain to syslog: {syslog_message}")
    except Exception as e:
        dpx_logging.error(f"Failed to log verdict chain to syslog: {e}", exc_info=True)