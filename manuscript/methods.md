# 2. Methods

### 2.1 Developer Framework Selection

Selecting an appropriate software‑development framework is a foundational step in any technology project. Teams typically weigh the predictability of waterfall methods—where requirements are fixed before coding—against the responsiveness of agile methods, which prioritize short, iterative cycles and continuous stakeholder feedback. The choice hinges on team size, regulatory constraints, and the volatility of external dependencies.

In our two‑person academic setting, we adopted a hybrid approach, that fused waterfall’s upfront discipline with agile’s iterative flexibility. We articulated four non‑negotiable pillars at project outset—LMS‑agnostic outputs, WCAG‑compliant accessibility, permissive open‑source licensing, and deployment on commodity hardware—then organized work into two‑week sprints that ended with a runnable release and retrospective. These pillars acted as architectural guardrails, while the sprints allowed us to refine requirements and refactor code without losing sight of core objectives.

A separate but critical consideration was the rapid evolution of AI toolchains. Model APIs, licence terms, and performance characteristics changed multiple times during development, rendering a purely waterfall plan impractical. Shorter sprints enabled timely adaptation—such as replacing a deprecated TTS endpoint or integrating updated SadTalker weights—while our pillar objectives ensured each pivot still advanced the overarching goal of an open, standards‑native platform. This experience suggests that traditional, rigid frameworks may be ill‑suited to AI‑driven projects; instead, a structured yet flexible methodology that blends fixed objectives with frequent reassessment is essential for maintaining momentum amid continual technological change.

### 2.2 Component‑Selection Strategy — **“The LEGO Approach”**

Because our goal was to deliver a **low‑cost, freely adoptable** platform, we deliberately restricted our search to **open‑source alternatives**, avoiding paid commercial services such as Synthesia, D‑ID, or ElevenLabs. While commercial APIs can accelerate prototyping, their recurring fees, opaque roadmaps, and restrictive licences undermine long‑term sustainability for academic programs and resource‑constrained institutions. Assembling the pipeline entirely from permissively licensed projects ensures that educators can deploy CLAS on campus servers—or even personal laptops—without usage charges and can modify the codebase to meet local security or pedagogic requirements.

We therefore adopted what we call the **“LEGO Approach”**: treating the open‑source ecosystem as a box of interoperable bricks that can be snapped together, swapped out, or upgraded independently. Instead of hunting for a monolithic, end‑to‑end solution, we decomposed the avatar‑generation workflow into four functional blocks and scouted the best‑fit project for each:

1. **Voice Cloning** – capturing a speaker’s timbre from a brief reference sample.  
2. **Neural TTS Playback** – re‑using the cloned voice to narrate arbitrary scripts.  
3. **Talking‑Head Video Synthesis** – animating a static facial image in sync with narrated audio.  
4. **SCORM‑Ready Presentation Builder** – packaging the resulting video (plus optional slides) into a format any learning‑management system (LMS) can ingest.

For every block we evaluated candidate projects against five criteria:  
(i) permissive licence (MIT, Apache‑2.0, or equivalent);  
(ii) active maintainer community;  
(iii) Python API for seamless Flask integration;  
(iv) GPU/CPU requirements compatible with commodity hardware; and  
(v) output quality confirmed by pilot tests with two instructors.  
Table 1 summarises the shortlist and final selections: **Bark** for voice cloning/TTS (LGPL, containerised for licence compliance), **SadTalker** for video synthesis (MIT), **python‑pptx** with a custom SCORM wrapper for presentation export (MIT), and **FFmpeg** for media post‑processing (LGPL).

This modular LEGO mentality yielded two advantages. **First**, it insulated the project from the rapid churn of AI tooling; if a brick became deprecated or adopted an incompatible licence, we could replace only that piece rather than refactor the entire stack. **Second**, it enabled parallel experimentation—while one developer fine‑tuned lip‑sync parameters in *SadTalker*, the other iterated on slide‑template styling in *python‑pptx* without merge conflicts. The subsections that follow detail how each brick was stitched into the Flask/Celery backbone and validated against our benchmark script.

### 2.3 GPU Strategy and Cloud Deployment

Deep‑learning workloads underpinning voice cloning, TTS, and talking‑head synthesis are **GPU‑intensive**. Although most models can fall back to CPU execution, inference times grow from minutes to hours—undermining the rapid‑iteration ethos of our sprints. Purchasing on‑premise GPUs (e.g., NVIDIA A5000 ≈ US $2 000 or H100 ≈ US $30 000) was beyond our academic budget and would have locked us into a single hardware profile even as model requirements evolved.

Three infrastructure paths were evaluated:

| Option | Pros | Cons |
|--------|------|------|
| **On‑prem GPUs** | Full control; no ongoing fees | High upfront cost; hardware obsolescence |
| **General‑purpose clouds (AWS, Azure, GCP)** | Wide instance catalogue; mature tooling | Requires DevOps expertise; long‑lived instances incur idle costs |
| **Specialized AI clouds (e.g., Hugging Face, Replicate, RunPod)** | Pay‑per‑second billing; curated GPU presets; minimal setup | Smaller ecosystem; vendor lock‑in risk |

We selected **Hugging Face Inference Endpoints** for development and benchmarking because it offered *serverless* GPU instances that could be spun up in under a minute and billed only while active. Available tiers ranged from **CPU‑only ($0)** for quick syntax tests to **NVIDIA T4 ($0.10 min⁻¹)** for routine renders, up to **A100/H100 (>$2 min⁻¹)** for stress‑testing high‑resolution outputs. This elasticity let us match hardware to task without capital expenditure:

| Task | Instance Type | Avg Cost |
|------|---------------|----------|
| Unit test (CPU) | Intel Xeon | \$0 (free tier) |
| 1080p lip‑sync render | NVIDIA T4 | \$0.90 per 9‑min job |
| Batch slide set (10 videos) | NVIDIA A10G | \$4.80 per 12‑min job |
| Stress test, 4K output | NVIDIA H100 | \$7.20 per 3‑min job |

SSH tunnelling and a lightweight Hugging Face SDK allowed Celery workers on our local MacBook M2 to off‑load heavy inference to cloud GPUs transparently, returning results via signed URLs. This approach decoupled model experimentation from physical hardware, accelerated performance tuning, and kept costs predictable—an essential benefit given the fast‑moving AI landscape described in Section 2.1. The same mechanism also positions downstream adopters to choose the cost‑performance point that suits their institutional constraints, further supporting CLAS’s mission as a low‑barrier, open‑source solution.

### 2.4 Programming‑Language and Framework Decisions — “Python All the Way Down”

From a practical standpoint, the next architectural question was **which programming language(s) and web framework** would let us (a) prototype rapidly, (b) integrate natively with state‑of‑the‑art AI libraries, and (c) remain approachable for future contributors in medical‑education research groups. We opted for an **all‑Python stack** for both the backend and minimal frontend, anchored by the Flask micro‑framework.

#### Rationale for a Single‑Language MVP
| Criterion | Why Python? |
|-----------|-------------|
| **AI Ecosystem** | Virtually every open‑source model we considered—Bark, SadTalker, TTS‑X, Stable Diffusion—provides first‑class Python bindings, eliminating the need for language bridges. |
| **Contributor Familiarity** | Python is already common in bioinformatics and educational‑data science; keeping everything in one language lowers onboarding friction for researchers and graduate students. |
| **Rapid Prototyping** | Flask’s zero‑boilerplate philosophy lets a two‑person team stand up REST endpoints, background tasks, and templated HTML pages in hours rather than days. |
| **Async Workflows** | Celery, a Python‑native task queue, integrates seamlessly with Flask and enables GPU‑bound jobs to run asynchronously without blocking the web server. |
| **Document Generation** | Libraries such as `python-pptx`, `moviepy`, and `pdfkit` allowed us to automate slide decks, video concatenation, and documentation from within the same runtime environment. |

#### Minimalist Frontend
To keep our MVP lightweight, we served server‑rendered Jinja2 templates for the instructor dashboard and relied on vanilla JavaScript plus HTMX for reactive UI elements. While this approach lacks the polish of a full React or Vue front end, it shortened the feedback loop: every template update was a single `CTRL+S` away, with hot‑reload courtesy of Flask’s debug server.

#### Future‑Proofing Considerations
We recognise that an all‑Python front end may not scale indefinitely. The project roadmap (see Multimedia Appendix 2) outlines a migration path toward a decoupled API backend and a Next.js or SvelteKit front end once the codebase attracts a broader contributor pool. However, for an MVP built by two developers under grant‑funding time constraints, **“Python all the way down”** maximised velocity without sacrificing maintainability.

In sum, the language and framework choices aligned with our guiding pillars: *low cost*, *ease of adoption*, and *modular flexibility*—principles that mirror the LEGO philosophy described in Section 2.2.

### 2.5 Benchmarking Protocol  

To keep performance claims transparent and reproducible, we established a standard benchmarking script executed at the close of each sprint and before every tagged release. The test asset consisted of a 500‑word instructional script and a single high‑resolution PNG head‑shot—chosen to approximate a typical five‑minute micro‑lecture. For local trials we used a MacBook M2 (8‑core GPU, 16 GB RAM); for cloud trials we mapped the same script to Hugging Face Inference Endpoints at three GPU tiers (T4, A10G, H100). Metrics collected were: (i) total render time from task submission to MP4 + WebVTT output; (ii) peak CPU and GPU utilisation captured via `psutil` and `nvidia-smi`; (iii) final file size; and (iv) error count and type, automatically parsed from Celery logs. Benchmark data and analysis notebooks are archived alongside the code repository to enable independent verification.

### 2.6 Accessibility & Compliance Validation  

Accessibility and standards compliance were integral pillars rather than after‑thoughts. Each output video underwent automated testing with *pa11y* against WCAG 2.1 AA criteria, focusing on caption synchrony, colour‑contrast of slide overlays, and keyboard navigability of the embedded player. Any failures blocked a release until resolved. For interoperability, the SCORM packages generated by our custom wrapper were uploaded to Rustici SCORM Cloud’s test harness; a score of 100/100 was required for promotion to the `main` branch. A parallel licence‑compliance audit confirmed that all third‑party components retained permissive licences (MIT, Apache‑2.0, or LGPL containerised for separation). Because no learner or patient data were processed, and all synthesis used publicly available models, the Stony Brook IRB classified the project as non‑human‑subjects research.

### 2.7 Open‑Source Dissemination & Community Engagement  

To maximise adoption and collaborative improvement, CLAS is released under the MIT licence on GitHub, with each version assigned a Zenodo DOI for citation stability. The repository includes a one‑command installer (`make install`), a quick‑start notebook, detailed contribution guidelines, and an archive of Technical Decision Records (TDRs) for architectural transparency. We announced each release on the AMEE Technology‑Enhanced Learning (TEL) and AAMC Group on Information Resources (GIR) listservs, as well as on Twitter/X via the #MedEd and #OpenSource hashtags, inviting educators to fork the project, file issues, or submit pull requests. Governance follows the Contributor Covenant code of conduct and a lightweight “Benevolent Maintainer” model until the contributor base grows large enough to warrant a steering committee. Quarterly dependency updates and security scans are scheduled via GitHub Actions to ensure sustainability beyond the initial grant period.
