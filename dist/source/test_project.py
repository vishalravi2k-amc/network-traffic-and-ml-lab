import contextlib
import io
import json
import socket
import struct
import tempfile
import unittest
from pathlib import Path

from analyzer import CaptureError,decode,read_pcap,summarize,write_outputs
from generate_traffic import run
from make_sample import checksum,packets,write_sample


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)

    def tearDown(self): self.tmp.cleanup()

    def test_sample_counts_and_tcp_http_distinction(self):
        rows=[decode(r) for r in read_pcap(write_sample(self.root/'sample.pcap'))]
        s=summarize(rows)
        self.assertEqual(s['packets'],16)
        self.assertEqual(s['protocols'],{'TCP':8,'HTTP':2,'UDP':4,'ICMP':2})
        self.assertEqual(s['transports'],{'TCP':10,'UDP':4,'ICMP':2})
        self.assertEqual(s['statuses'],{'ok':16})
        self.assertEqual(s['duration_seconds'],1.5)
        self.assertEqual(sum(s['protocols'].values()),16)
        self.assertIn('GET /demo',rows[3]['info'])

    def test_checksums_in_constructed_packets(self):
        for data in packets():
            ip=data[14:];self.assertEqual(checksum(ip[:20]),0)
            body=ip[20:]
            if ip[9] in (6,17):
                pseudo=ip[12:20]+struct.pack('!BBH',0,ip[9],len(body))
                self.assertEqual(checksum(pseudo+body),0)
            else: self.assertEqual(checksum(body),0)

    def test_endianness_and_nanosecond_timestamps(self):
        packet=packets()[0]
        for endian in ('<','>'):
            for magic,scale in [(0xa1b2c3d4,1000000),(0xa1b23c4d,1000000000)]:
                data=struct.pack(endian+'IHHIIII',magic,2,4,0,0,65535,1)
                data+=struct.pack(endian+'IIII',1,scale//2,len(packet),len(packet))+packet
                path=self.root/'endian.pcap';path.write_bytes(data)
                row=list(read_pcap(path))[0]
                self.assertEqual(row[1],1.5)
                self.assertEqual(decode(row)['protocol'],'TCP')

    def test_supported_link_headers(self):
        ethernet=packets()[0];ip=ethernet[14:]
        fixtures={0:struct.pack('<I',2)+ip,108:struct.pack('!I',2)+ip,
                  101:ip,228:ip,113:b'\0'*14+b'\x08\x00'+ip,
                  276:b'\x08\x00'+b'\0'*18+ip,
                  1:ethernet[:12]+b'\x81\x00\x00\x01\x08\x00'+ip}
        for link,data in fixtures.items():
            self.assertEqual(decode((1,0,len(data),data,link))['protocol'],'TCP')

    def test_bad_container_rejected(self):
        for data in (b'bad',b'\x0a\x0d\x0d\x0a'+b'\0'*20):
            path=self.root/'bad.pcap';path.write_bytes(data)
            with self.assertRaises(CaptureError): list(read_pcap(path))
        path=write_sample(self.root/'truncated.pcap')
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaises(CaptureError): list(read_pcap(path))

    def test_malformed_and_fragment_are_not_transport_decoded(self):
        self.assertEqual(decode((1,0,1,b'x',1))['status'],'malformed')
        data=bytearray(packets()[0]);data[20:22]=b'\x20\x00'
        row=decode((1,0,len(data),bytes(data),1))
        self.assertEqual(row['protocol'],'IPv4-FRAGMENT')
        self.assertEqual(row['source_port'],'')

    def test_empty_capture_and_zero_duration(self):
        path=self.root/'empty.pcap'
        path.write_bytes(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
        self.assertEqual(list(read_pcap(path)),[])
        self.assertEqual(summarize([])['average_bits_per_second'],0)
        data=packets()[0]
        self.assertEqual(summarize([decode((1,0,len(data),data,1))])['average_bits_per_second'],0)

    def test_outputs_and_html_escape(self):
        data=packets()[0];row=decode((1,0,len(data),data,1))
        row['info']='<script>alert(1)</script>'
        s=summarize([row]);write_outputs([row],s,self.root,'test.pcap')
        dashboard=(self.root/'dashboard.html').read_text()
        self.assertNotIn('<script>alert(1)</script>',dashboard)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',dashboard)
        self.assertEqual(json.loads((self.root/'summary.json').read_text())['packets'],1)
        self.assertEqual(len((self.root/'packets.csv').read_text().splitlines()),2)

    def test_local_http_and_udp_end_to_end(self):
        # Reserve ephemeral ports briefly instead of assuming default ports are free.
        with socket.socket() as a, socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as b:
            a.bind(('127.0.0.1',0));b.bind(('127.0.0.1',0))
            hp,up=a.getsockname()[1],b.getsockname()[1]
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream): run(2,hp,up,delay=0)
        self.assertIn('Completed 2 HTTP requests',stream.getvalue())


if __name__=='__main__': unittest.main()
