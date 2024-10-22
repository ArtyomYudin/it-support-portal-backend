import json
import logging
import os
import socket
import ssl
import struct
import sys
import threading

from django.db.models.functions import NullIf

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

        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        #context.options |= (
        #        ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_2
        #)
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.set_ciphers('AES256-SHA')
        context.load_verify_locations(self.server_cert)
        context.load_cert_chain(certfile=self.server_cert, keyfile=self.server_key)

        client = None
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
            client = context.wrap_socket(client)
            #client.settimeout(2.0)
        except socket.error as e:
            client.close()
            client = None
            return logger.warning('Error creating socket: %s' % e)
        try:
            client.bind(('0.0.0.0', self.SPORT))
            client.connect((self.HOST, self.PORT))
        except socket.gaierror as e:
            client.close()
            client = None
            return logger.warning('Address-related error connecting to server: %s' % e)
        except socket.error as e:
            client.close()
            client = None
            return logger.warning('Connection error: %s' % e)

        if client is None:
            logger.info('could not open socket')
        #    #sys.exit(1)

        return client

    def receive_data(self):

        while True:
            received = None
            #data = client.recv()
            #if data:
            #    received = json.loads(data[4:].decode('utf-8'))
            #    print(f'RECEIVED: {received}')
            try:
                recv_data = client.recv(4096)
            except:
                # Handle the case when server process terminates
                print("Server closed connection, thread exiting.")
                #thread.interrupt_main()
                break
            if not recv_data:
                # Recv with no data, server closed connection
                print("Server closed connection, thread exiting.")
                #thread.interrupt_main()
                break
            else:
                received = json.loads(recv_data[4:].decode('utf-8'))
                #print("Received data: ", json.loads(recv_data[4:].decode('utf-8')))

        return received

        #try:
        #    client.send(create_buffer(filter_events_command))
        #    print(client)
        #    while True:
        #        data = client.recv()
        #        if data:
        #            received = json.loads(data[4:].decode('utf-8'))
        #            print(f'RECEIVED: {received}')
        #finally:
        #    client.close()
        #    logger.info('Connection closed')

#pacs_tcp_client = TcpClient()
#pacs_tcp_client.connect()
