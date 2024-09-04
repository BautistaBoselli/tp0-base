import signal
import socket
import logging
import signal
import sys

from common.utils import store_bets, decode_message, Bet

BET_BATCH_MESSAGE_LENGTH = 8
BET_MESSAGE_LENGTH = 4

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.stop_processes = False
        self.current_client_socket = None
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def graceful_shutdown(self, signum, frame):
        
        self.stop_processes = True
        if self.current_client_socket:
            self.current_client_socket.close()
        self._server_socket.close()


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while not self.stop_processes:
            try:
                self.__accept_new_connection()
                self.__handle_client_connection()
            except OSError as e:
                if self.current_client_socket:
                    self.current_client_socket.close()
                self._server_socket.close()
                break
    
    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        self.current_client_socket = c
        return               

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = self.read_bets()
            bets = self.parse_bets(msg)
            logging.info(f'bets to store: {bets}')
            store_bets(bets)
            logging.info(f'action: store_bets | result: success | amount of bets: {len([bets])}')
            addr = self.current_client_socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            self.safe_write("BETS ACK\n")
        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            self.current_client_socket.close()

    def read_bets(self):
        msg_len_bytes = self.safe_read(BET_BATCH_MESSAGE_LENGTH)
        if not msg_len_bytes:
            raise OSError("Connection closed")
        msg_length = int.from_bytes(msg_len_bytes, 'big')
        logging.info(f'action: receive_message | result: in_progress | msg_length: {msg_length} ')
        msg = self.safe_read(msg_length)
        if not msg:
            raise OSError("Connection closed")
        return msg

    def parse_bets(self, msg):
        bets = []
        while msg:
            bet_len = int.from_bytes(msg[:BET_MESSAGE_LENGTH], 'big')
            msg = msg[BET_MESSAGE_LENGTH:]
            bet_to_decode = msg[:bet_len]
            bet = decode_message(bet_to_decode)
            bets.append(bet)
            msg = msg[bet_len:]
        return bets

    def safe_read(self, size):
        data = b''
        while len(data) < size:
            chunk = self.current_client_socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    # This function avoids short-writes by writing to the socket the whole message until finished
    def safe_write(self, msg):
        msg_bytes = msg.encode('utf-8')
        while len(msg_bytes) > 0:
            sent = self.current_client_socket.send(msg_bytes)
            msg_bytes = msg_bytes[sent:]