"""
Client module for connecting to the Bambulabs 3D printer API
and getting all the printer data.
"""

__all__ = ['Printer']

import base64
from io import BytesIO
from typing import Any, BinaryIO

from bambulabs_api.ams import AMSHub
from bambulabs_api.filament_info import FilamentTray
from bambulabs_api.printer_info import NozzleType
from bambulabs_api.states_info import PrintStatus, GcodeState
from .camera_client import PrinterCamera
from .ftp_client import PrinterFTPClient
from .mqtt_client import PrinterMQTTClient
from .filament_info import Filament, AMSFilamentSettings
from PIL import Image


class Printer:
    """
    Client Class for connecting to the Bambulabs 3D printer
    """

    def __init__(self, ip_address: str, access_code: str, serial: str):
        self.ip_address = ip_address
        self.access_code = access_code
        self.serial = serial

        self.mqtt_client = PrinterMQTTClient(self.ip_address,
                                             self.access_code,
                                             self.serial)
        self.camera_client = PrinterCamera(self.ip_address,
                                           self.access_code)
        self.ftp_client = PrinterFTPClient(self.ip_address,
                                           self.access_code)

    def camera_client_alive(self) -> bool:
        """
        Check if the camera client is connected to the printer

        Returns
        -------
        bool
            Check if the camera loop is running.
        """
        return self.camera_client.alive

    def mqtt_client_connected(self):
        """
        Get the mqtt client is connected to the printer.

        Returns
        -------
        bool
            Check if the mqtt client is connected.
        """
        return self.mqtt_client.is_connected()

    def mqtt_client_ready(self):
        """
        Get the mqtt client is ready to send commands.

        Returns
        -------
        bool
            Check if the mqtt client is ready.
        """
        return self.mqtt_client.ready()

    def current_layer_num(self):
        """
        Get current layer number

        Returns
        -------
        int
            Current layer number
        """
        return self.mqtt_client.current_layer_num()

    def total_layer_num(self):
        """
        Get total layer number

        Returns
        -------
        int
            Total layer number
        """
        return self.mqtt_client.total_layer_num()

    def camera_start(self):
        """
        Start the camera

        Returns
        -------
        bool
            If the camera successfully connected
        """
        return self.camera_client.start()

    def mqtt_start(self):
        """
        Start the mqtt client

        Returns:
            MQTTErrorCode: error code of loop start
        """
        self.mqtt_client.connect()
        return self.mqtt_client.start()

    def mqtt_stop(self):
        """
        Stop the mqtt client
        """
        self.mqtt_client.stop()

    def camera_stop(self):
        """
        Stop the camera client
        """
        self.camera_client.stop()

    def connect(self):
        """
        Connect to the printer
        """
        self.mqtt_start()
        self.camera_start()

    def disconnect(self):
        """
        Disconnect from the printer
        """
        self.mqtt_client.stop()
        self.camera_client.stop()

    def get_time(self) -> (int | str | None):
        """
        Get the remaining time of the print job in seconds.

        Returns
        -------
        int
            Remaining time of the print job in seconds.
        str
            "Unknown" if the remaining time is unknown.
        None if the printer is not printing.
        """
        return self.mqtt_client.get_remaining_time()

    def mqtt_dump(self) -> dict[Any, Any]:
        """
        Get the mqtt dump of the messages recorded from the printer

        Returns:
            dict[Any, Any]: the json that is recorded from the printer.
        """
        return self.mqtt_client.dump()

    def get_percentage(self) -> (int | str | None):
        """
        Get the percentage of the print job completed.

        Returns
        -------
        int
            Percentage of the print job completed.
        str
            "Unknown" if the percentage is unknown.
        None if the printer is not printing.
        """
        return self.mqtt_client.get_last_print_percentage()

    def get_state(self) -> GcodeState:
        """
        Get the state of the printer.

        Returns
        -------
        GcodeState
            The state of the printer.
        """
        return self.mqtt_client.get_printer_state()

    def get_print_speed(self) -> int:
        """
        Get the print speed of the printer.

        Returns
        -------
        int
            The print speed of the printer.
        """
        return self.mqtt_client.get_print_speed()

    def get_bed_temperature(self) -> float | None:
        """
        Get the bed temperature of the printer.

        Returns
        -------
        float
            The bed temperature of the printer.
        None if the printer is not printing.
        """
        return self.mqtt_client.get_bed_temperature()

    def get_nozzle_temperature(self) -> float | None:
        """
        Get the nozzle temperature of the printer.

        Returns
        -------
        float
            The nozzle temperature of the printer.
        None if the printer is not printing.
        """
        return self.mqtt_client.get_nozzle_temperature()

    def get_chamber_temperature(self) -> float | None:
        """
        Get the chamber temperature of the printer.

        Returns
        -------
        float
            The chamber temperature of the printer.
        None if the printer is not printing.
        """
        return self.mqtt_client.get_chamber_temperature()

    def nozzle_type(self) -> NozzleType:
        """
        Get the nozzle type currently registered to printer

        Returns:
            NozzleType: nozzle diameter
        """
        return self.mqtt_client.nozzle_type()

    def nozzle_diameter(self) -> float:
        """
        Get the nozzle diameter currently registered to printer

        Returns:
            float: nozzle diameter
        """
        return self.mqtt_client.nozzle_diameter()

    def get_file_name(self) -> str:
        """
        Get the name of the file being printed.

        Returns
        -------
        str
            The name of the file being printed.
        """
        return self.mqtt_client.get_file_name()

    def get_light_state(self) -> str:
        """
        Get the state of the printer light.

        Returns
        -------
        str
            The state of the printer light.
        """
        return self.mqtt_client.get_light_state()

    def turn_light_on(self) -> bool:
        """
        Turn on the printer light.

        Returns
        -------
        bool
            True if the light is turned on successfully.
        """
        return self.mqtt_client.turn_light_on()

    def turn_light_off(self) -> bool:
        """
        Turn off the printer light.

        Returns
        -------
        bool
            True if the light is turned off successfully.
        """
        return self.mqtt_client.turn_light_off()

    def gcode(self, gcode: str | list[str], gcode_check: bool = True) -> bool:
        """
        Send a gcode command to the printer.

        Parameters
        ----------
        gcode : str | list[str]
            The gcode command or list of gcode commands to be sent.

        gcode_check: (bool): whether to check gcode validity.
                        Default to True.

        Returns
        -------
        bool
            True if the gcode command is sent successfully.

        Raises
        ------
        ValueError
            If the gcode command is invalid.
        """
        return self.mqtt_client.send_gcode(gcode, gcode_check=gcode_check)

    def upload_file(self, file: BinaryIO, filename: str = "ftp_upload.gcode") -> str:  # noqa
        """
        Upload a file to the printer.

        Parameters
        ----------
        file : BinaryIO
            The file to be uploaded.
        filename : str, optional
            The name of the file, by default "ftp_upload.gcode".

        Returns
        -------
        str
            The path of the uploaded file.
        """
        try:
            if file and filename:
                return self.ftp_client.upload_file(file, filename)
        except Exception as e:
            raise Exception(f"Exception occurred during file upload: {e}")  # noqa  # pylint: disable=raise-missing-from,broad-exception-raised
        finally:
            file.close()
        return "No file uploaded."

    def start_print(self, filename: str,
                    plate_number: int | str,
                    use_ams: bool = True,
                    ams_mapping: list[int] = [0],
                    skip_objects: list[int] | None = None,
                    flow_calibration: bool = True,
                    ) -> bool:
        """
        Start printing a file.

        Parameters
        ----------
        filename: str
            The name of the file to be printed.
        plate_number: (int | str)
            The plate number of the file to be printed (assuming the 3mf file
            is created with Bambustudio/Orcaslicer). Or the path as a string.
        use_ams: bool, optional
            Whether to use the AMS system, by default True.
        ams_mapping: list[int], optional
            The mapping of the filament trays to the plate numbers,
            by default [0].
        skip_objects: (list[int] | None, optional) List of gcode objects to
            skip. Defaults to None.
        flow_calibration : bool, optional
            Whether to use the automatic flow calibrationn, by default True.

        Returns
        -------
        bool
            True if the file is printed successfully.
        """
        return self.mqtt_client.start_print_3mf(filename,
                                                plate_number,
                                                use_ams,
                                                ams_mapping,
                                                skip_objects,
                                                flow_calibration)

    def stop_print(self) -> bool:
        """
        Stop the printer from printing.

        Returns
        -------
        bool
            True if the printer is stopped successfully.
        """
        return self.mqtt_client.stop_print()

    def pause_print(self) -> bool:
        """
        Pause the printer from printing.

        Returns
        -------
        bool
            True if the printer is paused successfully.
        """
        return self.mqtt_client.pause_print()

    def resume_print(self) -> bool:
        """
        Resume the printer from printing.

        Returns
        -------
        bool
            True if the printer is resumed successfully.
        """
        return self.mqtt_client.resume_print()

    def set_bed_temperature(self, temperature: int) -> bool:
        """
        Set the bed temperature of the printer.

        Parameters
        ----------
        temperature : int
            The temperature to be set.

        Returns
        -------
        bool
            True if the temperature is set successfully.
        """
        return self.mqtt_client.set_bed_temperature(temperature)

    def home_printer(self) -> bool:
        """
        Home the printer.

        Returns
        -------
        bool
            True if the printer is homed successfully.
        """
        return self.mqtt_client.auto_home()

    def move_z_axis(self, height: int) -> bool:
        """
        Move the Z-axis of the printer.

        Parameters
        ----------
        height : float
            The height for the bed.

        Returns
        -------
        bool
            True if the Z-axis is moved successfully.
        """
        return self.mqtt_client.set_bed_height(height)

    def set_filament_printer(
        self,
        color: str,
        filament: str | AMSFilamentSettings,
        ams_id: int = 255,
        tray_id: int = 254,
    ) -> bool:
        """
        Set the filament of the printer.

        Parameters
        ----------
        color : str
            The color of the filament.
        filament : str | AMSFilamentSettings
            The filament to be set.
        ams_id : int
            The index of the AMS, by default the external spool 255.
        tray_id : int
            The index of the spool/tray in the ams, by default the external
            spool 254.

        Returns
        -------
        bool
            True if the filament is set successfully.
        """
        assert len(color) == 6, "Color must be a 6 character hex code"
        if isinstance(filament, str):
            filament = Filament(filament)
        return self.mqtt_client.set_printer_filament(
            filament,
            color,
            ams_id=ams_id,
            tray_id=tray_id)

    def set_nozzle_temperature(self, temperature: int) -> bool:
        """
        Set the nozzle temperature of the printer.

        Parameters
        ----------
        temperature : int
            The temperature to be set.

        Returns
        -------
        bool
            True if the temperature is set successfully.
        """
        return self.mqtt_client.set_nozzle_temperature(temperature)

    def set_print_speed(self, speed_lvl: int) -> bool:
        """
        Set the print speed of the printer.

        Parameters
        ----------
        speed_lvl : int
            The speed level to be set.
            0: Slowest
            1: Slow
            2: Fast
            3: Fastest

        Returns
        -------
        bool
            True if the speed level is set successfully.
        """
        assert 0 <= speed_lvl <= 3, "Speed level must be between 0 and 3"
        return self.mqtt_client.set_print_speed_lvl(speed_lvl)

    def delete_file(self, file_path: str) -> str:
        """
        Delete a file from the printer.

        Parameters
        ----------
        file_path : str
            The path of the file to be deleted.

        Returns
        -------
        str
            The path of the deleted file.
        """
        return self.ftp_client.delete_file(file_path)

    def calibrate_printer(self, bed_level: bool = True,
                          motor_noise_calibration: bool = True,
                          vibration_compensation: bool = True) -> bool:
        """
        Calibrate the printer.

        Parameters
        ----------
        bed_level : bool, optional
            Whether to calibrate the bed level, by default True.
        motor_noise_calibration : bool, optional
            Whether to calibrate the motor noise, by default True.
        vibration_compensation : bool, optional
            Whether to calibrate the vibration compensation, by default True.

        Returns
        -------
        bool
            True if the printer is calibrated successfully.
        """
        return self.mqtt_client.calibration(bed_level,
                                            motor_noise_calibration,
                                            vibration_compensation)

    def load_filament_spool(self) -> bool:
        """
        Load the filament spool to the printer.

        Returns
        -------
        bool
            True if the filament spool is loaded successfully.
        """
        return self.mqtt_client.load_filament_spool()

    def unload_filament_spool(self) -> bool:
        """
        Unload the filament spool from the printer.

        Returns
        -------
        bool
            True if the filament spool is unloaded successfully.
        """
        return self.mqtt_client.unload_filament_spool()

    def retry_filament_action(self) -> bool:
        """
        Retry the filament action.

        Returns
        -------
        bool
            True if the filament action is retried successfully.
        """
        return self.mqtt_client.resume_filament_action()

    def get_camera_frame(self) -> str:
        """
        Get the camera frame of the printer.

        Returns
        -------
        str
            Base64 encoded image of the camera frame.
        """
        return self.get_camera_frame_()

    def get_camera_frame_(self) -> str:
        return self.camera_client.get_frame()

    def get_camera_image(self) -> Image.Image:
        """
        Get the camera frame of the printer.

        Returns
        -------
        Image.Image
            Pillow Image of printer camera frame.
        """
        im = Image.open(BytesIO(base64.b64decode(self.get_camera_frame_())))
        return im

    def get_current_state(self) -> PrintStatus:
        """
        Get the current state of the printer.

        Returns
        -------
        PrintStatus
            The current state of the printer.
        """
        return self.mqtt_client.get_current_state()

    def get_skipped_objects(self) -> list[int]:
        """
        Get the current state of the printer.

        Returns
        -------
        PrintStatus
            The current state of the printer.
        """
        return self.mqtt_client.get_skipped_objects()

    def skip_objects(self, obj_list: list[int]) -> bool:
        """
        Skip Objects during printing.

        Args:
            obj_list (list[int]): object list to skip objects.

        Returns:
            bool: if publish command is successful
        """
        return self.mqtt_client.skip_objects(obj_list=obj_list)

    def set_part_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the part fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self.mqtt_client.set_part_fan_speed(speed)

    def set_aux_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the aux part fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self.mqtt_client.set_aux_fan_speed(speed)

    def set_chamber_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the chamber fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self.mqtt_client.set_chamber_fan_speed(speed)

    def set_auto_step_recovery(self, auto_step_recovery: bool = True) -> bool:
        """
        Set whether or not to set auto step recovery

        Args:
            auto_step_recovery (bool): flag to set auto step recovery.
                Default True.

        Returns:
            bool: success of the auto step recovery command command
        """
        return self.mqtt_client.set_auto_step_recovery(
            auto_step_recovery)

    def vt_tray(self) -> FilamentTray:
        """
        Get the filament information from the tray information.

        Returns:
            Filament: filament information
        """
        return self.mqtt_client.vt_tray()

    def ams_hub(self) -> AMSHub:
        """
        Get ams hub, all AMS's hooked up to printer

        Returns:
            AMSHub: ams information
        """
        self.mqtt_client.process_ams()
        return self.mqtt_client.ams_hub

    def subtask_name(self) -> str:
        """
        Get current subtask name (current print details)

        Returns:
            str: current subtask name
        """
        return self.mqtt_client.subtask_name()

    def gcode_file(self) -> str:
        """
        Get current gcode file (current print details)

        Returns:
            str: current gcode_file name
        """
        return self.mqtt_client.gcode_file()

    def print_error_code(self) -> int:
        """
        Get current gcode file (current print details)

        Returns:
            int: error code (0 if normal)
        """
        return self.mqtt_client.print_error_code()

    def print_type(self) -> str:
        """
        Get what type of print the current printing file is from (cloud, local)

        Returns:
            str: print type
        """
        return self.mqtt_client.print_type()

    def wifi_signal(self) -> str:
        """
        Get Wifi signal in dBm

        Returns:
            str: Wifi signal
        """
        return self.mqtt_client.wifi_signal()

    def reboot(self) -> bool:
        """
        Reboot printer. Warning: this will reboot printer and may require
        manual reconnecting.

        Returns:
            bool: if printer has been rebooted correctly
        """
        return self.mqtt_client.reboot()
