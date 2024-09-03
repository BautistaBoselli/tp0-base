import signal
import socket
import logging
import signal
import sys

from common.utils import store_bets, decode_message, Bet

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
        
        
            

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg_length = self.safe_read(BET_MESSAGE_LENGTH)
            # if nothing is received, return
            if not msg_length:
                return
            msg_len_bytes = int.from_bytes(msg_length, 'big')
            logging.info(f'action: receive_message | result: in_progress | msg_length: {msg_len_bytes} ')
            
            
            msg = self.safe_read(msg_len_bytes)
            bets = decode_message(msg)

            store_bets([bets])
            logging.info(f'action: store_bets | result: success | amount of bets: {len([bets])}')
            
            addr = self.current_client_socket.getpeername()
            Bet.log_fields(bets, addr[0])



            # TODO: Modify the send to avoid short-writes
            self.current_client_socket.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            self.current_client_socket.close()

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

    def safe_read(self, size):
        data = b''
        while len(data) < size:
            chunk = self.current_client_socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data