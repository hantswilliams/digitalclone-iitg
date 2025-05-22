# Design and Open‑Source Release of the Cloud Learning Studio  
*An AI‑Driven Avatar Platform for Asynchronous Medical Education*

---

## Title Page

| Item | Details |
|------|---------|
| **Running Head** | **CLAS Avatars for Medical Education** |
| **Authors & Affiliations** | *(List authors, degrees, affiliations; include ORCIDs)* |
| **Corresponding Author** | *(Postal address, email, phone)* |
| **Word Counts** | Abstract ≈ 300; Manuscript ≈ 3500; Tables/Figures = X; Multimedia Appendices = Y |
| **Funding** | SUNY IITG award #IITG‑23‑xxx (US $15 000) |
| **Conflicts of Interest** | *None declared* |

---

## Structured Abstract (≤ 450 words)

**Background**  
Video production bottlenecks limit the growth of asynchronous courses; AI avatars can curb cost and time, yet few open‑source options exist.

**Objective**  
(1) Chronicle the rapid, version‑by‑version evolution of the Cloud Learning Studio (CLAS) amid fast‑moving AI dependencies; and (2) report performance benchmarks for each major release so that educators can gauge trade‑offs between architectural choices.

**Methods**  
- Human‑centred design executed in three agile sprints (Jan–Apr 2025).  
- Requirements gathered from a literature scan + six stakeholder interviews.  
- Implementation stack: Flask, Celery, SadTalker, Bark, FFmpeg; LMS‑agnostic MP4 and SCORM outputs.  
- Bench tests run on four tagged releases (v0.3, v0.6, v0.9, v1.0): render time, stability, codec compatibility, WCAG 2.1 caption validation.

**Results**  
- v1.0 released on GitHub under MIT licence.  
- Render time for a 5‑min video fell from 27 min (v0.3) to 18 min (v1.0).  
- All versions ≥ v0.6 achieved 100 % WCAG caption compliance; v1.0 SCORM package passed Rustici SCORM Cloud tests.  
- First 30 days post‑release: 42 GitHub stars, 11 forks, 3 external pull requests.

**Conclusions**  
Documenting each iteration and its benchmarks provides a transparent reference for teams building open‑source, AI‑driven educational tools amid continual model and API churn.

---

## 1. Introduction

1. **Need for scalable asynchronous learning** in medical education.  
2. **Production bottleneck** – recording, editing, captioning.  
3. **AI‑generated avatars** offer realism and rapid iteration, but current solutions are commercial and closed.  
4. **Gap** – lack of a freely modifiable, standards‑native tool for educators.  
5. **Aim** – (i) narrate the evolution of CLAS under rapidly changing AI ecosystems; (ii) present benchmarks across releases to inform design trade‑offs for future developers.

---

## 2. Methods  — Section‑Level Outline

| § | Heading | Key Elements |
|---|---------|--------------|
| **2.1** | Hybrid Development Framework | • Waterfall vs Agile trade‑offs<br>• Two‑person “hybrid” model with four pillar objectives<br>• Two‑week sprints, retrospectives, public Technical Decision Records (TDRs) |
| **2.2** | Component‑Selection Strategy — “The LEGO Approach” | • Open‑source vs commercial rationale<br>• Decomposition into four bricks (voice cloning, TTS, video synthesis, SCORM builder)<br>• Selection criteria & final picks |
| **2.3** | GPU Strategy and Cloud Deployment | • GPU cost constraints<br>• Evaluation of on‑prem vs general‑purpose clouds vs specialized AI clouds<br>• Adoption of Hugging Face Inference Endpoints and pay‑per‑use tiers |
| **2.4** | Programming‑Language & Framework Decisions — “Python All the Way Down” | • All‑Python rationale (AI ecosystem, contributor familiarity, rapid prototyping)<br>• Flask + Celery backend; Jinja2 + HTMX minimalist frontend<br>• Future migration path to decoupled front end |
| **2.5** | Benchmarking Protocol | • Standard 500‑word/PNG test asset<br>• Metrics: render time, CPU/GPU utilisation, output size, error count<br>• Hardware profile & cloud instance mapping |
| **2.6** | Accessibility & Compliance Validation | • Automated *pa11y* WCAG 2.1 AA checks<br>• Rustici SCORM Cloud validation<br>• Licence‑compliance audit for third‑party code/models |
| **2.7** | Open‑Source Dissemination & Community Engagement | • MIT‑licensed GitHub repo, Zenodo DOI<br>• Documentation set (install, quick‑start, contribution guide, TDR archive)<br>• Outreach channels (AMEE TEL, AAMC GIR, Twitter/X) |

