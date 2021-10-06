#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body


class HTTPClient(object):
    def get_host(self, url):
        host = url.split(":")[0]
        return host

    def get_host_port(self, url):
        if ":" in url:
            tempUrl = url.split(":")
            port = int(tempUrl[-1])
            return port
        return 80

    def get_remote_ip(self, host):
        try:
            remote_ip = socket.gethostbyname(host)
        except socket.gaierror:
            sys.exit()

        return remote_ip

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        return int(data.split("\r\n")[0].split(" ")[1])

    def get_headers(self, data):
        return data.split("\r\n")

    def get_body(self, data):
        return data.split("\r\n\r\n")[-1]

    def get_location(self, headers):
        for header in headers:
            if "Location:" in header:
                return header.split(": ")[-1]

    def get_args(self, args):
        res = ""
        if not args:
            return res
        print(f"ARGS: {args}")
        for i, (key, value) in enumerate(args.items()):
            print(i, key, value)
            res += f"{key}={value}"
            if i < len(args.keys()) - 1:
                res += "&"
        return f"{res}"

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        parsedURL = urllib.parse.urlparse(url)
        host = self.get_host(parsedURL.netloc)
        port = self.get_host_port(parsedURL.netloc)
        ip = self.get_remote_ip(host)
        path = parsedURL.path if parsedURL.path else "/"
        query = f"?{parsedURL.query}" if parsedURL.query else ""

        self.connect(ip, port)
        payload = f'GET {path}{query} HTTP/1.0\r\nHost: {host}\r\n\r\n'
        print(f"{payload}")
        self.sendall(payload)
        self.socket.shutdown(socket.SHUT_WR)
        response = self.recvall(self.socket)

        print("########REQUEST############")
        print(payload)
        print("########RESPONSE############")
        print(response)

        headers = self.get_headers(response)
        code = self.get_code(response)
        if code == 301:
            print('301 MOVED')
            newURL = self.get_location(headers)

            parsedURL = urllib.parse.urlparse(newURL)
            host = self.get_host(parsedURL.netloc)
            port = self.get_host_port(parsedURL.netloc)
            ip = self.get_remote_ip(host)
            path = parsedURL.path if parsedURL.path else "/"
            query = f"?{parsedURL.query}" if parsedURL.query else ""

            self.connect(ip, port)
            payload = f'GET {path}{query} HTTP/1.0\r\nHost: {host}\r\n\r\n'
            print(payload)
            self.sendall(payload)
            self.socket.shutdown(socket.SHUT_WR)
            response = self.recvall(self.socket)
            code = self.get_code(response)
            print(response)

        body = self.get_body(response)
        self.socket.close()

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        parsedURL = urllib.parse.urlparse(url)
        host = self.get_host(parsedURL.netloc)
        port = self.get_host_port(parsedURL.netloc)
        ip = self.get_remote_ip(host)
        path = parsedURL.path if parsedURL.path else "/"
        query = f"?{parsedURL.query}" if parsedURL.query else ""
        strArgs = self.get_args(args)

        self.connect(ip, port)
        payload = f'''POST {path}{query} HTTP/1.0\r\nHost: {host}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {str(len(strArgs))}\r\n\r\n{strArgs}'''
        print(f"{payload}")
        self.sendall(payload)
        self.socket.shutdown(socket.SHUT_WR)
        response = self.recvall(self.socket)

        print("########REQUEST############")
        print(payload)
        print("########RESPONSE############")
        print(response)

        code = self.get_code(response)
        body = self.get_body(response)
        self.socket.close()

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command(sys.argv[2], sys.argv[1]))
    else:
        print(client.command(sys.argv[1]))
