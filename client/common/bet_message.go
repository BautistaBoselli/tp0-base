package common

import (
	"bytes"
	"encoding/binary"
	"os"
)

type BetMessage struct {
	agency     string
	name       string
	surname    string
	dni        string
	birthdate  string
	bet_number string
}

// Serialize serializes the BetMessage into a byte array to be sent
func (bm *BetMessage) Serialize() ([]byte, error) {
	buf := new(bytes.Buffer)

	// Write agency
	if err := bm.SerializeString(buf, bm.agency); err != nil {
		return nil, err
	}

	// Write name
	if err := bm.SerializeString(buf, bm.name); err != nil {
		return nil, err
	}

	// Write surname
	if err := bm.SerializeString(buf, bm.surname); err != nil {
		return nil, err
	}

	// Write dni
	if err := bm.SerializeString(buf, bm.dni); err != nil {
		return nil, err
	}

	// Write birthdate
	if err := bm.SerializeString(buf, bm.birthdate); err != nil {
		return nil, err
	}

	// Write bet number
	if err := bm.SerializeString(buf, bm.bet_number); err != nil {
		return nil, err
	}

	// Calculate the total length of the message
	totalLength := int32(buf.Len())
	finalBuf := new(bytes.Buffer)

	// Write the total length of the message in the final buffer
	if err := bm.SerializeLength(finalBuf, totalLength); err != nil {
		return nil, err
	}

	// Write the original buffer data after the total length
	if _, err := finalBuf.Write(buf.Bytes()); err != nil {
		return nil, err
	}

	return finalBuf.Bytes(), nil
}

// SerializeString writes a string to the buffer in the following format:
// - 2 bytes with the length of the string
// - n bytes with the string
func (bm *BetMessage) SerializeString(buf *bytes.Buffer, str string) error {
	strBytes := []byte(str)
	if err := binary.Write(buf, binary.BigEndian, int16(len(strBytes))); err != nil {
		return err
	}
	if err := binary.Write(buf, binary.BigEndian, strBytes); err != nil {
		return err
	}

	return nil
}

// SerializeLength writes the length of the message to the buffer
func (bm *BetMessage) SerializeLength(buf *bytes.Buffer, length int32) error {
	if err := binary.Write(buf, binary.BigEndian, length); err != nil {
		return err
	}

	return nil
}

// obtainBetMessage reads the environment variables and returns a BetMessage
func obtainBetMessage() *BetMessage {
	agency := os.Getenv("AGENCIA")
	name := os.Getenv("NOMBRE")
	surname := os.Getenv("APELLIDO")
	dni := os.Getenv("DNI")
	birthdate := os.Getenv("NACIMIENTO")
	bet_number := os.Getenv("NUMERO")

	if agency == "" || name == "" || surname == "" || dni == "" || birthdate == "" || bet_number == "" {
		return nil
	}

	return &BetMessage{
		agency:     agency,
		name:       name,
		surname:    surname,
		dni:        dni,
		birthdate:  birthdate,
		bet_number: bet_number,
	}
}
