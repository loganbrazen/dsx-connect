from enum import Enum

from pydantic_settings import BaseSettings

from dsx_connect.dsxa_client.verdict_models import DPASeverityEnum


class ConfigDatabaseType(str, Enum):
    MEMORY_COLLECTION: str = 'memory'
    TINYDB: str = 'tinydb'
    SQLITE3: str = 'sqlite3'
    MONGODB: str = 'mongodb'


class DatabaseConfig(BaseSettings):
    """
    Configuration settings for the database.

    Attributes:
        type (str): The type of database to use. Options include 'memory', 'tinydb', 'sqlite3', and 'mongodb'.
        loc (str): The file location of the database (used for all database types except 'memory').
        retain (int): Database retention setting. Set to -1 to retain forever, 0 to retain nothing,
        or a positive integer N to retain N records.
    """
    type: str = ConfigDatabaseType.TINYDB
    loc: str = "data/dsx-connect.db.json"
    retain: int = 1000

    scan_stats_db: str = "data/scan-stats.db.json"

    class Config:
        env_nested_delimiter = "__"


class ScannerConfig(BaseSettings):
    # scan_binary_url: str = "http://a668960fee4324868b4154722ad9a909-856481437.us-east-1.elb.amazonaws.com/scan/binary/v2"
    scan_binary_url: str = "http://0.0.0.0:8080/scan/binary/v2"

    class Config:
        env_nested_delimiter = "__"


class ScanResultTaskWorkerConfig(BaseSettings):
    syslog_server_url: str = "127.0.0.1"
    syslog_server_port: int = 514


class TaskQueueConfig(BaseSettings):
    production_mode: bool = False
    name: str = 'dsx-connect:tasks'
    broker: str = 'redis://localhost:6379/0'
    backend: str = 'redis://localhost:6379/0'

    # Task and queue names
    scan_request_queue: str = "scan_request_queue"
    verdict_action_queue: str = "verdict_action_queue"
    scan_result_queue: str = "scan_result_queue"
    scan_request_task: str = "dsx_connect.taskworkers.taskworkers.scan_request_task"
    verdict_action_task: str = "dsx_connect.taskworkers.taskworkers.verdict_action_task"
    scan_result_task: str = "dsx_connect.taskworkers.taskworkers.scan_result_task"  # New task


class SecurityConfig(BaseSettings):
    item_action_severity_threshold: DPASeverityEnum = DPASeverityEnum.MEDIUM  # Default threshold


class DSXConnectConfig(BaseSettings):
    results_database: DatabaseConfig = DatabaseConfig()
    scanner: ScannerConfig = ScannerConfig()
    taskqueue: TaskQueueConfig = TaskQueueConfig()

    scan_result_task_worker: ScanResultTaskWorkerConfig = ScanResultTaskWorkerConfig()

    class Config:
        env_nested_delimiter = "__"
        env_prefix = "DSXCONNECT_"


# Singleton with reload capability
class ConfigManager:
    _config: DSXConnectConfig = None

    @classmethod
    def get_config(cls) -> DSXConnectConfig:
        if cls._config is None:
            cls._config = DSXConnectConfig()
        return cls._config

    @classmethod
    def reload_config(cls) -> DSXConnectConfig:
        cls._config = DSXConnectConfig()
        return cls._config


config = ConfigManager.get_config()
