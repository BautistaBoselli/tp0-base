package common

import (
	"bufio"
	"io"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
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
	}
	c.conn = conn
	return nil
}

func (c *Client) sendBetMessage(bet *BetMessage) error {
	// Serialize the message
	msg, err := bet.Serialize()
	if err != nil {
		log.Criticalf("action: serialize_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	// Send the message to the server
	written := 0
	for written < len(msg) {
		n, err := c.conn.Write(msg[written:])
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM)

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-sigs:
			if c.conn != nil {
				c.conn.Close()
			}
			return
		case <-time.After(c.config.LoopPeriod):
		default:
			c.createClientSocket()

			bet := obtainBetMessage()
			if bet == nil {
				log.Criticalf("action: obtain_bet_message | result: fail | client_id: %v", c.config.ID)
				return
			}

			err := c.sendBetMessage(bet)
			if err != nil {
				log.Errorf("action: send_bet_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
				return
			}

			read_size := len("BETS ACK\n")
			server_response := make([]byte, read_size)
			bytesRead, err := SafeRead(bufio.NewReader(c.conn), server_response, read_size)
			if bytesRead == 0 {
				log.Errorf("action: receive_message | result: fail | client_id: %v",
					c.config.ID,
				)
			}

			c.conn.Close()
			if string(server_response) == "BETS ACK\n" {
				log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v", bet.dni, bet.bet_number)
			}

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				string(server_response),
			)

			// Wait a time between sending one message and the next one
			time.Sleep(c.config.LoopPeriod)

		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func SafeRead(buf io.Reader, response []byte, read_size int) (int, error) {
	read := 0
	for read < read_size {
		n, err := buf.Read(response[read:])
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
