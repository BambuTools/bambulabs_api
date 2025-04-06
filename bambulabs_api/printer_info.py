__all__ = [
    "NozzleType",
    "PrinterType",
    "P1FirmwareVersion",
    "PrinterFirmwareInfo"
]

from dataclasses import dataclass
from enum import Enum

NOZZLE_DIAMETER = {
    0.8,
    0.6,
    0.4,
    0.2,
}


class PrinterType(str, Enum):
    """
    Enum class for the printer type

    Attributes
    ----------
    P1S: P1S printer
    P1P: P1P printer
    A1: A1P printer
    A1_MINI: A1_MINI printer
    X1C: X1C printer
    X1E: X1E printer
    """
    P1S = "P1S"
    P1P = "P1P"
    H2D = "H2D"
    A1 = "A1"
    A1_MINI = "A1_MINI"
    X1C = "X1C"
    X1E = "X1E"


@dataclass
class PrinterFirmwareInfo:
    printer_type: PrinterType
    firmware_version: str


class P1FirmwareVersion(str, Enum):
    V_01_07_00_00 = "01.07.00.00"
    V_01_06_01_02 = "01.06.01.02"
    V_01_06_01_00 = "01.06.01.00"
    V_01_06_00_00 = "01.06.00.00"
    V_01_05_02_00 = "01.05.02.00"
    V_01_05_01_00 = "01.05.01.00"
    V_01_04_02_00 = "01.04.02.00"
    V_01_04_01_00 = "01.04.01.00"
    V_01_04_00_00 = "01.04.00.00"


class NozzleType(str, Enum):
    """
    Enum class for the nozzle type

    Attributes
    ----------
    STAINLESS_STEEL: The stainless steel nozzle type.
    HARDENED_STEEL: The hardened steel nozzle type.
    """
    STAINLESS_STEEL = "stainless_steel"
    HARDENED_STEEL = "hardened_steel"
