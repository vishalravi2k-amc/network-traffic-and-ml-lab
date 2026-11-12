"""One-command offline demonstration; no capture privileges required."""
import webbrowser
from pathlib import Path
from analyzer import decode,read_pcap,summarize,write_outputs
from make_sample import write_sample

root=Path(__file__).resolve().parent
sample=write_sample(root/'samples'/'synthetic_localhost.pcap')
rows=[decode(r) for r in read_pcap(sample)]
summary=summarize(rows)
write_outputs(rows,summary,root/'output',sample.name)
print('SYNTHETIC sample analysis:',summary)
page=(root/'output'/'dashboard.html').resolve()
print('Open in a browser:',page)
webbrowser.open(page.as_uri())
