package common

import (
	"bytes"
	"encoding/binary"
)

type BetBatch struct {
	bets []BetMessage
}

func (bb *BetBatch) Serialize() ([]byte, error) {
	buf := new(bytes.Buffer)

	// Serialize each bet
	for _, bet := range bb.bets {
		betBytes, err := bet.Serialize()
		if err != nil {
			return nil, err
		}
		buf.Write(betBytes)
	}

	// Calculate the total length of the message
	totalLength := int16(buf.Len())
	finalBuf := new(bytes.Buffer)

	// Write a 0 on the first byte to indicate the type of message
	if err := binary.Write(finalBuf, binary.BigEndian, int8(0)); err != nil {
		return nil, err
	}

	// Write the total length of the batch in the final buffer
	if err := bb.SerializeLength(finalBuf, totalLength); err != nil {
		return nil, err
	}

	// Write the final buffer
	finalBuf.Write(buf.Bytes())

	return finalBuf.Bytes(), nil
}

// SerializeLength writes the length of the message with all the bets to the buffer
func (bb *BetBatch) SerializeLength(buf *bytes.Buffer, length int16) error {
	if err := binary.Write(buf, binary.BigEndian, length); err != nil {
		return err
	}

	return nil
}

func (bb *BetBatch) AddBet(bet BetMessage) {
	bb.bets = append(bb.bets, bet)
}

// NewBetBatch creates a new BetBatch from a slice of BetMessages
func NewBetBatch(batchAmount int, bet_messages []BetMessage) BetBatch {
	bb := BetBatch{
		bets: make([]BetMessage, 0, batchAmount),
	}

	limiter := batchAmount

	if batchAmount > len(bet_messages) {
		limiter = len(bet_messages)
	}
	// Add batchAmount bets to the batch
	for i := 0; i < limiter; i++ {
		bb.AddBet(bet_messages[i])
	}

	return bb
}