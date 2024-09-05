import signal
import socket
import logging
import signal
import sys

from common.utils import has_won, load_bets, serialize_winners, store_bets, decode_message, Bet

BET_BATCH_MESSAGE_LENGTH = 2
BET_MESSAGE_LENGTH = 2

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
            # If a error happens while reading an exception will be raised and an error will be logged and sent to the client
            first_byte = self.safe_read(1)
            if not first_byte:
                raise OSError("Connection closed")
            # logging.info(f'the first byte is {first_byte}')
            # If first byte is a "1", the client is telling he finished and we can get the bets
            msg = self.read_bets()
            bets = self.parse_bets(msg)
            if not bets:
                raise ValueError("Invalid message")
            store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            addr = self.current_client_socket.getpeername()
            # Only first bet in batch is logged, for control purposes
            Bet.logFields(bets[0], addr[0])
            self.safe_write("BETS ACK\n")
            if first_byte == b'\x01':
                logging.info("FINISHED_RECEIVED")
                # self.safe_write("READY\n")
                all_bets = load_bets()
                winners = []
                for bet in all_bets:
                    if has_won(bet):
                        winners.append(bet)
                logging.info(f'action: sorteo | result: success')
                self.send_winners(winners)
                   
        except OSError as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            logging.error(f"action: receive_message | result: fail | error: {e}") 
        except ValueError as e:        
            self.safe_write("ERROR\n")
            logging.error(f"action: receive_message | result: fail | error: {e}")  
            logging.critical(f'invalid bets found, shutting down connection')
            self.stop_processes = True
            if self.current_client_socket:
                self.current_client_socket.close()
            self._server_socket.close()
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
            try:
                bet_len = int.from_bytes(msg[:BET_MESSAGE_LENGTH], 'big')
                msg = msg[BET_MESSAGE_LENGTH:]
                bet_to_decode = msg[:bet_len]
                bet = decode_message(bet_to_decode)
                bets.append(bet)
                msg = msg[bet_len:]
            except ValueError:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
                return []
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
        length = len(msg_bytes).to_bytes(2, 'big')
        msg_bytes = length + msg_bytes
        while len(msg_bytes) > 0:
            sent = self.current_client_socket.send(msg_bytes)
            msg_bytes = msg_bytes[sent:]

    def send_winners(self, winners):
        winners_dni = [winner.document for winner in winners]
        winners_msg = serialize_winners(winners_dni)
        length = len(winners_msg).to_bytes(2, 'big')
        winners_msg = length + winners_msg
        while len(winners_msg) > 0:
            sent = self.current_client_socket.send(winners_msg)
            winners_msg = winners_msg[sent:]