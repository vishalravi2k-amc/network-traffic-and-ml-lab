# PacketScope — Network Traffic Analysis

Theme E project by **Gowthami.M**, **USN 1AM23CI042**, AMC Engineering College, CSE (AI & ML).

A static browser application for analyzing classic PCAP files locally. Includes a synthetic demo, packet explorer, details dialog, protocol chart, endpoint summaries, filtering, sorting, CSV export, source viewer, Wireshark instructions and the 10-page report.

## Website and source

- [Open the working website](https://gowthami-network-traffic.vishalravi20k.chatgpt.site/) (currently owner-private; sign in with the owning ChatGPT account).
- [GitHub repository](https://github.com/vishalravi2k-amc/network-traffic-and-ml-lab) (currently private).
- [Project report PDF](dist/report.pdf)
- [ML methods and result tables](ml/README.md)

## Run
Serve `dist/` with a static server. Example: `python3 -m http.server 8000 --directory dist` and open http://localhost:8000. ES modules and sample fetches require HTTP hosting rather than opening index.html directly.

## Test
`npm test` (Node.js, no installed dependencies required).

The complete standalone Python project is in `network/`. Run `python network/run_demo.py` for the offline sample dashboard. Run its tests with `cd network` followed by `python -m unittest discover -s tests -v`. Individual source downloads are also available from the website.

To reproduce the ML comparisons, install `ml/requirements.txt` in a Python virtual environment and run `python ml/train_compare.py`; see `ml/README.md` for exact commands. Training is done locally in Python; the website displays saved results.

## Scope
Browser-local file analysis, up to 20 MB and 100,000 packets. Classic PCAP 2.4; IPv4 TCP/UDP/ICMP and segment-start HTTP/1 detection. PCAPNG must be converted with Wireshark/editcap. No live capture in the browser, IPv6 dissection, reassembly, DNS decoder, TLS decryption, input checksum validation or attack verdicts. Demo data is synthetic.

## Report
`dist/report.pdf` names Gowthami.M and USN 1AM23CI042. Editable report and viva notes are in `dist/source/`.

## Privacy
Capture bytes are parsed locally in the browser and are not sent to an analysis server. The site requests its static assets and optional Google Fonts; uploaded capture content is not included in those requests.

## ML comparisons
The `ml/` directory contains all three supplied datasets, reproducible training code, trained models, predictions, split records and result tables. The website ML comparison page displays the verified results. See `ml/README.md` for the experimental method.
