# Article figures

## semantic-control-plane-architecture.jpg

Six-panel architecture figure used in the Medium article:

1. The Semantic Control Plane (high-level architecture)
2. Bounded Repair Loop with Early Exit
3. Validation Ladder
4. Ontology Selection vs. Grounding
5. Execution State Machine
6. Provenance & Observability Flow

**Referenced from:** [`../agentic-ontogpt-medium.md`](../agentic-ontogpt-medium.md)

```markdown
![Semantic Control Plane architecture](figures/semantic-control-plane-architecture.jpg)
```

### Publishing notes

- **Medium:** upload this JPEG when pasting the article (or open the local MHTML which embeds it).
- **Local MHTML:** `docs/articles/agentic-ontogpt-medium.mhtml` (self-contained, generated via medium-article-generator + pandoc `--embed-resources`).
- **Source name (attachment):** `5EC361A0-4BFA-4775-94FE-13CA527D9A21` (JPEG).

If the binary is missing from this directory on GitHub, add it with:

```bash
git add docs/articles/figures/semantic-control-plane-architecture.jpg
git commit -m "docs: add semantic control plane architecture figure"
git push
```
