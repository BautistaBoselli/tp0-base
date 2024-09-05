import csv
import datetime
import time
import struct
import logging


""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

    def logFields(self, ip):
        return logging.info(f'action: receive_message | result: success | ip: {ip} | msg: {self.agency},{self.first_name},{self.last_name},{self.document},{self.birthdate},{self.number}')

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]: # type: ignore
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])

def decode_message(message: bytes) -> Bet:
    """
    Decodes a message in the format:
    <agency>,<first_name>,<last_name>,<document>,<birthdate>,<number>
    """
    decoded_strings = []
    offset = 0
    
    for _ in range(6):
        """
        Extract the length of the string (2 bytes)
        H is an unsigned short (2 bytes)
        > is big-endian
        """
        try:
            length = struct.unpack_from('>H', message, offset)[0]
        except struct.error:
            raise ValueError("Invalid message")
        
        offset += 2
        
        # Extract the string of that length
        string_bytes = message[offset:offset + length]
        string_value = string_bytes.decode('utf-8')
        if string_value == "":
            raise ValueError("Empty field")
        decoded_strings.append(string_value)
        
        # Move the offset past the current string
        offset += length

    bet = Bet(decoded_strings[0], decoded_strings[1], decoded_strings[2],
              decoded_strings[3], decoded_strings[4], decoded_strings[5])
    
    return bet

def serialize_winners(winners):
    data = bytearray()

    for winner in winners:
        data += len(winner).to_bytes(2, 'big')
        data += winner.encode('utf-8')

    return data