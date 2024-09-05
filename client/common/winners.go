package common

import (
	"bytes"
	"encoding/binary"
)

type Winners struct {
	documents []string
	amount    int
}

func Decode(data []byte) (int, []string, error) {
	winners := Winners{
		documents: make([]string, 0),
		amount:    0,
	}
	buf := bytes.NewReader(data)

	for buf.Len() > 0 {
		// Read the length of the string (2 bytes)
		var length uint16
		err := binary.Read(buf, binary.BigEndian, &length)
		if err != nil {
			return -1, nil, err
		}

		// Read the string bytes
		stringBytes := make([]byte, length)
		_, err = buf.Read(stringBytes)
		if err != nil {
			return -1, nil, err
		}

		// Convert bytes to string and append to the list
		winners.documents = append(winners.documents, string(stringBytes))
		winners.amount++
	}

	return winners.amount, winners.documents, nil
}
