import logging
import socket
import sys

#from socket import *

logger = logging.getLogger(__name__)

class TcpClient:
    HOST = '172.20.57.7'  # The remote host
    PORT: int = 24532

    def connect(self):
        s = None
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #try:
        #    logger.info("Try to connect")
        #    s.connect((self.HOST, self.PORT))
        #    s.settimeout(1.0)
        #except OSError as msg:
        #    s.close()
        #    s = None

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
        except socket.error as e:
            s.close()
            s = None
            return logger.warning("Error creating socket: %s" % e)
        try:
            s.connect((self.HOST, self.PORT))
        except socket.gaierror as e:
            s.close()
            s = None
            return logger.warning("Address-related error connecting to server: %s" % e)
        except socket.error as e:
            s.close()
            s = None
            return logger.warning("Connection error: %s" % e)

        #if s is None:
        #    logger.info("could not open socket")
        #    #sys.exit(1)

        with s:
            s.sendall(b'Hello, world')
            data = s.recv(1024)
        print('Received', repr(data))

        #logger = logging.getLogger(__name__)
        #logger.debug("bla bla")
        #logger.info("bla bla")
        #logger.warning("bla bla")
        #logger.error("bla bla")
        #logger.critical("bla bla")


        return self