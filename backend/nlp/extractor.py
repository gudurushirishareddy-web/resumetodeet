"""
NLP Extraction Engine
Hybrid approach: Regex + spaCy NER + Rule-based parsing + Keyword matching
Designed for the DEET Resume Format Template
"""
import re
import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ─── Skills Database ─────────────────────────────────────────────────────────

SKILLS_DB = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "r",
        "go", "golang", "ruby", "php", "swift", "kotlin", "scala", "rust",
        "perl", "matlab", "julia", "haskell", "lua", "dart", "bash", "shell",
        "assembly", "cobol", "fortran", "vba", "groovy", "elixir"
    ],
    "web_technologies": [
        "html", "css", "html5", "css3", "react", "reactjs", "react.js",
        "angular", "angularjs", "vue", "vuejs", "vue.js", "node", "nodejs",
        "node.js", "express", "expressjs", "flask", "django", "fastapi",
        "spring", "springboot", "laravel", "bootstrap", "tailwind",
        "jquery", "graphql", "rest", "restful", "api", "json", "xml",
        "sass", "less", "webpack", "vite", "next.js", "nextjs", "nuxt"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "mssql", "sql server", "firebase", "cassandra", "elasticsearch",
        "dynamodb", "mariadb", "neo4j", "supabase"
    ],
    "tools_platforms": [
        "git", "github", "gitlab", "docker", "kubernetes", "aws", "azure",
        "gcp", "google cloud", "jenkins", "ci/cd", "linux", "unix",
        "postman", "jira", "confluence", "figma", "photoshop", "vs code",
        "visual studio", "intellij", "eclipse", "jupyter", "anaconda",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
        "numpy", "matplotlib", "hadoop", "spark", "kafka", "rabbitmq",
        "nginx", "apache", "heroku", "netlify", "vercel", "terraform"
    ],
    "core_concepts": [
        "machine learning", "deep learning", "artificial intelligence",
        "natural language processing", "nlp", "computer vision",
        "data structures", "algorithms", "object oriented programming",
        "oop", "design patterns", "microservices", "agile", "scrum",
        "data science", "big data", "cloud computing", "devops",
        "cybersecurity", "networking", "operating systems", "dbms",
        "software engineering", "system design", "blockchain",
        "iot", "internet of things", "ar", "vr", "embedded systems"
    ]
}

ALL_SKILLS = set()
SKILL_CATEGORY_MAP = {}
for cat, skills in SKILLS_DB.items():
    for s in skills:
        ALL_SKILLS.add(s.lower())
        SKILL_CATEGORY_MAP[s.lower()] = cat


# ─── Section Keywords ─────────────────────────────────────────────────────────

SECTION_KEYWORDS = {
    'career_objective': [
        'career objective', 'objective', 'career goal', 'professional summary',
        'summary', 'about me', 'profile', 'abstract', 'introduction',
        'professional profile', 'career profile', 'overview'
    ],
    'education': [
        'education', 'educational background', 'academic background',
        'academic qualification', 'qualifications', 'academic details',
        'educational qualification', 'academics'
    ],
    'skills': [
        'technical skills', 'skills', 'skill set', 'core competencies',
        'technologies', 'technical expertise', 'key skills',
        'areas of expertise', 'competencies', 'proficiency'
    ],
    'experience': [
        'work experience', 'experience', 'professional experience',
        'employment history', 'work history', 'internship',
        'internships', 'industrial training', 'training'
    ],
    'projects': [
        'projects', 'academic projects', 'personal projects',
        'project work', 'key projects', 'major projects',
        'project experience', 'project details'
    ],
    'certifications': [
        'certifications', 'certification', 'certificates',
        'courses', 'online courses', 'achievements',
        'professional certifications', 'training & certifications'
    ],
    'participations': [
        'participations', 'hackathons', 'events', 'extra curricular',
        'extracurricular', 'activities', 'co-curricular', 'competitions',
        'achievements', 'awards', 'honors'
    ],
    'additional': [
        'additional information', 'personal information', 'interests',
        'hobbies', 'languages known', 'languages', 'declaration',
        'references', 'miscellaneous'
    ]
}