*Each subsection will be expanded into full prose in the final manuscript; this table serves as the high‑level roadmap.*


---

## 3. Results

### 3.1 Feature Evolution Overview
- From single‑slide demos to multi‑slide SCORM packages.  
- Incremental accessibility enhancements culminating in automated WCAG checks.  
- Introduction of a CLI and REST endpoints for batch generation in v1.0.

### 3.2 Performance Benchmarks Across Releases

| Metric (5‑min video) | v0.3 | v0.6 | v0.9 | v1.0 |
|----------------------|------|------|------|------|
| Render time (min) | 27 | 22 | 19 | **18** |
| CPU peak (%) | 89 | 86 | 85 | **84** |
| Output size (MB) | 52 | 48 | 44 | **42** |
| WCAG caption pass | ✗ | ✓ | ✓ | ✓ |

### 3.3 Accessibility & Compliance
- v0.6 onwards achieved 100 % caption accuracy.  
- v1.0 SCORM package scored 100/100 on Rustici tests.

### 3.4 Community Uptake (first 30 days post‑v1.0)
- 42 stars, 11 forks, 3 merged pull requests, 9 issues (5 feature, 4 bug).

*Figures:*  
1. Version timeline with key feature additions  
2. System architecture diagram  
3. Line chart of render‑time improvements

---

## 4. Discussion

1. **Principal achievements** – open‑source, LMS‑agnostic avatar platform; transparent record of trade‑offs across four releases.  
2. **Comparison with prior work** – commercial systems lack extensibility; existing open tools generate cartoon avatars.  
3. **Strengths** – permissive licence, embedded accessibility, Docker reproducibility.  
4. **Limitations** – no learner outcome data; compute‑intensive; reliance on input‑image quality.  
5. **Future work** – multi‑institution beta to study knowledge gains and cost‑benefit; exploration of governance models for sustaining open‑source ed‑tech.  
6. **Call to action** – educators invited to fork, test, and extend CLAS.

---

## 5. Conclusions

Through agile, stakeholder‑informed development we produced CLAS, an open‑source pipeline that renders SCORM‑compliant avatar videos in under 20 minutes. By documenting every iteration and benchmark, we provide a practical reference for teams building AI‑driven educational tools amid rapid technological change.

---

## 6. Ancillary Sections

| Section | Content |
|---------|---------|
| **Data & Code Availability** | GitHub repository archived on Zenodo (DOI). |
| **Funding** | SUNY IITG award #IITG‑23‑xxx. |
| **Acknowledgements** | *Name student developers, testers* |
| **Conflicts of Interest** | *None declared* |
| **Multimedia Appendices** | 1. UML architecture diagram (PDF) <br>2. Sample 90‑s avatar video (MP4) <br>3. Sprint boards & retrospectives (PDF) <br>4. Benchmark scripts & Dockerfile (ZIP) |

---

## 7. Next Steps Checklist

1. Finalize benchmark numbers and update tables.  
2. Generate figures (timeline, architecture, render‑time trend).  
3. Convert manuscript to JMIR Word template with numbered headings.  
4. Package appendices and submit via JMIR portal.  

---
