# Network Traffic Analysis

Theme E | Cryptography and Network Security experiential learning

A small Python project for inspecting authorized localhost traffic in Wireshark
and generating a packet dashboard, CSV table and JSON summary. It includes all
source code, automated tests, an editable report, a PDF report and a reproducible
synthetic PCAP sample. Python 3.10+; no pip packages required.

## Start here

Extract the ZIP on a Windows, Linux or macOS computer. On Windows, double-click
`run_demo.bat` after installing Python. Or open a terminal in this folder:

```sh
python run_demo.py
```

Use `python3` on Linux/macOS or `py -3` on Windows if needed. The browser opens
`output/dashboard.html`. If it does not, open that file manually. This first demo
uses **constructed teaching packets, not captured traffic**. The sample contains
16 frames: 8 TCP-labelled, 2 HTTP-labelled, 4 UDP and 2 ICMP. The two HTTP packets
also belong to TCP at the transport layer, giving 10 TCP transport packets.

On an iPhone you can read the PDF and preview the included HTML. Run Python and
the live Wireshark exercise on a laptop or lab computer.

## Capture real localhost traffic for your demonstration

1. Install Python 3.10+ from https://www.python.org/downloads/ and Wireshark from
   https://www.wireshark.org/download.html. On Windows, include Npcap during setup.
2. Open Wireshark. Select **Adapter for loopback traffic capture** on Windows,
   **lo** on Linux or **lo0** on macOS. Localhost traffic will not appear on the
   ordinary Wi-Fi interface.
3. Set this **capture filter** before starting:

   ```text
   host 127.0.0.1 and (tcp port 8080 or udp port 9999 or icmp)
   ```

4. Start capture, then run:

   ```sh
   python generate_traffic.py
   ```

   It starts local servers, verifies five HTTP responses and five UDP echoes,
   then stops the servers. It binds only to `127.0.0.1`. It does not capture packets.
5. Optionally add ICMP: Windows `ping -n 2 127.0.0.1`; Linux/macOS
   `ping -c 2 127.0.0.1`. The Python generator itself does not send ICMP.
6. Stop capture. Inspect the packets using the display filters below. Save as
   `my_capture.pcap` using the classic pcap format. Changing the extension alone
   does not convert a PCAPNG file. If needed, convert with Wireshark's editcap:

   ```sh
   editcap -F pcap my_capture.pcapng my_capture.pcap
   ```

   Windows PowerShell, if editcap is not on PATH:

   ```powershell
   & "C:\Program Files\Wireshark\editcap.exe" -F pcap my_capture.pcapng my_capture.pcap
   ```

7. Analyze your saved file:

   ```sh
   python analyzer.py my_capture.pcap --out my_results
   ```

8. Open `my_results/dashboard.html`. Keep `packets.csv`, `summary.json` and your
   PCAP as evidence. Your counts will differ from the synthetic fixture because
   the OS controls segmentation, acknowledgements and timing.

Use only your own or explicitly authorized lab traffic. This exercise needs no
other devices, website traffic or private credentials.

## Wireshark display filters

| Purpose | Display filter |
|---|---|
| Local IPv4 packets | `ip.addr == 127.0.0.1` |
| TCP conversation | `tcp.port == 8080` |
| SYN flags, including SYN ACK | `tcp.flags.syn == 1` |
| HTTP requests | `http.request` |
| HTTP responses | `http.response` |
| UDP echo exchange | `udp.port == 9999` |
| Ping traffic | `icmp` |

Capture filters select packets to record. Display filters hide/show packets
already recorded and do not delete them. If Wireshark does not recognize HTTP
on port 8080, use **Analyze > Decode As** and select HTTP for that TCP port.
Use **Follow > TCP Stream** to inspect the request and response. Compare
**Statistics > Protocol Hierarchy** and **Statistics > Conversations** with the
project output; hierarchy counts can overlap across layers, unlike the project's
exclusive protocol-label chart.

