#!/usr/bin/python3

import base64
import struct
import socket
import ssl

from threading import Thread
import time

from bambulabs_api.logger import logger

__all__ = ["PrinterCamera"]


class PrinterCamera:
    def __init__(
        self,
        hostname: str,
        access_code: str,
        port: int = 6000,
        username: str = 'bblp'
    ):
        self.__username = username
        self.__access_code = str(access_code)
        self.__hostname = str(hostname)
        self.__port = port

        self.__thread = None
        self.last_frame = None
        self.alive = False

    def start(self):
        """
        Start the camera worker thread

        Returns
        -------
        bool
            If the camera thread was started successfully. False if already
            running.
        """
        if not self.alive:
            self.alive = True
            self.__thread = Thread(target=self.retriever)
            self.__thread.daemon = True
            self.__thread.start()
            return True
        else:
            return False

    def stop(self):
        """
        Stop the camera client
        """
        self.alive = False
        if self.__thread is not None:
            self.__thread.join()
            self.__thread = None

    def get_frame(self):
        if self.last_frame is None:
            raise Exception("No frame available.")  # noqa  # pylint: disable=broad-exception-raised
        encoded_image = base64.b64encode(self.last_frame).decode("utf-8")
        return encoded_image

    def retriever(self):
        logger.info("Starting camera thread.")

        auth_data = bytearray()
        connect_attempts = 0

        auth_data += struct.pack("<I", 0x40)    # '@'\0\0\0
        auth_data += struct.pack("<I", 0x3000)  # \0'0'\0\0
        auth_data += struct.pack("<I", 0)       # \0\0\0\0
        auth_data += struct.pack("<I", 0)       # \0\0\0\0
        for i in range(0, len(self.__username)):
            auth_data += struct.pack("<c", self.__username[i].encode('ascii'))
        for i in range(0, 32 - len(self.__username)):
            auth_data += struct.pack("<x")
        for i in range(0, len(self.__access_code)):
            auth_data += struct.pack("<c",
                                     self.__access_code[i].encode('ascii'))
        for i in range(0, 32 - len(self.__access_code)):
            auth_data += struct.pack("<x")

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        jpeg_start = bytearray([0xff, 0xd8, 0xff, 0xe0])
        jpeg_end = bytearray([0xff, 0xd9])

        read_chunk_size = 4096  # 4096 is the max we'll get even if we increase this.  # noqa

        while self.alive:
            try:
                with socket.create_connection((self.__hostname, self.__port)) as sock:  # noqa
                    try:
                        connect_attempts += 1
                        sslSock = ctx.wrap_socket(sock,
                                                  server_hostname=self.__hostname)      # noqa
                        logger.info("Attempting to connect...")
                        sslSock.write(auth_data)
                        img = None
                        payload_size = 0

                        status = sslSock.getsockopt(socket.SOL_SOCKET,
                                                    socket.SO_ERROR)
                        if status != 0:
                            logger.warning(f"Socket error: {status}")  # noqa  # pylint: disable=logging-fstring-interpolation
                    except socket.error as e:  # noqa
                        logger.warning(f"Error in socket: {e}")        # noqa  # pylint: disable=logging-fstring-interpolation
                        continue

                    sslSock.setblocking(False)
                    sslSock.settimeout(5.0)

                    while self.alive:
                        try:
                            logger.debug("Reading chunk...")
                            dr = sslSock.recv(read_chunk_size)

                        except ssl.SSLWantReadError:
                            time.sleep(1)
                            continue

                        except Exception as e:  # noqa  # pylint: disable=broad-exception-caught
                            logger.error(f"Exception. Type: {type(e)} Args: {e}")  # noqa  # pylint: disable=logging-fstring-interpolation
                            time.sleep(1)
                            break

                        logger.debug(f"Read chunk {len(dr)}")          # noqa  # pylint: disable=logging-fstring-interpolation

                        if img is not None and len(dr) > 0:
                            logger.debug("Appending to Image")
                            img += dr
                            if len(img) > payload_size:
                                img = None
                            elif len(img) == payload_size:
                                if img[:4] != jpeg_start:
                                    pass
                                elif img[-2:] != jpeg_end:
                                    pass
                                else:
                                    self.last_frame = img
                                img = None

                        elif len(dr) == 16:
                            logger.debug("Got header")
                            connect_attempts = 0
                            img = bytearray()
                            payload_size = int.from_bytes(dr[0:3],
                                                          byteorder='little')

                        elif len(dr) == 0:
                            time.sleep(5)
                            logger.error("Wrong access code or IP")
                            break

                        else:
                            logger.error("something bad happened")
                            time.sleep(1)
                            break

            except Exception as e:  # noqa  # pylint: disable=broad-exception-caught
                logger.error(f"Error occurred: {e}")           # noqa  # pylint: disable=logging-fstring-interpolation
                continue
            finally:
                time.sleep(5)
                logger.info("Reconnecting...")
                continue
