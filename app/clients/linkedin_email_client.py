import os
import re
import imaplib
import email
import email.message
import email.utils
import html
from email.header import decode_header
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging
from app.models.job import JobPosting, LinkedInSyncResponse
from app.models.profile import ANSER_PROFILE
from app.storage.profile_store import PROFILE_STORE
from app.storage.linkedin_job_store import LINKEDIN_JOB_STORE
from app.services.matching_engine import enrich_job_posting

logger = logging.getLogger("LinkedInEmailClient")

# Regex to find canonical LinkedIn job posting URLs
LINKEDIN_JOB_URL_PATTERN = re.compile(
    r"https?://(?:[a-zA-Z0-9-]+\.)?linkedin\.com/(?:comm/)?jobs/view/(\d+)",
    re.IGNORECASE
)

# Unwanted navigation or settings keywords to ignore
UNWANTED_TITLE_KEYWORDS = [
    "unsubscribe", "manage alert", "settings", "privacy", "help",
    "view all jobs", "see all jobs", "explore more", "email preferences",
    "view job", "apply now", "learn more"
]

# Indeed Job Alert regex patterns
INDEED_JOB_KEY_PATTERN = re.compile(r"[?&]jk=([a-f0-9]+)", re.IGNORECASE)
INDEED_HTML_LINK_PATTERN = re.compile(
    r"<a\s+[^>]*href=[\"']([^\"']*indeed\.com/[^\"']*?[?&]jk=([a-f0-9]+)[^\"']*)[\"'][^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL
)
INDEED_UNWANTED_KEYWORDS = [
    "unsubscribe", "manage alert", "settings", "privacy", "help",
    "view all jobs", "see all jobs", "explore more", "email preferences",
    "edit alert", "create alert", "salaries", "indeed logo", "indeed job alert",
    "job alert", "new jobs", "matching your search", "of new jobs"
]

def decode_mime_header(header_val: Optional[str]) -> str:
    """Decodes MIME encoded headers into a clean unicode string."""
    if not header_val:
        return ""
    decoded_fragments = decode_header(header_val)
    parts = []
    for frag, enc in decoded_fragments:
        if isinstance(frag, bytes):
            try:
                parts.append(frag.decode(enc or "utf-8", errors="replace"))
            except Exception:
                parts.append(frag.decode("latin1", errors="replace"))
        else:
            parts.append(str(frag))
    return "".join(parts).strip()

def is_trusted_linkedin_sender(from_header: str) -> bool:
    """
    Validates that the email genuinely originates from an authorized LinkedIn domain.
    Filters out untrusted, spoofed, or phishing senders.
    """
    if not from_header:
        return False
    _, addr = email.utils.parseaddr(from_header)
    addr_lower = addr.lower().strip()
    if "@" not in addr_lower:
        return False
    domain = addr_lower.split("@", 1)[1]
    return domain == "linkedin.com" or domain.endswith(".linkedin.com")

def is_trusted_indeed_sender(from_header: str) -> bool:
    """
    Validates that the email genuinely originates from an authorized Indeed domain.
    Filters out untrusted, spoofed, or phishing senders.
    """
    if not from_header:
        return False
    _, addr = email.utils.parseaddr(from_header)
    addr_lower = addr.lower().strip()
    if "@" not in addr_lower:
        return False
    domain = addr_lower.split("@", 1)[1]
    trusted_domains = ("indeed.com", "indeedemail.com", "jobalert.indeed.com")
    return domain in trusted_domains or domain.endswith(".indeed.com") or domain.endswith(".indeedemail.com")

def is_trusted_alert_sender(from_header: str) -> Tuple[bool, str]:
    """
    Validates email origin against trusted job alert domains (LinkedIn & Indeed).
    Returns (is_trusted, provider_type) where provider_type is 'linkedin', 'indeed', or ''.
    """
    if is_trusted_linkedin_sender(from_header):
        return True, "linkedin"
    if is_trusted_indeed_sender(from_header):
        return True, "indeed"
    return False, ""