## Files and implementation

| File | Purpose |
|---|---|
| `analyzer.py` | PCAP reader, link/IP/transport decoding, statistics and exports |
| `generate_traffic.py` | Real localhost HTTP and UDP generator |
| `make_sample.py` | Reproducible synthetic fixture with valid checksums |
| `run_demo.py` | Generate sample, analyze it and open the dashboard |
| `tests/test_project.py` | Nine unit/integration tests |
| `samples/synthetic_localhost.pcap` | Synthetic fixture, viewable in Wireshark |
| `output/` | Pre-generated sample dashboard, CSV and JSON |
| `report/Network_Traffic_Analysis_Report.pdf` | Project report |
| `report/Network_Traffic_Analysis_Report.md` | Editable report source |
| `VIVA.md` | Short explanation and viva answers |

PCAP records are read with bounds checks. Link headers are removed before IPv4
is parsed. TCP flags, ports, sequence and acknowledgement numbers are extracted.
HTTP is recognized only when a TCP payload begins with a supported HTTP/1 method
or response line; port numbers alone do not determine HTTP. UDP and ICMP headers
are decoded separately. Bidirectional endpoint pairs are grouped into conversations.

Protocol share = labelled packets / total packets x 100.
Observed mean bit rate = sum of frame wire lengths x 8 / capture duration.
The rate is not the physical link speed or application goodput.

## Validation

```sh
python -m unittest discover -s tests -v
```

Nine tests passed in the build environment, including real localhost HTTP and
UDP exchanges, known sample counts, valid fixture checksums, PCAP byte orders,
microsecond/nanosecond formats, link headers, malformed input, empty input and
HTML escaping. Five default-port HTTP/UDP rounds also completed successfully.
Wireshark GUI capture was not executed in the build environment because capture
privileges were unavailable. Windows/macOS live capture must be checked locally.

## Limits and troubleshooting

- Input: uncompressed classic PCAP, version 2.4. Convert PCAPNG first. Supported
  link types: Ethernet (including VLAN), NULL/LOOP, raw IPv4 and Linux cooked v1/v2.
- Detailed decoding is IPv4 only. ARP is labelled by EtherType but not decoded.
  IPv6 and other protocols are counted as unsupported; fragmented IPv4 is not
  reassembled. Malformed frames remain in the table with an explanation.
- No TCP reassembly, DNS decoding, TLS decryption, checksum validation of input,
  packet-loss measurement, intrusion detection or malicious-traffic verdicts.
- HTTP spanning segments may be missed. Wireshark is the reference for detailed
  protocol analysis. The fixture's valid checksums are verified by tests.
- All decoded rows are kept in memory. Use small classroom captures. The HTML
  table shows at most 10,000 rows; CSV and summary cover all parsed records.
- A zero-duration capture has rate 0 by convention, not a measured throughput.
- `Address already in use`: stop the process using 8080/9999 or pass
  `--http-port 8081 --udp-port 10000`, updating Wireshark filters accordingly.
- No packets: select loopback, start capture before running the generator,
  verify Npcap/capture permissions and ensure the filter uses the same ports.
- Invalid PCAP: stop/save the capture completely and convert the actual format.
- Keep captured files private if they contain sensitive data; the bundled sample
  contains only artificial localhost traffic.

## Submission

Fill your roll number, guide and date on the editable report before final
submission. Add screenshots from your own Wireshark capture if your instructor
requires live evidence. The report's result table describes only the supplied
synthetic sample. The linked Drive document could not be read during preparation;
the user-provided assignment screenshot is the requirements source.

## References

- Wireshark loopback capture: https://wiki.wireshark.org/capturesetup/loopback
- Wireshark display filtering: https://www.wireshark.org/docs/wsug_html_chunked/ChWorkDisplayFilterSection.html
- editcap file conversion: https://www.wireshark.org/docs/man-pages/editcap.html
