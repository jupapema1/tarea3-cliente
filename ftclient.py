import zmq,os
import sys
import hashlib

partSize = 1024 * 1024 * 10

def writeBytes(filename,info):
    newName=filename
    #print("Writing file...[{}]".format(newName))

    with open(newName,"wb") as f:
        f.write(info)
    #print("Downloaded [{}]".format(newName))

def crearCarp(loc):
    if os.path.isdir('./'+loc) == False:
        print("Creating directory.../{}".format(loc))
        os.mkdir('./'+loc) 


def downloadFile(filename,socket,ID):
    #print("Download not implemented yet!!!!")
    socket.send_multipart([ID,b'down',filename])
    response=socket.recv_multipart()
    filename,info=response
    print("write[{}]".format(filename))
    writeBytes(filename.decode(),info)

def computeHashFile(filename):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha1 = hashlib.sha1()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def computeHash(bytes):
    sha1 = hashlib.sha1()
    sha1.update(bytes)
    return sha1.hexdigest()

def uploadFile(context, filename, servers):
    sockets = []
    direcciones=[]
    for ad in servers:
        s = context.socket(zmq.REQ)
        s.connect("tcp://"+ ad.decode("ascii"))
        direcciones.append(ad.decode())
        sockets.append(s)

    with open(filename, "rb") as f:
        completeSha1= bytes(computeHashFile(filename), "ascii")
        finished = False
        part = 0

        indexFile=open("./ind-{}.txt".format(filename.decode()),'w')
        indexFile.write("filename:{}\n".format(filename.decode()))
        indexFile.write("complete:{}\n".format(completeSha1.decode()))
        while not finished:
            print("Subiendo parte {}".format(part))
            f.seek(part*partSize)
            bt = f.read(partSize)
            sha1bt = bytes(computeHash(bt), "ascii")
            s = sockets[part % len(sockets)]
            loc=direcciones[part%len(direcciones)]
            s.send_multipart([b"upload", filename, bt, sha1bt, completeSha1])
            indexFile.write("{}:{}:{}\n".format(part,sha1bt.decode(),loc))
            response = s.recv()
            print("Respuesta recibida del servidor: {}".format(response.decode()))
            part = part + 1
            if len(bt) < partSize:
                finished = True
                indexFile.write("total:{}".format(part))

def downFile(context,filename):
    infos=[]
    with open(filename) as f:
        for line in f:
            l=line.split('\n')[0].split(':')
            #print(l)
            if l[0]=='filename':
                fn=l[1]
                print("Descargando: {}".format(fn))
            elif l[0]=='complete':
                cpt=l[1]
            elif len(l)==4:
                infos.append(l)
            elif l[0]=='total':
                tot=int(l[1])-1

    for inf in infos:
        print("Descargando parte {}/{}".format(inf[0],tot))
        s = context.socket(zmq.REQ)
        s.connect('tcp://{}:{}'.format(inf[2],inf[3]))
        s.send_multipart([b'down',inf[1].encode()])
        res=s.recv_multipart()
        s.close()
        #print("Respuesta del servidor: {}".format(res[0].decode()))
        writeBytes('.'+inf[1],res[1])

    print("Recuperando archivo original...")
    
    with open('d-'+fn,"wb") as f:
        for i in range(tot+1):        
            with open('.'+infos[i][1],'rb') as f1:
                bt=f1.read()
                f.write(bt)
                #print(bt)
            os.remove('.'+infos[i][1])

    print("Descarga completada!")

    #newSha1=computeHashFile('d-'+fn)

    #if(newSha1==cpt):
    #    print("Descarga satisfactoria!!")

def main():
    #####################
    dire='localhost'
    #####################

    if len(sys.argv) != 3:
        print("Must be called with a filename")
        print("Sample call: python ftclient <operation> <filename>")
        exit()

    operation = sys.argv[1]
    filename = sys.argv[2].encode('ascii')

    context = zmq.Context()
    proxy = context.socket(zmq.REQ)
    proxy.connect("tcp://{}:6666".format(dire))

    print("Operation: {}".format(operation))
    if operation == "up":
        proxy.send_multipart([b"availableServers"])
        servers = proxy.recv_multipart()
        print("Hay {} servidores disponibles".format(len(servers)))
        uploadFile(context, filename, servers)
        print("El archivo [{}] fue subido.".format(filename))
    elif operation == "down":
        print("Iniciando descarga...")
        downFile(context,filename.decode())

    elif operation == "share":
        print("Not implemented yet")
    else:
        print("Operation not found!!!")

if __name__ == '__main__':
    main()
