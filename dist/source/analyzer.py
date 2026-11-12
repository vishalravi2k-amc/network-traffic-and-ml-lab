"""Small offline IPv4 packet analyzer. Python 3.10+, standard library only.

Reads classic PCAP; Wireshark handles capture and PCAPNG conversion.
This is a teaching parser, not a replacement for Wireshark dissection.
"""
import argparse
import csv
import html
import ipaddress
import json
import struct
from collections import Counter
from pathlib import Path


class CaptureError(ValueError):
    pass


def read_pcap(path):
    """Stream records, validating container boundaries before decoding."""
    formats = {b'\xd4\xc3\xb2\xa1': ('<', 1e6), b'\xa1\xb2\xc3\xd4': ('>', 1e6),
               b'\x4d\x3c\xb2\xa1': ('<', 1e9), b'\xa1\xb2\x3c\x4d': ('>', 1e9)}
    with open(path, 'rb') as f:
        head = f.read(24)
        if head[:4] == b'\x0a\x0d\x0d\x0a':
            raise CaptureError('PCAPNG: convert first: editcap -F pcap input.pcapng output.pcap')
        if len(head) != 24 or head[:4] not in formats:
            raise CaptureError('Not a valid classic PCAP file.')
        endian, scale = formats[head[:4]]
        major, minor, _, _, snaplen, link = struct.unpack(endian + 'HHIIII', head[4:])
        link &= 0xffff
        if (major, minor) != (2, 4):
            raise CaptureError('Only PCAP version 2.4 is supported.')
        if link not in (0, 1, 101, 108, 113, 228, 276):
            raise CaptureError(f'Unsupported link type {link}; inspect this capture in Wireshark.')
        number = 0
        while True:
            rec = f.read(16)
            if not rec:
                break
            if len(rec) != 16:
                raise CaptureError('Truncated PCAP record header.')
            sec, fraction, caplen, wirelen = struct.unpack(endian + 'IIII', rec)
            if caplen > 16 * 1024 * 1024 or caplen > snaplen or caplen > wirelen or fraction >= scale:
                raise CaptureError('Invalid PCAP record length or timestamp.')
            data = f.read(caplen)
            if len(data) != caplen:
                raise CaptureError('Truncated PCAP packet data.')
            number += 1
            yield number, sec + fraction / scale, wirelen, data, link


def network_payload(data, link):
    if link == 1:  # Ethernet, including stacked VLAN tags
        if len(data) < 14:
            raise CaptureError('Short Ethernet header')
        proto, offset = struct.unpack('!H', data[12:14])[0], 14
        while proto in (0x8100, 0x88a8):
            if len(data) < offset + 4:
                raise CaptureError('Short VLAN header')
            proto = struct.unpack('!H', data[offset + 2:offset + 4])[0]
            offset += 4
        return proto, data[offset:]
    if link in (0, 108):  # BSD/Npcap loopback, host or network byte order
        if len(data) < 4:
            raise CaptureError('Short loopback header')
        family = data[:4]
        return (0x0800 if family in (b'\x02\0\0\0', b'\0\0\0\x02') else 0), data[4:]
    if link in (113, 276):  # Linux cooked v1 / v2
        offset, at = (16, 14) if link == 113 else (20, 0)
        if len(data) < offset:
            raise CaptureError('Short cooked header')
        return struct.unpack('!H', data[at:at + 2])[0], data[offset:]
    return (0x0800 if data and data[0] >> 4 == 4 else 0), data


