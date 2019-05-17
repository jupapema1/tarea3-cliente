
import zmq
import sys,os,socket

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

def crearCarp(loc):
    if os.path.isdir('./'+loc) == False:
        print("Creando carpeta.../{}".format(loc))
        os.mkdir('./'+loc) 

def main():
    direccion='localhost'

    if len(sys.argv) != 2:
        print("Sample call: python ftserver <folder>")
        exit()

    clientsAddress = get_ip()
    serversFolder = sys.argv[1]
    #clientsAddress = clientsAddress + ":" + clientsPort

    crearCarp(serversFolder)

    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://{}:5555".format(direccion))

    proxy.send_multipart([b"newServer", bytes(clientsAddress, "ascii")])
    m = proxy.recv()
    print(m)

    clients = context.socket(zmq.REP)
    clients.bind("tcp://*:{}".format(m.decode()))

    while True:
        print("\nEsperando usuarios para subir archivos!!!\n")
        operation, *rest = clients.recv_multipart()
        if operation == b"upload":
            print("Subiendo...")
            filename, byts, sha1byts, sha1complete = rest
            storeAs = serversFolder+ '/' + sha1byts.decode("ascii")
            #storeAs=serversFolder+filename.decode()
            print("Guardando como {}".format(storeAs))
            with open(storeAs, "wb") as f:
                f.write(byts)
            print("Subida completada")
            clients.send(b"Done")
        if operation==b'down':          
            fn=rest[0].decode()
            print("Descargando... {}".format(fn))
            with open('./{}/{}'.format(serversFolder,fn),'rb') as f:
                clients.send_multipart([fn.encode(),f.read()])
        else:
            print("Unsupported operation: {}".format(operation))
        

if __name__ == '__main__':
    main()
