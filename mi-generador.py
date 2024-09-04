import sys

# Obtiene las lineas del archivo
def get_lines(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            return lines
    except FileNotFoundError:
        print("File '",filename,"' not found, provide a valid file")
        return -1

# Obtiene la linea donde se debe insertar los clientes
def get_insert_line(lines_list):
    insert_index = 0
    for i, line in enumerate(lines_list):
        if line.strip() == "networks:":
            insert_index = i + 1
            while lines[insert_index].strip():  
                insert_index += 1
            break
    return insert_index

# Limpia los clientes anteriores
def clean_old_clients(lines_list):
    clean_lines = []
    skip = False
    for line in lines_list:
        if line.strip().startswith("client"):
            skip = True
        if skip and line.strip() == "":
            skip = False
            continue
        if not skip:
            clean_lines.append(line)
    return clean_lines

# Genera los servicios de los clientes en base al parametro del script
def generate_clients(clients):
    client_services = []
    for i in range(1, clients + 1):
        client_name = f"  client{i}:\n"
        client_container_name = f"    container_name: client{i}\n"
        client_image = "    image: client:latest\n"
        client_entrypoint = "    entrypoint: /client\n"
        client_environment = (
            "    environment:\n"
            f"      - CLI_ID={i}\n"
        )
        client_volumes = f"    volumes:\n      - type: bind\n        source: ./client/config.yaml\n        target: /config.yaml\n      - ./.data/dataset/agency-{i}.csv:/agency.csv\n"
        client_networks = "    networks:\n      - testing_net\n"
        client_depends_on = "    depends_on:\n      - server\n"

        client_service = (
            client_name +
            client_container_name +
            client_image +
            client_entrypoint +
            client_environment +
            client_volumes +
            client_networks +
            client_depends_on
        )
        client_services.append(client_service)
    return client_services

if __name__ == '__main__':
    filename = sys.argv[1];
    clients = int(sys.argv[2]);

    lines = get_lines(filename)
    if lines == -1:
        sys.exit(1)

    lines = clean_old_clients(lines)

    insert_index = get_insert_line(lines);
    if insert_index == -1:
        sys.exit(1)

    clients_services = generate_clients(clients)

    lines = lines[:insert_index] + ['\n'] + clients_services + lines[insert_index:]
    try:
        with open(filename, 'w') as file:
            file.writelines(lines)
    except:
        print("Error while writing to file '",filename,"'")
        sys.exit(1)


    