def decode(record):
    number, stamp, wirelen, data, link = record
    row = dict(number=number, timestamp=stamp, source='', destination='',
               source_port='', destination_port='', transport='OTHER', protocol='OTHER',
               length=wirelen, captured_length=len(data), info='', status='ok')
    try:
        proto, ip = network_payload(data, link)
        if proto != 0x0800:
            row.update(protocol='ARP' if proto == 0x0806 else 'OTHER', status='unsupported',
                       info='Non-IPv4 frame; detailed decoding is outside project scope')
            return row
        if len(ip) < 20 or ip[0] >> 4 != 4:
            raise CaptureError('Invalid IPv4 header')
        ihl, total = (ip[0] & 15) * 4, struct.unpack('!H', ip[2:4])[0]
        if ihl < 20 or total < ihl or len(ip) < total:
            raise CaptureError('Invalid or truncated IPv4 packet')
        row.update(source=str(ipaddress.IPv4Address(ip[12:16])),
                   destination=str(ipaddress.IPv4Address(ip[16:20])))
        if struct.unpack('!H', ip[6:8])[0] & 0x3fff:
            row.update(protocol='IPv4-FRAGMENT', transport='IPv4', status='unsupported',
                       info='Fragmented IPv4; reassembly not implemented')
            return row
        body = ip[ihl:total]
        if ip[9] == 6:
            if len(body) < 20:
                raise CaptureError('Short TCP header')
            sport, dport, seq, ack = struct.unpack('!HHII', body[:12])
            offset, flags = (body[12] >> 4) * 4, body[13]
            if offset < 20 or offset > len(body):
                raise CaptureError('Invalid TCP data offset')
            flagstr = ','.join(n for v, n in [(1,'FIN'),(2,'SYN'),(4,'RST'),(8,'PSH'),(16,'ACK'),(32,'URG'),(64,'ECE'),(128,'CWR')] if flags & v)
            row.update(source_port=sport, destination_port=dport, transport='TCP', protocol='TCP',
                       info=f'{flagstr} seq={seq} ack={ack}')
            payload = body[offset:]
            # A single-segment HTTP/1 start line is evidence; a port alone is not.
            if payload.startswith((b'GET ',b'POST ',b'HEAD ',b'PUT ',b'DELETE ',b'OPTIONS ',b'PATCH ',b'HTTP/1.')):
                row.update(protocol='HTTP', info=payload.split(b'\r\n',1)[0][:160].decode('ascii','replace'))
        elif ip[9] == 17:
            if len(body) < 8:
                raise CaptureError('Short UDP header')
            sport, dport, size = struct.unpack('!HHH', body[:6])
            if size < 8 or size > len(body):
                raise CaptureError('Invalid UDP length')
            row.update(source_port=sport, destination_port=dport, transport='UDP', protocol='UDP',
                       info=f'UDP payload {size - 8} bytes')
        elif ip[9] == 1:
            if len(body) < 8:
                raise CaptureError('Short ICMP header')
            row.update(transport='ICMP', protocol='ICMP',
                       info={8:'Echo request',0:'Echo reply'}.get(body[0],f'Type {body[0]}') + f', code {body[1]}')
        else:
            row.update(protocol='IPv4-OTHER', status='unsupported', info=f'IP protocol number {ip[9]}')
    except (CaptureError, struct.error, ValueError) as exc:
        row.update(protocol='MALFORMED', status='malformed', info=str(exc))
    return row


def summarize(rows):
    """Exclusive protocol labels; transport counts also include HTTP over TCP."""
    duration = max(r['timestamp'] for r in rows) - min(r['timestamp'] for r in rows) if rows else 0
    total_bytes = sum(r['length'] for r in rows)
    pairs = Counter()
    for r in rows:
        if r['source'] and r['destination']:
            a, b = sorted([f"{r['source']}:{r['source_port']}",f"{r['destination']}:{r['destination_port']}"])
            pairs[f"{r['transport']} | {a} <-> {b}"] += 1
    return dict(packets=len(rows), wire_bytes=total_bytes, duration_seconds=round(duration,6),
                average_bits_per_second=round(total_bytes * 8 / duration,2) if duration > 0 else 0,
                protocols=dict(Counter(r['protocol'] for r in rows)),
                transports=dict(Counter(r['transport'] for r in rows)),
                statuses=dict(Counter(r['status'] for r in rows)), conversations=dict(pairs.most_common(10)))


