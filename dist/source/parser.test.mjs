import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parsePcap,summarize} from '../dist/parser.js';
const raw=fs.readFileSync(new URL('../dist/samples/synthetic_localhost.pcap',import.meta.url));
const buffer=raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength);
const rows=parsePcap(buffer),s=summarize(rows);
assert.equal(rows.length,16);assert.deepEqual(s.protocols,{TCP:8,HTTP:2,UDP:4,ICMP:2});assert.deepEqual(s.transports,{TCP:10,UDP:4,ICMP:2});assert.equal(s.bytes,987);assert.equal(s.duration,1.5);assert.equal(s.rate,5264);assert.deepEqual(s.statuses,{ok:16});assert.equal(rows[3].info,'GET /demo HTTP/1.1');assert.equal(rows[0].flags,'SYN');
assert.equal(summarize([]).rate,0);assert.equal(summarize([rows[0]]).rate,0);
assert.throws(()=>parsePcap(buffer.slice(0,-1)),/invalid or truncated/);
assert.throws(()=>parsePcap(new ArrayBuffer(3)),/complete/);
const pcapng=new ArrayBuffer(24);new DataView(pcapng).setUint32(0,0x0a0d0d0a);assert.throws(()=>parsePcap(pcapng),/PCAPNG/);
const fragmented=buffer.slice(0);new DataView(fragmented).setUint16(24+16+14+6,0x2000);const frag=parsePcap(fragmented)[0];assert.equal(frag.protocol,'IPv4-FRAGMENT');assert.equal(frag.sourcePort,'');
// Check byte orders and time resolutions by translating the container, not packet data.
for(const le of [false,true])for(const ns of [false,true]){
 const out=buffer.slice(0),src=new DataView(buffer),dst=new DataView(out);dst.setUint32(0,ns?0xa1b23c4d:0xa1b2c3d4,le);dst.setUint16(4,2,le);dst.setUint16(6,4,le);for(const off of [8,12,16,20])dst.setUint32(off,src.getUint32(off,true),le);
 let p=24;while(p<src.byteLength){const len=src.getUint32(p+8,true);for(const off of [0,4,8,12])dst.setUint32(p+off,src.getUint32(p+off,true)*(off===4&&ns?1000:1),le);p+=16+len;}
 assert.deepEqual(summarize(parsePcap(out)).protocols,s.protocols);assert.equal(summarize(parsePcap(out)).duration,1.5);
}
console.log('Browser decoder passed sample, statistics, timestamps, byte order, fragmentation, malformed container and empty-input checks.');
