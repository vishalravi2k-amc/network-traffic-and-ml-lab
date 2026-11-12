AMC ENGINEERING COLLEGE

Bengaluru<br/>Department of Computer Science and Engineering<br/>Artificial Intelligence and Machine Learning

Network Traffic Analysis

Project Report

Theme E<br/>Cryptography and Network Security<br/>Experiential Learning Task

Submitted by<br/>**Gowthami.M**

USN 1AM23CI042<br/>Roll number ____________________

Submitted to<br/>Faculty or guide ____________________

Submission date ____________________

Python source code, sample packet capture and analysis outputs accompany this report. The reported sample measurements come from a constructed teaching capture. A live Wireshark procedure is included for the classroom demonstration.


---

# 1 Abstract and project scope

This project demonstrates how network packets can be inspected to understand communication between a client and server. It follows Theme E in the supplied assignment: capture authorized localhost or lab traffic in Wireshark and identify basic protocol details. The implementation combines Wireshark inspection with a Python program that reads a saved capture and produces a searchable HTML dashboard, a CSV packet table and a JSON summary.

Two workflows are provided. The offline workflow uses a reproducible synthetic packet capture so the analyzer can run immediately without administrator permissions. The live workflow starts HTTP and UDP services on the loopback address 127.0.0.1 and generates real traffic for Wireshark to record. These workflows are identified separately throughout the report.

## 1.1 Objectives

&#8226; Identify source and destination IPv4 addresses, TCP or UDP ports, frame lengths and protocol labels.

&#8226; Explain TCP connection establishment, an HTTP request and response, UDP echo communication and optional ICMP echo traffic.

&#8226; Summarize packet counts, protocol distribution, observed frame bit rate and bidirectional endpoint pairs.

&#8226; Export results that can be compared with Wireshark and reproduced from the supplied source code.

## 1.2 Scope and requirement traceability

| Assignment requirement | Project component |
| --- | --- |
| Authorized localhost capture | Loopback-only traffic generator and Wireshark capture instructions |
| Identify basic protocols | TCP, UDP, ICMP and single-segment HTTP/1 inspection |
| Working source code | Analyzer, sample builder, traffic generator and launchers |
| Project report | Design, procedure, sample results, validation and limitations |

Requirements source: the assignment screenshot supplied with the request. The linked Google Drive document was not accessible during preparation, so additional requirements in that document have not been verified.


---

# 2 Background and protocol concepts

A packet capture records frames visible to a capture interface, together with timestamps and length information. Protocol headers describe how data is addressed and interpreted. By examining the headers and permitted payload data, a student can relate application actions to network communication.

| Protocol | Role in this project | Important fields |
| --- | --- | --- |
| IPv4 | Addresses the local endpoints | Source, destination, total length and protocol number |
| TCP | Carries the HTTP exchange as a reliable byte stream | Ports, sequence number, acknowledgement number and flags |
| HTTP/1 | Represents the request and response | Request line, response status and headers |
| UDP | Carries independent echo datagrams | Source port, destination port and UDP length |
| ICMP | Demonstrates optional ping traffic | Type, code and echo request or reply |

## 2.1 TCP and HTTP

A TCP connection commonly begins with SYN, SYN ACK and ACK. The SYN flags synchronize sequence numbers; acknowledgements indicate the next expected sequence value. Once established, the connection carries the HTTP request and response. FIN flags are used during an orderly close. TCP acknowledgement does not by itself prove that an application processed the data.

HTTP and TCP belong to different layers. The dashboard assigns one display label per packet: a recognized HTTP packet is labelled HTTP instead of TCP. The transport summary still counts that packet as TCP. Therefore, the synthetic sample has eight TCP labels and two HTTP labels, but ten TCP transport packets.

## 2.2 UDP and ICMP

UDP does not establish a TCP-style connection and provides no built-in retransmission guarantee. The local echo server returns each received message, and the client verifies the reply. ICMP echo requests and replies are separate network control messages; they do not use TCP or UDP ports.

## 2.3 Localhost and capture filters

The loopback address lets the client and server communicate on the same computer. A capture filter selects traffic to record; a display filter changes which recorded packets are shown. Wireshark documents these as separate filtering mechanisms [1, 2].


