__all__ = ["AMSFilamentSettings", "Filament"]

import dataclasses
from enum import Enum
from functools import cache, cached_property
from typing import Any


@dataclasses.dataclass(frozen=True)
class AMSFilamentSettings:
    """
    Dataclass for the filament settings

    The filament settings are a set of values that indicate the settings of the filament.

    Attributes
    ----------

    tray_info_idx: The tray info index.
    nozzle_temp_min: The minimum nozzle temperature.
    nozzle_temp_max: The maximum nozzle temperature.
    tray_type: The tray type.
    """  # noqa
    tray_info_idx: str
    nozzle_temp_min: int
    nozzle_temp_max: int
    tray_type: str


class Filament(AMSFilamentSettings, Enum):
    """
    Enum class for the filament settings

    The filament settings are a set of values that indicate the settings of the filament.

    Attributes
    ----------

    POLYLITE_PLA: The Polylite PLA filament settings.
    POLYTERRA_PLA: The Polyterra PLA filament settings.
    BAMBU_ABS: The Bambu ABS filament settings.
    BAMBU_PA_CF: The Bambu PA-CF filament settings.
    BAMBU_PC: The Bambu PC filament settings.
    BAMBU_PLA_Basic: The Bambu PLA Basic filament settings.
    BAMBU_PLA_Matte: The Bambu PLA Matte filament settings.
    SUPPORT_G: The Support G filament settings.
    SUPPORT_W: The Support W filament settings.
    BAMBU_TPU_95A: The Bambu TPU 95A filament settings.
    BAMBU_ASA_AERO: The Bambu ASA AERO filament settings.
    BAMBU_PLA_METAL: The Bambu PLA Metal filament settings.
    BAMBU_PETG_TRANSLUCENT: The Bambu PETG Translucent filament settings.
    BAMBU_PLA_MARBLE: The Bambu PLA Marble filament settings.
    BAMBU_PLA_WOOD: The Bambu PLA Wood filament settings.
    BAMBU_PLA_SILK_PLUS: The Bambu PLA Silk Plus filament settings.
    BAMBU_PETG_HF: The Bambu PETG HF filament settings.
    BAMBU_TPU_FOR_AMS: The Bambu TPU for AMS filament settings.
    BAMBU_SUPPORT_FOR_ABS: The Bambu Support for ABS filament settings.
    BAMBU_PC_FR: The Bambu PC FR filament settings.
    BAMBU_PLA_GALAXY: The Bambu PLA Galaxy filament settings.
    BAMBU_PA6_GF: The Bambu PA6 GF filament settings.
    BAMBU_PLA_AERO: The Bambu PLA AERO filament settings.
    BAMBU_ASA_CF: The Bambu ASA CF filament settings.
    BAMBU_PETG_CF: The Bambu PETG CF filament settings.
    BAMBU_SUPPORT_FOR_PA_PET: The Bambu Support for PA PET filament settings.
    BAMBU_PLA_SPARKLE: The Bambu PLA Sparkle filament settings.
    BAMBU_ABS_GF: The Bambu ABS GF filament settings.
    BAMBU_PAHT_CF: The Bambu PAHT CF filament settings.
    BAMBU_PLA_BASIC: The Bambu PLA Basic filament settings.
    BAMBU_PLA_MATTE: The Bambu PLA Matte filament settings.
    BAMBU_PA6_CF: The Bambu PA6 CF filament settings.
    BAMBU_PLA_SILK: The Bambu PLA Silk filament settings.
    BAMBU_PVA: The Bambu PVA filament settings.
    BAMBU_PLA_CF: The Bambu PLA CF filament settings.
    BAMBU_SUPPORT_FOR_PLA_PETG: The Bambu Support for PLA PETG filament settings.
    BAMBU_TPU_95A_HF: The Bambu TPU 95A HF filament settings.
    BAMBU_PPA_CF: The Bambu PPA CF filament settings.
    BAMBU_ASA: The Bambu ASA filament settings.
    BAMBU_PLA_GLOW: The Bambu PLA Glow filament settings.
    ABS: The ABS filament settings.
    ASA: The ASA filament settings.
    PA: The PA filament settings.
    PA_CF: The PA-CF filament settings.
    PC: The PC filament settings.
    PETG: The PETG filament settings.
    PLA: The PLA filament settings.
    PLA_CF: The PLA-CF filament settings.
    PVA: The PVA filament settings.
    TPU: The TPU filament settings.
    """  # noqa
    POLYLITE_PLA = "GFL00", 190, 250, "PLA"
    POLYTERRA_PLA = "GFL01", 190, 250, "PLA"
    BAMBU_ABS = "GFB00", 240, 270, "ABS"
    BAMBU_PA_CF = "GFN03", 270, 300, "PA-CF"
    BAMBU_PC = "GFC00", 260, 280, "PC"
    BAMBU_PLA_Basic = "GFA00", 190, 250, "PLA"
    BAMBU_PLA_Matte = "GFA01", 190, 250, "PLA"
    SUPPORT_G = "GFS01", 190, 250, "PA-S"
    SUPPORT_W = "GFS00", 190, 250, "PLA-S"
    BAMBU_TPU_95A = "GFU01", 200, 250, "TPU"

    BAMBU_ASA_AERO = "GFB02", 240, 280, "ASA"
    BAMBU_PLA_METAL = "GFA02", 190, 230, "PLA"
    BAMBU_PETG_TRANSLUCENT = "GFG01", 230, 260, "PETG"
    BAMBU_PLA_MARBLE = "GFA07", 190, 230, "PLA"
    BAMBU_PLA_WOOD = "GFA16", 190, 240, "PLA"
    BAMBU_PLA_SILK_PLUS = "GFA06", 210, 240, "PLA"
    BAMBU_PETG_HF = "GFG02", 230, 260, "PETG"
    BAMBU_TPU_FOR_AMS = "GFU02", 230, 230, "TPU"
    BAMBU_SUPPORT_FOR_ABS = "GFS06", 190, 220, "Support"
    BAMBU_PC_FR = "GFC01", 260, 280, "PC"
    BAMBU_PLA_GALAXY = "GFA15", 190, 230, "PLA"
    BAMBU_PA6_GF = "GFN08", 260, 290, "PA6"
    BAMBU_PLA_AERO = "GFA11", 220, 260, "PLA"
    BAMBU_ASA_CF = "GFB51", 250, 280, "ASA"
    BAMBU_PETG_CF = "GFG50", 240, 270, "PETG"
    BAMBU_SUPPORT_FOR_PA_PET = "GFS03", 280, 300, "Support"
    BAMBU_PLA_SPARKLE = "GFA08", 190, 230, "PLA"
    BAMBU_ABS_GF = "GFB50", 240, 270, "ABS"
    BAMBU_PAHT_CF = "GFN04", 260, 290, "PAHT"
    BAMBU_PLA_BASIC = "GFA00", 190, 230, "PLA"
    BAMBU_PLA_MATTE = "GFA01", 190, 230, "PLA"
    BAMBU_PA6_CF = "GFN05", 260, 290, "PA6"
    BAMBU_PLA_SILK = "GFA05", 210, 230, "PLA"
    BAMBU_PVA = "GFS04", 220, 250, "PVA"
    BAMBU_PLA_CF = "GFA50", 210, 240, "PLA"
    BAMBU_SUPPORT_FOR_PLA_PETG = "GFS05", 190, 220, "Support"
    BAMBU_TPU_95A_HF = "GFU00", 230, 230, "TPU"
    BAMBU_PPA_CF = "GFN06", 280, 310, "PPA"
    BAMBU_ASA = "GFB01", 240, 270, "ASA"
    BAMBU_PLA_GLOW = "GFA12", 190, 230, "PLA"

    ABS = "GFB99", 240, 270, "ABS"
    ASA = "GFB98", 240, 270, "ASA"
    PA = "GFN99", 270, 300, "PA"
    PA_CF = "GFN98", 270, 300, "PA"
    PC = "GFC99", 260, 280, "PC"
    PETG = "GFG99", 220, 260, "PETG"
    PLA = "GFL99", 190, 250, "PLA"
    PLA_CF = "GFL98", 190, 250, "PLA"
    PVA = "GFS99", 190, 250, "PVA"
    TPU = "GFU99", 200, 250, "TPU"

    @classmethod
    def _missing_(cls, value: Any):
        if isinstance(value, str):
            for filament in cls:
                if value == filament.name:
                    return filament

        raise ValueError(f"Filament {value} not found")


