"""Generate real HTTP/TCP and UDP traffic on 127.0.0.1 only.

Start Wireshark loopback capture BEFORE running this script.
Uses temporary local HTTP/UDP servers and closes them when finished.
"""
import argparse
import json
import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'

    def do_GET(self):
        payload=json.dumps({'project':'Network Traffic Analysis','path':self.path,'status':'ok'}).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(payload)))
        self.send_header('Connection','close')
        self.end_headers();self.wfile.write(payload)

    def log_message(self,*args):
        pass


def run(count=5, http_port=8080, udp_port=9999, delay=0.15):
    server=None;udp=None;thread=None;worker=None
    stop=threading.Event()
    try:
        server=ThreadingHTTPServer(('127.0.0.1',http_port),Handler)
        udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1',udp_port));udp.settimeout(0.2)
        def echo():
            while not stop.is_set():
                try:
                    data,peer=udp.recvfrom(2048);udp.sendto(data,peer)
                except socket.timeout:
                    continue
        worker=threading.Thread(target=echo,daemon=True);worker.start()
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        # Disable system proxy settings so every request remains local.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for i in range(count):
            with opener.open(f'http://127.0.0.1:{http_port}/demo?request={i+1}',timeout=3) as reply:
                result=json.load(reply)
                if result['status']!='ok':
                    raise RuntimeError('Unexpected HTTP response')
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
                client.settimeout(3)
                msg=f'LAB-MESSAGE-{i+1}'.encode()
                client.sendto(msg,('127.0.0.1',udp_port))
                answer,_=client.recvfrom(2048)
                if answer!=msg:
                    raise RuntimeError('UDP echo verification failed')
            print(f'Round {i+1}: HTTP 200 OK; UDP echo verified')
            time.sleep(delay)
        print(f'Completed {count} HTTP requests and {count} UDP request/reply pairs on localhost.')
    finally:
        stop.set()
        if worker: worker.join(timeout=1)
        if udp: udp.close()
        if server:
            if thread: server.shutdown();thread.join(timeout=1)
            server.server_close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--count',type=int,default=5)
    p.add_argument('--http-port',type=int,default=8080)
    p.add_argument('--udp-port',type=int,default=9999)
    args=p.parse_args()
    if not 1 <= args.count <= 100 or not all(1024 <= x <= 65535 for x in [args.http_port,args.udp_port]):
        p.error('Count must be 1-100; ports must be 1024-65535.')
    try:
        run(args.count,args.http_port,args.udp_port)
    except OSError as exc:
        p.exit(1,f'Local demo failed: {exc}. Check whether the ports are already in use.\n')


if __name__=='__main__': main()