---

# 3 System design

Wireshark performs live capture and detailed interactive inspection. Python generates controlled local traffic and performs offline analysis. No cloud service, database, API key or third-party Python package is required for the project itself.

Data flow: live generator -> Wireshark -> PCAP -> analyzer -> HTML/CSV/JSON. The synthetic sample builder supplies an alternative PCAP input.

## 3.1 Module responsibilities

| Module | Responsibility |
| --- | --- |
| generate_traffic.py | Starts local HTTP and UDP servers, sends messages, validates replies and releases sockets. |
| make_sample.py | Constructs a deterministic PCAP with valid IPv4 and transport checksums. |
| analyzer.py | Validates PCAP records, decodes supported headers, computes totals and writes output files. |
| run_demo.py | Builds the sample, runs analysis and opens the local dashboard. |
| tests/test_project.py | Checks packet interpretation, malformed input, exports and real local communication. |

## 3.2 Requirements

Use a Windows, Linux or macOS computer with Python 3.10 or later and a modern browser. Install Wireshark for the live exercise; Windows loopback capture requires Npcap [1]. The Python programs use only the standard library. The HTML output opens locally without a web server. An iPhone can read the report, but the Python and Wireshark exercise should be run on a laptop or laboratory computer.


---

# 4 Implementation and algorithm

## 4.1 Packet processing

The PCAP reader checks the magic value, byte order, version, link type and record lengths. It supports microsecond and nanosecond capture formats. Each packet receives a stable record number. An invalid container stops processing with an explanation; malformed packets inside a valid container remain visible with a malformed status.

The decoder removes the Ethernet, VLAN, loopback, raw-IP or Linux cooked header as appropriate. It validates the IPv4 header length and total length before reading the transport header. Fragmented IPv4 traffic is explicitly marked unsupported because the project does not implement reassembly.

```text
for record in read_pcap(capture):
    row = decode(record)
    rows.append(row)
summary = summarize(rows)
write_outputs(rows, summary, output_directory, source_name)
```

For TCP, the program extracts endpoint ports, sequence and acknowledgement values, data offset and flags. It identifies HTTP only if a segment payload begins with a supported HTTP/1 method or response prefix. For UDP, it validates the datagram length and records the payload size. For ICMP, it identifies echo request and echo reply types.

## 4.2 Statistics and grouping

```text
Protocol share (%) = protocol label count / packet count * 100
Duration = latest packet timestamp - earliest packet timestamp
Observed mean bit/s = total frame wire bytes * 8 / duration
```

A bidirectional conversation key consists of the transport and a sorted pair of address-and-port endpoints. This aggregates both directions of an exchange. It is an endpoint-pair summary, not a full TCP session tracker: repeated connections with the same endpoints may be grouped together.

## 4.3 Output design

The HTML dashboard displays packet totals, bytes, duration, rate, protocol bars, top conversations and a searchable packet table. CSV preserves all decoded rows, while JSON contains machine-readable statistics. Displayed packet text is HTML-escaped. The HTML table is limited to 10,000 rows, but the summary and CSV include every record read.

All decoded rows are held in memory, making this a small-capture classroom tool. It does not validate input checksums, reconstruct TCP streams or make security verdicts. The sample builder computes checksums, and the test suite independently checks their arithmetic.


---

# 5 Installation and demonstration

## 5.1 Offline demonstration

Extract the project ZIP. On Windows, double-click run_demo.bat after installing Python. Alternatively, open a terminal in the extracted folder and run the command below. Use python3 on Linux or macOS if python is unavailable.

```text
python run_demo.py
```

The program creates samples/synthetic_localhost.pcap, analyzes it and opens output/dashboard.html. If automatic opening fails, open the HTML file manually. This is a synthetic demonstration and must not be described as a measured live capture.

## 5.2 Live Wireshark demonstration

1. Open Wireshark and select the loopback interface: Adapter for loopback traffic capture on Windows, lo on Linux, or lo0 on macOS [1]. Set this capture filter before starting:

```text
host 127.0.0.1 and (tcp port 8080 or udp port 9999 or icmp)
```

2. Start capture. Run the generator from the project directory:

