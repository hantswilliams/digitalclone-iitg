# Voice‑Cloned Talking‑Head Lecturer — Generation Workflow

This document captures the **exact order of operations** required to turn a lecturer’s portrait and short voice reference into a finished talking‑head video.

---

## 1 · Script Generation

| Step | Action | Service / Tool | Resulting Artefact |
|------|--------|----------------|--------------------|
| 1.1 | Instructor enters a prompt **or** pastes finished text | • Manual input (UI)<br>• *or* Llama‑3‑8B via Ollama | `script.txt` containing lecture text |

---

## 2 · Speaker Voice Cloning

| Step | Action | Service / Tool | Resulting Artefact |
|------|--------|----------------|--------------------|
| 2.1 | Upload 10–30 s reference audio | Asset upload endpoint | `reference_voice.wav` (stored in MinIO) |
| 2.2 | Generate speaker embedding | Zyphra API (internal call) | `speaker_embed` (base64 / ID) |

---

## 3 · Text‑to‑Speech Synthesis

| Step | Action | Service / Tool | Resulting Artefact |
|------|--------|----------------|--------------------|
| 3.1 | Send `script.txt` + `speaker_embed` | Zyphra `/audio/text-to-speech` | `speech.webm` |
| 3.2 | Convert to WAV (16 kHz mono) | FFmpeg (Celery task) | `speech.wav` |

---

## 4 · Talking‑Head Video Generation

| Step | Action | Service / Tool | Resulting Artefact |
|------|--------|----------------|--------------------|
| 4.1 | Upload or select portrait | Asset upload endpoint | `avatar.png` |
| 4.2 | Animate portrait with audio | KDTalker Gradio `/gradio_infer` | `video.mp4` |
| 4.3 | Store video & metadata | MinIO + PostgreSQL | Signed S3 URL returned |

---

### Sequence Diagram (simplified)

```plaintext
User ──> UI ──> Flask API ──> Celery
                               │
 1 Script ─────────────────────┘
                               │
 2 Voice Clone (Zyphra) ───────┤
                               │
 3 TTS (Zyphra) ───────────────┤
                               │
 4 Video (KDTalker) ───────────┘
```

---

## Error Handling & Idempotency

1. Each stage persists its artefact **before** triggering the next.  
2. Celery retries transient API failures (max 3, exponential back‑off).  
3. Partial artefacts clean‑up cron runs nightly (older than 7 days, status ≠ `COMPLETED`).

---

## Integration Points

| Artifact | Storage | Down‑stream consumer |
|----------|---------|----------------------|
| `script.txt` | PostgreSQL (TEXT) | TTS request |
| `reference_voice.wav` | MinIO `uploads/voice/` | Zyphra clone |
| `speech.wav` | MinIO `generated/audio/` | KDTalker |
| `video.mp4` | MinIO `generated/video/` | UI preview / LMS export |

---

## Compliance Notes

* **Zyphra (Apache‑2.0)** → commercial use permitted.  
* **KDTalker (CC BY‑NC 4.0)** → teaching use OK; commercial resale requires separate licence.  
* All reference voices encrypted at rest; auto‑delete configurable (default = 30 days).