def write_outputs(rows, summary, out, source):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    fields = ['number','timestamp','source','destination','source_port','destination_port','transport','protocol','length','captured_length','info','status']
    with (out / 'packets.csv').open('w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    esc = lambda v: html.escape(str(v), quote=True)
    start = min((r['timestamp'] for r in rows),default=0)
    table = ''.join('<tr>' + ''.join(f'<td>{esc(v)}</td>' for v in [r['number'],f"{r['timestamp']-start:.6f}",r['source'],r['destination'],r['source_port'],r['destination_port'],r['protocol'],r['length'],r['info']]) + '</tr>' for r in rows[:10000])
    bars = ''.join(f'<div class="barrow"><b>{esc(k)}</b><meter min="0" max="{max(summary["packets"],1)}" value="{v}"></meter><span>{v} packets</span></div>' for k,v in summary['protocols'].items())
    cards = ''.join(f'<article><small>{label}</small><strong>{esc(value)}</strong></article>' for label,value in [('Packets',summary['packets']),('Captured frame wire bytes',summary['wire_bytes']),('Duration in seconds',summary['duration_seconds']),('Mean observed bit/s',summary['average_bits_per_second'])])
    conversations = ''.join(f'<li>{esc(k)} <b>{v} packets</b></li>' for k,v in summary['conversations'].items())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Network Traffic Analysis</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f2f5fa;color:#16253c;font:16px system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:36px 22px}header{background:#10243e;color:white;padding:32px;border-radius:16px}h1{font-size:34px;margin:10px 0}header p{color:#c6d6e8}.tag{color:#71e8bd;font-weight:700;font-size:12px;letter-spacing:2px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}article,section{background:white;border:1px solid #dce3ed;border-radius:12px;padding:22px}article small{display:block;color:#55657b}strong{display:block;font-size:27px;margin-top:12px}section{margin-bottom:22px}h2{margin-top:0;font-size:22px}.barrow{display:grid;grid-template-columns:100px 1fr 100px;gap:16px;margin:14px 0;align-items:center}meter{width:100%;height:24px}input{padding:12px;border:1px solid #a8b8ca;border-radius:7px;width:100%;margin-bottom:16px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}th,td{padding:11px;text-align:left;border-bottom:1px solid #dce3ed}th{background:#eaf0f7}li{margin:12px 0}li b{margin-left:12px}footer{color:#53647c;font-size:13px;line-height:1.7}@media(max-width:700px){.cards{grid-template-columns:1fr 1fr}h1{font-size:26px}.barrow{grid-template-columns:70px 1fr 90px;gap:8px}}@media print{input{display:none}.scroll{overflow:visible}table{white-space:normal;font-size:9px}header{color:black;background:white}}</style>
<main><header><span class="tag">THEME E / LOCALHOST LAB</span><h1>Network Traffic Analysis</h1><p>Protocol inspection, packet statistics and conversation summaries.</p><p>Input: SOURCE</p></header><div class="cards">CARDS</div><section><h2>Protocol distribution</h2>BARS<p>Exclusive labels: HTTP packets are counted as HTTP here and as TCP in the transport totals.</p></section><section><h2>Top conversations</h2><ul>CONVERSATIONS</ul></section><section><h2>Packet explorer</h2><label for="search">Filter by protocol, address, port or packet information</label><input id="search" placeholder="Try HTTP, SYN or 8080"><div class="scroll"><table><thead><tr><th>No.</th><th>Time (s)</th><th>Source</th><th>Destination</th><th>Src port</th><th>Dst port</th><th>Protocol</th><th>Bytes</th><th>Information</th></tr></thead><tbody>ROWS</tbody></table></div><p>DISPLAYNOTE</p></section><footer>Offline analysis only. Sample filenames beginning with synthetic contain constructed teaching packets, not a live capture. No checksum validation, TCP stream reassembly or threat detection is performed. Unsupported or malformed frames remain in packet totals. Rate is observed frame bits divided by capture duration, not link capacity.</footer></main><script>document.getElementById('search').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});</script></html>'''
    for key,value in [('SOURCE',esc(source)),('CARDS',cards),('BARS',bars),('CONVERSATIONS',conversations),('ROWS',table),('DISPLAYNOTE',f'Showing {min(len(rows),10000)} of {len(rows)} packets. CSV contains all packets.')]:
        page = page.replace(key,value)
    (out/'dashboard.html').write_text(page,encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', help='Classic .pcap file')
    parser.add_argument('--out',default='output',help='Output directory')
    args = parser.parse_args()
    try:
        rows = [decode(r) for r in read_pcap(args.capture)]
        summary = summarize(rows)
        write_outputs(rows,summary,args.out,Path(args.capture).name)
    except (OSError,CaptureError) as exc:
        parser.exit(2,f'Error: {exc}\n')
    print(json.dumps(summary,indent=2))
    print(f'Dashboard: {(Path(args.out)/"dashboard.html").resolve()}')


if __name__ == '__main__':
    main()