def extract_jobs_from_html(html_content: str, date_str: str = "") -> List[Dict[str, Any]]:
    """
    Extracts real job postings from official LinkedIn Job Alert HTML emails.
    Extracts job title, company name, location string, canonical link, and timestamp.
    """
    extracted: List[Dict[str, Any]] = []
    seen_ids = set()

    # Pattern finding <a> tags linking to jobs/view/<job_id>
    link_pattern = re.compile(
        r"<a\s+[^>]*href=[\"']([^\"']*linkedin\.com/(?:comm/)?jobs/view/(\d+)[^\"']*)[\"'][^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL
    )

    for m in link_pattern.finditer(html_content):
        _, job_id, inner_html = m.groups()
        if job_id in seen_ids:
            continue

        raw_title = re.sub(r"<[^>]+>", " ", inner_html).strip()
        raw_title = html.unescape(raw_title)
        raw_title = re.sub(r"\s+", " ", raw_title)
        raw_title = re.sub(r"\s*Easy Apply\s*$", "", raw_title, flags=re.IGNORECASE).strip()

        if not raw_title or any(kw in raw_title.lower() for kw in UNWANTED_TITLE_KEYWORDS):
            continue

        # Look in the adjacent HTML container chunk following this link for Company and Location
        sub = html_content[m.end():]
        boundary = re.search(r"(</div>\s*</div>|</tr>|</td>|<a\s)", sub, re.IGNORECASE)
        after_chunk = sub[:boundary.start()] if boundary else sub[:300]
        clean_after = re.sub(r"<[^>]+>", " ", after_chunk).strip()
        clean_after = html.unescape(clean_after)
        clean_after = re.sub(r"\s+", " ", clean_after)

        company = "Unspecified Company"
        location = "Unspecified Location"

        # Check for middle-dot separator: "Company · Location"
        dot_match = re.search(r"([A-Za-z0-9\s.,&'/\-]+?)\s*·\s*([A-Za-z0-9\s.,()/'\-]+)", clean_after)
        if dot_match:
            cand_comp = dot_match.group(1).strip()
            cand_loc = dot_match.group(2).strip()
            if cand_comp and not any(kw in cand_comp.lower() for kw in UNWANTED_TITLE_KEYWORDS):
                company = cand_comp
            if cand_loc and not any(kw in cand_loc.lower() for kw in UNWANTED_TITLE_KEYWORDS):
                location = cand_loc

        # If raw_title itself contains "·" (e.g. "Software Engineer Devsinc · Lahore (On-site)")
        if "·" in raw_title:
            title_parts = [p.strip() for p in raw_title.split("·", 1)]
            if len(title_parts) == 2:
                raw_title = title_parts[0]
                if location == "Unspecified Location" or not location:
                    location = title_parts[1]

        seen_ids.add(job_id)
        clean_url = f"https://www.linkedin.com/jobs/view/{job_id}"
        extracted.append({
            "job_id": job_id,
            "title": raw_title,
            "company": company,
            "location": location,
            "url": clean_url,
            "posted_date": date_str
        })

    return extracted

