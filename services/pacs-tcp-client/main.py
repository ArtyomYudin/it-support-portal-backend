import json
import logging
import os
import socket
import ssl
import struct
import sys
import asyncio

from db_class import DB


class TcpClient:
    def __init__(self, is_verbose=False):
        if is_verbose:
            self.log_level=logging.DEBUG
        else:
            self.log_level=logging.INFO

        log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
        self.logger = logging.getLogger('pacs_tcp_client')
        self.logger.setLevel(self.log_level)

        # writing to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)

        self.db = DB(user='itsupport', password='gRzXJHxq7qLM', database='itsupport', host='10.3.0.2')
        #self.db.connect()

    HOST = '172.20.57.7'  # The remote host
    PORT: int = 24532

    server_key = f'{os.path.dirname(__file__)}/certs/key.pem'
    server_cert = f'{os.path.dirname(__file__)}/certs/cert.pem'

    @staticmethod
    def create_buffer(post_json_data):
        buffer = post_json_data.encode('utf-8')
        buffer_with_byte = bytearray(4 + len(buffer))
        struct.pack_into('<I', buffer_with_byte, 0, len(buffer))
        buffer_with_byte[4:] = buffer
        return bytes(buffer_with_byte)

    def connect(self):
        client = None
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


        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.options &= ~ssl.OP_NO_TLSv1_3 & ~ssl.OP_NO_TLSv1_2 & ~ssl.OP_NO_TLSv1_1
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1
        #context.set_ciphers('AES256-SHA')
        context.set_ciphers('DEFAULT@SECLEVEL=0')
        context.load_verify_locations(self.server_cert)
        context.load_cert_chain(certfile=self.server_cert, keyfile=self.server_key)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client = context.wrap_socket(client, server_hostname='SKD')
        except socket.error as e:
            client.close()
            client = None
            return self.logger.warning('Error creating socket: %s' % e)
        try:
            client.connect((self.HOST, self.PORT))
            self.logger.info(f'Connection to server {self.HOST} on port {self.PORT}')
        except socket.gaierror as e:
            client.close()
            client = None
            return self.logger.warning('Address-related error connecting to server: %s' % e)
        except socket.error as e:
            client.close()
            client = None
            return self.logger.warning('Connection error: %s' % e)

        if client is None:
            self.logger.info('could not open socket')
            sys.exit(1)

        #try:
        with client as c:
            c.sendall(self.create_buffer(filter_events_command))
            #print(create_buffer(filter_events_command))
            while True:
                data = c.recv(1024)
                if data:
                    received = json.loads(data[4:].decode('utf-8'))
                    match received['Command']:
                        case 'ping':
                            c.sendall(self.create_buffer(ping_command))
                        case 'events':
                            asyncio.run(self.db.execute('''INSERT INTO public.pacs_event(created, ap_id, owner_id, card, code) VALUES(1, 1, 1, 1, 1)''' ))
                            self.logger.debug(f'RECEIVED: {received}')

        #finally:
        #    client.close()


if __name__ == '__main__':
    pacs_tcp_client = TcpClient(True)
    pacs_tcp_client.connect()