@dataclasses.dataclass
class FilamentTray:
    """
    Dataclass for the filament tray

    Attributes
    ----------

    id: The ID of the tray.
    tag_uid: The tag UID.
    tray_id_name: The tray ID name.
    tray_info_idx: The tray info index.
    tray_type: The tray type.
    tray_sub_brands: The tray sub brands.
    tray_color: The filament color of the tray.
    tray_weight: The tray weight.
    tray_diameter: The tray diameter.
    drying_temp: The tray temperature.
    drying_time: The tray time.
    bed_temp_type: The bed temperature type.
    bed_temp: The bed temperature.
    nozzle_temp_max: The maximum nozzle temperature for the filament.
    nozzle_temp_min: The minimum nozzle temperature for the filament.
    xcam_info: The XCam information.
    tray_uuid: The tray UUID.
    """
    id: int
    tag_uid: str
    tray_id_name: str
    tray_info_idx: str
    tray_type: str
    tray_sub_brands: str
    tray_color: str
    tray_weight: str
    tray_diameter: str
    drying_temp: str
    drying_time: str
    bed_temp_type: str
    bed_temp: str
    nozzle_temp_max: int
    nozzle_temp_min: int
    xcam_info: str
    tray_uuid: str
    cols: list[str] | None = None

    @cache
    @staticmethod
    def keys() -> set[str]:
        """
        Get the keys of the dataclass.

        Returns:
            set[str]: the keys of the dataclass
        """
        return set(f.name for f in dataclasses.fields(FilamentTray))

    @staticmethod
    def from_dict(d: dict[str, Any]):
        """
        Initialize the dataclass from a dictionary.

        Args:
            d (dict[str, Any]): dictionary to initialize the dataclass with
            the keys of the dataclass.

        Returns:
            FilamentTray: the dataclass initialized with the dictionary
        """
        keys = FilamentTray.keys()
        d = {k: v for k, v in d.items() if k in keys}

        return FilamentTray(**d)

    @cached_property
    def filament(self) -> Filament:
        """
        Get the filament information from the tray information.

        Returns:
            Filament: filament information
        """
        return Filament(
            AMSFilamentSettings(
                self.tray_info_idx,
                self.nozzle_temp_min,
                self.nozzle_temp_max,
                self.tray_type
            )
        )
