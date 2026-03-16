"""
NLP Extraction Accuracy Evaluator
Computes per-field extraction accuracy against ground truth labels.
Run: python evaluator.py
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nlp.extractor import get_extractor

# ─── Ground-truth test cases ──────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "tc1",
        "text": """RAVI KUMAR SHARMA
+91 98765 43210 | ravi.sharma@gmail.com | Hyderabad, Telangana
linkedin.com/in/ravikumar | github.com/ravikumar

Career Objective
Passionate CS graduate seeking a Software Engineer role.

Education
B.Tech – Computer Science
JNTU Hyderabad | 2020 – 2024
CGPA: 8.4 / 10

Technical Skills
Programming Languages: Python, Java, JavaScript
Web Technologies: React, Node.js, Flask
Tools / Platforms: Git, Docker, AWS

Academic Projects
Resume Parser – Built using Flask and spaCy. Technologies: Python, Flask, spaCy.

Certifications
Python for Everybody – Coursera

Additional Information
Languages: Telugu, English
Hobbies: Competitive Programming, Blogging
""",
        "expected": {
            "name": "Ravi Kumar Sharma",
            "email": "ravi.sharma@gmail.com",
            "phone": "+91 98765 43210",
            "skills_contains": ["Python", "Java", "JavaScript", "React"],
            "education_count": 1,
            "certifications_count": 1,
            "languages_contains": ["Telugu", "English"]
        }
    },
    {
        "id": "tc2",
        "text": """PRIYA VENKATESH
priya.v@yahoo.com
9876543210
Bangalore, Karnataka

OBJECTIVE
Seeking a Data Scientist position to leverage my ML skills.

EDUCATION
M.Sc Data Science
Indian Institute of Science, Bangalore | 2022 – 2024
CGPA 9.1

B.Sc Mathematics
Bangalore University | 2019 – 2022
Percentage: 88%

SKILLS
Python, R, TensorFlow, PyTorch, pandas, numpy, SQL, Machine Learning, Deep Learning

PROJECTS
Sentiment Analysis Tool – NLP project using BERT. Technologies: Python, TensorFlow, BERT.
Stock Prediction – LSTM model for stock forecasting. Technologies: Python, PyTorch, pandas.

CERTIFICATIONS
Deep Learning Specialization – Coursera / deeplearning.ai
Google Data Analytics – Google

LANGUAGES: Kannada, English, Hindi
HOBBIES: Reading, Chess
""",
        "expected": {
            "name": "Priya Venkatesh",
            "email": "priya.v@yahoo.com",
            "phone": "9876543210",
            "skills_contains": ["Python", "TensorFlow"],
            "education_count": 2,
            "certifications_count": 2,
            "languages_contains": ["Kannada", "English"]
        }
    }
]


def evaluate():
    extractor = get_extractor()
    results = []
    total_fields = 0
    correct_fields = 0

    print("\n" + "="*60)
    print("  DEET NLP Extraction Accuracy Evaluation")
    print("="*60)

    for tc in TEST_CASES:
        extracted = extractor.extract(tc["text"])
        expected = tc["expected"]
        tc_correct = 0
        tc_total = 0
        field_results = {}

        # Name
        tc_total += 1
        name_match = extracted.get("name", "").lower() == expected["name"].lower()
        if name_match:
            tc_correct += 1
        field_results["name"] = {
            "expected": expected["name"],
            "got": extracted.get("name", ""),
            "pass": name_match
        }

        # Email
        tc_total += 1
        email_match = extracted.get("email", "").lower() == expected["email"].lower()
        if email_match:
            tc_correct += 1
        field_results["email"] = {
            "expected": expected["email"],
            "got": extracted.get("email", ""),
            "pass": email_match
        }

        # Phone (digits only comparison)
        tc_total += 1
        import re
        exp_digits = re.sub(r'\D', '', expected["phone"])
        got_digits = re.sub(r'\D', '', extracted.get("phone", ""))
        phone_match = exp_digits in got_digits or got_digits in exp_digits
        if phone_match:
            tc_correct += 1
        field_results["phone"] = {
            "expected": expected["phone"],
            "got": extracted.get("phone", ""),
            "pass": phone_match
        }

        # Skills
        tc_total += 1
        all_skills = [s.lower() for s in extracted.get("skills", {}).get("all", [])]
        skills_req = expected.get("skills_contains", [])
        skills_found = all(s.lower() in all_skills for s in skills_req)
        if skills_found:
            tc_correct += 1
        field_results["skills"] = {
            "expected_contains": skills_req,
            "got_count": len(all_skills),
            "pass": skills_found
        }

        # Education count
        tc_total += 1
        edu_count = len(extracted.get("education", []))
        edu_match = edu_count >= expected.get("education_count", 0)
        if edu_match:
            tc_correct += 1
        field_results["education"] = {
            "expected_min": expected.get("education_count"),
            "got": edu_count,
            "pass": edu_match
        }

        # Certifications
        tc_total += 1
        cert_count = len(extracted.get("certifications", []))
        cert_match = cert_count >= expected.get("certifications_count", 0)
        if cert_match:
            tc_correct += 1
        field_results["certifications"] = {
            "expected_min": expected.get("certifications_count"),
            "got": cert_count,
            "pass": cert_match
        }

        # Languages
        tc_total += 1
        got_langs = [l.lower() for l in extracted.get("languages", [])]
        exp_langs = expected.get("languages_contains", [])
        langs_match = all(l.lower() in got_langs for l in exp_langs)
        if langs_match:
            tc_correct += 1
        field_results["languages"] = {
            "expected_contains": exp_langs,
            "got": extracted.get("languages", []),
            "pass": langs_match
        }

        accuracy = (tc_correct / tc_total) * 100
        results.append({
            "test_id": tc["id"],
            "accuracy": accuracy,
            "correct": tc_correct,
            "total": tc_total,
            "fields": field_results,
            "quality_score": extracted.get("quality_score", 0)
        })

        total_fields += tc_total
        correct_fields += tc_correct

        # Print results
        print(f"\n📄 Test Case: {tc['id']}  (Accuracy: {accuracy:.1f}%)")
        print(f"   Quality Score: {extracted.get('quality_score', 0)}/100")
        for field, fr in field_results.items():
            status = "✅" if fr["pass"] else "❌"
            print(f"   {status} {field}: {fr}")

    overall = (correct_fields / total_fields) * 100 if total_fields else 0
    print(f"\n{'='*60}")
    print(f"  Overall Accuracy: {overall:.1f}%  ({correct_fields}/{total_fields} fields correct)")
    print("="*60)

    # Save report
    report = {
        "overall_accuracy": overall,
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "test_cases": results
    }
    report_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'accuracy_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to: {report_path}\n")
    return report


if __name__ == '__main__':
    evaluate()
