__all__ = ["AMS", "AMSHub"]

from typing import Any, Iterator
from bambulabs_api.filament_info import FilamentTray


class AMSHub:
    """
    Represents the Bambulabs AMS (Automated Material System) system hub.

    Returns:
        AMSHub: AMSHub object containing all AMS objects.
    """
    def __init__(self) -> None:
        self.ams_hub: dict[int, AMS] = {}

    def parse_list(self, ams_dict: list[dict[str, Any]]):
        for a in ams_dict:
            id = a.get("id")
            if id:
                id = int(id)
                self.ams_hub[id] = AMS(**a)

    def __getitem__(self, ind: int) -> "AMS":
        return self.ams_hub[ind]

    def __setitem__(self, ind: int, item: "AMS"):
        self.ams_hub[ind] = item

    def __iter__(self) -> Iterator["AMS"]:
        return iter(self.ams_hub.values())


class AMS:
    """
    Represents the Bambulab's AMS (Automated Material System) system.
    """

    def __init__(self, humidity: int, humidity_pct: int, temperature: float, **kwargs: dict[str, Any]) -> None:
        self.filament_trays: dict[int, FilamentTray] = {}

        self.humidity = humidity
        self.humidity_pct = humidity_pct
        self.temperature = temperature

        if "tray" in kwargs:
            self.process_trays(kwargs["tray"])  # type: ignore

    def process_trays(self, trays: list[dict[str, Any]]):
        for t in trays:
            id = t.get("id")
            tray_n: Any | None = t.get("tray_info_idx", None)
            if id and tray_n is not None:
                id = int(id)
                self.filament_trays[id] = FilamentTray.from_dict(t)

    def set_filament_tray(
        self,
        filament_tray: FilamentTray,
        tray_index: int
    ) -> None:
        """
        Set the filament tray at the given index. Will overwrite any existing
        tray at the given index.

        Args:
            filament_tray (FilamentTray): description of the filament tray
            tray_index (int): tray index
        """
        self.filament_trays[tray_index] = filament_tray

    def get_filament_tray(self, tray_index: int) -> FilamentTray | None:
        """
        Get the filament tray at the given index. If no tray exists at the
        index, return None.

        Args:
            tray_index (int): tray index of the filament tray

        Returns:
            FilamentTray | None: filament tray at the given index
        """
        return self.filament_trays.get(tray_index)

    def __getitem__(self, index: int):
        return self.filament_trays[index]

    def __setitem__(self, index: int, filament_tray: FilamentTray):
        self.filament_trays[index] = filament_tray

    def __iter__(self) -> Iterator[FilamentTray]:
        """Iterate over the FilamentTray objects inside this AMS."""
        return iter(self.filament_trays.values())
