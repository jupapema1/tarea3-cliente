import zmq,socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def main():
    print("Iniciando servidor proxy en el puerto 5555...")
    print("Direccion del proxy: {}".format(get_ip()))

    servAddresses = []
    countPuertos=10000

    context = zmq.Context()
    servers = context.socket(zmq.REP)
    servers.bind("tcp://*:5555")

    clients = context.socket(zmq.REP)
    clients.bind("tcp://*:6666")

    poller = zmq.Poller()
    poller.register(servers, zmq.POLLIN)
    poller.register(clients, zmq.POLLIN)

    while True:
        print("\nEsperando mensajes...\n")
        socks = dict(poller.poll())
        if clients in socks:
            recc=clients.recv_multipart()
            operation, *msg = recc
            print("Mensaje del cliente: {}".format(recc))
            if operation == b"availableServers":
                clients.send_multipart(servAddresses)
            #print(msg)

        if servers in socks:
            recs=servers.recv_multipart()
            operation, *rest = recs
            print("Mensaje del servidor: {}".format(recs))
            if operation == b"newServer":
                sa=rest[0].decode()+':'+str(countPuertos)
                servAddresses.append(sa.encode())
                print(servAddresses)
                servers.send(str(countPuertos).encode())
                countPuertos+=1

if __name__ == '__main__':
    main()
