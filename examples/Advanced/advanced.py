import time
import bambulabs_api as bl

IP = '192.168.1.200'
SERIAL = 'AC12309BH109'
ACCESS_CODE = '12347890'

if __name__ == '__main__':
    print('Starting bambulabs_api example')
    print('Connecting to Bambulabs 3D printer')
    print(f'IP: {IP}')
    print(f'Serial: {SERIAL}')
    print(f'Access Code: {ACCESS_CODE}')

    # Create a new instance of the API
    printer = bl.Printer(IP, ACCESS_CODE, SERIAL)

    # Set the printer type and firmware version
    printer.mqtt_client.printer_info = bl.PrinterFirmwareInfo(
        printer_type=bl.PrinterType.H2D.value,
        firmware_version=bl.P1FirmwareVersion.V_01_07_00_00.value,
    )

    # Connect to the Bambulabs 3D printer
    printer.connect()

    time.sleep(2)

    # Get the printer status
    status = printer.get_state()
    print(f'Printer status: {status}')

    # Turn the light off
    printer.turn_light_off()

    time.sleep(2)

    # Turn the light on
    printer.turn_light_on()

    # Disconnect from the Bambulabs 3D printer
    printer.disconnect()
