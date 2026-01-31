__all__ = ["PrinterFTPClient"]


import ftplib
from io import BytesIO
import ssl
from PIL import Image

from typing import Any, BinaryIO

from PIL.ImageFile import ImageFile

from bambulabs_api.logger import logger


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""  # noqa

    def __init__(self, *args, unwrap: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None
        self.unwrap = unwrap

    """Explicit FTPS, with shared TLS session"""
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=self.sock.session)
        return conn, size

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):  # type: ignore
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        self.voidcmd('TYPE I')
        conn = self.transfercmd(cmd, rest)
        try:
            while True:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            # shutdown ssl layer
            if isinstance(conn, ssl.SSLSocket) and self.unwrap:
                conn.unwrap()  # Fix for storbinary waiting indefinitely for response message from server  # noqa
                pass
        finally:
            conn.close()  # This is the addition to the previous comment.
        return self.voidresp()


class PrinterFTPClient:
    def __init__(self,
                 server_ip: str,
                 access_code: str,
                 user: str = 'bblp',
                 port: int = 990) -> None:
        self.ftps = ImplicitFTP_TLS()

        self.server_ip = server_ip
        self.port = port
        self.user = user
        self.access_code = access_code

    @staticmethod
    def connect_and_run(func):
        """
        A decorator that connects to the FTP server before running the function and closes the connection after running the function.

        Args:
            func (function): the function to be decorated
        """  # noqa

        def wrapper(self: 'PrinterFTPClient', *args, **kwargs) -> Any:
            logger.info("Connecting to FTP server...")
            self.ftps.connect(host=self.server_ip, port=self.port)
            self.ftps.login(self.user, self.access_code)
            logger.info("Connected to FTP server")
            logger.info(self.ftps.prot_p())

            try:
                return func(self, *args, **kwargs)  # type: ignore
            except Exception as e:                                  # noqa  # pylint: disable=broad-exception-caught
                logger.error(f"Failed to execute function: {e}")   # noqa  # pylint: disable=logging-fstring-interpolation
            finally:
                self.ftps.close()
                logger.info("Connection to FTP server closed")
        return wrapper

    @connect_and_run
    def upload_file(self, file: BinaryIO, file_path: str) -> str:
        return self.ftps.storbinary(f'STOR {file_path}', file, blocksize=32768,
                                 callback=lambda x: logger.debug(f"Uploaded {x} bytes"))   # noqa  # pylint: disable=logging-fstring-interpolation

    @connect_and_run
    def list_directory(self, path: str | None = None) -> tuple[str, list[str]]:
        """
        List paths in the given directory.

        Args:
            path (str | None): Path to check. Default None.

        Returns:
            tuple[str, list[str]]: ftp result and list of paths in directory.
        """
        lines: list[str] = []
        res = self.ftps.retrlines(
            f'LIST {path if path is not None else ""}',
            lines.append)
        return res, lines

    def list_images_dir(self) -> tuple[str, list[str]]:
        """
        List paths in the image directory.

        Returns:
            tuple[str, list[str]]: ftp result and list of files in image
                directory.
        """
        return self.list_directory("image")

    def list_cache_dir(self) -> tuple[str, list[str]]:
        """
        List paths in the cache directory.

        Returns:
            tuple[str, list[str]]: ftp result and list of files in cache
                directory.
        """
        return self.list_directory("cache")

    def list_timelapse_dir(self) -> tuple[str, list[str]]:
        """
        List paths in the timelapse directory.

        Returns:
            tuple[str, list[str]]: ftp result and list of files in timelapse
                directory.
        """
        return self.list_directory("timelapse")

    def list_logger_dir(self) -> tuple[str, list[str]]:
        """
        List paths in the logger directory.

        Returns:
            tuple[str, list[str]]: ftp result and list of files in logger
                directory.
        """
        return self.list_directory("logger")

    def last_image_print(self) -> ImageFile | None:
        """
        Get the last image stored in the image directory - generally the
        preview of the last print.

        Returns:
            ImageFile | None: last file/image in the image directory,
                otherwise None.
        """
        _, img_dir = self.list_images_dir()
        if img_dir:
            img_path = img_dir[-1].split(" ")[-1]
            b = self.download_file(f"image/{img_path}")
            return Image.open(b)

        return None

    @connect_and_run
    def download_file(
            self,
            file_path: str,
            blocksize: int = 524288) -> BytesIO:
        """
        Get the last image stored in the image directory - generally the
        preview of the last print.

        Args:
            file_path (str): path of file to download.
            blocksize (int): block size. Default: 524288.

        Returns:
            BytesIO: downloaded file in BytesIO.
        """
        b = BytesIO()
        self.ftps.retrbinary(f'RETR {file_path}', b.write, blocksize=blocksize)
        return b

    @connect_and_run
    def delete_file(self, file_path: str) -> str:
        logger.info(f"Deleting file: {file_path}")     # noqa  # pylint: disable=logging-fstring-interpolation
        return self.ftps.delete(file_path)

    def close(self) -> None:
        self.ftps.quit()
