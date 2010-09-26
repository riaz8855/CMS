#!/usr/bin/python
# -*- coding: utf-8 -*-

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import socket
import sys
import os
import tempfile
import shutil
import hashlib
import Configuration

# FIXME - Bad hack
def maybe_mkdir(d):
    try:
        os.mkdir(d)
    except:
        pass

class FileStorage:
    def __init__(self, basedir, listen_address = None, listen_port = None):
        if listen_address == None:
            listen_address = Configuration.file_storage[0]
        if listen_port == None:
            listen_port = Configuration.file_storage[1]

        # Create server
        server = SimpleXMLRPCServer((listen_address, listen_port))
        server.register_introspection_functions()

        # Create server directories
        self.basedir = basedir
        self.tmpdir = os.path.join(self.basedir, "tmp")
        self.objdir = os.path.join(self.basedir, "objects")
        self.descdir = os.path.join(self.basedir, "descriptions")
        maybe_mkdir(self.basedir)
        maybe_mkdir(self.tmpdir)
        maybe_mkdir(self.objdir)
        maybe_mkdir(self.descdir)

        server.register_function(self.get)
        server.register_function(self.put)

        # Run the server's main loop
        server.serve_forever()

    def put(self, address, port, description = ""):
        fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fileSocket.connect((address, port))
        # FIXME - Error management
        tempFile, tempFilename = tempfile.mkstemp(dir = self.tmpdir)
        tempFile = os.fdopen(tempFile, "w")
        hasher = hashlib.sha1()
        while True:
            data = fileSocket.recv(8192)
            if not data:
                break
            tempFile.write(data)
            hasher.update(data)
        tempFile.close()
        fileSocket.close()
        digest = hasher.hexdigest()
        shutil.move(tempFilename, os.path.join(self.objdir, digest))
        descFile = open(os.path.join(self.descdir, digest), "w")
        print >> descFile, description
        descFile.close()
        return digest

    def get(self, address, port, digest):
        fileSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fileSocket.connect((address, port))
        # FIXME - Error management
        try:
            with open(os.path.join(self.objdir, digest)) as inputFile:
                while True:
                    data = inputFile.read(8192)
                    if not data:
                        break
                    remaining = len(data)
                    while remaining > 0:
                        sent = fileSocket.send(data[-remaining:])
                        remaining -= sent
        except IOError:
            fileSocket.close()
            return False
        fileSocket.close()
        return True

if __name__ == "__main__":
    fs = FileStorage("fs")

