# Bambulabs API

This package provides a Python API for interacting with BambuLab 3D Printers. The API enables you to control and monitor your printer programmatically, making it an essential tool for developers, makers, and automation enthusiasts. The project is open-source and available on PyPI.

## Support

If you've found this package useful, help us support more printers with the link below.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mchrisgm)

## Status

[![flake8](https://github.com/BambuTools/bambulabs_api/actions/workflows/flake8.yml/badge.svg)](https://github.com/BambuTools/bambulabs_api/actions/workflows/flake8.yml)
[![pytest-unit-tests](https://github.com/BambuTools/bambulabs_api/actions/workflows/pytest-unit-tests.yml/badge.svg)](https://github.com/BambuTools/bambulabs_api/actions/workflows/pytest-unit-tests.yml)
[![GitHub Pages](https://github.com/BambuTools/bambulabs_api/actions/workflows/static.yml/badge.svg)](https://github.com/BambuTools/bambulabs_api/actions/workflows/static.yml)

## Documentation

Comprehensive documentation for this package, including API reference and usage guides, can be found [here](https://bambutools.github.io/bambulabs_api/).

## Installation

To install the package, use `pip`:

```bash
pip install bambulabs_api
```

Make sure you have Python 3.10 or higher installed.

## Features

- **Connect and control** BambuLab 3D printers programmatically.
- **Monitor printer status** in real-time.
- **Execute commands** and manage print jobs directly through Python code.
- **Easy setup** and integration with Python environments.

## Usage Example

Below is a basic example demonstrating how to connect to a BambuLab 3D printer and retrieve its status using the API:

```python
import time
import bambulabs_api as bl

IP = '192.168.1.200'
SERIAL = 'AC12309BH109'
ACCESS_CODE = '12347890'

if __name__ == '__main__':
    print('Starting bambulabs_api example')
    print('Connecting to BambuLab 3D printer')
    print(f'IP: {IP}')
    print(f'Serial: {SERIAL}')
    print(f'Access Code: {ACCESS_CODE}')

    # Create a new instance of the API
    printer = bl.Printer(IP, ACCESS_CODE, SERIAL)

    # Connect to the BambuLab 3D printer
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
```

## Known Limitations

* X1 Printers are not fully supported yet - camera integration is not yet implemented (for api versions < 2.7.0 please see the [No Camera Example](https://bambutools.github.io/bambulabs_api/examples.html#basic-no-camera)).
* H2D printers have not been tested yet.


## Development

If you want to contribute to the development of this API or run it in a development environment, follow these steps:

### Prerequisites

- **Conda**: Make sure you have Conda installed on your system.
- **Git**: Ensure Git is installed for cloning the repository.

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/BambuTools/bambulabs_api.git
   ```

2. Change directory:

   ```bash
   cd bambulabs_api
   ```

3. Create the Conda environment using the provided `environment.yml` file:

   ```bash
   conda env create -f environment.yml
   ```

   Note: Apple M chip workaround
   The binary for myst_parser is not available for M1 devices yet, as a workaround
   - Delete myst_parser from environment.yml
   - run `conda env create -f environment.yml`
   - Execute step 4 then run `pip install myst_parser`

4. Activate the environment:

   ```bash
   conda activate bl_api
   ```

5. Install the package in development mode:

   ```bash
   pip install -e .
   ```

### Running Tests

To ensure everything is working correctly, you can run the tests using `pytest`:

```bash
pytest
```

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

Please make sure your code follows PEP 8 guidelines and that you run tests before submitting a PR.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/BambuTools/bambulabs_api/blob/main/LICENSE) file for more details.

## Support

If you encounter any issues or have questions, feel free to open an issue on the [GitHub repository](https://github.com/BambuTools/bambulabs_api/issues).

## Acknowledgements

This package is an open-source project developed and maintained by the community. Special thanks to all contributors who have helped improve and enhance this API.
