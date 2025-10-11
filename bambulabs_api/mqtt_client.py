__all__ = ["PrinterMQTTClient"]

import json
from bambulabs_api.logger import logger
import ssl
import datetime
from typing import Any, Callable, Union
from re import match

import paho.mqtt.client as mqtt
import paho.mqtt.properties
import paho.mqtt.reasoncodes
from paho.mqtt.enums import CallbackAPIVersion

from bambulabs_api.ams import AMS, AMSHub
from bambulabs_api.printer_info import (
    NozzleType,
    PrinterFirmwareInfo,
    PrinterType)

from .filament_info import AMSFilamentSettings, FilamentTray
from .states_info import GcodeState, PrintStatus


def set_temperature_support(printer_info: PrinterFirmwareInfo):
    printer_type = printer_info.printer_type
    if printer_type in (PrinterType.P1P, PrinterType.P1S,
                        PrinterType.X1E, PrinterType.X1C, ):
        return printer_info.firmware_version < "01.06"
    elif printer_type in (PrinterType.A1, PrinterType.A1_MINI):
        return printer_info.firmware_version <= "01.04"


def is_valid_gcode(line: str):
    """
    Check if a line is a valid G-code command

    Args:
        line (str): The line to check

    Returns:
        bool: True if the line is a valid G-code command, False otherwise
    """
    # Remove whitespace and comments
    line = line.split(";")[0].strip()

    # Check if line is empty or starts with a valid G-code command (G or M)
    if not line or not match(r"^[GM]\d+", line):
        return False

    # Check for proper parameter formatting
    tokens = line.split()
    for token in tokens[1:]:
        if not match(r"^[A-Z]-?\d+(\.\d+)?$", token):
            return False

    return True


