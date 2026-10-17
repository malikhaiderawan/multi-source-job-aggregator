# 🚀 Multi-Source Job Aggregator & Automated Application Gateway
### Complete Architecture, Setup Guide, Workflow Diagrams & UI Button Reference Manual

> **Welcome!** Ye document is project ko zero se run karne, har component ko samajhne, aur har UI button ka maqsad janne ke liye banaya gaya hai. Chahe aap is repository ko pehli baar clone kar rahe ho ya production me deploy karna chahein, is file me step-by-step sari commands, system diagrams aur button flows mojood hain.

---

## 📑 Table of Contents
1. [⚡ Quick Start Guide (Run in 3 Minutes)](#1--quick-start-guide-run-in-3-minutes)
2. [🏗️ System Architecture & Data Flow](#2-️-system-architecture--data-flow)
   - [High-Level Architecture](#high-level-architecture)
   - [Job Ingestion & Scoring Flow](#job-ingestion--scoring-flow)
   - [Application Tailoring & ATS Tracker Flow](#application-tailoring--ats-tracker-flow)
3. [🔘 Complete UI & Button Action Map](#3--complete-ui--button-action-map)
   - [Top Navigation Bar](#top-navigation-bar)
   - [Header & Ingestion Controls](#header--ingestion-controls)
   - [Category Tabs & Filtering Controls](#category-tabs--filtering-controls)
   - [Job Card Action Buttons](#job-card-action-buttons)
   - [Tailor ✨ Application Modal Buttons](#tailor--application-modal-buttons)
   - [Tracker Page Buttons & Features](#tracker-page-buttons--features)
4. [⚙️ Configuration & Environment Variables (.env)](#4-️-configuration--environment-variables-env)
   - [Gmail IMAP Setup (LinkedIn & Indeed Alerts)](#gmail-imap-setup-linkedin--indeed-alerts)
   - [Hostinger SMTP Setup (Direct Recruiter Outreach)](#hostinger-smtp-setup-direct-recruiter-outreach)
5. [🧪 Testing & Verification](#5--testing--verification)
6. [📂 Folder Structure Reference](#6--folder-structure-reference)
7. [🛠️ Troubleshooting & Common Fixes](#7-️-troubleshooting--common-fixes)

---

## 1. ⚡ Quick Start Guide (Run in 3 Minutes)

### Prerequisites (Zaroori Cheezein)
- **Python**: Version 3.9 ya higher (`python3 --version`)
- **Node.js**: Version 18 ya higher (`node -v`)
- **Git**: Installed on your system (`git --version`)

---

### Step 1: Repository Clone Karein
```bash
git clone https://github.com/malikhaiderawan/multi-source-job-aggregator.git
cd multi-source-job-aggregator
```

---

### Step 2: Environment File Configure Karein
```bash
# Example file ko copy karke .env banayein
cp .env.example .env
```
Apni `.env` file ko kisi bhi text editor (VS Code, Nano, etc.) me open karein aur zaroori credentials enter karein:
- **Gmail IMAP App Password**: Agar aap LinkedIn/Indeed alerts sync karna chahte hain.
- **Hostinger SMTP Password**: Agar aap recruiter emails live send karna chahte hain (warna dry-run simulation mode me safe chalega).

---

### Step 3: Backend Setup (Python Virtual Environment)
```bash
# 1. Virtual environment create karein
python3 -m venv .venv

# 2. Virtual environment activate karein
# macOS / Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 3. Required packages install karein
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Frontend Setup (Next.js & Tailwind CSS)
```bash
# Frontend directory me jayein aur npm dependencies install karein
cd frontend
npm install
cd ..
```

---

### Step 5: Start the Application (2 Easy Options)

#### Option A: One-Click Startup Script (Recommended)
Project root me ek executable bash script mojood hai jo backend aur frontend dono ko saath start kar deta hai:
```bash
chmod +x dev.sh
./dev.sh
```

#### Option B: Two Separate Terminals
**Terminal 1 (Backend FastAPI):**
```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```
*Backend runs at: [http://localhost:8000](http://localhost:8000) (Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs))*

**Terminal 2 (Frontend Next.js):**
```bash
cd frontend
npm run dev
```
*Frontend runs at: [http://localhost:3000](http://localhost:3000)*

Ab apna browser kholein aur visit karein: **[http://localhost:3000](http://localhost:3000)** 🎉

---

## 2. 🏗️ System Architecture & Data Flow

### High-Level Architecture
```mermaid
graph TD
    subgraph Client ["Client Browser (Next.js 14)"]
        UI["Modern Dashboard (Tailwind CSS)"]
        Discover["/ (Job Discovery & Matching)"]
        Tracker["/tracker (ATS Application Funnel)"]
    end

    subgraph BackendGateway ["Backend API (FastAPI)"]
        API["FastAPI App (main.py)"]
        RouterJobs["/api/v1/jobs (Aggregator Router)"]
        RouterTracker["/api/v1/tracker (ATS Router)"]
        RouterProfiles["/api/v1/profiles (Candidate Router)"]
        RouterEmail["/api/v1/email (SMTP & IMAP Router)"]
        RouterGen["/api/v1/generate (Tailored AI Engine)"]
    end

    subgraph CoreServices ["Core Intelligence Engine"]
        Aggregator["Multi-Source Aggregator"]
        Deduplicator["Smart Deduplicator (URL + Title/Company)"]
        LocationClassifier["Location Classifier (Lahore / PK / Remote)"]
        MatchingEngine["Candidate Scoring Engine (60-100% Match)"]
        TailoredGen["Strict Pitch Generator (Zero Hallucinations)"]
    end

    subgraph ExternalSources ["External Data Sources"]
        LinkedInIMAP["LinkedIn Job Alerts (IMAP SSL 993)"]
        IndeedIMAP["Indeed Job Alerts (IMAP SSL 993)"]
        MustakbilWeb["Mustakbil Pakistan (Async Scraper)"]
        JoobleAPI["Jooble API (Global & PK)"]
        RemotiveAPI["Remotive (Remote Tech Jobs)"]
        JobicyAPI["Jobicy (Global Remote)"]
        ArbeitnowAPI["Arbeitnow (Remote / EU)"]
        WWR["WeWorkRemotely RSS/API"]
    end

    subgraph Storage ["Local High-Performance Storage (data/)"]
        JobStore[("linkedin_jobs.json (Email Ingestion Store)")]
        TrackerStore[("tracker_applications.json (ATS Funnel)")]
        ProfileStore[("candidate_profiles.json (Active Profiles)")]
        SentLogs[("sent_emails.json (Audit Trail)")]
    end

    UI --> Discover
    UI --> Tracker
    Discover --> RouterJobs
    Discover --> RouterEmail
    Discover --> RouterGen
    Tracker --> RouterTracker
    UI --> RouterProfiles

    RouterJobs --> Aggregator
    Aggregator --> LinkedInIMAP
    Aggregator --> IndeedIMAP
    Aggregator --> MustakbilWeb
    Aggregator --> JoobleAPI
    Aggregator --> RemotiveAPI
    Aggregator --> JobicyAPI
    Aggregator --> ArbeitnowAPI
    Aggregator --> WWR

    Aggregator --> Deduplicator
    Deduplicator --> LocationClassifier
    LocationClassifier --> MatchingEngine
    MatchingEngine --> JobStore
    RouterTracker --> TrackerStore
    RouterProfiles --> ProfileStore
    RouterEmail --> SentLogs
    RouterGen --> TailoredGen
    TailoredGen --> ProfileStore
```

---

### Job Ingestion & Scoring Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as User / Candidate
    participant UI as Frontend (localhost:3000)
    participant API as FastAPI (routes_jobs)
    participant IMAP as IMAP Client (Gmail SSL)
    participant Dedupe as Deduplicator Engine
    participant Engine as Matching Engine
    participant Cache as linkedin_jobs.json

    User->>UI: Clicks "Sync Emails"
    UI->>API: POST /api/v1/email/sync-alerts
    API->>IMAP: Connects via TLS to imap.gmail.com:993
    IMAP->>IMAP: Parses LinkedIn & Indeed Job Alert emails
    IMAP-->>API: Extracted structured positions
    API->>Cache: Persists verified alerts with file locks
    API-->>UI: Sync Complete (count of alerts ingested)

    User->>UI: Clicks "Refresh Jobs" (or page loads)
    UI->>API: GET /api/v1/jobs?candidate_id=anser_nawaz
    API->>Cache: Reads local verified alerts
    API->>API: Fetches parallel open job APIs (Remotive, Jobicy, Mustakbil, Jooble, etc.)
    API->>Dedupe: Normalizes URLs, removes duplicate titles & companies
    API->>Engine: Evaluates Skills, Seniority, and Location Eligibility
    Engine->>Engine: Lahore Local = 100%, PK Remote = 95%, Non-Lahore Onsite = 6% (Penalized)
    Engine-->>UI: Returns sorted jobs by Match Score descending
    UI-->>User: Displays cards with badges (e.g. 79% Match, 📍 Lahore On-site)
```

---

### Application Tailoring & ATS Tracker Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as User / Candidate
    participant Card as Job Card
    participant Modal as ApplicationModal (Tailor ✨)
    participant Gen as Tailored Generator
    participant SMTP as Hostinger SMTP (Port 465 SSL)
    participant ATS as Tracker Store

    User->>Card: Clicks "Tailor ✨"
    Card->>Modal: Opens tailored application modal
    Modal->>Gen: POST /api/v1/generate/tailor
    Gen->>Gen: Formats genuine candidate experience (No hallucinations!)
    Gen-->>Modal: Returns (1) Tailored CV Bullets, (2) Cover Letter, (3) Recruiter Pitch
    
    User->>Modal: Reviews text, picks Tone (Professional/Confident/Direct)
    alt Manual Apply
        User->>Modal: Clicks "Copy to Clipboard"
        User->>Card: Clicks "Job Link / Apply" -> Applies on portal
        User->>Card: Clicks "Mark Applied"
        Card->>ATS: Updates status to "applied"
    else Automated SMTP Outreach
        User->>Modal: Checks "I confirm review of this email"
        User->>Modal: Clicks "Send Application via SMTP"
        Modal->>SMTP: POST /api/v1/email/send-application
        SMTP->>SMTP: Connects via SSL to smtp.hostinger.com:465
        SMTP->>SMTP: Sends From: "Anser Nawaz <anser@malikaxiomtech.com>"
        SMTP-->>Modal: Sent successfully (or dry-run simulated)
        Modal->>ATS: Automatically creates tracked application in "applied" stage
    end
    ATS-->>User: Badge changes to "✓ Applied", viewable in /tracker
```

---

## 3. 🔘 Complete UI & Button Action Map

Har ek button aur interactive element ka function neeche detail se samjhaya gaya hai taake koi bhi confusion na rahe:

### Top Navigation Bar
| UI Element | Type | Maqsad aur Kaam |
| :--- | :--- | :--- |
| **Discover** | Nav Link | Main job discovery portal par le jata hai jahan multi-platform jobs (LinkedIn, Indeed, Jooble, etc.) score ho kar aati hain. |
| **Tracker** | Nav Link | Personal ATS Kanban Board (`/tracker`) par le jata hai jahan aap applied, interviewing, saved, aur offer stages ko manage karte hain. |
| **Active Candidate Badge** *(e.g. "Anser Nawaz (6+ Years)")* | Interactive Modal Trigger | Is par click karne se **Profile Switcher Modal** khulta hai. Aap multiple candidate profiles (Anser Nawaz, Haider Nawaz, ya naya custom profile) switch kar sakte hain. Switch karte hi sari jobs naye candidate ke skills aur experience ke mutabiq re-score ho jati hain! |
| **Send Digest** | Action Button | Backend ke `/api/v1/email/send-digest` endpoint ko trigger karta hai. Ye candidate ke profile ke mutabiq **70%+ match** wali top jobs ka khubsurat executive HTML digest generate karke candidate ki email par dispatch karta hai. |

---

### Header & Ingestion Controls
| UI Element | Type | Maqsad aur Kaam |
| :--- | :--- | :--- |
| **Refresh Jobs** | Button (Blue) | Multi-source aggregator ko call karta hai. Open APIs (Remotive, Jobicy, Mustakbil, Jooble, etc.) aur local cache se fresh jobs fetch karta hai, duplicate positions ko remove karta hai, aur real-time scoring recalculate karta hai. |
| **Sync Emails** | Button (Purple) | Background IMAP worker ko trigger karta hai jo Gmail se connect ho kar LinkedIn aur Indeed Job Alert emails scan karta hai. Naye jobs nikaal kar `data/linkedin_jobs.json` me store karta hai taake local market ki genuine jobs show hon. |
| **Skills Pill Badges** *(React Native, Flutter, Next.js, Node.js...)* | Tag Badges | Active candidate ke verified primary skills ko represent karte hain jin ki buniyad par scoring algorithm matching score calculate karta hai. |

---

### Counter Cards (Metrics Bar)
- **Total Positions**: Deduplication ke baad available total valid jobs ki taadad.
- **Lahore Local**: Lahore on-site aur hybrid jobs ki taadad (Highest priority for local candidates).
- **Pakistan Remote**: Pakistan-wide remote positions jo verified hain.
- **Worldwide Remote**: International remote positions jahan Pakistani engineers legally eligible hain.
- **Tracked In ATS**: Aap ke personal job tracker me kitni applications track ho chuki hain.

---

### Category Tabs & Filtering Controls
| UI Element | Maqsad |
| :--- | :--- |
| **Category Tabs** *(All, Mobile, Frontend, Backend, Full-Stack & Lead)* | One-click filter jo specialized engineering domains ko isolate karta hai. Agar aap sirf React Native/Flutter chahein toh **Mobile** par click karein. |
| **Eligibility Dropdown** | Filter karta hai: All Regions, 📍 Lahore On-site / Hybrid, 🇵🇰 Pakistan (Local & Remote), 🌐 Worldwide Remote, ❓ Unconfirmed Remote. |
| **Keywords / Skills Search** | Title ya description me live search karta hai (e.g., "GraphQL", "Docker", "Python"). |
| **Location Input** | Specific city ya country filter karne ke liye (e.g., "Lahore", "Remote", "Dubai"). |
| **Min Match % Slider** | Minimum match score threshold set karta hai (e.g. 75%+). Is se low-match ya irrelevant positions hide ho jati hain. |
| **Provider Dropdown** | Specific platform filter karne ke liye (LinkedIn Alert, Indeed Alert, Mustakbil, Remotive, Jooble, etc.). |
| **Quick Filter Pills** *(📍 Lahore, 🇵🇰 Pakistan, 🌐 Remote)* | Ek click me popular locations filter karne ke shortcut buttons. |
| **Clear all filters** | Tamam active filters ko reset karke default state par le aata hai. |

---

### Job Card Action Buttons
| UI Element | Maqsad |
| :--- | :--- |
| **Tailor ✨** *(or Tailor Application)* | **Sab se powerful feature!** Is par click karte hi AI application generator active candidate ke verified profile (6+ years experience, genuine projects like AfroTech, Fofo, KNO, Blockonaire) ka customized cover letter, CV bullet points aur recruiter pitch generate karta hai. Koi fake data invent nahi karta! |
| **Mark Applied** | Job ko bina modal khole direct aap ke ATS Tracker me "Applied" stage par move kar deta hai. Card par status update ho kar **"✓ Applied"** ho jata hai. |
| **View Pitch** | Agar job pehle se applied/tracked hai, toh ye button show hota hai. Is par click karke aap tailored application text aur notes dobara dekh sakte hain. |
| **Job Link / Apply** | Original job posting (LinkedIn, Indeed, Company website) ko new browser tab me open karta hai taake aap direct apply kar sakein. |

---

### Tailor ✨ Application Modal Buttons
| UI Element | Maqsad |
| :--- | :--- |
| **Tone Selector** *(Professional / Confident / Direct)* | Generated cover letter aur recruiter email ka tone switch karta hai. |
| **Content Tabs** *(Cover Letter, Recruiter Email, CV Bullets)* | Cover letter, short recruiter email, aur tailored resume bullet points ke darmiyan switch karta hai. |
| **Copy to Clipboard** | Pure text ko one-click copy karta hai taake aap portal par paste kar sakein. |
| **Approval Checkbox** | Safety gate! Ye ensure karta hai ke user ne email pitch review kar li hai. Bina checkbox select kiye automated email dispatch enable nahi hoti. |
| **Send Application via SMTP** | Hostinger SMTP (`smtp.hostinger.com:465 SSL`) ke zariye recruiter ko direct email dispatch karta hai with professional header: `From: Anser Nawaz <anser@malikaxiomtech.com>`. Agar credentials na hon, toh ye safety dry-run simulation me chalti hai. |
| **Track Application / Save to ATS** | Job ko custom notes aur stage (`saved`, `applied`, `interviewing`, `offer`) ke saath ATS database me save karta hai. |

---

### Tracker Page Buttons & Features (`/tracker`)
| UI Element | Maqsad |
| :--- | :--- |
| **Kanban Board View** | Drag-and-drop ya dropdown cards ke zariye job applications ko 5 stages me organize karta hai: `Saved`, `Applied`, `Interviewing`, `Offer`, `Rejected`. |
| **Table View** | Applications ko structured tabular format me show karta hai with salary, match score, company, date, aur direct links. |
| **Stage Dropdown** | Kisi bhi application ka status foran change karta hai (e.g. Applied se Interviewing). |
| **Notes & Salary Input** | Interview rounds, contact person, aur expected salary save karne ki suvidha deta hai. |

---

## 4. ⚙️ Configuration & Environment Variables (.env)

Project root me `.env` file tamam external services ko control karti hai:

```bash
# ==============================================================
# 1. Search & API Integration Keys (Optional)
# ==============================================================
BRAVE_SEARCH_API_KEY=""
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SERPER_API_KEY="af3b851937396b936aa328e72fc1b3735ed9a126"
JOOBLE_API_KEY="c05c4df6-25b4-4602-b38f-8f89feaaf0ab"

# ==============================================================
# 2. Candidate Profile & Sender Details
# ==============================================================
CANDIDATE_NAME="Anser Nawaz"
CANDIDATE_EMAIL="anser@malikaxiomtech.com"
CANDIDATE_PHONE="+92 305 4100126"
CANDIDATE_LOCATION="Lahore, Punjab, Pakistan"

SENDER_NAME="Anser Nawaz"
SENDER_EMAIL="anser@malikaxiomtech.com"
SENDER_TITLE="Co-Founder & CTO | Lead Engineer"
SENDER_COMPANY="MalikAxiom Technology"
SENDER_WEBSITE="https://malikaxiomtech.com"
SENDER_PORTFOLIO="https://contra.com/ansernawaz786"
SENDER_POSTAL_ADDRESS="Lahore, Punjab, Pakistan"

# ==============================================================
# 3. Email Digest & Notification Settings
# ==============================================================
DIGEST_RECIPIENT_EMAIL="ansernawaz786@gmail.com"
DIGEST_MIN_MATCH_SCORE=70

# ==============================================================
# 4. Outgoing SMTP (Hostinger / Custom Domain)
# ==============================================================
SMTP_HOST="smtp.hostinger.com"
SMTP_PORT=465
SMTP_USER="hello@malikaxiomtech.com"
SMTP_USERNAME="hello@malikaxiomtech.com"
SMTP_PASS=""     # <-- Apni Hostinger email ka password yahan enter karein!

# ==============================================================
# 5. Incoming Job Alerts (Gmail IMAP Ingestion)
# ==============================================================
LINKEDIN_ALERT_IMAP_SERVER="imap.gmail.com"
LINKEDIN_ALERT_IMAP_PORT=993
LINKEDIN_ALERT_EMAIL_USER="ansernawaz786@gmail.com"
LINKEDIN_ALERT_EMAIL_PASS="pcss dvhb onjq ruti"  # Gmail 16-digit App Password
LINKEDIN_ALERT_IMAP_FOLDER="INBOX"
LINKEDIN_ALERT_MARK_READ=false

# ==============================================================
# 6. Frontend URL
# ==============================================================
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

---

### Gmail IMAP Setup (LinkedIn & Indeed Alerts)
LinkedIn aur Indeed Job Alerts ko automate karne ke liye Gmail ka **App Password** use hota hai:
1. Apne Google Account me jayein: [myaccount.google.com/security](https://myaccount.google.com/security).
2. **2-Step Verification** enable karein.
3. Search bar me type karein **App Passwords**.
4. App name me likhein `JobAggregator` aur **Create** click karein.
5. Google aapko 16-character ka code dega (e.g. `pcss dvhb onjq ruti`). Is code ko `.env` me `LINKEDIN_ALERT_EMAIL_PASS` me paste kar dein.

---

### Hostinger SMTP Setup (Direct Recruiter Outreach)
Hostinger email se outgoing pitches bhejne ke liye:
- `SMTP_HOST`: `smtp.hostinger.com`
- `SMTP_PORT`: `465` (SSL security ke saath)
- `SMTP_USERNAME`: `hello@malikaxiomtech.com`
- `SMTP_PASS`: Aapki Hostinger mailbox ka password.
- Application automatically `From: Anser Nawaz <anser@malikaxiomtech.com>` header set karti hai with `Reply-To: anser@malikaxiomtech.com`.

---

## 5. 🧪 Testing & Verification

Project me **54 automated unit aur integration tests** shamil hain jo scoring algorithm, location filtering, candidate isolation, email dispatch safety, aur deduping ko verify karte hain.

Tests run karne ke liye:
```bash
# Virtual environment activate karein
source .venv/bin/activate

# Pure test suite ko execute karein
pytest tests/ -v
```

Expected output:
```text
============================== 54 passed in 4.32s ==============================
```

Frontend build verify karne ke liye:
```bash
cd frontend
npm run build
```

---

## 6. 📂 Folder Structure Reference

```text
multi-source-job-aggregator/
├── app/
│   ├── api/v1/                   # FastAPI REST Endpoints
│   │   ├── routes_jobs.py        # /jobs - Aggregation & Filtering
│   │   ├── routes_tracker.py     # /tracker - ATS CRUD Operations
│   │   ├── routes_profiles.py    # /profiles - Candidate Switcher
│   │   ├── routes_generate.py    # /generate - Tailored Application Engine
│   │   └── routes_email.py       # /email - SMTP Dispatch & IMAP Sync
│   ├── clients/                  # API & Scraping Connectors
│   │   ├── linkedin_email_client.py # IMAP Parser (LinkedIn + Indeed)
│   │   ├── mustakbil_client.py   # Mustakbil.com Scraper (Lahore/PK)
│   │   ├── jooble_client.py      # Jooble API
│   │   ├── remotive_client.py    # Remotive Remote API
│   │   ├── jobicy_client.py      # Jobicy Remote API
│   │   ├── arbeitnow_client.py   # Arbeitnow Tech API
│   │   └── wwr_client.py         # WeWorkRemotely RSS/API
│   ├── models/                   # Pydantic Schemas
│   │   ├── job.py                # JobPosting, MatchBreakdown, Application
│   │   └── profile.py            # CandidateProfile, Experience, Projects
│   ├── services/                 # Intelligence & Business Logic
│   │   ├── aggregator.py         # Multi-Source Coordinator
│   │   ├── deduplicator.py       # URL & Title/Company Deduping
│   │   ├── location_classifier.py# Lahore / Pakistan / Remote Classifier
│   │   ├── matching_engine.py    # 60-100% Experience & Seniority Scoring
│   │   ├── tailored_generator.py # Strict Zero-Hallucination Pitch Generator
│   │   └── email_service.py      # Hostinger SMTP & Digest Dispatcher
│   └── storage/                  # Thread-Safe File Storage
│       ├── file_utils.py         # Cross-platform File Locking (fcntl)
│       ├── linkedin_job_store.py # Ingested Alert Database
│       ├── tracker_store.py      # ATS Kanban Applications Database
│       └── profile_store.py      # Candidate Profile Store & Switcher
├── frontend/
│   ├── app/                      # Next.js 14 App Router
│   │   ├── page.tsx              # Main Job Discovery Dashboard
│   │   ├── tracker/page.tsx      # ATS Kanban & Table Board
│   │   └── layout.tsx            # Global Layout & Fonts
│   ├── components/
│   │   ├── JobCard.tsx           # Interactive Job Card with Match Badges
│   │   ├── Navbar.tsx            # Top Navbar with Digest & Candidate Switcher
│   │   ├── ApplicationModal.tsx  # Tailor Application Modal & SMTP Sender
│   │   └── ProfileSwitcherModal.tsx # Candidate Switcher Dialog
│   ├── lib/
│   │   └── api-client.ts         # Axios/Fetch API Gateway Client
│   └── types/
│       └── job.ts                # TypeScript Interfaces
├── data/                         # Local Data Store (Auto-generated)
│   ├── candidate_profiles.json   # Candidates Profile State
│   ├── linkedin_jobs.json        # Ingested Alert Cache
│   ├── tracker_applications.json # Saved ATS Applications
│   └── sent_emails.json          # Audit Logs of Dispatched Pitches
├── tests/                        # 54 Pytest Integration & Unit Tests
├── .env.example                  # Environment Variables Template
├── dev.sh                        # One-Click Development Startup Script
├── main.py                       # FastAPI Application Entrypoint
├── pytest.ini                    # Pytest Configuration
├── requirements.txt              # Python Dependencies
├── README.md                     # General Project Summary
└── MAIN.md                       # Complete Learning & Architecture Manual (This File)
```

---

## 7. 🛠️ Troubleshooting & Common Fixes

### 1. Port 8000 ya 3000 pehle se use me hai (`Address already in use`)
Agar aapko error aaye ke port occupied hai, toh terminal me ye command chala kar process kill kar sakte hain:
```bash
# Port 8000 (Backend) kill karein:
lsof -ti:8000 | xargs kill -9

# Port 3000 (Frontend) kill karein:
lsof -ti:3000 | xargs kill -9
```

### 2. Gmail IMAP Authentication Error
- Ensure karein ke aap regular Gmail password nahi balke **16-digit Google App Password** use kar rahe hain.
- Ensure karein ke `LINKEDIN_ALERT_IMAP_SERVER="imap.gmail.com"` aur `LINKEDIN_ALERT_IMAP_PORT=993` configured hai.

### 3. Hostinger SMTP Error
- Hostinger port `465` SSL connection use karta hai. Ensure karein ke aapka `.env` me `SMTP_PORT=465` set hai.
- Agar aap password enter nahi karte, toh system crash nahi hota balke safely **dry-run simulation mode** me run hota hai aur audit log `data/sent_emails.json` me save ho jata hai.

### 4. Candidates Profile Reset ya Change karna
Agar aap profiles ko default state par lana chahte hain, toh `data/candidate_profiles.json` delete kar dein. Backend agle restart par automatically dono fresh profiles (`anser_nawaz` aur `haider_nawaz`) generate kar dega.

---

### 💡 Summary For Brother / Collaborator:
> **Bhai ke liye quick note:**
> 1. Repo clone karein: `git clone https://github.com/malikhaiderawan/multi-source-job-aggregator.git`
> 2. `cp .env.example .env` karein.
> 3. `./dev.sh` run karein (ye script Python venv aur frontend packages khud check karke dono ko run kar dega).
> 4. Browser me `http://localhost:3000` open karein aur job hunting enjoy karein! 🚀
