# Enterprise authentication: Google ADC + Vertex AI Gemini

This guide is for **enterprise / production** use of Path A (`adk run agents/pipeline`) and Path B (ADK graph demos) **without** a Google AI Studio API key.

Prefer **Application Default Credentials (ADC)** + **Vertex AI** over `GOOGLE_API_KEY`.

Developer / quick-start API-key mode remains documented in [`.env.example`](../.env.example).  
ADC mode uses [`.env.adc.example`](../.env.adc.example).

---

## When to use this

| Mode | Auth | Typical use |
|------|------|-------------|
| API key | `GOOGLE_API_KEY` (AI Studio / Express) | Local experiments |
| **ADC + Vertex** | ADC + `GOOGLE_GENAI_USE_VERTEXAI` | Enterprise, VPC, IAM, audit |

agentic-ontogpt does **not** require code changes for ADC: ADK / `google-genai` pick up Vertex env vars and the ADC chain automatically.

---

## Prerequisites

1. **Google Cloud project** with billing enabled  
2. **Enable APIs**:

   ```bash
   gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
   ```

3. **IAM** on the identity that runs agents:

   | Role | Purpose |
   |------|---------|
   | `roles/aiplatform.user` | Call Vertex AI Gemini |
   | (optional) other roles | GCS, BigQuery, Secret Manager, etc. |

4. **gcloud CLI** for local ADC: https://cloud.google.com/sdk/docs/install  

---

## Environment variables

```bash
cp .env.adc.example .env
```

| Variable | Example | Purpose |
|----------|---------|---------|
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` | Vertex AI backend (not AI Studio) |
| `GOOGLE_CLOUD_PROJECT` | `my-gcp-project` | Quota and billing project |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Region (or `global` if allowed) |
| `ADK_LLM_MODEL` | `gemini-2.0-flash` | Default ADK model |

**Do not set** in pure ADC mode:

```bash
unset GOOGLE_API_KEY
unset GEMINI_API_KEY
```

Other secrets unchanged: `BIOPORTAL_API_KEY`, optional `OPENAI_API_KEY` for SPIRES, `AGENTIC_ONTOGPT_MODE`.

---

## Providing ADC

### Local development

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
```

### Workloads on Google Cloud

Attach a service account with `roles/aiplatform.user`; set the same three Vertex env vars. Metadata server supplies ADC (no JSON key).

### Outside GCP

Prefer Workload Identity Federation. Last resort:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/secure/path/sa-key.json
```

---

## Smoke checks

```bash
gcloud auth application-default print-access-token >/dev/null && echo "ADC OK"
echo "VERTEX=$GOOGLE_GENAI_USE_VERTEXAI PROJECT=$GOOGLE_CLOUD_PROJECT"

python -m pytest tests/ -q
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template

pip install google-adk
adk run agents/pipeline
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

---

## Mapping to parallel paths

| Path | ADC impact |
|------|------------|
| **A** `adk run agents/pipeline` | Vertex Gemini via ADC |
| **B** graph demos | Same via ADK |
| **C** headless / simulation | No Gemini; ADC irrelevant |

See root [README — Parallel execution paths](../README.md#parallel-execution-paths-same-control-plane).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `401 API key not valid` | Still on AI Studio | `GOOGLE_GENAI_USE_VERTEXAI=TRUE`; unset API keys |
| Permission denied on `aiplatform` | Missing IAM | Grant `roles/aiplatform.user` |
| Model not found | Wrong region/model | Align location and Vertex model id |
| Works locally, fails on Cloud Run | SA missing | Attach SA + Vertex AI User |

---

## References

- ADK Gemini auth: https://google.github.io/adk-docs/agents/models/google-gemini/  
- Vertex Gen AI SDK: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview  
- ADC: https://cloud.google.com/docs/authentication/application-default-credentials  
