# Short demonstration script

My project is Network Traffic Analysis under Theme E. I generate HTTP and UDP
traffic on my own computer and capture it on Wireshark's loopback interface.
I identify source and destination addresses, ports, packet lengths and protocols.
My Python analyzer reads the saved PCAP and creates a dashboard, CSV and summary.
The bundled sample is synthetic and is provided so the project can be demonstrated
without capture permissions. For the live demonstration, I run the generator
while Wireshark is recording and then analyze my saved capture.

# Viva questions

1. **What is network traffic analysis?** Examining packets and their metadata to
   understand communication, protocol behaviour and traffic patterns.
2. **Why use 127.0.0.1?** It is an IPv4 loopback address; this exercise's traffic
   stays on the same computer.
3. **Why do the IP addresses match?** Both client and server run locally. TCP/UDP
   ports distinguish their endpoints.
4. **What is TCP's handshake?** SYN, SYN ACK and ACK establish a TCP connection.
5. **TCP versus UDP?** TCP provides an ordered reliable byte stream with connection
   state. UDP sends independent datagrams without built-in delivery guarantees.
6. **Is HTTP separate from TCP?** They are at different layers. HTTP/1 in this
   project uses TCP. A packet may carry both protocols.
7. **What do ports 8080 and 9999 do?** They identify this project's HTTP and UDP
   servers. A port by itself does not prove which application protocol is present.
8. **What is ICMP?** A network control protocol used by ping for echo requests and
   replies. ICMP does not use TCP/UDP ports.
9. **Capture versus display filters?** A capture filter controls recording; a
   display filter changes which saved packets are visible.
10. **What is PCAP?** A packet-capture format containing a global header and
    timestamped packet records. PCAPNG uses a different block-based structure.
11. **How is the bit rate calculated?** Total recorded frame wire bytes times
    eight, divided by the interval between the earliest and latest packet.
12. **Can this detect attacks?** No. It describes traffic; it does not classify
    a flow as malicious or prove that a system is secure.
13. **Can it read HTTPS messages?** No. It does not decrypt TLS.
14. **Why do sample counts differ from live counts?** The sample is constructed;
    live packet segmentation, acknowledgements and timing depend on the OS.
15. **What are the limits?** IPv4 only, classic PCAP input, no fragment/TCP
    reassembly, no input checksum validation, no DNS decoder and small captures.
