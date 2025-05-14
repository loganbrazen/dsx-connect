class DSXConnectAPIEndpoints:
    SCAN_REQUEST = "/dsx-connect/scan-request"
    SCAN_REQUEST_TEST = "/dsx-connect/test/scan-request"
    CONNECTION_TEST = "/dsx-connect/test/connection"
    DSXA_CONNECTION_TEST = "/dsx-connect/test/dsxa-connection"
    CONFIG = "/dsx-connect/config"


class ConnectorEndpoints:
    READ_FILE = "/read_file"
    ITEM_ACTION = "/item_action"
    FULL_SCAN = "/full_scan"
    WEBHOOK_EVENT = "/webhook/event"