```text
python generate_traffic.py
```

3. Confirm five successful HTTP responses and five verified UDP echo rounds. To add ICMP, optionally run ping -n 2 127.0.0.1 on Windows or ping -c 2 127.0.0.1 on Linux/macOS. The generator itself does not send ICMP.

4. Stop and save the capture as classic PCAP. If Wireshark saved PCAPNG, convert it with editcap; changing a filename extension is insufficient [3].

```text
editcap -F pcap my_capture.pcapng my_capture.pcap
python analyzer.py my_capture.pcap --out my_results
```

5. Open my_results/dashboard.html and retain the PCAP, packets.csv and summary.json as evidence. Use your actual capture counts when describing the live demonstration.

## 5.3 Safe and repeatable operation

The services bind only to 127.0.0.1 and terminate after the requested rounds. The HTTP client disables proxy use to keep requests local. Capture only your own or explicitly authorized traffic. If a port is occupied, use --http-port 8081 --udp-port 10000 and update the capture filter. No external scanning or third-party traffic is needed.


---

# 6 Packet inspection in Wireshark

The goal of the exercise is to explain what each packet means, rather than only display a graph. Apply one filter at a time, select a packet, and expand the IPv4 and transport headers. A display filter only changes the visible selection; it does not remove packets from the saved capture [2].

| Observation | Display filter | What to explain |
| --- | --- | --- |
| Local endpoints | ip.addr == 127.0.0.1 | Client and server share the loopback address. |
| HTTP TCP flow | tcp.port == 8080 | Server port and the client ephemeral port. |
| TCP handshake | tcp.flags.syn == 1 | SYN and SYN ACK; inspect the following ACK. |
| HTTP request | http.request | GET method, request path and Host header. |
| HTTP response | http.response | Status 200 OK and response headers. |
| UDP messages | udp.port == 9999 | One request and one echoed response per round. |
| ICMP messages | icmp | Echo request and echo reply; no ports. |

## 6.1 Suggested demonstration sequence

Begin with the TCP SYN packet and identify the client and server ports. Find the corresponding SYN ACK and ACK. Next, display the HTTP request and response. Use Follow TCP Stream to view the application exchange. If port 8080 is not decoded as HTTP, use Analyze > Decode As and select HTTP for that TCP port.

Then switch to the UDP filter and compare a request with its response. Finally, inspect ICMP if ping was run. Show the project dashboard and compare its exclusive labels with the TCP transport count. Wireshark Protocol Hierarchy contains counts from multiple layers, so those figures should not be added as mutually exclusive categories.

## 6.2 Evidence to collect for submission

&#8226; A Wireshark view of the loopback TCP handshake with the selected packet headers visible.

&#8226; An HTTP request or Follow TCP Stream view, and a UDP echo request/reply view.

&#8226; Your generated dashboard and a saved PCAP that reproduces the displayed summary.

Live screenshots are not fabricated or included as completed evidence. Add screenshots from your own demonstration if the instructor requires them. Avoid including unrelated traffic or sensitive data.


---

# 7 Results from the supplied sample

The following measurements were computed by running analyzer.py on samples/synthetic_localhost.pcap. The file is a deterministic teaching fixture with constructed timestamps and packets. These results validate the implementation; they are not measurements of a live network.

| Metric | Verified value |
| --- | --- |
| Total packets | 16 |
| Sum of frame wire lengths | 987 bytes |
| Capture duration | 1.5 seconds |
| Mean observed frame rate | 5264.0 bit/s |
| Decoded packet status | 16 ok; 0 malformed; 0 unsupported |

| Exclusive label | Packets | Share |
| --- | --- | --- |
| TCP | 8 | 50.0% |
| HTTP | 2 | 12.5% |
| UDP | 4 | 25.0% |
| ICMP | 2 | 12.5% |

## 7.1 Interpretation

The ten TCP transport packets include connection establishment, one HTTP request, one HTTP response and connection closure. Eight receive the TCP display label; the two application-bearing packets receive HTTP. Four UDP packets represent two request/reply pairs. Two ICMP packets represent one echo request/reply pair.

The sample contains three endpoint-pair conversations. The HTTP conversation uses client port 50000 and server port 8080; the UDP conversation uses ports 50001 and 9999. Both addresses are 127.0.0.1. ICMP has no transport ports.

