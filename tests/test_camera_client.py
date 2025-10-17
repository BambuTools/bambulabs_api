from unittest.mock import patch

from bambulabs_api.camera_client import PrinterCamera


def test_camera_is_reusable():
    camera = PrinterCamera('1.2.3.4', 'fake_code')

    # Mock the retriever method so it doesn't do any network I/O.
    with patch.object(camera, 'retriever', return_value=None):
        # First cycle
        camera.start()
        camera.stop()

        # Second cycle
        camera.start()  # This was failing before.
        camera.stop()
