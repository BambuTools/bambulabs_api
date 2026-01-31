from importlib import metadata

try:
    __version__ = metadata.version("bambulabs_api")
except Exception:
    __version__ = "0.dev0+unknown"

from bambulabs_api import client, mqtt_client, ftp_client, ams

# flake8: noqa: F405
from .client import *  # noqa
from .filament_info import Filament, AMSFilamentSettings, FilamentTray  # noqa
from .states_info import PrintStatus, GcodeState  # noqa
from .mqtt_client import *  # noqa
from .ftp_client import *  # noqa
from .ams import *  # noqa
from bambulabs_api.logger import logger  # noqa: F401


__all__ = []
__all__.extend(client.__all__)
__all__.extend(mqtt_client.__all__)
__all__.extend(ftp_client.__all__)
__all__.extend(ams.__all__)
__all__.append("logger")