# ─── Regex Patterns ──────────────────────────────────────────────────────────

EMAIL_PATTERN = re.compile(
    r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'
)
PHONE_PATTERN = re.compile(
    r'(?:\+?91[\s\-]?)?'
    r'(?:[6-9]\d{9}|'
    r'[6-9]\d{4}[\s\-]\d{5}|'
    r'\d{5}[\s\-]\d{5}|'
    r'\(\d{3,5}\)[\s\-]?\d{5,8})',
    re.IGNORECASE
)
LINKEDIN_PATTERN = re.compile(
    r'(?:linkedin\.com/in/|linkedin:\s*)([a-zA-Z0-9\-_]+)',
    re.IGNORECASE
)
GITHUB_PATTERN = re.compile(
    r'(?:github\.com/|github:\s*)([a-zA-Z0-9\-_]+)',
    re.IGNORECASE
)
URL_PATTERN = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+',
    re.IGNORECASE
)
YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}\b')
CGPA_PATTERN = re.compile(
    r'(?:cgpa|gpa|grade)[:\s]*([0-9]\.[0-9]{1,2})\s*(?:/\s*(?:10|4))?',
    re.IGNORECASE
)
PERCENTAGE_PATTERN = re.compile(
    r'([0-9]{2,3}(?:\.[0-9]{1,2})?)\s*%',
    re.IGNORECASE
)
DEGREE_PATTERN = re.compile(
    r'\b(b\.?tech|b\.?e|b\.?sc|b\.?ca|bca|b\.?com|b\.?a|'
    r'm\.?tech|m\.?e|m\.?sc|mca|m\.?ca|m\.?com|m\.?a|mba|'
    r'ph\.?d|phd|bachelor|master|diploma|12th|10th|intermediate|'
    r'higher secondary|secondary|ssc|hsc)\b',
    re.IGNORECASE
)
CITY_PATTERN = re.compile(
    r'\b(hyderabad|bangalore|bengaluru|mumbai|delhi|chennai|pune|'
    r'kolkata|ahmedabad|jaipur|lucknow|noida|gurugram|gurgaon|'
    r'vizag|visakhapatnam|warangal|tirupati|vijayawada|kochi|'
    r'coimbatore|indore|bhopal|chandigarh|nagpur)\b',
    re.IGNORECASE
)


# ─── Main Extractor ───────────────────────────────────────────────────────────