class PrinterMQTTClient:
    """
    Printer class for handling MQTT communication with the printer
    """

    def __init__(
            self,
            hostname: str,
            access: str,
            printer_serial: str,
            username: str = "bblp",
            port: int = 8883,
            timeout: int = 60,
            pushall_timeout: int = 60,
            pushall_on_connect: bool = True,
            strict: bool = False,
    ):
        self._hostname = hostname
        self._access = access
        self._username = username
        self._printer_serial = printer_serial

        self._port = port
        self._timeout = timeout

        self._client: mqtt.Client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv311,
        )
        self._client.username_pw_set(username, access)
        self._client.tls_set(  # type: ignore
            tls_version=ssl.PROTOCOL_TLS,
            cert_reqs=ssl.CERT_NONE
        )
        self._client.tls_insecure_set(True)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self.on_connect_handler: Callable[[
            'PrinterMQTTClient',
            mqtt.Client,
            Any,
            mqtt.ConnectFlags,
            paho.mqtt.reasoncodes.ReasonCode,
            paho.mqtt.properties.Properties | None
        ], None] = lambda a, b, c, d, e, f: None
        self.on_message_handler: Callable[[
            'PrinterMQTTClient',
            mqtt.Client,
            Any,
            mqtt.MQTTMessage
        ], None] = lambda a, b, c, d: None
        self.on_disconnect_handler: Callable[[
            'PrinterMQTTClient',
            mqtt.Client,
            Any,
            mqtt.DisconnectFlags,
            paho.mqtt.reasoncodes.ReasonCode,
            Union[paho.mqtt.properties.Properties, None],
        ], None] = lambda a, b, c, d, e, f: None

        self.pushall_timeout: int = pushall_timeout
        self.pushall_aggressive = pushall_on_connect
        self._last_update: int = 0

        self.command_topic = f"device/{printer_serial}/request"
        logger.info(f"{self.command_topic}")   # noqa: E501  # pylint: disable=logging-fstring-interpolation
        self._data: dict[Any, Any] = {}

        self.ams_hub: AMSHub = AMSHub()
        self.strict = strict

        self.printer_info: PrinterFirmwareInfo = PrinterFirmwareInfo(
            PrinterType.P1S,
            "01.04.00.00"
        )

    def is_connected(self):
        """
        Check if the mqtt client is connected

        Returns
        -------
        bool
            If the mqtt client is connected
        """
        return self._client.is_connected()

    @staticmethod
    def __ready(func: Callable[..., Any]) -> Callable[..., Any]:  # noqa # pylint: disable=missing-function-docstring, no-self-argument
        def wrapper(
                self: 'PrinterMQTTClient',
                *args: list[Any],
                **kwargs: dict[str, Any]) -> Any:
            if not self.ready():
                logger.error("Printer Values Not Available Yet")

                if self.strict:
                    raise Exception("Printer not found")
            return func(self, *args, **kwargs)  # noqa # pylint: disable=not-callable
        return wrapper

    def ready(self) -> bool:
        return bool(self._data)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: paho.mqtt.reasoncodes.ReasonCode,
        properties: Union[paho.mqtt.properties.Properties, None],
    ) -> None:
        logger.info(f"Client Disconnected: {client} {userdata} "
                    f"{disconnect_flags} {reason_code} {properties}")
        self.on_disconnect_handler(
            self,
            client,
            userdata,
            disconnect_flags,
            reason_code,
            properties)

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage
    ) -> None:  # pylint: disable=unused-argument  # noqa
        # Current date and time
        doc = json.loads(msg.payload)
        self.manual_update(doc)

        self.on_message_handler(self, client, userdata, msg)

    def manual_update(self, doc: dict[str, Any]) -> None:
        for k, v in doc.items():
            if k not in self._data:
                self._data[k] = {}
            self._data[k] |= v
        logger.debug(self._data)

        firmware_version = self.firmware_version()
        if firmware_version is not None:
            self.printer_info.firmware_version = firmware_version

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        rc: paho.mqtt.reasoncodes.ReasonCode,
        properties: paho.mqtt.properties.Properties | None
    ) -> None:  # pylint: disable=unused-argument
        """
        _on_connect Callback function for when the client
        receives a CONNACK response from the server.

        Parameters
        ----------
        client : mqtt.Client
            The client instance for this callback
        userdata : String
            User data
        flags : Arraylike
            Response flags sent by the broker
        rc : int
            The connection result
        """
        logger.info(f"Connection result code: {rc}")
        if rc == 0 or not rc.is_failure:
            logger.info("Connected successfully")
            client.subscribe(f"device/{self._printer_serial}/report")
            if self.pushall_aggressive:
                self._client.publish(
                    self.command_topic, json.dumps(
                        {
                            "pushing": {"command": "pushall"},
                            "info": {"command": "get_version"},
                            "upgrade": {"command": "get_history"},
                        }))
            logger.info("Connection Handshake Completed")
        else:
            logger.warning(f"Connection failed with result code {rc}")

        self.on_connect_handler(
            self,
            client,
            userdata,
            flags,
            rc,
            properties
        )

    def connect(self) -> None:
        """
        Connects to the MQTT server asynchronously
        """
        self._client.connect_async(self._hostname, self._port, self._timeout)

    def start(self):
        """
        Starts the MQTT client

        Returns:
            MQTTErrorCode: error code of loop start
        """
        return self._client.loop_start()

    def loop_forever(self):
        """
        Loop client forever (synchonous, blocking call)

        Returns:
            MQTTErrorCode: error code of loop start
        """
        return self._client.loop_forever()

    def stop(self):
        """
        Stops the MQTT client
        """
        self._client.loop_stop()

    def dump(self) -> dict[Any, Any]:
        """
        Dump the current state of the printer message

        Returns:
            dict[Any, Any]: The latest data recorded
        """
        return self._data

    @__ready
    def __get_print(self, key: str, default: Any = None) -> Any:
        self._update()
        return self._data.get("print", {}).get(key, default)

    @__ready
    def __get_info(self, key: str, default: Any = None) -> Any:
        return self._data.get("info", {}).get(key, default)

    def _update(self) -> bool:
        current_time = int(datetime.datetime.now().timestamp())
        if self._last_update + self.pushall_timeout > current_time:
            return False
        self._last_update = current_time
        return self.pushall()

    def info_get_version(self) -> bool:
        """
        Request the printer for hardware and firmware info.

        Returns:
            bool: success state of the get info command
        """
        return self.__publish_command({"info": {"command": "get_version"}})

    def request_firmware_history(self):
        """
        Request firmware history for printer.

        Returns:
            bool: success state of the get info command
        """
        return self.__publish_command(
            {
                "upgrade": {
                    "command": "get_history"
                }
            }
        )

    def get_firmware_history(self) -> list[Any]:
        """
        Get list of history firmware versions.

        Returns:
            list[Any]: list of firmware history.
        """
        return self._data.get("upgrade", {}).get("firmware_optional", [])

    def firmware_version(self):
        """
        Get the firmware verions.

        Returns:
            str: firmware version
        """
        ota: dict[str, Any] | None = next(
            (v for v in self.__get_info("module", [])
             if v.get("name", "") == "ota"), None)
        if ota is not None:
            return ota.get("sw_ver", None)
        else:
            return None

    def pushall(self) -> bool:
        """
        Force the printer to send a full update of the current state
        Warning: Pushall should be used sparingly - large numbers of updates
        can result in the printer lagging.

        Returns:
            bool: success state of the pushall command
        """
        return self.__publish_command({"pushing": {"command": "pushall"}})

    def get_last_print_percentage(self) -> int | str | None:
        """
        Get the last print percentage

        Returns:
            int | str | None: The last print percentage
        """
        return self.__get_print("mc_percent", None)

    def get_remaining_time(self) -> int | str | None:
        """
        Get the remaining time for the print

        Returns:
            int | str | None: The remaining time for the print
        """
        return self.__get_print("mc_remaining_time", None)

    def get_sequence_id(self):
        """
        Get the current sequence ID

        Returns:
            int : Get the current sequence ID
        """
        return int(self.__get_print("sequence_id", 0))

    def get_printer_state(self) -> GcodeState:
        """
        Get the printer state

        Returns:
            GcodeState: printer state
        """
        return GcodeState(self.__get_print("gcode_state", -1))

    def get_file_name(self) -> str:
        """
        Get the file name of the current/last print

        Returns:
            str: file name
        """
        return self.__get_print("gcode_file", "")

    def get_print_speed(self) -> int:
        """
        Get the print speed

        Returns:
            int: print speed
        """
        return int(self.__get_print("spd_mag", 100))

    def __publish_command(self, payload: dict[Any, Any]) -> bool:
        """
        Generate a command payload and publish it to the MQTT server

        Args:
            payload (dict[Any, Any]): command to send to the printer
        """
        if self._client.is_connected() is False:
            logger.error("Not connected to the MQTT server")
            return False

        command = self._client.publish(self.command_topic, json.dumps(payload))
        logger.debug(f"Published command: {payload}")
        command.wait_for_publish()
        return command.is_published()

    def turn_light_off(self) -> bool:
        """
        Turn off the printer light
        """
        return self.__publish_command({"system": {"led_mode": "off"}})

    def turn_light_on(self) -> bool:
        """
        Turn on the printer light
        """
        return self.__publish_command({"system": {"led_mode": "on"}})

    def get_light_state(self) -> str:
        """
        Get the printer light state

        Returns:
            str: led_mode
        """
        light_report: list[dict[str, str]] = self.__get_print(
            "lights_report", [])

        if not light_report:
            return "unknown"

        return light_report[0].get("mode", "unknown")

    def start_print_3mf(self, filename: str,
                        plate_number: int | str,
                        use_ams: bool = True,
                        ams_mapping: list[int] = [0],
                        skip_objects: list[int] | None = None,
                        flow_calibration: bool = True,
                        ) -> bool:
        """
        Start the print

        Parameters:
            filename (str): The name of the file to print
            plate_number (int): The plate number to print to
            use_ams (bool, optional): Use the AMS system. Defaults to True.
            ams_mapping (list[int], optional): The AMS mapping. Defaults to
                [0].
            skip_objects (list[int] | None, optional): List of gcode objects to
                skip. Defaults to [].

        Returns:
            str: print_status
        """
        if skip_objects is not None and not skip_objects:
            skip_objects = None

        if isinstance(plate_number, int):
            plate_location = f"Metadata/plate_{int(plate_number)}.gcode"
        else:
            plate_location = plate_number
        return self.__publish_command(
            {
                "print":
                {
                    "command": "project_file",
                    "param": plate_location,
                    "file": filename,
                    "bed_leveling": True,
                    "bed_type": "textured_plate",
                    "flow_cali": bool(flow_calibration),
                    "vibration_cali": True,
                    "url": f"ftp:///{filename}",
                    "layer_inspect": False,
                    "sequence_id": "10000000",
                    "use_ams": bool(use_ams),
                    "ams_mapping": list(ams_mapping),
                    "skip_objects": skip_objects,
                }
            })

    def set_onboard_printer_timelapse(self, enable: bool = True):
        """
        Enable/disable the printer's onboard timelapse/video
        functionality.

        Args:
            enable (bool): object list to skip objects.
                Defaults to True.

        Returns:
            bool: if publish command is successful.
        """
        return self.__publish_command({
            "camera": {
                "command": "ipcam_record_set",
                "control": "disable" if not enable else "enable"
            }
        })

    def skip_objects(self, obj_list: list[int]) -> bool:
        """
        Skip Objects during printing.

        Args:
            obj_list (list[int]): object list to skip objects.

        Returns:
            bool: if publish command is successful
        """
        return self.__publish_command(
            {
                "print":
                {
                    "command": "skip_objects",
                    "obj_list": obj_list,
                }
            })

    def get_skipped_objects(self) -> list[int]:
        """
        Get skipped Objects.

        Args:

        Returns:
            bool: if publish command is successful
        """
        return self.__get_print("s_obj", [])

    def get_current_state(self) -> PrintStatus:
        """
        Get the current printer state from stg_cur

        Returns:
            PrintStatus: current_state
        """
        return PrintStatus(self.__get_print("stg_cur", -1))

    def stop_print(self) -> bool:
        """
        Stop the print

        Returns:
            str: print_status
        """
        return self.__publish_command({"print": {"command": "stop"}})

    def pause_print(self) -> bool:
        """
        Pause the print

        Returns:
            str: print_status
        """
        if self.get_printer_state() == GcodeState.PAUSE:
            return True
        return self.__publish_command({"print": {"command": "pause"}})

    def resume_print(self) -> bool:
        """
        Resume the print

        Returns:
            str: print_status
        """
        if self.get_printer_state() == GcodeState.RUNNING:
            return True
        return self.__publish_command({"print": {"command": "resume"}})

    def __send_gcode_line(self, gcode_command: str) -> bool:
        """
        Send a G-code line command to the printer

        Args:
            gcode_command (str): G-code command to send to the printer
        """
        return self.__publish_command({"print": {"sequence_id": "0",
                                                 "command": "gcode_line",
                                                 "param": f"{gcode_command}"}})

    def send_gcode(
            self,
            gcode_command: str | list[str],
            gcode_check: bool = True) -> bool:
        """
        Send a G-code line command to the printer

        Args:
            gcode_command (str | list[str]): G-code command(s) to send to the
                printer
            gcode_check: (bool): whether to check gcode validity.
                Default to True.
        """
        if isinstance(gcode_command, str):
            if gcode_check and not is_valid_gcode(gcode_command):
                raise ValueError("Invalid G-code command")

            return self.__send_gcode_line(gcode_command)
        elif isinstance(gcode_command, list):  # type: ignore
            if gcode_check and any(
                    not is_valid_gcode(g) for g in gcode_command):
                raise ValueError("Invalid G-code command")
            return self.__send_gcode_line("\n".join(gcode_command))

    def set_bed_temperature(
            self,
            temperature: int,
            override: bool = False
    ) -> bool:
        """
        Set the bed temperature. Note P1 firmware version above 01.06 does not
        support M140. M190 is used instead (set and wait for temperature).
        To prevent long wait times, if temperature is set to below 40 deg cel,
        no temperature is set, override flag is provided to circumvent this.

        Args:
            temperature (int): The temperature to set the bed to
            override (bool): Whether to override guards. Default to False

        Returns:
            bool: success of setting the bed temperature
        """
        if set_temperature_support(self.printer_info):
            return self.__send_gcode_line(f"M140 S{temperature}\n")
        else:
            if temperature < 40 and not override:
                logger.warning(
                    "Attempting to set low bed temperature not recommended. "
                    "Set override flag to true to if you're sure you want to "
                    f"run M190 S{temperature};"
                )
                return False
            return self.__send_gcode_line(f"M190 S{temperature}\n")

    def get_fan_gear(self):
        """
        Get fan_gear

        Returns:
            int: consolidated fan value for part, aux and chamber fan speeds
        """
        return self.__get_print("fan_gear", 0)

    def get_part_fan_speed(self):
        """
        Get part fan speed

        Returns:
            int: 0-255 value representing part fan speed
        """
        return self.get_fan_gear() % 256

    def get_aux_fan_speed(self):
        """
        Get auxiliary fan speed

        Returns:
            int: 0-255 value representing auxiliary fan speed
        """
        return ((self.get_fan_gear() >> 8)) % 256

    def get_chamber_fan_speed(self):
        """
        Get chamber fan speed

        Returns:
            int: 0-255 value representing chamber fan speed
        """
        return self.get_fan_gear() >> 16

    def set_part_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the part fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self._set_fan_speed(speed, 1)

    def set_aux_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the aux part fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self._set_fan_speed(speed, 2)

    def set_chamber_fan_speed(self, speed: int | float) -> bool:
        """
        Set the fan speed of the chamber fan

        Args:
            speed (int | float): The speed to set the part fan

        Returns:
            bool: success of setting the fan speed
        """
        return self._set_fan_speed(speed, 3)

    def _set_fan_speed(self, speed: int | float, fan_num: int) -> bool:
        """
        Set the fan speed of a fan

        Args:
            speed (int | float): The speed to set the fan to
            fan_num (int): Id of the fan to be set

        Returns:
            bool: success of setting the fan speed
        """
        if isinstance(speed, int):
            if speed > 255 or speed < 0:
                raise ValueError(f"Fan Speed {speed} is not between 0 and 255")
            return self.__send_gcode_line(f"M106 P{fan_num} S{speed}\n")

        elif isinstance(speed, float):  # type: ignore
            if speed < 0 or speed > 1:
                raise ValueError(f"Fan Speed {speed} is not between 0 and 1")
            speed = round(255 / speed)
            return self.__send_gcode_line(f"M106 P{fan_num} S{speed}\n")

        raise ValueError("Fan Speed is not float or int")

    def set_bed_height(self, height: int) -> bool:
        """
        Set the absolute height of the bed (Z-axis).
        0 is the bed at the nozzle tip and 256 is the bed at the bottom of the printer.

        Args:
            height (int): height to set the bed to

        Returns:
            bool: success of the bed height setting
        """  # noqa
        return self.__send_gcode_line(f"G90\nG0 Z{height}\n")

    def auto_home(self) -> bool:
        """
        Auto home the printer

        Returns:
            bool: success of the auto home command
        """
        return self.__send_gcode_line("G28\n")

    def request_access_code(self):
        """
        Request the printer for access code.

        Returns:
            bool: success of the auto home command
        """
        return self.__publish_command({
            "system": {
                "command": "get_access_code",
            }
        })

    def get_access_code(self) -> str:
        """
        Get local access code.

        Returns:
            list[Any]: list of firmware history.
        """
        code = self._data.get("system", {}).get("command", None)
        if code is None:
            return self._access
        elif code != self._access:
            logger.error(
                f"Unexpected state: our access code is {self._access}; "
                f"reported is {code}")
            return code
        else:
            return code

    def set_auto_step_recovery(self, auto_step_recovery: bool = True) -> bool:
        """
        Set whether or not to set auto step recovery

        Args:
            auto_step_recovery (bool): flag to set auto step recovery.
                Default True.

        Returns:
            bool: success of the auto step recovery command command
        """
        return self.__publish_command({"print": {
            "command": "gcode_line", "auto_recovery": auto_step_recovery
        }})

    def set_print_speed_lvl(self, speed_lvl: int = 1) -> bool:
        """
        Set the print speed

        Args:
            speed_lvl (int, optional): Set the speed level of printer. Defaults to 1.

        Returns:
            bool: success of setting the print speed
        """  # noqa
        return self.__publish_command(
            {"print": {"command": "print_speed", "param": f"{speed_lvl}"}}
        )

    def set_nozzle_temperature(
            self,
            temperature: int,
            override: bool = False
    ) -> bool:
        """
        Set the nozzle temperature. Note P1 firmware version above 01.06 does
        not support M104. M109 is used instead (set and wait for temperature).
        To prevent long wait times, if temperature is set to below 40 deg cel,
        no temperature is set, override flag is provided to circumvent this.

        Args:
            temperature (int): The temperature to set the bed to
            override (bool): Whether to override guards. Default to False
        Args:
            temperature (int): temperature to set the nozzle to

        Returns:
            bool: success of setting the nozzle temperature
        """
        if set_temperature_support(self.printer_info):
            return self.__send_gcode_line(f"M104 S{temperature}\n")
        else:
            if temperature < 60 and not override:
                logger.warning(
                    "Attempting to set low bed temperature not recommended. "
                    "Set override flag to true to if you're sure you want to "
                    f"run M109 S{temperature};"
                )
                return False
            return self.__send_gcode_line(f"M109 S{temperature}\n")

    def set_printer_filament(
        self,
        filament_material: AMSFilamentSettings,
        colour: str,
        ams_id: int = 255,
        tray_id: int = 254,
    ) -> bool:
        """
        Set the printer filament manually fed into the printer

        Args:
            filament_material (Filament): filament material to set.
            colour (str): colour of the filament.
            ams_id (int): ams id. Default to external filament spool: 255.
            tray_id (int): tray id. Default to external filament spool: 254.

        Returns:
            bool: success of setting the printer filament
        """
        assert len(colour) == 6, "Colour must be a 6 character hex string"

        return self.__publish_command(
            {
                "print": {
                    "command": "ams_filament_setting",
                    "ams_id": ams_id,
                    "tray_id": tray_id,
                    "tray_info_idx": filament_material.tray_info_idx,
                    "tray_color": f"{colour.upper()}FF",
                    "nozzle_temp_min": filament_material.nozzle_temp_min,
                    "nozzle_temp_max": filament_material.nozzle_temp_max,
                    "tray_type": filament_material.tray_type
                }
            }
        )

    def load_filament_spool(self) -> bool:
        """
        Load the filament into the printer

        Returns:
            bool: success of loading the filament
        """
        return self.__publish_command(
            {
                "print": {
                    "command": "ams_change_filament",
                    "target": 255,
                    "curr_temp": 215,
                    "tar_temp": 215,
                }
            }
        )

    def unload_filament_spool(self) -> bool:
        """
        Unload the filament from the printer

        Returns:
            bool: success of unloading the filament
        """
        return self.__publish_command(
            {
                "print": {
                    "command": "ams_change_filament",
                    "target": 254,
                    "curr_temp": 215,
                    "tar_temp": 215,
                }
            }
        )

    def resume_filament_action(self) -> bool:
        """
        Resume the current filament action

        Returns:
            bool: success of resuming the filament action
        """
        return self.__publish_command(
            {
                "print": {
                    "command": "ams_control",
                    "param": "resume",
                }
            }
        )

    def calibration(
            self,
            bed_levelling: bool = True,
            motor_noise_cancellation: bool = True,
            vibration_compensation: bool = True) -> bool:
        """
        Start the full calibration process

        Returns:
            bool: success of starting the full calibration process
        """
        bitmask = 0

        if bed_levelling:
            bitmask |= 1 << 1
        if vibration_compensation:
            bitmask |= 1 << 2
        if motor_noise_cancellation:
            bitmask |= 1 << 3

        return self.__publish_command(
            {
                "print": {
                    "command": "calibration",
                    "option": bitmask
                }
            }
        )

    def get_bed_temperature(self) -> float:
        """
        Get the bed temperature

        Returns:
            float: bed temperature
        """
        return float(self.__get_print("bed_temper", 0.0))

    def get_bed_temperature_target(self) -> float:
        """
        Get the bed temperature target

        Returns:
            float: bed temperature target
        """
        return float(self.__get_print("bed_target_temper", 0.0))

    def get_nozzle_temperature(self) -> float:
        """
        Get the nozzle temperature

        Returns:
            float: nozzle temperature
        """
        return float(self.__get_print("nozzle_temper", 0.0))

    def get_nozzle_temperature_target(self) -> float:
        """
        Get the nozzle temperature target

        Returns:
            float: nozzle temperature target
        """
        return float(self.__get_print("nozzle_target_temper", 0.0))

    def get_chamber_temperature(self) -> float:
        """
        Get the chamber temperature

        Returns:
            float: chamber temperature
        """
        primary = self.__get_print("chamber_temper", None)
        try:
            return float(primary)
        except (TypeError, ValueError):
            pass  # fall back

        device = self.__get_print("device", {})
        if isinstance(device, dict):
            ctc = device.get("ctc", {})
            if isinstance(ctc, dict):
                info = ctc.get("info", {})
                if isinstance(info, dict):
                    try:
                        return float(info.get("temp", 0.0))
                    except (TypeError, ValueError):
                        pass

        return 0.0

    def current_layer_num(self) -> int:
        """
        Get the number of layers of the current/last print

        Returns:
            int: number of layers
        """
        return int(self.__get_print("layer_num", 0))

    def total_layer_num(self) -> int:
        """
        Get the total number of layers of the current/last print

        Returns:
            int: number of layers
        """
        return int(self.__get_print("total_layer_num", 0))

    def gcode_file_prepare_percentage(self) -> int:
        """
        Get the gcode file preparation percentage

        Returns:
            int: percentage
        """
        return int(self.__get_print("gcode_file_prepare_percent", 0))

    def nozzle_diameter(self) -> float:
        """
        Get the nozzle diameter currently registered to printer

        Returns:
            float: nozzle diameter
        """
        return float(self.__get_print("nozzle_diameter", 0))

    def nozzle_type(self) -> NozzleType:
        """
        Get the nozzle type currently registered to printer

        Returns:
            NozzleType: nozzle diameter
        """
        return NozzleType(
            self.__get_print("nozzle_type", "stainless_steel"))

    def set_nozzle_info(
            self,
            nozzle_type: NozzleType,
            nozzle_diameter: float = 0.4) -> bool:
        """
        Set the nozzle info.

        Args:
            nozzle_type (NozzleType): nozzle type to set.
            nozzle_diameter (Optional[float]): diameter of nozzle.
                Defaults to 0.4.

        Returns:
            bool: if publish command is successful.
        """
        return self.__publish_command(
            {
                "system": {
                    "accessory_type": "nozzle",
                    "command": "set_accessories",
                    "nozzle_diameter": nozzle_diameter,
                    "nozzle_type": nozzle_type.value,
                }
            }
        )

    def new_printer_firmware(self) -> str | None:
        """
        Get if a new firmware version is available.

        Returns:
            str | None: newest firmware version if available else None.
        """
        return next(
            (
                i.get("new_ver", None) for i in (
                    self.__get_print(
                        "upgrade_state", {}
                    ).get("new_ver_list", [])
                ) if i.get("name", "") == "ota"
            ), None)

    def upgrade_firmware(self, override: bool = False) -> bool:
        """
        Upgrade to latest firmware. Logs warning is firmware version
        may cause api to fail.

        Args:
            override (bool): nozzle type to set.
                Default to False.

        Returns:
            bool: if the printer upgraded to the latest firmware.
                Returns false if firmware is causes api to break and
                override is not provided.
        """
        new_firmware = self.new_printer_firmware()
        if new_firmware is not None:
            if new_firmware >= "1.08" and not override:
                logger.warning(
                    f"You are about to upgrade to {new_firmware}."
                    "Firmware above 1.08 may result in api incompatibility"
                )
                return False
            return self.__publish_command({
                "upgrade": {
                    "command": "upgrade_confirm",
                    "src_id": 2,
                }
            })
        else:
            return False

    def downgrade_firmware(self, firmware_version: str) -> bool:
        """
        Downgrade the firmware to a given version. Requires firmware version
        to be listed in the firmware history.

        Args:
            firmware_version (str): target firmware version to downgrade to.
                Firmware version must be in the version history.

        Returns:
            bool: if the printer downgraded to the target firmware.
        """
        firmware_history = self.get_firmware_history()
        if not firmware_history:
            logger.warning("Firmware history not up to date")
            return False
        firmware = next(
            (firmware["firmware"] for firmware in firmware_history
             if firmware.get("firmware", {}).get(
                 "version", None) == firmware_version), None)

        if firmware is None:
            logger.warning(
                f"Firmware {firmware_version} not found in listed firmware")
            return False

        return self.__publish_command(
            {
                "upgrade": {
                    "command": "upgrade_history",
                    "src_id": 2,
                    "firmware_optional": {
                        "firmware": firmware,
                    }
                }
            }
        )

    def process_ams(self):
        """
        Get the filament information from the AMS system
        """
        ams_info: dict[str, Any] = self.__get_print("ams")

        self.ams_hub = AMSHub()
        if not ams_info or ams_info.get("ams_exist_bits", "0") == "0":
            return

        ams_units: list[dict[str, Any]] = ams_info.get("ams", [])

        for k, v in enumerate(ams_units):
            humidity = int(v.get("humidity", 0))
            temp = float(v.get("temp", 0.0))
            id = int(v.get("id", k))

            ams = AMS(humidity=humidity, temperature=temp)

            trays: list[dict[str, Any]] = v.get("tray", [])

            if trays:
                for tray_id, tray in enumerate(trays):
                    tray_id = int(tray.get("id", tray_id))
                    tray_n: Any | None = tray.get("n", None)
                    if tray_n:
                        ams.set_filament_tray(
                            tray_index=tray_id,
                            filament_tray=FilamentTray.from_dict(tray))

            self.ams_hub[id] = ams

    def vt_tray(self) -> FilamentTray:
        """
        Get Filament Tray of the external spool.

        Returns:
            FilamentTray: External Spool Filament Tray
        """
        tray = self.__get_print("vt_tray")
        return FilamentTray.from_dict(tray)

    def subtask_name(self) -> str:
        """
        Get current subtask name (current print details)

        Returns:
            str: current subtask name
        """
        return self.__get_print("subtask_name")

    def gcode_file(self) -> str:
        """
        Get current gcode file (current print details)

        Returns:
            str: current gcode_file name
        """
        return self.__get_print("gcode_file")

    def print_error_code(self) -> int:
        """
        Get current gcode file (current print details)

        Returns:
            int: error code (0 if normal)
        """
        return int(self.__get_print("print_error", 0))

    def print_type(self) -> str:
        """
        Get what type of print the current printing file is from (cloud, local)

        Returns:
            str: print type
        """
        return self.__get_print("print_type")

    def wifi_signal(self) -> str:
        """
        Get Wifi signal in dBm

        Returns:
            str: Wifi signal
        """
        return self.__get_print("wifi_signal", "")

    def reboot(self) -> bool:
        """
        Reboot printer. Warning: this will reboot printer and may require
        manual reconnecting.

        Returns:
            bool: if printer has been rebooted correctly
        """
        logger.warning("Sending reboot command!")
        return self.__publish_command(
            {
                "system": {
                    "command": "reboot"
                }
            }
        )
