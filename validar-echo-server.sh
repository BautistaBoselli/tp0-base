#!/bin/bash
SERVER_PORT=$(awk -F '=' '/SERVER_PORT/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2}' "./config/config.ini")
if [ -z "$SERVER_PORT" ]; then
    echo "SERVER_PORT no se encuentra en el archivo de configuración"
    exit 1
fi

ECHO_TEST="testing echo server"

make docker-compose-up

docker build -t ubuntu-nc ./ej3
docker run -d -t --name netcat-client --network tp0_testing_net ubuntu-nc

RESPONSE=$(docker exec netcat-client sh -c "echo $ECHO_TEST | nc server $SERVER_PORT")

echo "Respuesta del servidor: $RESPONSE"

if [ "$RESPONSE" == "$ECHO_TEST" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi

docker stop netcat-client
docker rm netcat-client
make docker-compose-down