def extract_jobs_from_text(plain_content: str, date_str: str = "") -> List[Dict[str, Any]]:
    """
    Extracts job postings from official LinkedIn Job Alert plain text emails.
    """
    extracted: List[Dict[str, Any]] = []
    seen_ids = set()

    lines = [l.strip() for l in plain_content.splitlines() if l.strip()]

    for idx, line in enumerate(lines):
        m = LINKEDIN_JOB_URL_PATTERN.search(line)
        if not m:
            continue

        job_id = m.group(1)
        if job_id in seen_ids:
            continue

        # Look backwards up to 4 lines for title and company/location
        candidates = []
        for back_idx in range(idx - 1, max(-1, idx - 5), -1):
            prev = lines[back_idx]
            if "linkedin.com" in prev or "http" in prev:
                break
            if any(kw in prev.lower() for kw in ["view job", "manage alert", "see all", "unsubscribe"]):
                continue
            candidates.insert(0, prev)

        title = "Untitled Role"
        company = "Unspecified Company"
        location = "Unspecified Location"

        if len(candidates) >= 2:
            company_loc_line = candidates[-1]
            title = candidates[-2]
            if "·" in company_loc_line:
                parts = company_loc_line.split("·", 1)
                company = parts[0].strip()
                location = parts[1].strip()
            elif "," in company_loc_line:
                parts = company_loc_line.split(",", 1)
                company = parts[0].strip()
                location = company_loc_line
            else:
                company = company_loc_line
        elif len(candidates) == 1:
            title = candidates[0]

        if any(kw in title.lower() for kw in UNWANTED_TITLE_KEYWORDS):
            continue

        seen_ids.add(job_id)
        clean_url = f"https://www.linkedin.com/jobs/view/{job_id}"
        extracted.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "url": clean_url,
            "posted_date": date_str
        })

    return extracted

def extract_indeed_jobs_from_html(html_content: str, date_str: str = "") -> List[Dict[str, Any]]:
    """
    Extracts verified job postings from official Indeed Job Alert HTML emails.
    """
    extracted: List[Dict[str, Any]] = []
    seen_ids = set()

    for m in INDEED_HTML_LINK_PATTERN.finditer(html_content):
        full_url, job_id, inner_html = m.groups()
        if job_id in seen_ids:
            continue

        raw_title = re.sub(r"<[^>]+>", " ", inner_html).strip()
        raw_title = html.unescape(raw_title)
        raw_title = re.sub(r"\s+", " ", raw_title)
        raw_title = re.sub(r"\s*Easily apply\s*$", "", raw_title, flags=re.IGNORECASE).strip()

        if not raw_title or len(raw_title) < 2 or any(kw in raw_title.lower() for kw in INDEED_UNWANTED_KEYWORDS):
            continue

        sub = html_content[m.end():m.end() + 1500]
        clean = re.sub(r"<[^>]+>", "\n", sub)
        clean_lines = [l.strip() for l in clean.splitlines() if l.strip() and not l.strip().startswith("<")]

        company = "Indeed Employer"
        location = "Pakistan"
        salary = "Disclosed on Indeed"

        info_lines = []
        for l in clean_lines:
            lower_l = l.lower()
            if any(skip in lower_l for skip in ["easily apply", "urgent", "responsive employer", "active ", "hiring multiple", "just posted"]):
                continue
            if re.match(r"^\d+\+?\s+days?\s+ago$", lower_l) or re.match(r"^today|yesterday$", lower_l):
                continue
            info_lines.append(l)

        if len(info_lines) >= 1:
            company = info_lines[0]
        if len(info_lines) >= 2:
            cand = info_lines[1]
            if any(s_kw in cand.lower() for s_kw in ["rs", "pkr", "month", "year", "$", "a month", "a year"]):
                salary = cand
                if len(info_lines) >= 3:
                    location = info_lines[2]
            else:
                location = cand
                if len(info_lines) >= 3 and any(s_kw in info_lines[2].lower() for s_kw in ["rs", "pkr", "month", "year", "$", "a month"]):
                    salary = info_lines[2]

        if " - " in company:
            c_parts = company.split(" - ", 1)
            company = c_parts[0].strip()
            if location == "Pakistan":
                location = c_parts[1].strip()

        seen_ids.add(job_id)
        canonical_url = f"https://pk.indeed.com/viewjob?jk={job_id}"
        extracted.append({
            "job_id": job_id,
            "title": raw_title,
            "company": company,
            "location": location,
            "salary": salary,
            "url": canonical_url,
            "posted_date": date_str,
            "source": "Indeed Alert"
        })

    return extracted

