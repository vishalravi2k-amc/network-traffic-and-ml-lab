/** Classic PCAP decoder. All analysis runs in the visitor's browser. */
export function parsePcap(buffer) {
  const v=new DataView(buffer), bytes=new Uint8Array(buffer);
  if(v.byteLength<24)throw Error('This is not a complete classic PCAP file.');
  const magic=v.getUint32(0,false);
  if(magic===0x0a0d0d0a)throw Error('This file is PCAPNG. In Wireshark, save it as classic PCAP, or run: editcap -F pcap input.pcapng output.pcap');
  const formats={0xd4c3b2a1:[true,1e6],0xa1b2c3d4:[false,1e6],0x4d3cb2a1:[true,1e9],0xa1b23c4d:[false,1e9]};
  const fmt=formats[magic];if(!fmt)throw Error('Unrecognized format. Choose an uncompressed classic .pcap file.');
  const [le,scale]=fmt;
  if(v.getUint16(4,le)!==2||v.getUint16(6,le)!==4)throw Error('Only PCAP version 2.4 is supported.');
  const snap=v.getUint32(16,le),link=v.getUint32(20,le)&65535;
  if(![0,1,101,108,113,228,276].includes(link))throw Error(`Link type ${link} is not supported. Inspect this file in Wireshark.`);
  let pos=24;const rows=[];
  while(pos<v.byteLength){
    if(pos+16>v.byteLength)throw Error('The capture has an incomplete record header. Save it again in Wireshark.');
    const sec=v.getUint32(pos,le),frac=v.getUint32(pos+4,le),cap=v.getUint32(pos+8,le),len=v.getUint32(pos+12,le);pos+=16;
    if(cap>snap||cap>len||cap>16*1024*1024||frac>=scale||pos+cap>v.byteLength)throw Error('The capture contains an invalid or truncated packet record.');
    if(rows.length>=100000)throw Error('This classroom analyzer supports up to 100,000 packets. Export a smaller capture.');
    rows.push(decode(bytes.subarray(pos,pos+cap),link,rows.length+1,sec+frac/scale,len));pos+=cap;
  }
  return rows;
}
function decode(b,link,number,timestamp,length){
  const r={number,timestamp,length,captured:b.length,source:'',destination:'',sourcePort:'',destinationPort:'',transport:'OTHER',protocol:'OTHER',status:'ok',info:'',flags:'',sequence:null,acknowledgement:null};
  const u16=i=>(b[i]<<8)|b[i+1];const u32=i=>((b[i]*16777216)+(b[i+1]<<16)+(b[i+2]<<8)+b[i+3]);
  const need=(i,n)=>{if(i+n>b.length)throw Error('Truncated packet header');};
  try{
    let off=0,type=0x800;
    if(link===1){need(0,14);type=u16(12);off=14;while([0x8100,0x88a8].includes(type)){need(off,4);type=u16(off+2);off+=4;}}
    else if(link===0||link===108){need(0,4);type=(u32(0)===2||u32(0)===0x02000000)?0x800:0;off=4;}
    else if(link===113||link===276){off=link===113?16:20;need(0,off);type=u16(link===113?14:0);}
    else type=b.length&&b[0]>>4===4?0x800:0;
    if(type!==0x800){r.protocol=type===0x806?'ARP':'OTHER';r.status='unsupported';r.info='Non-IPv4 frame; detailed decoding is outside project scope';return r;}
    need(off,20);const ihl=(b[off]&15)*4,total=u16(off+2),ipproto=b[off+9];
    if(b[off]>>4!==4||ihl<20||total<ihl||off+total>b.length)throw Error('Invalid or truncated IPv4 packet');
    r.source=Array.from(b.subarray(off+12,off+16)).join('.');r.destination=Array.from(b.subarray(off+16,off+20)).join('.');
    if(u16(off+6)&0x3fff){r.protocol='IPv4-FRAGMENT';r.transport='IPv4';r.status='unsupported';r.info='IPv4 fragmentation; reassembly is not implemented';return r;}
    const t=off+ihl,end=off+total;
    if(ipproto===6){
      if(end-t<20)throw Error('Short TCP header');
      const h=(b[t+12]>>4)*4;if(h<20||t+h>end)throw Error('Invalid TCP data offset');
      r.sourcePort=u16(t);r.destinationPort=u16(t+2);r.transport='TCP';r.protocol='TCP';r.sequence=u32(t+4);r.acknowledgement=u32(t+8);
      r.flags=[[1,'FIN'],[2,'SYN'],[4,'RST'],[8,'PSH'],[16,'ACK'],[32,'URG'],[64,'ECE'],[128,'CWR']].filter(([val])=>b[t+13]&val).map(([,name])=>name).join(', ');
      r.info=`${r.flags}  seq=${r.sequence} ack=${r.acknowledgement}`;
      const payload=new TextDecoder().decode(b.subarray(t+h,Math.min(end,t+h+160)));
      if(/^(GET |POST |HEAD |PUT |DELETE |OPTIONS |PATCH |HTTP\/1\.)/.test(payload)){r.protocol='HTTP';r.info=payload.split('\r\n')[0];}
    }else if(ipproto===17){
      if(end-t<8)throw Error('Short UDP header');const len=u16(t+4);if(len<8||t+len>end)throw Error('Invalid UDP length');
      r.sourcePort=u16(t);r.destinationPort=u16(t+2);r.transport='UDP';r.protocol='UDP';r.info=`UDP payload ${len-8} bytes`;
    }else if(ipproto===1){
      if(end-t<8)throw Error('Short ICMP header');r.transport='ICMP';r.protocol='ICMP';r.info=`${b[t]===8?'Echo request':b[t]===0?'Echo reply':`Type ${b[t]}`}, code ${b[t+1]}`;
    }else{r.protocol='IPv4-OTHER';r.status='unsupported';r.info=`IP protocol number ${ipproto}`;}
  }catch(e){r.protocol='MALFORMED';r.status='malformed';r.info=e.message;}
  return r;
}
export function summarize(rows){
  let earliest=Infinity,latest=-Infinity,total=0;const protocols={},transports={},statuses={},flows={};
  for(const r of rows){earliest=Math.min(earliest,r.timestamp);latest=Math.max(latest,r.timestamp);total+=r.length;protocols[r.protocol]=(protocols[r.protocol]||0)+1;transports[r.transport]=(transports[r.transport]||0)+1;statuses[r.status]=(statuses[r.status]||0)+1;
    if(r.source&&r.destination){const pair=[`${r.source}${r.sourcePort!==''?':'+r.sourcePort:''}`,`${r.destination}${r.destinationPort!==''?':'+r.destinationPort:''}`].sort();const key=`${r.transport} | ${pair.join(' ↔ ')}`;flows[key]=(flows[key]||0)+1;}
  }
  const duration=rows.length?latest-earliest:0;
  return {packets:rows.length,bytes:total,duration,rate:duration>0?8*total/duration:0,protocols,transports,statuses,flows,earliest:rows.length?earliest:0};
}
