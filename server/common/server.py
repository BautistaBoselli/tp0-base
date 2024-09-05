import signal
import socket
import logging
import threading
import queue

from common.utils import has_won, load_bets, prepend_length, serialize_winners, store_bets, decode_message, Bet

BET_BATCH_MESSAGE_LENGTH = 2
BET_MESSAGE_LENGTH = 2
FIRST_BYTE_1 = b'\x01'
NUMBER_OF_AGENCIES = 5
MAX_WORKERS = 10  # Number of worker threads

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
        self.connection_queue = queue.Queue()
        self.bets_lock = threading.Lock()
        self.all_bets_received = threading.Event()
        self.workers = []
        for _ in range(MAX_WORKERS):
            worker = threading.Thread(target=self.worker_thread)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def graceful_shutdown(self, signum, frame):
        self.stop_processes = True
        if self.current_client_socket:
            self.current_client_socket.close()
        self._server_socket.close()
        self.all_bets_received.set()  # Ensure the main thread can exit

    def run(self):
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.start()

        # Wait for all bets to be received or for the server to be stopped
        self.all_bets_received.wait()

        if not self.stop_processes:
            self.pick_winners()

    def accept_connections(self):
        while not self.stop_processes and len(self.clients) < NUMBER_OF_AGENCIES:
            try:
                client_socket, addr = self._server_socket.accept()
                self.connection_queue.put((client_socket, addr))
            except OSError as e:
                if self.stop_processes:
                    break
                logging.error(f"Error accepting connection: {e}")

        if not self.stop_processes:
            self.pick_winners()


    def worker_thread(self):
        while not self.stop_processes:
            try:
                client_socket, addr = self.connection_queue.get(timeout=1)
                self.handle_client(client_socket, addr)
            except queue.Empty:
                continue

    def handle_client(self, client_socket, addr):
        try:
            first_byte = self.safe_read(client_socket, 1)
            if not first_byte:
                raise OSError("Connection closed")
            msg = self.read_bets(client_socket)
            bets = self.parse_bets(msg)
            if not bets:
                raise ValueError("Invalid message")
            with self.bets_lock:
                store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            # Only first bet in batch is logged, for control purposes
            Bet.logFields(bets[0], addr[0])
            self.safe_write(client_socket, "BETS ACK\n")
            # If the first byte is a "1", the client is telling he finished and we should
            #  store the socket connection to inform the client of the winners
            if first_byte == FIRST_BYTE_1:
                agency_id = int(self.safe_read(client_socket, 1).decode('utf-8'))
                if not agency_id:
                    raise OSError("Connection closed")
                self.clients[agency_id] = client_socket
                logging.info(f'clients: {len(self.clients.keys())}')
                logging.info(f'current clients: {self.clients}')
                if len(self.clients) == NUMBER_OF_AGENCIES:
                    self.all_bets_received.set()
        except (OSError, ValueError) as e:
            logging.error(f"Error handling client: {e}")
        finally:
            if first_byte != FIRST_BYTE_1:
                client_socket.close()

    def read_bets(self, client_socket):
        """
        Reads the bets from the client socket.
        """
        msg = self.safe_read(client_socket, BET_BATCH_MESSAGE_LENGTH)
        if not msg:
            raise OSError("Connection closed")
        batch_len = int.from_bytes(msg, 'big')
        msg = self.safe_read(client_socket, batch_len)
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
            logging.info(f'agency_id: {agency_id} | winners: {msg}')
            while len(msg) > 0:
                sent = self.clients[agency_id].send(msg)
                msg = msg[sent:]


    # This function avoids short-reads by reading from the socket the whole message until finished
    def safe_read(self, client_socket, size):
        data = b''
        while len(data) < size:
            chunk = client_socket.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    
    # This function avoids short-writes by writing to the socket the whole message until finished
    def safe_write(self, client_socket, msg):
        msg_bytes = msg.encode('utf-8')
        length = len(msg_bytes).to_bytes(2, 'big')
        msg_bytes = length + msg_bytes
        while len(msg_bytes) > 0:
            sent = client_socket.send(msg_bytes)
            msg_bytes = msg_bytes[sent:]

