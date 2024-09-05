import signal
import socket
import logging
import signal
import sys

from common.utils import has_won, load_bets, prepend_length, serialize_winners, store_bets, decode_message, Bet

BET_BATCH_MESSAGE_LENGTH = 2
BET_MESSAGE_LENGTH = 2
FIRST_BYTE_1 = b'\x01'
NUMBER_OF_AGENCIES = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.stop_processes = False
        self.current_client_socket = None
        signal.signal(signal.SIGTERM, self.graceful_shutdown)
        self.clients = {}

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
            if len(self.clients.keys()) == NUMBER_OF_AGENCIES:
                logging.info("All agencies connected")
                self.pick_winners()
                break
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
            first_byte = self.safe_read(1)
            if not first_byte:
                raise OSError("Connection closed")
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
            # If the first byte is a "1", the client is telling he finished and we should
            #  store the socket connection to inform the client of the winners
            if first_byte == FIRST_BYTE_1:
                # Read one more byte to get the agency id
                agency_id = self.safe_read(1)
                agency_id = int(agency_id.decode('utf-8'))
                if not agency_id:
                    raise OSError("Connection closed")
                # Store the socket connection to inform the client of the winners
                self.clients[agency_id] = self.current_client_socket
        except OSError as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            logging.error(f"action: receive_message | result: fail | error: {e}") 
        except ValueError as e:        
            self.safe_write("ERROR\n")
            logging.error(f"action: receive_message | result: fail | error: {e}")  
            logging.critical(f'invalid bets found, shutting down connection')
            self.graceful_shutdown(signal.SIGTERM, None)
        


    def read_bets(self):
        """
        Reads the first 2 bytes of the message to get the length of the batch.
        Then reads the batch of bets and returns it.
        """
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
        """
        Parses the bets from the message received by decoding each bet.
        If there is an error like a missing field, the function returns an empty list.
        """
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
    

    # This function avoids short-reads by reading from the socket the whole message until finished
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


    def pick_winners(self):
        """
        Picks the winners from the bets stored in the file.
        """
        logging.info("FINISHED_RECEIVED")
        all_bets = load_bets()
        winners = []
        for bet in all_bets:
            if has_won(bet):
                winners.append(bet)
        logging.info(f'action: sorteo | result: success')
        self.send_winners(winners)


    def send_winners(self, winners):
        """
        Sends the winners to the client.
        """
        winners_agency = [winner.agency for winner in winners]
        winners_dni = [winner.document for winner in winners]
        dict_agency_dni = {}
        for agency, dni in zip(winners_agency, winners_dni):
            if agency not in dict_agency_dni:
                dict_agency_dni[agency] = []
            dict_agency_dni[agency].append(dni)
        serialized_dict = {key: serialize_winners(value) for key, value in dict_agency_dni.items()}
        msg_dict = {key: prepend_length(value) for key, value in serialized_dict.items()}
        logging.info(f'current clients: {self.clients}')
        for agency_id, msg in msg_dict.items():
            while len(msg) > 0:
                sent = self.clients[agency_id].send(msg)
                msg = msg[sent:]


    