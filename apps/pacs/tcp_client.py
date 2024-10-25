import json
import logging
import os
import socket
import ssl
import struct
import sys
import threading
from time import sleep

logger = logging.getLogger(__name__)


class TcpClient:
    HOST = '172.20.57.7'  # The remote host
    PORT: int = 24532
    SPORT: int = 31415

    server_key = f'{os.path.dirname(__file__)}/certs/key.pem'
    server_cert = f'{os.path.dirname(__file__)}/certs/cert.pem'

    def connect(self):

        filter_events_command = json.dumps({
            'Command': 'filterevents',
            'Id': 1,
            'Version': 1,
            'Filter': 1,
        })

        ping_command = json.dumps({
            'Command': 'ping',
            'Id': 1,
            'Version': 1,
        })

        def create_buffer(post_json_data):
            buffer = post_json_data.encode('utf-8')
            buffer_with_byte = bytearray(4 + len(buffer))
            struct.pack_into('<I', buffer_with_byte, 0, len(buffer))
            buffer_with_byte[4:] = buffer
            return bytes(buffer_with_byte)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.options &= ~ssl.OP_NO_TLSv1_3 & ~ssl.OP_NO_TLSv1_2 & ~ssl.OP_NO_TLSv1_1
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1
        #context.set_ciphers('AES256-SHA')
        context.set_ciphers('DEFAULT@SECLEVEL=0')
        context.load_verify_locations(self.server_cert)
        context.load_cert_chain(certfile=self.server_cert, keyfile=self.server_key)

        #client = None
        #s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #try:
        #    logger.info('Try to connect')
        #    s.connect((self.HOST, self.PORT))
        #    s.settimeout(1.0)
        #except OSError as msg:
        #    s.close()
        #    s = None

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client = context.wrap_socket(client, server_hostname='SKD')
        except socket.error as e:
           # client.close()
            print('1')
            #client = None
            return logger.warning('Error creating socket: %s' % e)
        try:
            #client.bind(('172.30.4.133', self.SPORT))
            client.connect((self.HOST, self.PORT))
            print(client)
        except socket.gaierror as e:
            client.close()
            print('2')
            #client = None
            return logger.warning('Address-related error connecting to server: %s' % e)
        except socket.error as e:
            client.close()
            print('3')
            #client = None
            return logger.warning('Connection error: %s' % e)

        if client is None:
            print('4')
            logger.info('could not open socket')
        #    #sys.exit(1)

        #try:
            #with client:
        client.sendall(create_buffer(filter_events_command))
        #print(create_buffer(filter_events_command))
        while True:
            data = client.recv(1024)
            if data:
                received = json.loads(data[4:].decode('utf-8'))
                print(f'RECEIVED: {received}')
                    #else: print(data)
        #finally:
        #    client.close()
        #    print('5')

pacs_tcp_client = TcpClient()
pacs_tcp_client.connect()

