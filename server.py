#!/usr/bin/env python 
# Mason Cooper (coopem4) & John Drogo (drogoj)
n_blocks = 128
blocksize = 4096

import threading
import socket 
import os

class Server:
  backlog = 5 
  # this set will serve as a filesystem index
  files = set()

  def __init__(self, port):
    # creates server object
    global blocksize, n_blocks
    host = '' 
    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    self.s.bind((host,port)) 
    self.port = port
    print "Block size is", blocksize
    print "Number of blocks is", n_blocks

  def process_line(self, client):
    # recv's until \n
    recieved = ''
    while True:
      cur = client.recv(1)
      if cur == "\n":
        break
      elif not cur:
        return cur
      else:
        recieved += cur
    return recieved

  def listen(self):
    # Handles initial client connections and thread creation
    self.s.listen(self.backlog)
    print "Listening on port", self.port
    while True: 
      client, address = self.s.accept()
      print "Received incoming connection from", address[0]
      cmd = self.process_line(client)
      thread = threading.Thread(target=self.handler, args=(cmd, client))
      thread.start()

  # the following functions implement the server functionality requested
  def store(self, client, args):
    thread = str(threading.current_thread().ident)
    if len(args) != 3:
      client.send("ERROR: INVALID COMMAND.\n")
      print "[thread",thread+"] Sent: ERROR: INVALID COMMAND."
      return
    if args[1] in self.files:
      client.send("ERROR: FILE EXISTS.\n")
      print "[thread",thread+"] Sent: ERROR: FILE EXISTS."
      data = client.recv(args[2]) # can we assume data will be sent regardless of error?
      return
    # actually do the storing stuff
    data = client.recv(int(args[2]))
    f = open(args[1], 'w')
    f.write(data)
    self.files.add(args[1])
    client.send("ACK\n")
    print "[thread",thread+"] Sent: ACK"


  def read(self, client, args):
    thread = str(threading.current_thread().ident)
    if len(args) != 4:
      client.send("ERROR: INVALID COMMAND.\n")
      print "[thread",thread+"] Sent: ERROR: INVALID COMMAND."
      return
    if args[1] not in self.files:
      client.send("ERROR: NO SUCH FILE.\n")
      print "[thread",thread+"] Sent: ERROR: NO SUCH FILE."
      return
    data = open(args[1], "r").read()
    if int(args[2])+int(args[3]) > len(data) or int(args[2]) < 0 or int(args[3]) < 0:
      client.send("ERROR: INVALID BYTE RANGE.\n")
      print "[thread",thread+"] Sent: ERROR: INVALID BYTE RANGE."
      return
    # TODO: (1) Memory dump / print output
    result = "ACK " + str(args[3])+"\n"+data[int(args[2]):int(args[2])+int(args[3])]
    client.send(result)

  def delete(self, client, args):
    thread = str(threading.current_thread().ident)
    if len(args) != 2:
      client.send("ERROR: INVALID COMMAND.\n")
      print "[thread",thread+"] Sent: INVALID COMMAND."
      return
    if args[1] not in self.files:
      client.send("ERROR: NO SUCH FILE.\n")
      print "[thread",thread+"] Sent: ERROR: NO SUCH FILE."
      return
    os.remove(args[1])
    self.files.remove(args[1])
    client.send("ACK\n")
    print "[thread",thread+"] Sent: ACK"



  def dir(self, client):
    files_sorted = sorted(self.files, key=str.lower)
    result = str(len(self.files))+"\n"
    for f in files_sorted:
      result += f + "\n"
    client.send(result)

  def handler(self, cmd, client):
    # Handles specific client connections until they close
    thread = str(threading.current_thread().ident)
    while cmd:
      print "[thread",thread+"] Rcvd:", cmd
      args = cmd.split(' ')
      if args[0] == "STORE":
        self.store(client, args)
      elif args[0] == "READ":
        self.read(client, args)
      elif args[0] == "DELETE":
        self.delete(client, args)
      elif args[0] == "DIR":
        self.dir(client)
      else:
        client.send("ERROR: INVALID COMMAND.\n")
        print "[thread",thread+"] Sent: ERROR: INVALID COMMAND."
      cmd = self.process_line(client).strip()
    print "[thread",thread+"] Client closed its socket....terminating."
    client.close()


if __name__ == "__main__":
  s = Server(8765)
  s.listen()