def extract_indeed_jobs_from_text(plain_content: str, date_str: str = "") -> List[Dict[str, Any]]:
    """
    Extracts job postings from official Indeed Job Alert plain text emails.
    """
    extracted: List[Dict[str, Any]] = []
    seen_ids = set()

    lines = [l.strip() for l in plain_content.splitlines() if l.strip()]

    for idx, line in enumerate(lines):
        m = INDEED_JOB_KEY_PATTERN.search(line)
        if not m or "indeed.com" not in line.lower():
            continue

        job_id = m.group(1)
        if job_id in seen_ids:
            continue

        candidates = []
        for back_idx in range(idx - 1, max(-1, idx - 7), -1):
            prev = lines[back_idx]
            if "indeed.com" in prev or "http" in prev:
                break
            if any(kw in prev.lower() for kw in INDEED_UNWANTED_KEYWORDS) or any(kw in prev.lower() for kw in ["view job", "manage alert", "see all", "unsubscribe", "easily apply"]):
                continue
            candidates.insert(0, prev)

        title = "Untitled Role"
        company = "Indeed Employer"
        location = "Pakistan"
        salary = "Disclosed on Indeed"

        if len(candidates) >= 2:
            title = candidates[0]
            comp_loc = candidates[1]
            if " - " in comp_loc:
                parts = comp_loc.split(" - ", 1)
                company = parts[0].strip()
                location = parts[1].strip()
            elif "," in comp_loc:
                parts = comp_loc.split(",", 1)
                company = parts[0].strip()
                location = comp_loc.strip()
            else:
                company = comp_loc

            if len(candidates) >= 3 and any(s_kw in candidates[2].lower() for s_kw in ["rs", "pkr", "month", "year", "$"]):
                salary = candidates[2]
        elif len(candidates) == 1:
            title = candidates[0]

        if any(kw in title.lower() for kw in INDEED_UNWANTED_KEYWORDS):
            continue

        seen_ids.add(job_id)
        canonical_url = f"https://pk.indeed.com/viewjob?jk={job_id}"
        extracted.append({
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "url": canonical_url,
            "posted_date": date_str,
            "source": "Indeed Alert"
        })

    return extracted

