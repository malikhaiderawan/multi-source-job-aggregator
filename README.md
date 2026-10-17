# 🎯 Job Discovery & Application Assistant (Anser Nawaz & Multi-Candidate)

A senior-level tech job discovery, matching, and application automation gateway custom-engineered for **Anser Nawaz** (Senior Full-Stack & Mobile Engineer with 6+ years of professional experience) with built-in **Multi-Candidate Profile Switching**, **Candidate-Specific Tracker Isolation**, and **Atomic Concurrency Protection**.

Built with a high-performance **FastAPI** Python backend and modern **Next.js 16 (React 19, TypeScript, Tailwind CSS 4)** frontend.

---

## 📑 Table of Contents
1. [Key Features](#-key-features)
2. [Quick Start (One-Click)](#-quick-start)
3. [How to Use the System (Step-by-Step Guide)](#-how-to-use-the-system)
   - [1. Discovering & Filtering Scored Jobs](#1-discovering--filtering-scored-jobs)
   - [2. Switching Candidates (Anser vs Other Profiles)](#2-switching-candidates)
   - [3. Tailoring Resume Bullets & Cover Letters](#3-tailoring-resume-bullets--cover-letters)
   - [4. Managing the ATS Application Tracker](#4-managing-the-ats-application-tracker)
   - [5. Sending Outreach Emails with Strict Approval](#5-sending-outreach-emails-with-strict-approval)
   - [6. Daily High-Match Email Digest](#6-daily-high-match-email-digest)
4. [Installation & Manual Setup](#-installation--manual-setup)
5. [Environment Variables (`.env`)](#-environment-variables)
6. [Data Isolation & Security Architecture](#-data-isolation--security-architecture)
7. [Running Tests & Quality Checks](#-running-tests--quality-checks)
8. [API Endpoints Reference](#-api-endpoints-reference)
9. [Urdu / Roman Urdu Quick Guide (اردو گائیڈ)](#-roman-urdu-quick-guide)

---

## 🌟 Key Features

* **Multi-Source Real-Time Aggregation (100% Compliant):**
  - Concurrently queries **Remotive**, **Jobicy API v2**, **Arbeitnow**, **WeWorkRemotely RSS**, and **Jooble**.
  - Specialized focus on **Lahore, Pakistan** local opportunities and **Worldwide Remote** roles.
  - Zero unauthorized LinkedIn scraping, session hijacking, or CAPTCHA bypass.
* **Smart Matching Engine (0–100% Score):**
  - Dynamically calculates skills overlap (40 pts), seniority level (25 pts), location match (25 pts), and salary disclosure (10 pts) against the active candidate.
* **Multi-Candidate Profile Switcher:**
  - Default profile: **Anser Nawaz** (6+ years, Mobile: React Native/Flutter/iOS/Android, Frontend: React/Next.js/TypeScript, Backend: Node.js/Python/FastAPI, Full-stack Architecture).
  - Built-in secondary profiles (e.g. Haider Nawaz) and modal to create new candidate profiles with instant live rescoring.
* **Strict Candidate Data Isolation:**
  - Bookmarked jobs, ATS statuses, private notes, and tailored application drafts are partitioned by validated `candidate_id`. Candidate A and Candidate B can track the exact same job independently without data collision.
* **Factual Application Materials Generator:**
  - Generates tailored CV bullet points, personalized cover letters, and recruiter outreach emails drawn strictly from verified career history (zero hallucinated skills).
* **Strict Email Approval Gate:**
  - Outreach emails require an explicit user approval checkbox before transmission. Includes safe dry-run simulation mode when SMTP credentials are not configured.
* **Atomic Storage & Concurrency Safety:**
  - Local JSON storage with OS-level reentrant file locking (`fcntl.flock` + `threading.RLock`) and atomic file replacement (`tempfile` + `os.replace`) to prevent corrupted records.
  - Sensitive files (`data/*.json`, `data/*.bak`, `.env`) are strictly ignored from Git.

---

## ⚡ Quick Start

Make sure you have **Python 3.9+** and **Node.js 18+** installed.

```bash
# 1. Clone or navigate to the directory
cd multi-source-job-aggregator

# 2. Run backend & frontend together in parallel
make dev
```
* **Frontend:** `http://localhost:3000`
* **FastAPI Backend & Swagger API Docs:** `http://localhost:8000/docs`

---

## 📖 How to Use the System

### 1. Discovering & Filtering Scored Jobs
1. Open `http://localhost:3000` in your web browser.
2. Filter by Category buttons:
   - **📱 Mobile:** React Native, Flutter, iOS, Android, cross-platform
   - **💻 Frontend:** React.js, Next.js, TypeScript, Tailwind CSS
   - **⚙️ Backend:** Node.js, Express, Python, FastAPI, Django, REST APIs
   - **🚀 Full-Stack:** Architecture, Microservices, Cloud, Technical Leadership
3. Select Location presets:
   - **🇵🇰 Lahore / Pakistan:** Local tech hubs in Lahore, Karachi, Islamabad
   - **🌐 Worldwide Remote:** Global remote opportunities
4. Adjust Minimum Match Score slider (e.g. 70%+) to focus only on high-match roles.

### 2. Switching Candidates
1. In the top navigation bar, click the **👤 Switch Candidate** button.
2. Choose from existing profiles (e.g., **Anser Nawaz** or **Haider Nawaz**).
3. Or click **➕ Add New Candidate** to input a new developer's name, skills, experience, and contact details.
4. Once switched, the entire discovery feed and application materials will automatically recalculate scores and tailor text for that candidate.

### 3. Tailoring Resume Bullets & Cover Letters
1. On any job card, click the **✨ Tailor Application** button.
2. A modal will open displaying:
   - **📄 Tailored CV Bullets:** 4-6 factual bullet points ready to paste into your resume.
   - **✉️ Customized Cover Letter:** Complete professional cover letter addressing the specific role and company.
   - **🚀 Recruiter Outreach Email:** Direct message formatted for LinkedIn or email outreach.
3. Use the **📋 Copy** buttons to copy any section directly to your clipboard.

### 4. Managing the ATS Application Tracker
1. From the Tailor Application modal, click **Bookmark**, **Pending Approval**, or **Mark Applied** to save the job to your board.
2. Navigate to **📊 Application Tracker** (`/tracker`) in the navbar.
3. Filter by stage: *Saved*, *Pending Approval*, *Applied*, *Interview Scheduled*, *Follow-up*, *Rejected*.
4. Change stages via the dropdown selector.
5. Add private notes (e.g., recruiter names, interview dates, salary discussed) directly in the inline note field—they save automatically.

### 5. Sending Outreach Emails with Strict Approval
1. Inside the **Recruiter Outreach Email** tab of any job modal:
2. Enter the recruiter's email address and customize the body text if desired.
3. **Approval Gate:** Check the box: `[✓] Require Approval Gate: I have reviewed this application email and explicitly approve transmitting it.`
4. Click **🚀 Send Approved Email**.
   - If SMTP credentials are configured in `.env`, the email is transmitted via SMTP.
   - If SMTP is not yet configured, the system logs the dispatch safely in dry-run mode and updates your tracker status to `Applied`.

### 6. Daily High-Match Email Digest
1. Click **📧 Trigger Digest** in the top navigation bar.
2. The system curates all postings with $\ge 70\%$ match score, formats an HTML and plain-text digest, and dispatches/logs the summary.

---

## 🛠️ Installation & Manual Setup

If you prefer running components manually in separate terminals:

### Backend Setup
```bash
# Navigate to repository root
cd multi-source-job-aggregator

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (Port 8000)
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd multi-source-job-aggregator/frontend

# Install dependencies
npm install

# Start Next.js development server (Port 3000)
npm run dev
```

---

## 🔒 Environment Variables

Copy `.env.example` to `.env` in the repository root:
```bash
cp .env.example .env
```

| Variable | Description | Default |
| :--- | :--- | :--- |
| `JOOBLE_API_KEY` | Optional Jooble API key for extended Pakistan jobs | None (gracefully isolated) |
| `CANDIDATE_NAME` | Primary candidate full name | `Anser Nawaz` |
| `CANDIDATE_EMAIL` | Sender email address for outreach | `ansernawaz786@gmail.com` |
| `DIGEST_RECIPIENT_EMAIL` | Target email for daily job alerts | `ansernawaz786@gmail.com` |
| `SMTP_HOST` | SMTP server host (e.g. `smtp.gmail.com`) | None (runs in dry-run mode) |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username / login | None |
| `SMTP_PASS` | SMTP application password / token | None |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000` |

---

## 🛡️ Data Isolation & Security Architecture

1. **Candidate Scoping:** All operations (`GET /api/v1/tracker`, `POST /api/v1/tracker`, status updates, notes) are strictly scoped to `candidate_id`. Cross-candidate access attempts return non-disclosing `404 Not Found`.
2. **Reentrant File Locking:** `file_lock` utilizes `fcntl.flock(LOCK_EX)` on POSIX/macOS and `threading.RLock()` internally. Reentrant state tracking eliminates nested deadlocks.
3. **Atomic JSON Writes:** Data writes create a temporary file in `data/`, flush and sync to disk (`os.fsync`), and atomically replace (`os.replace`) the destination file. No partial or corrupted files can occur.
4. **Git Privacy:** `.gitignore` excludes `data/*.json`, `data/*.bak*`, `data/*.tmp*`, and `.env*`. No personal contact details or application histories are committed.
5. **Legacy Review Workflow:** Older records lacking `candidate_id` are backed up to a timestamped `.bak` file and quarantined as `legacy_unassigned` for explicit assignment rather than being silently merged.

---

## 🧪 Running Tests & Quality Checks

Run the complete backend test suite:
```bash
make test
# OR
.venv/bin/pytest tests/ -v
```
**Current status: 26/26 tests passing.**

Run frontend linting & production build:
```bash
# Frontend linting
npm --prefix frontend run lint

# Production build
npm --prefix frontend run build
```

---

## 📡 API Endpoints Reference

### Jobs & Discovery
* `GET /api/v1/jobs`: Aggregated job postings with filters (`keyword`, `location`, `category`, `min_score`, `candidate_id`).
* `GET /health`: System health and active candidate status.

### Candidate Profiles
* `GET /api/v1/profiles`: List all candidates and active indicator.
* `GET /api/v1/profiles/active`: Retrieve active candidate metadata.
* `POST /api/v1/profiles`: Create a new validated candidate profile.
* `PUT /api/v1/profiles/{id}/activate`: Switch active candidate.
* `DELETE /api/v1/profiles/{id}`: Delete custom candidate (default Anser profile is protected).

### Application Tracker (ATS)
* `GET /api/v1/tracker`: List tracked jobs for candidate (`candidate_id`, `status`).
* `POST /api/v1/tracker`: Save or update tracked job item.
* `GET /api/v1/tracker/{tracker_id}`: Retrieve single tracked application.
* `PATCH /api/v1/tracker/{tracker_id}/status`: Update stage (`saved`, `pending_approval`, `applied`, `interview`, etc.).
* `DELETE /api/v1/tracker/{tracker_id}`: Delete tracked application.
* `GET /api/v1/tracker/legacy/unassigned`: Review legacy unassigned applications.
* `POST /api/v1/tracker/legacy/{tracker_id}/assign`: Safely assign a legacy record to a candidate.

### Generation & Email
* `POST /api/v1/generate/application`: Generate tailored CV bullets, cover letter, and recruiter email.
* `GET /api/v1/email/digest/preview`: Preview daily job digest HTML.
* `POST /api/v1/email/digest/send`: Trigger daily job digest dispatch.
* `POST /api/v1/email/approve-and-send`: Send outreach email with mandatory approval check.

---

## 🇵🇰 Roman Urdu Quick Guide

Yeh assistant Anser Nawaz (aur deegar custom candidates) k liye Lahore aur International Remote jobs discover aur apply karne k liye banaya gaya hai.

### Chalane ka tareeqa:
1. Terminal me project folder kholein aur command chalayein:
   ```bash
   make dev
   ```
2. Browser me `http://localhost:3000` open karein.

### Main Kaam aur Features:
* **Jobs Dhoondna:** Category (Mobile, Frontend, Backend, Full-stack) aur Location (Lahore ya Remote) select karein. Har job k sath match percentage show hogi.
* **Candidate Badalna:** Top navigation bar me **👤 Switch Candidate** par click karein. Aap Anser Nawaz se kisi doosre developer par switch kar saktay hain ya naya profile add kar saktay hain.
* **CV aur Cover Letter:** Job card par **✨ Tailor Application** click karein. System factual resume bullets aur custom cover letter bana kar dega.
* **Tracker Board:** Jobs ko Bookmark karein ya status change karein (`Applied`, `Interview`, `Follow-up`). Har candidate ka tracker alag aur mehfooz rehta hai.
* **Email Bhejna:** Recruiter email k liye pehle approval checkbox tick karein phir send button dabayein. Agar SMTP setup nahi hai to safe dry-run mode me save ho jata hai.