Example records: packet 1 is TCP SYN; packet 4 is HTTP GET; packet 6 is HTTP 200 OK; packet 11 is a UDP message; packet 15 is an ICMP echo request.

The observed bit rate is 987 x 8 / 1.5 = 5,264 bit/s. This quantity describes the synthetic capture interval. It is not link bandwidth, application throughput or a performance benchmark.


---

# 8 Testing and validation

The project was executed with Python 3.12 in a Linux build environment. Nine automated tests passed. The default traffic generator also completed five real HTTP requests and five UDP echo request/reply rounds. Live packet capture and Wireshark GUI inspection were not run because packet-capture privileges were unavailable.

| Test | Verification | Result |
| --- | --- | --- |
| Sample interpretation | 16 packets; TCP 8, HTTP 2, UDP 4, ICMP 2; TCP transport count 10 | Pass |
| Constructed checksums | IPv4, TCP, UDP and ICMP checksum sums | Pass |
| PCAP variants | Little/big endian; micro/nanosecond timestamps | Pass |
| Link headers | Ethernet/VLAN, loopback, raw IPv4 and Linux cooked v1/v2 | Pass |
| Bad containers | Invalid magic, PCAPNG rejection and truncated record | Pass |
| Malformed and fragmented | Safe status reporting without incorrect transport decoding | Pass |
| Empty and zero duration | No divide-by-zero; zero rate convention | Pass |
| Output files | JSON/CSV output and HTML escaping | Pass |
| Local integration | Two actual HTTP requests and two UDP echo exchanges on temporary ports | Pass |

## 8.1 Reproduce the tests

```text
python -m unittest discover -s tests -v
```

## 8.2 Validation boundaries

The tests verify the supported classroom workflow, not every possible packet format. Windows and macOS live-capture behaviour was not tested here. Check the selected interface, capture permissions and Npcap installation on the presentation computer. Browser launch was unavailable in the build environment; the HTML file is supplied, but browser rendering and interactive search should be checked on that computer.

No claim is made that the analyzer detects attacks, proves security, measures packet loss or validates input checksums. Unsupported protocols and malformed frames remain visible, preventing them from being silently counted as successfully decoded TCP or UDP traffic.


---

# 9 Limitations and conclusion

## 9.1 Limitations

&#8226; The analyzer accepts uncompressed classic PCAP version 2.4. PCAPNG must be converted first. Unsupported link types produce an explicit error.

&#8226; Detailed decoding is restricted to IPv4. ARP is only labelled by its Ethernet type; IPv6 and other traffic are not dissected.

&#8226; There is no IPv4 fragment reassembly, TCP stream reassembly, DNS decoder, TLS decryption or input checksum validation.

&#8226; HTTP recognition uses a segment-start heuristic. Split requests or responses may not be labelled HTTP. Wireshark is needed for detailed analysis.

&#8226; Endpoint grouping does not separate all TCP sessions. Memory use grows with capture size, and the dashboard shows only the first 10,000 records.

## 9.2 Future enhancements

Possible extensions include structured DNS decoding, IPv6 support, streaming aggregation for large captures and a Wireshark or TShark export adapter. Each should be validated with independent captures before being presented as supported functionality. Threat detection would require a separate design and evaluation dataset.

## 9.3 Conclusion

The project provides a reproducible way to connect localhost application activity with packet-level observations. The working Python programs generate local HTTP/UDP traffic, analyze a supported saved capture and export readable results. The verified synthetic fixture gives a stable starting point; the supplied Wireshark procedure enables the student to collect and explain their own live evidence.

## References

[1] Wireshark Wiki, Loopback capture setup. https://wiki.wireshark.org/capturesetup/loopback

[2] Wireshark User Guide, Filtering Packets While Viewing. https://www.wireshark.org/docs/wsug_html_chunked/ChWorkDisplayFilterSection.html

[3] Wireshark, editcap manual. https://www.wireshark.org/docs/man-pages/editcap.html

Documentation checked on 12 November 2026. Assignment scope was taken from the user-supplied Theme E screenshot. Source files and the README accompany this report.
