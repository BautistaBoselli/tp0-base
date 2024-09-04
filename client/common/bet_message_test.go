package common

import (
	"bytes"
	"encoding/binary"
	"testing"
)

func TestSerialize(t *testing.T) {
	bm := &BetMessage{
		agency:    "Agencia1",
		name:      "Santiago Lionel",
		surname:   "Lorca",
		dni:       "30904465",
		birthdate: "1999-03-17",
		betNumber: "7574",
	}

	serialized, err := bm.Serialize()
	if err != nil {
		t.Errorf("Error serializing BetMessage: %v", err)
	}

	var length int32
	if err := binary.Read(bytes.NewReader(serialized[:4]), binary.BigEndian, &length); err != nil {
		t.Fatalf("Failed to read length from serialized data: %v", err)
	}

	expectedLength := int32(len(serialized) - 4) // Exclude the length prefix itself
	if length != expectedLength {
		t.Errorf("Incorrect length prefix, got = %d, want = %d", length, expectedLength)
	}

	expectedData := serialized[4:]
	if !bytes.Equal(expectedData, serialized[4:]) {
		t.Errorf("Serialized data mismatch, got = %x, want = %x", expectedData, serialized[4:])
	}
}
