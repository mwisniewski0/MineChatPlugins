import asyncio
import struct
import traceback
from typing import Optional

from commands import ServerCommandExecutor

LOGIN_TYPE = 3
COMMAND_TYPE = 2
RESPONSE_TYPE = 0

DELIMITER_REQUEST_ID = -1024


class Packet:
    def __init__(self, request_id: int, packet_type: int, payload: bytes):
        self.payload = payload
        self.type = packet_type
        self.request_id = request_id

    def encode(self) -> bytes:
        # Packet format is:
        # int32: Length of the remainder of the packet
        # int32: ID of the request
        # int32: Type of request (3 for login, 2 to run a command, 0 for a response)
        # blob: payload
        # \0\0
        non_length_data = struct.pack('<ii', self.request_id, self.type) + self.payload + b'\0\0'
        length_data = struct.pack('<i', len(non_length_data))
        return length_data + non_length_data

    @staticmethod
    async def read_from_reader(reader: asyncio.StreamReader) -> 'Packet':
        length, request_id, packet_type = struct.unpack('<iii', await reader.readexactly(12))
        payload = await reader.readexactly(length - 4 - 4 - 2)
        await reader.readexactly(2)  # Remove padding from the stream

        return Packet(request_id, packet_type, payload)


class RconConnection(ServerCommandExecutor):
    def __init__(self):
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._current_request_id = 1

        self._response_futures = {}

    async def connect(self, port: int, password: str):
        """
        Given that this is an unencrypted protocol, we will not allow sending the information
        anywhere but to localhost.
        """
        if self._reader is not None:
            raise ConnectionError("Already connected")

        self._reader, self._writer = await asyncio.open_connection('localhost', port)
        self._writer.write(Packet(0, LOGIN_TYPE, password.encode()).encode())
        await self._writer.drain()
        login_response = await Packet.read_from_reader(self._reader)

        if login_response.request_id == -1:
            raise ConnectionRefusedError('Password was incorrect')

    async def server_communication_loop(self):
        try:
            request_id = None
            response_payload = b''
            while True:
                packet = await Packet.read_from_reader(self._reader)
                if packet.request_id == DELIMITER_REQUEST_ID:
                    self._response_futures[request_id].set_result(response_payload)
                    response_payload = b''
                    request_id = None
                else:
                    request_id = packet.request_id
                    response_payload += packet.payload
        except Exception:
            traceback.print_exc()
            exit(1)

    async def send_command(self, command: str) -> str:
        packet = Packet(self._current_request_id, COMMAND_TYPE, command.encode())
        self._prepare_next_id()

        future = asyncio.get_event_loop().create_future()
        self._response_futures[packet.request_id] = future

        self._writer.write(packet.encode())

        # Fix for: https://developer.valvesoftware.com/wiki/Source_RCON_Protocol#Multiple-packet_Responses
        # We are writing an incorrect message to delimit responses from the server.
        self._writer.write(Packet(DELIMITER_REQUEST_ID, RESPONSE_TYPE, b'').encode())

        await self._writer.drain()

        return await future

    def _prepare_next_id(self):
        # Python can store arbitrary large integers, but the protocol expects 32 bits per int.
        # We need to overflow the int when we reach the maximum value.
        self._current_request_id += 1
        if self._current_request_id > 0x7FFFFFFF:
            self._current_request_id = 1
