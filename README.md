# 📄 FormSaathi — Every Document. Clearly Understood.

> **FormSaathi** is an AI-powered official document comprehension assistant built using **Sarvam AI APIs**. It converts dense bureaucratic notices, scholarship forms, government circulars, and university admission brochures into simple, structured breakdowns and answers follow-up questions in the **exact same native script and language** as the user.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Powered by Sarvam AI](https://img.shields.io/badge/Powered%20by-Sarvam%20AI-blue.svg)](https://docs.sarvam.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 The Problem
Citizens and students across India frequently struggle to understand critical official documents — such as central/state scholarship schemes, entrance examination notices, reservation certificates, and university admission guidelines. These documents are burdened with:
- Complex administrative vocabulary and dense legalese
- Scattered deadlines across multiple annexures
- Complicated eligibility matrices (income limits, academic cutoffs)
- Lack of access in an applicant's preferred native language and script

Misunderstandings often lead to missed deadlines, rejected applications, or falling victim to touts.

---

## 💡 The Solution: FormSaathi
FormSaathi pairs **high-speed text extraction (PyMuPDF)** with **Sarvam AI foundation models (`sarvam-105b-conversations`)** and **Bulbul Text-to-Speech (`bulbul:v4-flash`)**:

1. **Instant Document Ingestion:** Upload any selectable text PDF (or 1-click test with preloaded official circulars).
2. **8-Part Structured Breakdown:** Automatically extracts:
   - 1️⃣ **Simple Summary:** Plain everyday explanation of the scheme/circular.
   - 2️⃣ **Important Dates:** Explicit deadlines, portal opening, exam dates, validity periods.
   - 3️⃣ **Eligibility Criteria:** Who qualifies, conditions, exceptions, income thresholds.
   - 4️⃣ **Required Documents & Certificates:** Explicit checklist of needed certificates and forms.
   - 5️⃣ **Fees and Financial Details:** Exact fee amounts, scholarship stipends, fee waivers.
   - 6️⃣ **What You Need to Do:** Step-by-step actionable checklist in chronological order.
   - 7️⃣ **Important Warnings & Penalties:** Consequences of fake certificates, late penalties.
   - 8️⃣ **Unclear or Missing Information:** Critical points not addressed in the document.
3. **Strict Script & Language Matching:**
   - **Script Consistency:** Answers are returned in the **exact same script as the user's input**!
     - Ask in **Telugu script (తెలుగు)** $\rightarrow$ Answer strictly in **Telugu script**.
     - Ask in **Devanagari script (हिन्दी / मराठी)** $\rightarrow$ Answer strictly in **Devanagari script**.
     - Ask in **Tamil script (தமிழ்)** $\rightarrow$ Answer strictly in **Tamil script**.
     - Ask in **Kannada script (ಕನ್ನಡ)** $\rightarrow$ Answer strictly in **Kannada script**.
     - Ask in **Malayalam script (മലയാളം)** $\rightarrow$ Answer strictly in **Malayalam script**.
     - Ask in **Bengali script (বাংলা)** $\rightarrow$ Answer strictly in **Bengali script**.
     - Ask in **English / Latin script** $\rightarrow$ Answer strictly in **English / Latin script**.
4. **Strict Zero-Hallucination Grounding:** FormSaathi answers strictly based on facts present in the uploaded document. If an item is missing (e.g. hostel allowance or laptop distribution), it explicitly states: *"This information was not found in the uploaded document."*
5. **Voice Accessibility (Bulbul TTS):** Read summaries aloud in natural Indian accents using Sarvam's `bulbul:v4-flash` engine.

---

## 🏗️ Architecture & Technology Stack

```
[ User PDF Upload / Preloaded Sample Notice ]
                     │
                     ▼
       [ PyMuPDF / fitz Extractor ]
  (Text parsing, page counts, scanned/OCR detector,
         context length overflow guard)
                     │
                     ▼
           [ FormSaathi Engine ]
  (Script detection, grounding prompts, anti-prompt injection,
         multilingual formatting)
           ┌─────────┴─────────┐
           ▼                   ▼
   [ Sarvam Chat API ]   [ Sarvam Bulbul TTS ]
(sarvam-105b-conversations)  (bulbul:v4-flash)
           │                   │
           └─────────┬─────────┘
                     ▼
       [ Streamlit Responsive UI ]
   (Accessible, high-contrast, laptop-ready)
```

- **Frontend & App Engine:** [Streamlit](https://streamlit.io/)
- **PDF Extraction:** [PyMuPDF](https://pymupdf.readthedocs.io/) (with automatic fallback to `PyPDF2`)
- **Core AI Models (Sarvam AI REST APIs):**
  - **Chat Completions:** `POST https://api.sarvam.ai/v1/chat/completions` (Model: `sarvam-105b-conversations`)
  - **Text-to-Speech:** `POST https://api.sarvam.ai/text-to-speech` (Model: `bulbul:v4-flash`)
- **Environment Management:** `python-dotenv`
- **HTTP Client:** `requests`

---

## 📂 Project Structure

```
formsathi/
├── app.py                      # Main Streamlit web application
├── pdf_extractor.py            # PDF parser, scanned PDF detector & context guard
├── sarvam_client.py            # Sarvam AI API client (Chat completions & Bulbul TTS)
├── test_formsathi.py           # Comprehensive unit test suite (extraction, script matching, grounding)
├── generate_sample_pdf.py      # Standalone generator for demo official PDFs
├── sample_docs/                # Pre-loaded official sample notifications
│   ├── National_Merit_Scholarship_2026.pdf
│   └── University_Admission_Notice_2026.pdf
├── requirements.txt            # Python dependencies
├── .env.example                # Safe environment configuration template
├── .gitignore                  # Excludes API keys and caches
└── README.md                   # Project documentation & demo guide
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- A Sarvam AI API Key (sign up at [dashboard.sarvam.ai](https://dashboard.sarvam.ai))

### 2. Clone the Repository
```bash
git clone https://github.com/Sangameshwar-1/formsaathi.git
cd formsaathi
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create your `.env` file from the provided template:
```bash
cp .env.example .env
```

Open `.env` and set your key:
```env
SARVAM_API_KEY=your_actual_sarvam_api_key_here
```
*(Note: You can also paste your API key directly in the web app sidebar during a live demonstration).*

### 5. Run the Test Suite
Verify that text extraction, language mappings, prompt integrity, and script matching pass:
```bash
python -m unittest test_formsathi.py
```

### 6. Launch FormSaathi
Start the Streamlit application:
```bash
streamlit run app.py
```

Open your browser at:
`http://localhost:8501`

---

## 🎯 Hackathon Demonstration & Judging Walkthrough

To present FormSaathi effectively during a 3-minute hackathon pitch:

### Step 1: Instant Ingestion
1. In the sidebar under **⚡ Quick Demo Samples**, click **"📄 Scholarship"**.
2. Notice the status card updates immediately:
   - File: `National_Merit_Scholarship_2026.pdf`
   - Status: `✓ Text Extracted` (Pages: 1 | Words: 366).
   - Expand **"🔍 View Extracted Document Text Preview"** to inspect raw extracted text.

### Step 2: Multilingual Explanation & Audio
1. In the sidebar, select **Telugu (తెలుగు)** (or Hindi / English).
2. Click **"✨ Explain Document"**.
3. Review the 8 structured sections generated by `sarvam-105b-conversations`:
   - **1. Simple Summary:** Plain-language explanation of the scholarship purpose.
   - **2. Important Dates:** Portal opening (Oct 15, 2026) and Deadline (Nov 30, 2026).
   - **3. Eligibility Criteria:** Class VII 55% marks, Annual parental income $\le$ ₹2.5 Lakhs.
   - **4. Required Documents:** Tahsildar income certificate, Aadhaar, marksheet, bank passbook.
   - **5. Fees & Financial Details:** ₹12,000/year benefit; ₹0 application fee.
   - **6. What You Need to Do:** Step 1 to Step 4 action sequence.
   - **7. Important Warnings:** Disqualification & penalties for forged certificates.
   - **8. Unclear or Missing Information:** Key items omitted from the circular.
4. Click **"🔊 Read Summary Aloud (Bulbul TTS)"** to hear the native Indian language speech synthesis.

### Step 3: Script-Matched Follow-Up Q&A
Demonstrate how questions are answered in the **exact same script**:

* **Demo Question 1 (Telugu Script Input):**
  - Click the quick button: **"📅 దరఖాస్తు చివరి తేదీ?"**
  - Result: Confirms November 30, 2026 in **pure Telugu script** (`నవంబర్ 30, 2026`).
* **Demo Question 2 (Document Checklist):**
  - Click the quick button: **"📑 అవసరమైన పత్రాలు?"**
  - Result: Provides the full document checklist in native Telugu script.
* **Demo Question 3 (Zero-Hallucination Grounding Test):**
  - Click the quick button: **"❓ హాస్టల్ అలవెన్స్? (పరీక్ష)"** (Asking if hostel allowance is provided).
  - Result: FormSaathi strictly answers that hostel allowance is **not covered or mentioned** in the document, proving zero-hallucination compliance.

---

## 🛡️ Security & Reliability Safeguards
- **Zero Hallucination Guarantee:** Prompts explicitly prohibit extrapolating facts, inventing deadlines, or fabricating fee amounts.
- **Script Matching Assurance:** Automatically detects the script of user queries and instructs the model to match it without English transliteration.
- **Untrusted Document Defense:** Uploaded document contents are isolated within delimited code blocks to defend against prompt injection attacks.
- **Scanned Document Detection:** Flags scanned/image-only PDFs where selectable text is missing, advising users that OCR preprocessing is needed.
- **Context Length Protection:** Long documents (>50,000 characters) are safely segmented with clear user notices instead of silently truncating.
- **No Secret Leakage:** `.env` and `.streamlit/secrets.toml` are excluded in `.gitignore`. The UI uses password-masked inputs and never prints keys to server logs.

---

## 📜 License
Released under the MIT License for open-source document accessibility and digital inclusion across Indian languages.