def parse_email_message(msg: email.message.Message) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Parses a single email.message.Message.
    Returns:
        (is_trusted_and_valid, list_of_raw_job_dicts, status_reason)
    """
    from_header = decode_mime_header(msg.get("From", ""))
    is_trusted, provider = is_trusted_alert_sender(from_header)
    if not is_trusted:
        return False, [], f"Rejected untrusted sender: {from_header}"

    date_header = decode_mime_header(msg.get("Date", ""))
    subject_header = decode_mime_header(msg.get("Subject", ""))

    date_str = ""
    if date_header:
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_header)
            date_str = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

    html_payload = ""
    plain_payload = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition", ""))
            if "attachment" in cdisp:
                continue
            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text_content = payload.decode(charset, errors="replace")
                if ctype == "text/html":
                    html_payload += text_content
                elif ctype == "text/plain":
                    plain_payload += text_content
            except Exception as e:
                logger.warning(f"Error decoding email part: {e}")
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text_content = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_payload = text_content
                else:
                    plain_payload = text_content
        except Exception as e:
            logger.warning(f"Error decoding singlepart email: {e}")

    # Prioritize HTML parsing if available, fallback to plain text
    raw_jobs: List[Dict[str, Any]] = []
    if provider == "indeed":
        if html_payload:
            raw_jobs = extract_indeed_jobs_from_html(html_payload, date_str=date_str)
        if not raw_jobs and plain_payload:
            raw_jobs = extract_indeed_jobs_from_text(plain_payload, date_str=date_str)
        for item in raw_jobs:
            item.setdefault("source", "Indeed Alert")
    else:
        if html_payload:
            raw_jobs = extract_jobs_from_html(html_payload, date_str=date_str)
        if not raw_jobs and plain_payload:
            raw_jobs = extract_jobs_from_text(plain_payload, date_str=date_str)
        for item in raw_jobs:
            item.setdefault("source", "LinkedIn Alert")

    return True, raw_jobs, f"Successfully parsed alert '{subject_header}'"

async def sync_linkedin_alert_emails(
    max_emails: int = 25,
    candidate_id: Optional[str] = None
) -> LinkedInSyncResponse:
    """
    Connects to the configured mailbox via secure IMAP/TLS, safely fetches
    LinkedIn Job Alert emails, extracts job postings, enriches them against
    the active candidate profile, and persists them into LINKEDIN_JOB_STORE.
    
    Non-destructive:
    - Never deletes messages.
    - Operates in read-only mode unless LINKEDIN_ALERT_MARK_READ=true.
    - Never stores full email bodies.
    - Never marks extracted jobs as 'applied'.
    """
    imap_server = os.getenv("LINKEDIN_ALERT_IMAP_SERVER", "imap.gmail.com")
    imap_port = int(os.getenv("LINKEDIN_ALERT_IMAP_PORT", "993"))
    email_user = (os.getenv("LINKEDIN_ALERT_EMAIL_USER") or "").strip()
    email_pass = (os.getenv("LINKEDIN_ALERT_EMAIL_PASS") or "").replace(" ", "").strip()
    imap_folder = os.getenv("LINKEDIN_ALERT_IMAP_FOLDER", "INBOX")
    mark_read = os.getenv("LINKEDIN_ALERT_MARK_READ", "false").lower() in ("true", "1", "yes")

    if not email_user or not email_pass:
        logger.info("LinkedIn Job Alert Ingestion: LINKEDIN_ALERT_EMAIL_USER or LINKEDIN_ALERT_EMAIL_PASS not configured.")
        return LinkedInSyncResponse(
            status="missing_credentials",
            message="Mailbox credentials not configured. Please set LINKEDIN_ALERT_EMAIL_USER and LINKEDIN_ALERT_EMAIL_PASS in .env to enable automated email alert sync.",
            emails_scanned=0,
            jobs_extracted=0,
            unique_jobs_added=0,
            duplicates_skipped=0,
            failures=0,
            eligibility_count={},
            jobs=[]
        )

    # Resolve active candidate profile for scoring
    target_profile = None
    if candidate_id:
        target_profile = PROFILE_STORE.get_profile(candidate_id)
    if not target_profile:
        target_profile = PROFILE_STORE.get_active_profile()

    emails_scanned = 0
    jobs_extracted = 0
    failures = 0
    extracted_jobs: List[JobPosting] = []

    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_user, email_pass)

        # Non-destructive by default: use readonly=True unless mark_read is explicitly enabled
        select_status, _ = mail.select(imap_folder, readonly=(not mark_read))
        if select_status != "OK":
            raise RuntimeError(f"Could not select IMAP folder '{imap_folder}'")

        # Search for LinkedIn and Indeed alert emails
        msg_id_set = set()
        for sender_query in ['(FROM "linkedin.com")', '(FROM "indeed.com")']:
            try:
                search_status, msg_nums = mail.search(None, sender_query)
                if search_status == "OK" and msg_nums and msg_nums[0]:
                    for num in msg_nums[0].split():
                        try:
                            msg_id_set.add(int(num))
                        except ValueError:
                            pass
            except Exception as q_err:
                logger.warning(f"IMAP search error for {sender_query}: {q_err}")

        if not msg_id_set:
            search_status, msg_nums = mail.search(None, 'ALL')
            if search_status == "OK" and msg_nums and msg_nums[0]:
                for num in msg_nums[0].split():
                    try:
                        msg_id_set.add(int(num))
                    except ValueError:
                        pass

        if not msg_id_set:
            mail.logout()
            return LinkedInSyncResponse(
                status="success",
                message=f"Connected to {imap_server}:{imap_folder}. No matching alert messages found.",
                emails_scanned=0,
                jobs_extracted=0,
                unique_jobs_added=0,
                duplicates_skipped=0,
                failures=0,
                eligibility_count={},
                jobs=[]
            )

        sorted_nums = sorted(list(msg_id_set))
        # Process the most recent messages up to max_emails
        target_ids = [str(n).encode() for n in sorted_nums[-max_emails:]]
        target_ids.reverse()

        for num in target_ids:
            emails_scanned += 1
            fetch_status, data = mail.fetch(num, "(RFC822)")
            if fetch_status != "OK" or not data or not data[0]:
                failures += 1
                continue

            raw_email_bytes = data[0][1]
            try:
                msg = email.message_from_bytes(raw_email_bytes)
            except Exception as parse_err:
                logger.warning(f"Failed to parse email message bytes: {parse_err}")
                failures += 1
                continue

            is_valid, raw_jobs_list, reason = parse_email_message(msg)
            if not is_valid:
                continue

            jobs_extracted += len(raw_jobs_list)

            for item in raw_jobs_list:
                loc = item["location"]
                is_remote = any(k in loc.lower() for k in ["remote", "worldwide", "anywhere"])
                src = item.get("source", "Email Alert")
                raw_id = item["job_id"]
                job_id = raw_id if str(raw_id).startswith(("linkedin_", "indeed_")) else f"{'indeed' if 'indeed' in src.lower() else 'linkedin'}_{raw_id}"
                sal = item.get("salary") or ("Disclosed on Indeed" if "indeed" in src.lower() else "Disclosed on LinkedIn")
                
                job = JobPosting(
                    id=job_id,
                    title=item["title"],
                    company=item["company"],
                    location=loc,
                    salary=sal,
                    url=item["url"],
                    source=src,
                    posted_date=item.get("posted_date", ""),
                    description_snippet=f"Verified opportunity from official {src}. Employer: {item['company']}. Location: {loc}.",
                    is_remote=is_remote,
                    application_status="untracked",
                    country="Pakistan" if any(k in loc.lower() for k in ["lahore", "pakistan", "karachi", "islamabad"]) else ""
                )

                enriched = enrich_job_posting(job, profile=target_profile)
                extracted_jobs.append(enriched)

            # If mark_read is explicitly enabled, set Seen flag
            if mark_read:
                mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()

    except Exception as err:
        logger.error(f"IMAP connection or ingestion error: {err}")
        return LinkedInSyncResponse(
            status="error",
            message=f"IMAP connection error: {str(err)}",
            emails_scanned=emails_scanned,
            jobs_extracted=jobs_extracted,
            unique_jobs_added=0,
            duplicates_skipped=0,
            failures=failures + 1,
            eligibility_count={},
            jobs=[]
        )

    # Persist unique jobs to LINKEDIN_JOB_STORE
    added_count, dup_count = LINKEDIN_JOB_STORE.save_jobs(extracted_jobs)

    # Compute location eligibility breakdown for new jobs
    eligibility_count: Dict[str, int] = {}
    for j in extracted_jobs:
        eligibility_count[j.location_eligibility] = eligibility_count.get(j.location_eligibility, 0) + 1

    summary_msg = (
        f"Scanned {emails_scanned} emails, extracted {jobs_extracted} jobs. "
        f"Added {added_count} new unique positions ({dup_count} duplicates skipped)."
    )

    return LinkedInSyncResponse(
        status="success",
        message=summary_msg,
        emails_scanned=emails_scanned,
        jobs_extracted=jobs_extracted,
        unique_jobs_added=added_count,
        duplicates_skipped=dup_count,
        failures=failures,
        eligibility_count=eligibility_count,
        jobs=extracted_jobs
    )
