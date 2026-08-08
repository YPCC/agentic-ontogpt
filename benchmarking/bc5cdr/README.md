# BC5CDR Track 2

Chemical + Disease NER on PubMed abstracts (BioCreative V).

```bash
python scripts/download_bc5cdr.py
python scripts/convert_bc5cdr.py --split test
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_bc5cdr_track2.py --limit 50
python scripts/run_bc5cdr_track2.py --limit 20 --oracle
AGENTIC_ONTOGPT_MODE=real python scripts/run_bc5cdr_track2.py --limit 20
```
