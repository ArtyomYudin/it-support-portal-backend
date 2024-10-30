import json
import logging
import os
import socket
import ssl
import struct
import sys
import asyncio

from db_class import DB
from tcp_client_class import TcpClient



HOST = '172.20.57.5'  # The remote host
PORT: int = 24532

server_key = f'{os.path.dirname(__file__)}/certs/key.pem'
server_cert = f'{os.path.dirname(__file__)}/certs/cert.pem'


if __name__ == '__main__':
    pacs_tcp_client = TcpClient(host=HOST, port=PORT, server_key=server_key, server_cert=server_cert, is_verbose=True)
    pacs_tcp_client.connect()
    #asyncio.run(c)