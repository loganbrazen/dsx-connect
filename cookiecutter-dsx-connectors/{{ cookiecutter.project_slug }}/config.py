from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings
from dsx_connect.models.connector_models import ItemActionEnum

class {{ cookiecutter.__package_config_class_name }}(BaseSettings):
    """
    Configuration for connector.  Note that configuration is a pydantic base setting class, so we get the benefits of
    type checking, as well as code completion in an IDE.  pydantic settings also allows for overriding these default
    settings via environment variables or a .env file.

    If you wish to add a prefix to the environment variable overrides, change the value of env_prefix below.

    Example:
        env_prefix = "DSXCONNECTOR_"
        ...
        export DSXCONNECTOR_LOCATION = 'some path'

    You can also read in an optional .env file, which will be ignored is not available
    """
    name: str = '{{ cookiecutter.__release_name }}'
    connector_url: HttpUrl = Field(default="http://0.0.0.0:{{ cookiecutter.connector_port }}",
                                   description="Base URL (http(s)://ip.add.ddr.ess|URL:port) of this connector entry point")
    item_action: ItemActionEnum = ItemActionEnum.NOTHING
    dsx_connect_url: HttpUrl = Field(default="{{ cookiecutter.__dsx_connect_url }}",
                                     description="Complete URL (http(s)://ip.add.ddr.ess|URL:port) of the dsxa entry point")
    test_mode: bool = True

    ### Connector specific configuration

    class Config:
        env_prefix = "DSXCONNECTOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"

# Singleton with reload capability
class ConfigManager:
    _config: {{ cookiecutter.__package_config_class_name }} = None

    @classmethod
    def get_config(cls) -> {{ cookiecutter.__package_config_class_name }}:
        if cls._config is None:
            cls._config = {{ cookiecutter.__package_config_class_name }}()
        return cls._config

    @classmethod
    def reload_config(cls) -> {{ cookiecutter.__package_config_class_name }}:
        cls._config = {{ cookiecutter.__package_config_class_name }}()
        return cls._config


config = ConfigManager.get_config()

