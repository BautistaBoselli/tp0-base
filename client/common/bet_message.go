package common

import (
	"bytes"
	"encoding/binary"
	"encoding/csv"
	"io"
)

type BetMessage struct {
	agency    string
	name      string
	surname   string
	dni       string
	birthdate string
	betNumber string
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
	if err := bm.SerializeString(buf, bm.betNumber); err != nil {
		return nil, err
	}

	// Calculate the total length of the message
	totalLength := int16(buf.Len())
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
// - 1 byte with the length of the string, by doing this we are limiting the field to 255 characters
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
func (bm *BetMessage) SerializeLength(buf *bytes.Buffer, length int16) error {
	if err := binary.Write(buf, binary.BigEndian, length); err != nil {
		return err
	}

	return nil
}

func obtainBetMessages(csvReader *csv.Reader, agencyId string, batchAmount int) ([]BetMessage, error) {
	betMessages := make([]BetMessage, 0, batchAmount)
	for i := 0; i < batchAmount; i++ {
		record, err := csvReader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}

		betMessages = append(betMessages, BetMessage{
			agency:    agencyId,
			name:      record[0],
			surname:   record[1],
			dni:       record[2],
			birthdate: record[3],
			betNumber: record[4],
		})
	}

	return betMessages, nil
}
