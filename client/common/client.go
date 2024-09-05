package common

import (
	"encoding/binary"
	"encoding/csv"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"errors"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

const MAX_BATCH_MESSAGE_SIZE = 8192

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	BatchMaxAmount int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	file, err := c.getFile()
	if err != nil {
		return
	}
	defer file.Close()

	csvReader := csv.NewReader(file)
	bets, err := obtainBetMessages(csvReader, c.config.ID)
	if err != nil {
		log.Errorf("action: obtain_bet_messages | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM)

	for len(bets) > 0 {
		select {
		case <-sigs:
			if c.conn != nil {
				c.conn.Close()
			}
			return
		case <-time.After(c.config.LoopPeriod):
		default:
			batchToSend, bytesToSend, err := c.getValidData(bets)
			if err != nil || bytesToSend == nil {
				log.Errorf("action: serialize_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
				return
			}
			bets = bets[len(batchToSend.bets):]

			if len(bets) == 0 {
				// Replace the first byte with a 1 to indicate the server this is the last batch
				bytesToSend[0] = 1
			}

			err = c.createClientSocket()
			if err != nil {
				bets = nil
				log.Criticalf("server socket not found, exiting")
				c.conn.Close()
				return
			}

			err = c.sendMessage(bytesToSend)
			if err != nil {
				log.Errorf("action: send_bet_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
				return
			}

			if len(bets) == 0 {
				// Send the client id to the server
				err = c.sendMessage([]byte(c.config.ID))
				if err != nil {
					log.Errorf("action: send_client_id | result: fail | client_id: %v | error: %v", c.config.ID, err)
					return
				}
			}

			serverResponse, err := c.getServerResponse()

			if string(serverResponse) == "BETS ACK\n" {
				log.Infof("action: apuesta_enviada | result: success | bets_sent: %d", len(batchToSend.bets))
				if len(bets) == 0 {
					c.waitLotteryResults(sigs)
				}
			}

			if string(serverResponse) == "ERROR\n" {
				log.Errorf("action: apuesta_enviada | result: fail | bets_sent: %d", len(batchToSend.bets))
				bets = nil
				return
			}
			c.conn.Close()

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				string(serverResponse),
			)

			// Wait a time between sending one message and the next one
			time.Sleep(c.config.LoopPeriod)

		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) sendMessage(bytes []byte) error {
	// Send the message to the server in a loop until all the message is sent to avoid short writes
	written := 0
	for written < len(bytes) {
		n, err := c.conn.Write(bytes[written:])
		if err != nil {
			log.Criticalf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return err
		}
		written += n
	}

	log.Infof("action: send_message | result: success | client_id: %v", c.config.ID)
	return nil
}

// SafeRead Read from the connection until the read_size is reached avoiding short reads
func (c *Client) SafeRead(response []byte, readSize int) (int, error) {
	read := 0
	for read < readSize {
		n, err := c.conn.Read(response[read:])
		if n == 0 {
			break
		}

		if err != nil {
			return 0, err
		}
		read += n
	}

	return read, nil
}

func (c *Client) getFile() (*os.File, error) {
	filename := "/agency.csv"
	file, err := os.Open(filename)
	if err != nil {
		log.Errorf("action: open_file | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return nil, err
	}
	return file, nil
}

func (c *Client) getValidData(bets []BetMessage) (BetBatch, []byte, error) {
	batchToSend := NewBetBatch(c.config.BatchMaxAmount, bets)
	bytesToSend, err := batchToSend.Serialize()
	if err != nil {
		return batchToSend, nil, err
	}
	prevBatchAmount := c.config.BatchMaxAmount
	for len(bytesToSend) > MAX_BATCH_MESSAGE_SIZE {
		log.Infof("batch size too big, reducing to %d", prevBatchAmount/2)
		batchToSend = NewBetBatch(prevBatchAmount/2, bets)
		bytesToSend, err = batchToSend.Serialize()
		if err != nil {
			return batchToSend, nil, err
		}
		prevBatchAmount = prevBatchAmount / 2
	}
	return batchToSend, bytesToSend, nil
}

func (c *Client) getServerResponse() ([]byte, error) {
	// readSize is always the first two bytes of the message
	readBuffer := make([]byte, 2)
	_, err := c.SafeRead(readBuffer, 2)
	if err != nil {
		return nil, err
	}
	readSize := int(binary.BigEndian.Uint16(readBuffer))
	serverResponse := make([]byte, readSize)
	bytesRead, err := c.SafeRead(serverResponse, readSize)
	if bytesRead == 0 {
		log.Errorf("action: receive_message | result: fail | client_id: %v",
			c.config.ID,
		)
	}
	return serverResponse, err
}

func (c *Client) waitLotteryResults(sigs chan os.Signal) error {
	lotteryResult := make(chan []byte)

	go func() {
		serverResponse, err := c.getServerResponse()
		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
		}
		lotteryResult <- serverResponse
	}()

	select {
	case response := <-lotteryResult:
		amountOfWinners, dnis, err := Decode(response)
		if err != nil {
			log.Errorf("action: decode_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return err
		}
		log.Infof("dnis ganadores: %v", dnis)
		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", amountOfWinners)
		if c.conn != nil {
			c.conn.Close()
		}
		return nil

	case <-sigs:
		log.Infof("action: wait_lottery_results | result: interrupted | client_id: %v", c.config.ID)
		return errors.New("interrupted by SIGTERM")
	}
}
