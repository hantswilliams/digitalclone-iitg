| Layer   | Technology                  | Purpose                                     |
| ------- | --------------------------- | ------------------------------------------- |
| UI      | React + Tailwind · HTMX     | Upload assets, prompt script, preview video |
| API     | Flask (blueprints)          | Auth, job submission, signed-URL delivery   |
| Async   | Celery + Redis              | GPU job queue, retries, monitoring          |
| Storage | PostgreSQL · MinIO          | Metadata, user assets, generated media      |
| Voice   | **Zyphra TTS** (Apache-2.0) | Speaker cloning & speech synthesis          |
| Avatar  | **KDTalker** (CC BY-NC 4.0) | Portrait-to-talking-head video              |
| Text    | Llama-3-8B via Ollama       | Prompt-to-lecture draft generation          |