class ResumeExtractor:
    """Intelligent resume information extractor."""

    def __init__(self):
        self.nlp = None
        self._load_spacy()

    def _load_spacy(self):
        try:
            import spacy
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                try:
                    self.nlp = spacy.load('en_core_web_md')
                except OSError:
                    logger.warning("spaCy model not found, using regex-only mode")
                    self.nlp = None
        except ImportError:
            logger.warning("spaCy not installed, using regex-only mode")
            self.nlp = None

    def extract(self, text: str) -> Dict[str, Any]:
        """Main extraction pipeline."""
        if not text or not text.strip():
            return self._empty_result()

        # Clean text
        cleaned = self._clean_text(text)
        lines = [l.strip() for l in cleaned.split('\n') if l.strip()]

        # Extract name FIRST (top of resume, first meaningful word/line)
        name = self._extract_name(lines, cleaned)

        # Extract contact info
        email = self._extract_email(cleaned)
        phone = self._extract_phone(cleaned)
        linkedin = self._extract_linkedin(cleaned)
        github = self._extract_github(cleaned)
        address = self._extract_address(cleaned)

        # Segment into sections
        sections = self._segment_sections(lines)

        # Extract from sections
        objective = self._extract_objective(sections, cleaned)
        skills = self._extract_skills(sections, cleaned)
        education = self._extract_education(sections, cleaned)
        experience = self._extract_experience(sections)
        projects = self._extract_projects(sections)
        certifications = self._extract_certifications(sections)
        participations = self._extract_participations(sections)
        languages = self._extract_languages(sections)
        hobbies = self._extract_hobbies(sections)

        # Build result
        result = {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "address": address,
            "career_objective": objective,
            "skills": skills,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": certifications,
            "participations": participations,
            "languages": languages,
            "hobbies": hobbies,
        }

        # Add confidence scores
        result["confidence"] = self._compute_confidence(result)
        result["quality_score"] = self._compute_quality_score(result)

        return result

    def _clean_text(self, text: str) -> str:
        """Remove noise and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        # Remove special unicode chars but keep basic punctuation
        text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\n]', ' ', text)
        # Collapse multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)
        # Collapse 3+ newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _extract_name(self, lines: List[str], full_text: str) -> str:
        """
        Extract name from the top of the resume.
        Per spec: name is the first word/line at the very top.
        """
        # Try spaCy first on first 300 chars
        if self.nlp:
            snippet = full_text[:300]
            doc = self.nlp(snippet)
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    name = ent.text.strip()
                    if 2 <= len(name.split()) <= 5 and not any(
                        c.isdigit() for c in name
                    ):
                        return self._title_case(name)

        # Rule-based: first non-empty, non-contact line
        skip_patterns = re.compile(
            r'(@|phone|email|linkedin|github|www\.|http|'
            r'resume|curriculum|cv|#|\+|\d{10})',
            re.IGNORECASE
        )
        for line in lines[:8]:
            line = line.strip()
            if (3 < len(line) < 60 and
                    not skip_patterns.search(line) and
                    not line.startswith('|') and
                    '|' not in line[:5]):
                # Likely a name if it has 1-4 words, mostly letters
                words = line.split()
                if 1 <= len(words) <= 5:
                    if all(re.match(r"[A-Za-z'\-\.]+$", w) for w in words):
                        return self._title_case(line)

        # Fallback: first line
        for line in lines[:3]:
            if line.strip() and len(line.strip()) > 2:
                return self._title_case(line.strip())
        return ""

    def _extract_email(self, text: str) -> str:
        matches = EMAIL_PATTERN.findall(text)
        if matches:
            # Prefer non-example emails
            for m in matches:
                if 'example' not in m.lower() and 'test' not in m.lower():
                    return m.lower()
            return matches[0].lower()
        return ""

    def _extract_phone(self, text: str) -> str:
        matches = PHONE_PATTERN.findall(text)
        for m in matches:
            digits = re.sub(r'\D', '', m)
            if len(digits) >= 10:
                return m.strip()
        return ""

    def _extract_linkedin(self, text: str) -> str:
        m = LINKEDIN_PATTERN.search(text)
        if m:
            return f"linkedin.com/in/{m.group(1)}"
        # Check for raw URL
        urls = URL_PATTERN.findall(text)
        for url in urls:
            if 'linkedin' in url.lower():
                return url
        return ""

    def _extract_github(self, text: str) -> str:
        m = GITHUB_PATTERN.search(text)
        if m:
            return f"github.com/{m.group(1)}"
        urls = URL_PATTERN.findall(text)
        for url in urls:
            if 'github' in url.lower():
                return url
        return ""

    def _extract_address(self, text: str) -> str:
        city_match = CITY_PATTERN.search(text)
        if city_match:
            return city_match.group(0).title()
        # Look for city/state/country pattern
        addr_pattern = re.compile(
            r'(?:address|location|city)[:\s]+([^\n|,]{3,50})',
            re.IGNORECASE
        )
        m = addr_pattern.search(text)
        if m:
            return m.group(1).strip()
        return ""

    def _segment_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        """Split resume text into named sections."""
        sections: Dict[str, List[str]] = {}
        current_section = 'header'
        sections[current_section] = []

        for line in lines:
            detected = self._detect_section_header(line)
            if detected:
                current_section = detected
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)

        return sections

    def _detect_section_header(self, line: str) -> Optional[str]:
        """Check if a line is a section header."""
        clean = line.strip().lower()
        clean = re.sub(r'[:\-_#*•●►]', '', clean).strip()
        for section, keywords in SECTION_KEYWORDS.items():
            for kw in keywords:
                if clean == kw or (len(clean) < 40 and kw in clean and
                                   len(clean) <= len(kw) + 10):
                    return section
        return None

    def _extract_objective(self, sections: Dict, full_text: str) -> str:
        lines = sections.get('career_objective', [])
        if lines:
            text = ' '.join(lines).strip()
            if text:
                return text

        # Fallback: find "objective" or "summary" keyword in raw text
        obj_pattern = re.compile(
            r'(?:career objective|objective|summary|about me)[:\s\n]+'
            r'([^0-9A-Z]{10,300})',
            re.IGNORECASE
        )
        m = obj_pattern.search(full_text)
        if m:
            return m.group(1).strip()[:500]
        return ""

    def _extract_skills(self, sections: Dict, full_text: str) -> Dict[str, List[str]]:
        """Extract skills organized by category."""
        skill_text = ' '.join(sections.get('skills', []))
        if not skill_text:
            skill_text = full_text

        found: Dict[str, List[str]] = {cat: [] for cat in SKILLS_DB}
        skill_text_lower = skill_text.lower()

        for skill in ALL_SKILLS:
            # Match whole word/phrase
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, skill_text_lower):
                cat = SKILL_CATEGORY_MAP[skill]
                # Store original casing from SKILLS_DB
                original = next(
                    (s for s in SKILLS_DB[cat] if s.lower() == skill), skill
                )
                if original not in found[cat]:
                    found[cat].append(original)

        # Also extract from "Programming Languages:", "Web Technologies:" lines
        for line in sections.get('skills', []):
            colon_match = re.match(r'^([^:]+):\s*(.+)$', line)
            if colon_match:
                items = [x.strip() for x in colon_match.group(2).split(',')]
                for item in items:
                    item_lower = item.lower()
                    if item_lower in ALL_SKILLS:
                        cat = SKILL_CATEGORY_MAP[item_lower]
                        if item not in found[cat]:
                            found[cat].append(item)
                    elif item and len(item) > 1:
                        # Add to tools_platforms as catch-all
                        if item not in found['tools_platforms']:
                            found['tools_platforms'].append(item)

        # Flatten to list with case-insensitive dedup
        seen_lower = set()
        all_skills = []
        for cat_skills in found.values():
            for s in cat_skills:
                if s.lower() not in seen_lower:
                    seen_lower.add(s.lower())
                    all_skills.append(s)

        return {
            "categorized": {k: v for k, v in found.items() if v},
            "all": list(dict.fromkeys(all_skills))
        }

    def _extract_education(self, sections: Dict, full_text: str) -> List[Dict]:
        """Extract education entries."""
        edu_lines = sections.get('education', [])
        entries = []

        if not edu_lines:
            return entries

        # Group lines into entries (split by blank lines or degree patterns)
        current_entry: List[str] = []
        for line in edu_lines:
            if not line.strip():
                if current_entry:
                    entry = self._parse_education_entry(current_entry)
                    if entry:
                        entries.append(entry)
                    current_entry = []
            else:
                # Start new entry if we hit another degree keyword
                if current_entry and DEGREE_PATTERN.search(line):
                    entry = self._parse_education_entry(current_entry)
                    if entry:
                        entries.append(entry)
                    current_entry = [line]
                else:
                    current_entry.append(line)

        if current_entry:
            entry = self._parse_education_entry(current_entry)
            if entry:
                entries.append(entry)

        return entries

    def _parse_education_entry(self, lines: List[str]) -> Optional[Dict]:
        text = ' '.join(lines)
        if not text.strip():
            return None

        entry = {"degree": "", "institution": "", "year": "", "score": ""}

        # Degree — use first line that has a degree keyword
        degree_m = DEGREE_PATTERN.search(text)
        if degree_m:
            entry["degree"] = degree_m.group(0)
            for line in lines:
                if DEGREE_PATTERN.search(line):
                    # Clean: take text before | or – delimiter, strip extras
                    clean_deg = re.split(r'[|–\-]', line)[0].strip()
                    # Remove institution-like words to avoid bleed
                    clean_deg = re.sub(
                        r'\s*(?:university|college|institute|school|academy)[^\n]*',
                        '', clean_deg, flags=re.IGNORECASE
                    ).strip()
                    if clean_deg:
                        entry["degree"] = clean_deg
                    break

        # Year — require full 4-digit years in context like "2020 – 2024" or "| 2020"
        year_ctx = re.findall(r'\b((?:19|20)\d{2})\b', text)
        if year_ctx:
            entry["year"] = year_ctx[-1] if len(year_ctx) == 1 else f"{year_ctx[0]} – {year_ctx[-1]}"

        # Institution (usually has "University", "College", "Institute", "School")
        inst_pattern = re.compile(
            r'\b([A-Z][a-zA-Z\s&\(\)]+(?:university|college|institute|school|'
            r'academy|polytechnic|iit|nit|bits)[a-zA-Z\s,]*)',
            re.IGNORECASE
        )
        inst_m = inst_pattern.search(text)
        if inst_m:
            inst_raw = inst_m.group(0).strip()
            # Remove leading degree words that may have bled in
            inst_raw = re.sub(
                r'^(?:b\.?tech|b\.?e|b\.?sc|bca|m\.?tech|m\.?sc|mca|mba|'
                r'bachelor|master|diploma|computer science(?: and engineering)?'
                r'|information technology)\s+',
                '', inst_raw, flags=re.IGNORECASE
            ).strip()
            entry["institution"] = inst_raw[:80]
        elif '|' in text:
            parts = text.split('|')
            if len(parts) >= 2:
                inst_candidate = parts[1].strip().split('|')[0].strip()
                # Remove year-like content
                inst_candidate = re.sub(r'\b(?:19|20)\d{2}\b.*$', '', inst_candidate).strip()
                if inst_candidate:
                    entry["institution"] = inst_candidate

        # Score
        cgpa_m = CGPA_PATTERN.search(text)
        if cgpa_m:
            entry["score"] = f"CGPA: {cgpa_m.group(1)}"
        else:
            pct_m = PERCENTAGE_PATTERN.search(text)
            if pct_m:
                entry["score"] = f"{pct_m.group(1)}%"

        return entry if any(entry.values()) else None

    def _extract_experience(self, sections: Dict) -> List[Dict]:
        exp_lines = sections.get('experience', [])
        entries = []
        if not exp_lines:
            return entries

        current: List[str] = []
        for line in exp_lines:
            if not line.strip():
                if current:
                    entry = self._parse_experience_entry(current)
                    if entry:
                        entries.append(entry)
                    current = []
            else:
                current.append(line)
        if current:
            entry = self._parse_experience_entry(current)
            if entry:
                entries.append(entry)

        return entries

    def _parse_experience_entry(self, lines: List[str]) -> Optional[Dict]:
        text = ' '.join(lines)
        if not text.strip():
            return None

        entry = {"company": "", "role": "", "duration": "", "description": ""}

        # Duration: look for date ranges
        dur_pattern = re.compile(
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+\d{4}'
            r'(?:\s*[-–to]+\s*'
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+\d{4}'
            r'|\s*[-–to]+\s*present)?)',
            re.IGNORECASE
        )
        dur_m = dur_pattern.search(text)
        if dur_m:
            entry["duration"] = dur_m.group(0).strip()
        else:
            years = YEAR_PATTERN.findall(text)
            if len(years) >= 2:
                entry["duration"] = f"{years[0]} – {years[-1]}"
            elif len(years) == 1:
                entry["duration"] = years[0]

        # First line often has role/company
        if lines:
            first = lines[0]
            if '|' in first:
                parts = first.split('|')
                entry["role"] = parts[0].strip()
                entry["company"] = parts[1].strip() if len(parts) > 1 else ""
            elif '-' in first:
                parts = first.split('-')
                entry["role"] = parts[0].strip()
                entry["company"] = parts[1].strip() if len(parts) > 1 else ""
            else:
                entry["role"] = first.strip()

        entry["description"] = ' '.join(lines[1:])[:300] if len(lines) > 1 else ""

        return entry if any(entry.values()) else None

    def _extract_projects(self, sections: Dict) -> List[Dict]:
        proj_lines = sections.get('projects', [])
        entries = []
        if not proj_lines:
            return entries

        current: List[str] = []
        for line in proj_lines:
            if not line.strip():
                if current:
                    entry = self._parse_project_entry(current)
                    if entry:
                        entries.append(entry)
                    current = []
            else:
                current.append(line)
        if current:
            entry = self._parse_project_entry(current)
            if entry:
                entries.append(entry)

        return entries

    def _parse_project_entry(self, lines: List[str]) -> Optional[Dict]:
        if not lines:
            return None
        first = lines[0]
        # Title is before ' – ', ' - Built', or ':' — stop at connector words
        title_match = re.match(r'^([^–]+?)(?:\s*[–\-]\s*(?:Built|Developed|Created|Designed|A |An |\d)|[:–]|$)', first)
        if title_match and title_match.group(1).strip():
            title = title_match.group(1).strip()
        else:
            title_match2 = re.match(r'^([^–\-:]{3,60})', first)
            title = title_match2.group(1).strip() if title_match2 else first.strip()[:60]
        # Description: rest of first line + subsequent lines
        desc_parts = [first[len(title):].lstrip(' –-:').strip()]
        desc_parts += lines[1:]
        desc = ' '.join(p for p in desc_parts if p).strip()
        # Extract technologies
        tech = []
        tech_line = ' '.join(lines).lower()
        for skill in ALL_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, tech_line):
                original = next(
                    (s for cat in SKILLS_DB.values() for s in cat if s.lower() == skill),
                    skill
                )
                if original not in tech:
                    tech.append(original)
        return {
            "title": title[:100],
            "description": desc[:300],
            "technologies": tech
        }

    def _extract_certifications(self, sections: Dict) -> List[Dict]:
        cert_lines = sections.get('certifications', [])
        entries = []
        for line in cert_lines:
            line = line.strip()
            if not line:
                continue
            # Skip lines that look like section headers
            if self._detect_section_header(line):
                break
            # Skip if looks like event/hackathon (has year and organizer pattern)
            if re.search(r'\d{4}.+(?:hackathon|fest|competition|ministry|university|college)', line, re.IGNORECASE):
                continue
            # Parse "Cert Name – Platform"
            parts = re.split(r'\s*[–\-]\s*', line, maxsplit=1)
            name = parts[0].strip()
            platform = parts[1].strip() if len(parts) > 1 else ''
            # Platform often has "/ Organization" — keep as-is
            if name and len(name) > 2:
                entries.append({"name": name, "platform": platform})
        return entries

    def _extract_participations(self, sections: Dict) -> List[Dict]:
        part_lines = sections.get('participations', [])
        entries = []
        for line in part_lines:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'[–\-]', line, maxsplit=1)
            entries.append({
                "event": parts[0].strip(),
                "organizer": parts[1].strip() if len(parts) > 1 else ""
            })
        return entries

    def _extract_languages(self, sections: Dict) -> List[str]:
        # Check additional section first
        for line in sections.get('additional', []):
            if re.search(r'language', line, re.IGNORECASE):
                m = re.search(r'(?:languages?)[:\s]+(.+)', line, re.IGNORECASE)
                if m:
                    return [l.strip() for l in re.split(r'[,/]', m.group(1)) if l.strip()]
        # Fallback: scan all section lines for inline LANGUAGES: X, Y pattern
        for lines in sections.values():
            for line in lines:
                m = re.search(r'(?:languages?)[:\s]+([A-Za-z,/ ]+)', line, re.IGNORECASE)
                if m:
                    langs = [l.strip() for l in re.split(r'[,/]', m.group(1)) if l.strip()]
                    if langs:
                        return langs
        return []

    def _extract_hobbies(self, sections: Dict) -> List[str]:
        for line in sections.get('additional', []):
            if re.search(r'hobb', line, re.IGNORECASE):
                m = re.search(r'(?:hobbies)[:\s]+(.+)', line, re.IGNORECASE)
                if m:
                    return [h.strip() for h in re.split(r'[,/]', m.group(1)) if h.strip()]
        # Fallback: scan all sections
        for lines in sections.values():
            for line in lines:
                m = re.search(r'(?:hobbies?|interests?)[:\s]+(.+)', line, re.IGNORECASE)
                if m:
                    hobbies = [h.strip() for h in re.split(r'[,/]', m.group(1)) if h.strip()]
                    if hobbies:
                        return hobbies
        return []

    def _compute_confidence(self, result: Dict) -> Dict[str, str]:
        """Per-field confidence scoring."""
        conf = {}
        conf['name'] = 'high' if result.get('name') and len(result['name'].split()) >= 2 else 'low'
        conf['email'] = 'high' if EMAIL_PATTERN.match(result.get('email', '')) else 'low'
        phone = re.sub(r'\D', '', result.get('phone', ''))
        conf['phone'] = 'high' if len(phone) >= 10 else 'low'
        conf['skills'] = ('high' if len(result.get('skills', {}).get('all', [])) > 3
                          else 'medium' if len(result.get('skills', {}).get('all', [])) > 0
                          else 'low')
        conf['education'] = ('high' if len(result.get('education', [])) > 0 else 'low')
        conf['experience'] = ('high' if len(result.get('experience', [])) > 0 else 'medium')
        return conf

    def _compute_quality_score(self, result: Dict) -> float:
        """Resume quality score 0–100."""
        score = 0
        if result.get('name'): score += 10
        if result.get('email'): score += 10
        if result.get('phone'): score += 10
        if result.get('address'): score += 5
        if result.get('linkedin'): score += 5
        if result.get('github'): score += 5
        skills = result.get('skills', {}).get('all', [])
        score += min(15, len(skills) * 1.5)
        score += min(15, len(result.get('education', [])) * 7)
        score += min(10, len(result.get('projects', [])) * 5)
        score += min(5, len(result.get('certifications', [])) * 2)
        if result.get('career_objective'): score += 5
        return round(min(100, score), 1)

    def _title_case(self, s: str) -> str:
        return ' '.join(w.capitalize() for w in s.split())

    def _empty_result(self) -> Dict:
        return {
            "name": "", "email": "", "phone": "", "linkedin": "",
            "github": "", "address": "", "career_objective": "",
            "skills": {"categorized": {}, "all": []},
            "education": [], "experience": [], "projects": [],
            "certifications": [], "participations": [],
            "languages": [], "hobbies": [],
            "confidence": {}, "quality_score": 0
        }


# Singleton
_extractor: Optional[ResumeExtractor] = None

def get_extractor() -> ResumeExtractor:
    global _extractor
    if _extractor is None:
        _extractor = ResumeExtractor()
    return _extractor
