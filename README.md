# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un ejemplo de cliente-servidor el cual corre en containers con la ayuda de [docker-compose](https://docs.docker.com/compose/). El mismo es un ejemplo práctico brindado por la cátedra para que los alumnos tengan un esqueleto básico de cómo armar un proyecto de cero en donde todas las dependencias del mismo se encuentren encapsuladas en containers. El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers.

Por otro lado, se presenta una guía de ejercicios que los alumnos deberán resolver teniendo en cuenta las consideraciones generales descriptas al pie de este archivo.

## Instrucciones de uso

El repositorio cuenta con un **Makefile** que posee encapsulado diferentes comandos utilizados recurrentemente en el proyecto en forma de targets. Los targets se ejecutan mediante la invocación de:

- **make \<target\>**:
  Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de _debugging_ y _troubleshooting_.

Los targets disponibles son:

- **docker-compose-up**: Inicializa el ambiente de desarrollo (buildear docker images del servidor y cliente, inicializar la red a utilizar por docker, etc.) y arranca los containers de las aplicaciones que componen el proyecto.
- **docker-compose-down**: Realiza un `docker-compose stop` para detener los containers asociados al compose y luego realiza un `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene.
- **docker-compose-logs**: Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose.
- **docker-image**: Buildea las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para testear nuevos cambios en las imágenes antes de arrancar el proyecto.
- **build**: Compila la aplicación cliente para ejecución en el _host_ en lugar de en docker. La compilación de esta forma es mucho más rápida pero requiere tener el entorno de Golang instalado en la máquina _host_.

### Servidor

El servidor del presente ejemplo es un EchoServer: los mensajes recibidos por el cliente son devueltos inmediatamente. El servidor actual funciona de la siguiente forma:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor procede a recibir una conexión nuevamente.

### Cliente

El cliente del presente ejemplo se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma.

1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
   recibe mensaje del cliente y procede a responder el mismo.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
   Servidor desconecta al cliente.
4. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

Al ejecutar el comando `make docker-compose-up` para comenzar la ejecución del ejemplo y luego el comando `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```

## Parte 1: Introducción a Docker

En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:

Se creo el script de bash indicado y se restringio su uso a forzar que se manden los 2 argumentos como indicaba la consigna, de no ser asi se finaliza el script con un mensaje de error. Luego se implemento el subscript "mi-generador.py" en python en el cual se lee todo el docker compose, se obtiene la linea en la que se insertarian los clientes y se insertan la cantidad indicada por parametro. Para esto se borran los clientes anteriores y se insertan los nuevos. Finalmente agregamos el resto de lineas faltantes del docker compose y se modifica el archivo original con las nuevas lineas

### Ejercicio N°2:

Para poder inyectar los archivos config a los containers se modifico el docker-compose.yml para que los archivos de configuracion se monten en los containers a partir de guardarlos en volumenes. Esto permite que la imagen persista entre los cambios a los archivos de config, ya que al estructurarlo de esta manera, cuando ocurran cambios en los volumenes estos se inyectan en los contenedores al iniciarlos, a diferencia de lo previo donde al estar las configuraciones dentro de la imagen, al haber cambios estas se deben reconstruir. En cuanto a la solucion en si, para poder ejecutar correctamente con los tests tuve que eliminar del docker compose y del script generador el tipo de log utilizado (info o debug) ya que al ejecutar las pruebas estas no se corrian adecuadamente. En el historial de commits todos los ultimos cambios y la reimplementacion del ej se deben a los tests que no corrian adecuadamente.

### Ejercicio N°3:

Ademas del script se creo una carpeta con un dockerfile para este ejercicio, de esta manera se puede distinguir del resto de dockerfiles. En este se instala netcat encima de la imagen de ubuntu. Luego en el script pedido primero se obtiene el puerto del servidor del archivo de configuracion (evitando hardcodear valores) y se declara el mensaje con el que se va a testear el server (se puede modificar manualmente alli). Luego se ejecuta el make docker-compose-up para levantar el server, los clientes y la network (aunque en este ejercicio no nos interesa si hay o no clientes en la network). Luego se buildea la imagen del netcat y se ejecuta conectando el container a la network creada por el docker-compose. Luego le pedimos al container del netcat que haga echo al mensaje que declaramos anteriormente y mediante un pipe se lo enviamos al container del server que lo interpreta y responde con el mismo mensaje. Despues revisamos que la respuesta haya sido la misma que el mensaje enviado y devolvemos el input solicitado por la consigna. Finalmente se detiene el server y se limpia la network. Para correr el script se debe ejecutar el comando ./validar-echo-server.sh en la terminal.

### Ejercicio N°4:

Se modificó el archivo de server.py para que el server al recibir la señal SIGTERM cierre el socket de un cliente si se hubiese quedado conectado, y luego cierre el socket del server y setee un bool que impide que el server siga loopeando, de esta forma quedan cerrados todos los sockets y puede detenerse adecuadamente el proceso.
Para los clients se modificó el archivo de client.go para que al recibir la señal SIGTERM esta se coloque sobre un channel que se lee en cada iteración del loop de mensajes que se envian al server, de esta forma si se recibe la señal en medio de una iteración esta termina y luego en la posterior iteracion se cierra el socket y se detiene el loop.
De esta forma conseguimos hacer un graceful shutdown tanto del server como de los clientes.

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base al código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:

Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente

Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Servidor

Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:

Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:

- Definición de un protocolo para el envío de los mensajes.
- Serialización de los datos.
- Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
- Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

Para este ejercicio el protocolo elegido para el envío de mensajes se mantuvo con TCP ya que necesitamos asegurar que se envíen correctamente todos los datos de la apuesta y por lo tanto nos beneficiamos de la confiabilidad que provee TCP.
Se creo una estructura para almacenar todos los datos de la apuesta:

```
<agencia, nombre, apellido, documento, nacimiento y numero>
```

Estos datos los guardamos todos como strings, si bien esto hace que las apuestas a enviar ocupen mucho más espacio del estrictamente necesario, este tipo de decisión resulta en un protocolo mucho más sencillo de trabajar para el cliente al serializarlo y mandarlo, como para el servidor al leerlo y deserializarlo para almacenarlo. Luego de almacenarlo el servidor envia un mensaje "BETS ACK" al cliente para confirmar que la apuesta fue guardada correctamente.
En cuanto a la serialización de la apuesta se realiza de la siguiente manera:
Los primeros 2 bytes del mensaje indican la longitud del mensaje a enviar (es decir, la apuesta entera) y luego, por cada campo, al ser todos strings se tratan de la misma manera: 2 bytes indican la longitud del campo y luego se encuentra el campo en si. De esta manera el servidor puede leer los primeros 2 bytes para saber cuantos bytes leer y luego por cada campo leer los 2 bytes iniciales para saber cuantos bytes leer de ese campo en particular. Todo esto se hace en BigEndian.
Luego el servidor puede decodificar facilmente toda la apuesta y la almacena con la función store_bet() provista por la cátedra.
Se implementó la lógica de apuestas en el cliente en el archivo bet_message.go, permitiendo separar la lógica de comunicación de la lógica de modelo de dominio. Asi mismo en el servidor se modifico el archivo utils.py para tener separadas las responsabilidades entre ambas capas.
También se implementaron nuevas formas de leer y escribir en los sockets para evitar los problemas de short read y short write tanto para el cliente como para el servidor.

### Ejercicio N°6:

Para este ejercicio se tuvieron que modificar varias cosas como la fuente de los datos ya que ahora se recibian por archivo y no por variable de entorno, esto resulto en que se deprecaron algunas funciones y se incorporaron nuevas. Se implementó el concepto de BetBatch como estructura simple para guardar un slice con las apuestas a enviar en un determinado batch, y se implementaron algunos metodos para estos batches para permitir serializarlos y para de una lista con todas las apuestas de un archivo generar un batch solo del BatchMAxAmount que se recibe por config.
Se modificó la forma de serializar para construir sobre la serialización de la apuesta individual que ya habíamos implementado para el ejercicio anterior, y se agrego un campo extra al mensaje que indica la cantidad de bytes totales que se envían en el batch. De esta forma el servidor puede leer los primeros 2 bytes para saber cuantos bytes leer y luego por cada apuesta leer los 2 bytes iniciales para saber cuantos bytes leer de esa apuesta en particular. Todo esto se hace en BigEndian. Estos son los campos que se envían en el mensaje:
Todos los tamaños son campos de 2 bytes, esto se debe a que como el máximo de un batch es 8kb, con 2 bytes alcanza para representar un número de 0 a 65535, lo cual es suficiente para representar la cantidad de bytes que se pueden mandar en un batch. De la misma forma tambien es más que suficiente para representar el tamaño de una apuesta individual

```
<tamaño en bytes del batch><tamaño apuesta1><apuesta1><tamaño apuesta2><apuesta2>...<tamaño apuestaN><apuestaN>
```

Para evitar pasarnos del tamaño máximo de bytes de un batch que es 8kb, se realiza un algoritmo que revisa si el tamaño serializado del batch es mayor a este número, en caso de no serlo se envía el batch normalmente, pero si lo fuera, el algoritmo vuelve a crear un batch pero con la mitad de las apuestas que tenia el batch original y lo serializa, y revisa nuevamente la condición hasta que el tamaño del batch sea menor a 8kb. De esta forma se asegura que el batch no sea mayor a 8kb y se envíe correctamente. Luego de obtener el batch de tamaño adecuado, se modifica la lista con todas las apuestas quitando de la misma aquellas que se envían en el batch y se envía el batch al servidor.
El servidor por su parte recibe el batch y lee los primeros 2 bytes para saber cuantos bytes leer y luego evitando short reads, lee esa cantidad, de esta forma tenemos en memoria todo el batch y procedemos a decodificar cada apuesta individualmente y la agregamos a una lista, la cual recibe la función store_bet() para almacenarla. Luego de almacenar todas las apuestas del batch, el servidor envía el mismo mensaje de ack que en el ejercicio anterior para confirmar que todas las apuestas fueron almacenadas correctamente.
Si el servidor tiene un problema al decodificar las apuestas del batch y se encuentra algun campo vacío, esto se interpreta como error y se levanta una excepcion específica para este que le enviara al cliente un mensaje de error. Tras esto se cierra el socket del servidor y se detiene el proceso ya que interpreto como que no tiene lógica realizar un sorteo si no están todos los participantes cargados correctamente.
Haciendo fine tuning de la cantidad de apuestas que se pueden enviar en un batch sin tener que dividirlo, se llegó al número de 140 apuestas por batch, lo cual permite que casi todos los batches se envíen sin tener que dividirlos.
Con el siguiente comando, se puede ver como va cargando el servidor en el archivo de bets.csv y analizar si esta cargando todo correctamente:

```
docker exec server cat bets.csv
```

Ejecutarlo mientras esta levantado el docker-compose y se estan enviando apuestas para ver como se va llenando el archivo.

### Ejercicio N°7:

Para esta parte se tuvieron que cambiar bastantes aspectos del protocolo. Para empezar se tuvo que cambiar la forma de enviar los mensajes, ya que ahora había que avisar al servidor cuando se terminaban de enviar las apuestas, para resolver esto decidi agregar un nuevo campo al mensaje de batches que indica si este es el último o no. Lo logre haciendo que ahora el primer byte actue de forma de booleano de todo el batch y sea 0 si es un batch común y 1 si es el último.
El cliente a medida que va avanzando en su loop y queda la ultima tanda de apuestas, cambia el primer byte del mensaje a 1 y envía el batch al servidor. Además de esto, en un mensaje aparte pero inmediatamente posterior al del último batch y en la misma conexión, se envía el número de agencia para que luego el servidor pueda asociar la conexion con la agencia que envió las apuestas.
De esta manera, el servidor lee este primer byte, procesa el resto del batch normalmente y si ese primer byte era un uno, sabe que ese cliente esta esperando al resultado de la lotería y que debe leer un byte más del socket, indicando el número de agencia. Como no puede hacerse el sorteo hasta que todos los clientes hayan enviado sus apuestas, el servidor guarda en un diccionario los sockets de los clientes que enviaron el último batch asociandolos con su nro de agencia como clave y cuando recibe el último batch de un cliente, lo agrega a esta lista. Luego cuando recibe el último batch de todos los clientes, procede a hacer el sorteo y a enviar los resultados a todos los clientes que enviaron el último batch.
Tambien debido a que empezó a aumentar la cantidad de mensajes distintos del servidor (BET_ACK, ERROR, Ganadores) se decidió protocolizar más los mensajes del server y se opto por uno similar al que usa el cliente al serializar sus mensajes, ahora el servidor manda en los primeros 2 bytes la longitud del mensaje y luego el mensaje en si. Esto facilita mucho la lectura de parte del cliente.
En cuanto a la lógica de envío de los ganadores desde el servidor al cliente, se implementó una nueva estructura Winners en la cual almacenar tanto los dnis ganadores como la cantidad, que es el valor realmente necesario para loggear. Desde el lado del servidor, se serializo siguiendo el protocolo estandar a lo largo del proyecto. 2 bytes de la longitud total del mensaje y luego 2 bytes de longitud de cada dni y luego el dni en si:

```
<tamaño en bytes del mensaje><tamaño dni1><dni1><tamaño dni2><dni2>...<tamaño dniN><dniN>
```

Finalmente, tuve que hacer varios cambios en el cliente para poder recibir el resultado del sorteo y que a la vez se pudiera cortar el proceso ante un SIGTERM, permitiendo un graceful shutdown. Para esto, cuando esperamos los resultados, los clientes tenían que escuchar de forma bloqueante sobre la conexión hasta obtener el resultado, pero esto no permitía que se cortara el proceso ante SIGTERM. Para solucionar esto, se utilizaron las go routines que corren de manera asincronica y concurrente, en ella se escucha una posible respuesta del servidor, mientras el cliente puede estar atento a una señal de cierre. Para lograr esto, hay un select que escucha tanto la señal de cierre como la respuesta del servidor obtenida en la go routine. De esta forma, si se recibe la señal de cierre, se cierra el socket y se termina el proceso, y si se recibe la respuesta del servidor, se imprime el mensaje y se termina el proceso.

## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:

Para este ejercicio solo fue necesario modificar el archivo de server.py. Se implementó una solución multiprocessing para que el servidor pueda atender a varios clientes a la vez y de paso, evitar cualquier posible conflicto con el GIL
El flujo es el siguiente:

1. El server se inicializa ahora con un manager, para manejar los sockets de los clientes que se compartiran entre los procesos, un lock para escribir en el archivo de apuestas y un diccionario para guardar los sockets de los clientes que enviaron el último batch. Ademas un lock y un Value para manejar la cantidad de agencias que enviaron el último batch. (el lock es para que el proceso central pueda leer sin que escriban los procesos hijos)
2. El proceso principal se encarga de aceptar las conexiones y crear un nuevo proceso hijo para atender a cada cliente que se conecta.
3. Cada proceso hijo se encarga de recibir los batches del cliente, procesarlos, escribirlos en el archivo tomando el lock, y enviar la respuesta correspondiente. Si el cliente envía el último batch, el proceso hijo se encarga de agregar el socket del cliente a la lista de sockets de clientes que enviaron el último batch y de incrementar el contador de agencias que enviaron el último batch.
4. Cuando el proceso principal que escucha las conexiones ya no escucha más conexiones debido a que los clientes enviaron el último batch, se lanza una excepción que verifica si se tiene la cantidad correcta de agencias, en cuyo caso se eligen los ganadores y se envían las respuestas a los clientes.
5. Finalmente se joinean todos los procesos hijos y se puede apagar el servidor cuando reciba un SIGTERM, ejecutando el graceful shutdown.

## Consideraciones Generales

Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios.El _fork_ deberá contar con una sección de README que indique como ejecutar cada ejercicio.

La Parte 2 requiere una sección donde se explique el protocolo de comunicación implementado.
La Parte 3 requiere una sección que expliquen los mecanismos de sincronización utilizados.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deben existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.

(hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Puden obtener un listado del último commit de cada rama ejecutando `git ls-remote`.

Finalmente, se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección provistos [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
