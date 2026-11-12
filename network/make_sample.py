"""Build a deterministic SYNTHETIC PCAP fixture; does not capture traffic."""
import socket
import struct
from pathlib import Path


def checksum(data):
    if len(data) % 2:
        data += b'\0'
    total = sum(struct.unpack('!' + 'H' * (len(data)//2),data))
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff


def frame(proto, body, ident):
    addr = socket.inet_aton('127.0.0.1')
    ip = struct.pack('!BBHHHBBH4s4s',0x45,0,20+len(body),ident,0x4000,64,proto,0,addr,addr)
    ip = ip[:10] + struct.pack('!H',checksum(ip)) + ip[12:]
    return b'\0'*12 + b'\x08\x00' + ip + body


def tcp(sport,dport,seq,ack,flags,payload=b''):
    addr = socket.inet_aton('127.0.0.1')
    segment = struct.pack('!HHIIBBHHH',sport,dport,seq,ack,0x50,flags,8192,0,0) + payload
    pseudo = addr + addr + struct.pack('!BBH',0,6,len(segment))
    return segment[:16] + struct.pack('!H',checksum(pseudo+segment)) + segment[18:]


def udp(sport,dport,payload):
    addr=socket.inet_aton('127.0.0.1')
    segment=struct.pack('!HHHH',sport,dport,8+len(payload),0)+payload
    pseudo=addr+addr+struct.pack('!BBH',0,17,len(segment))
    check=checksum(pseudo+segment) or 0xffff
    return segment[:6]+struct.pack('!H',check)+segment[8:]


def packets():
    request=b'GET /demo HTTP/1.1\r\nHost: 127.0.0.1:8080\r\nConnection: close\r\n\r\n'
    response=b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\nConnection: close\r\n\r\nHello'
    c,s=101,501
    sequence=[(50000,8080,100,0,2,b''),(8080,50000,500,c,18,b''),
              (50000,8080,c,s,16,b''),(50000,8080,c,s,24,request),
              (8080,50000,s,c+len(request),16,b''),
              (8080,50000,s,c+len(request),24,response),
              (50000,8080,c+len(request),s+len(response),16,b''),
              (50000,8080,c+len(request),s+len(response),17,b''),
              (8080,50000,s+len(response),c+len(request)+1,17,b''),
              (50000,8080,c+len(request)+1,s+len(response)+1,16,b'')]
    result=[frame(6,tcp(*args),i+1) for i,args in enumerate(sequence)]
    for i in range(2):
        msg=f'LAB-MESSAGE-{i+1}'.encode()
        result += [frame(17,udp(50001,9999,msg),20+i*2),frame(17,udp(9999,50001,msg),21+i*2)]
    for t in (8,0):
        body=struct.pack('!BBHHH',t,0,0,1,1)+b'LOCALHOST'
        body=body[:2]+struct.pack('!H',checksum(body))+body[4:]
        result.append(frame(1,body,30+t))
    return result


def write_sample(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb') as f:
        f.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
        for i, packet in enumerate(packets()):
            f.write(struct.pack('<IIII',1700000000+i//10,(i%10)*100000,len(packet),len(packet)))
            f.write(packet)
    return path


if __name__ == '__main__':
    path=write_sample(Path(__file__).parent/'samples'/'synthetic_localhost.pcap')
    print(f'Created {path} (16 synthetic teaching packets, not a live capture)')
