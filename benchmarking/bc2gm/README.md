# BC2GM Track 2

Gene/protein mention NER (BioCreative II GM).

```bash
python scripts/download_bc2gm.py
python scripts/convert_bc2gm.py --split test
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_bc2gm_track2.py --limit 50
python scripts/run_bc2gm_track2.py --limit 20 --oracle
AGENTIC_ONTOGPT_MODE=real python scripts/run_bc2gm_track2.py --limit 20
```
