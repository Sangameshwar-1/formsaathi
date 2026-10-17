"""
FormSaathi — Understand Any Official Document
A multilingual document understanding assistant powered by Sarvam AI.

Branding:
Name: FormSaathi
Tagline: "Every document. Clearly understood."
Description: "Understand official documents, discover important requirements, and get answers in your preferred language."
"""

import os
import io
import time
from typing import Optional
import streamlit as st
from dotenv import load_dotenv

# Import internal modules
from pdf_extractor import extract_text_from_pdf, ExtractedDocument
from sarvam_client import (
    SarvamClient,
    SarvamAPIError,
    SUPPORTED_LANGUAGES,
    DEFAULT_MODEL,
    detect_script,
)

# Load environment configuration
load_dotenv()

# Suggested questions localized to each language's native script
SUGGESTED_QUESTIONS = {
    "English": {
        "dates_btn": "📅 Last Date to Apply?",
        "dates_q": "What is the exact last date to apply and the verification timeline?",
        "docs_btn": "📑 Required Documents?",
        "docs_q": "Which documents and certificates are required to apply?",
        "elig_btn": "🎓 Eligibility Criteria?",
        "elig_q": "What are the eligibility conditions and annual income limits?",
        "miss_btn": "❓ Hostel Allowance? (Test Missing Info)",
        "miss_q": "Is hostel allowance or private coaching fee covered in this scheme?",
    },
    "Telugu": {
        "dates_btn": "📅 దరఖాస్తు చివరి తేదీ?",
        "dates_q": "దరఖాస్తు చేసుకోవడానికి చివరి తేదీ మరియు సమయం ఏమిటి?",
        "docs_btn": "📑 అవసరమైన పత్రాలు?",
        "docs_q": "దరఖాస్తు చేయడానికి ఏయే సర్టిఫికెట్లు మరియు పత్రాలు అవసరం?",
        "elig_btn": "🎓 అర్హత నిబంధనలు?",
        "elig_q": "ఈ పథకానికి అర్హత ప్రమాణాలు మరియు వార్షిక ఆదాయ పరిమితి ఎంత?",
        "miss_btn": "❓ హాస్టల్ అలవెన్స్? (పరీక్ష)",
        "miss_q": "ఈ పథకంలో హాస్టల్ అలవెన్స్ లేదా ప్రైవేట్ కోచింగ్ ఫీజు లభిస్తుందా?",
    },
    "Hindi": {
        "dates_btn": "📅 आवेदन की अंतिम तिथि?",
        "dates_q": "आवेदन करने की अंतिम तिथि और समय सीमा क्या है?",
        "docs_btn": "📑 आवश्यक दस्तावेज?",
        "docs_q": "आवेदन के लिए कौन-कौन से प्रमाण पत्र और दस्तावेज आवश्यक हैं?",
        "elig_btn": "🎓 पात्रता मानदंड?",
        "elig_q": "इस योजना के लिए पात्रता मानदंड और वार्षिक आय सीमा क्या है?",
        "miss_btn": "❓ छात्रावास भत्ता? (जांच)",
        "miss_q": "क्या इस योजना में छात्रावास भत्ता या कोचिंग शुल्क शामिल है?",
    },
    "Tamil": {
        "dates_btn": "📅 கடைசி தேதி?",
        "dates_q": "விண்ணப்பிக்க கடைசி தேதி மற்றும் காலக்கெடு என்ன?",
        "docs_btn": "📑 தேவையான ஆவணங்கள்?",
        "docs_q": "விண்ணப்பிக்க தேவையான ஆவணங்கள் மற்றும் சான்றிதழ்கள் எவை?",
        "elig_btn": "🎓 தகுதி வரம்புகள்?",
        "elig_q": "தகுதி வரம்புகள் மற்றும் ஆண்டு வருமான வரம்பு என்ன?",
        "miss_btn": "❓ விடுதிக் கட்டணம்? (ஆய்வு)",
        "miss_q": "இந்த திட்டத்தில் விடுதிக் கட்டணம் வழங்கப்படுகிறதா?",
    },
    "Kannada": {
        "dates_btn": "📅 ಕೊನೆಯ ದಿನಾಂಕ?",
        "dates_q": "ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ ಮತ್ತು ಸಮಯ ಯಾವುದು?",
        "docs_btn": "📑 ಅಗತ್ಯ ದಾಖಲೆಗಳು?",
        "docs_q": "ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಯಾವ ಪ್ರಮಾಣಪತ್ರಗಳು ಮತ್ತು ದಾಖಲೆಗಳು ಬೇಕು?",
        "elig_btn": "🎓 ಅರ್ಹತಾ ಮಾನದಂಡಗಳು?",
        "elig_q": "ಅರ್ಹತಾ ಮಾನದಂಡಗಳು ಮತ್ತು ವಾರ್ಷಿಕ ಆದಾಯ ಮಿತಿ ಎಷ್ಟು?",
        "miss_btn": "❓ ಹಾಸ್ಟೆಲ್ ಭತ್ಯೆ? (ಪರೀಕ್ಷೆ)",
        "miss_q": "ಈ ಯೋಜನೆಯಲ್ಲಿ ಹಾಸ್ಟೆಲ್ ಭತ್ಯೆ ನೀಡಲಾಗುತ್ತದೆಯೇ?",
    },
    "Malayalam": {
        "dates_btn": "📅 അവസാന തീയതി?",
        "dates_q": "അപേക്ഷിക്കാനുള്ള അവസാന തീയതി എപ്പോഴാണ്?",
        "docs_btn": "📑 ആവശ്യമായ രേഖകൾ?",
        "docs_q": "അപേക്ഷിക്കാൻ ആവശ്യമായ രേഖകൾ എന്തൊക്കെയാണ്?",
        "elig_btn": "🎓 യോഗ്യതാ മാനദണ്ഡങ്ങൾ?",
        "elig_q": "യോഗ്യതാ മാനദണ്ഡങ്ങളും വാർഷിക വരുമാന പരിധിയും എത്രയാണ്?",
        "miss_btn": "❓ ഹോസ്റ്റൽ അലവൻസ്? (ടെസ്റ്റ്)",
        "miss_q": "ഹോസ്റ്റൽ അലവൻസ് ഇതിൽ ലഭ്യമാണോ?",
    },
    "Bengali": {
        "dates_btn": "📅 শেষ তারিখ?",
        "dates_q": "আবেদন করার শেষ তারিখ এবং সময়সীমা কী?",
        "docs_btn": "📑 প্রয়োজনীয় নথি?",
        "docs_q": "আবেদন করার জন্য কী কী নথি এবং শংসাপত্র প্রয়োজন?",
        "elig_btn": "🎓 যোগ্যতার মানদণ্ড?",
        "elig_q": "যোগ্যতার মানদণ্ড এবং বার্ষিক আয়ের সীমা কত?",
        "miss_btn": "❓ হোস্টেল ভাতা? (পরীক্ষা)",
        "miss_q": "এই প্রকল্পে কি হোস্টেল ভাতা অন্তর্ভুক্ত আছে?",
    },
    "Marathi": {
        "dates_btn": "📅 अंतिम तारीख?",
        "dates_q": "अर्ज करण्याची अंतिम तारीख आणि वेळापत्रक काय आहे?",
        "docs_btn": "📑 आवश्यक कागदपत्रे?",
        "docs_q": "अर्जासाठी कोणती कागदपत्रे आणि प्रमाणपत्रे आवश्यक आहेत?",
        "elig_btn": "🎓 पात्रता निकष?",
        "elig_q": "पात्रतेचे निकष आणि वार्षिक उत्पन्न मर्यादा काय आहे?",
        "miss_btn": "❓ वसतिगृह भत्ता? (तपासणी)",
        "miss_q": "या योजनेत वसतिगृह भत्ता दिला जातो का?",
    },
}

# Streamlit Page Setup
st.set_page_config(
    page_title="FormSaathi — Every Document. Clearly Understood.",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Design System CSS
CUSTOM_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Noto Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* FormSaathi Header Styling */
    .saathi-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%);
        color: #ffffff;
        padding: 2.2rem 2.4rem;
        border-radius: 14px;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.25);
    }
    .saathi-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .saathi-tagline {
        font-size: 1.15rem;
        font-weight: 600;
        color: #93c5fd;
        margin-bottom: 0.5rem;
    }
    .saathi-desc {
        font-size: 0.95rem;
        color: #e2e8f0;
        max-width: 850px;
        line-height: 1.5;
        margin: 0;
    }

    /* Cards & Containers */
    .saathi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
    }
    .badge-blue {
        background-color: #dbeafe;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }
    .badge-green {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    .badge-amber {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
    }

    /* Explanation Section Card */
    .explanation-container {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 1.8rem;
        line-height: 1.7;
    }
    .explanation-container h3 {
        color: #1e3a8a !important;
        font-weight: 700;
        margin-top: 1.3rem;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 0.3rem;
    }

    /* Chat Messages */
    .chat-user {
        background-color: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
        color: #1e293b;
    }
    .chat-bot {
        background-color: #f8fafc;
        border-left: 4px solid #059669;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        color: #0f172a;
        line-height: 1.6;
    }
    .chat-role-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .label-user { color: #1d4ed8; }
    .label-bot { color: #047857; }

    /* Grounding Notice */
    .grounding-notice {
        font-size: 0.82rem;
        color: #64748b;
        background: #f1f5f9;
        padding: 0.55rem 0.85rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* Buttons */
    div.stButton > button:first-child {
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        transition: all 0.15s ease-in-out;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state():
    """Initializes persistent application session variables."""
    if "extracted_doc" not in st.session_state:
        st.session_state.extracted_doc: Optional[ExtractedDocument] = None
    if "document_name" not in st.session_state:
        st.session_state.document_name = ""
    if "explanation" not in st.session_state:
        st.session_state.explanation = ""
    if "explanation_language" not in st.session_state:
        st.session_state.explanation_language = "English"
    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = ""


init_session_state()


def get_sarvam_client(sidebar_key: str = "") -> SarvamClient:
    """Returns an authenticated SarvamClient instance."""
    # Priority: sidebar input if filled, otherwise .env / environment
    effective_key = sidebar_key.strip() if sidebar_key.strip() else os.getenv("SARVAM_API_KEY", "").strip()
    return SarvamClient(api_key=effective_key)


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### ⚙️ Settings & Configuration")

    # API Key Configuration
    env_key_present = bool(os.getenv("SARVAM_API_KEY", "").strip())
    sidebar_api_key = st.text_input(
        "Sarvam API Key",
        value="" if not env_key_present else "••••••••••••••••••••••••••••••••",
        type="password",
        help="Reads automatically from SARVAM_API_KEY in .env, or paste your key here.",
        placeholder="Enter your Sarvam API Key",
    )

    client = get_sarvam_client(sidebar_api_key if sidebar_api_key and "••" not in sidebar_api_key else "")

    if client.is_configured():
        st.markdown('<span class="badge badge-green">✓ Sarvam API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-amber">⚠️ API Key Missing</span>', unsafe_allow_html=True)
        st.caption("Add `SARVAM_API_KEY` to `.env` or paste it above to enable AI features.")

    st.divider()

    # Language Selection
    st.markdown("### 🌐 Explanation Language")
    language_options = list(SUPPORTED_LANGUAGES.keys())
    selected_language = st.selectbox(
        "Choose Preferred Language",
        options=language_options,
        index=0,
        format_func=lambda lang: SUPPORTED_LANGUAGES[lang]["display"],
        help="All summaries, explanations, and answers will be produced in this language.",
    )

    st.divider()

    # Pre-loaded Demo Documents for Fast Judging Evaluation
    st.markdown("### ⚡ Quick Demo Samples")
    st.caption("Click to instantly load realistic official government/college notifications:")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📄 Scholarship", use_container_width=True, help="National Merit-Cum-Means Scholarship 2026"):
            sample_path = os.path.join("sample_docs", "National_Merit_Scholarship_2026.pdf")
            if os.path.exists(sample_path):
                with open(sample_path, "rb") as f:
                    file_bytes = f.read()
                doc = extract_text_from_pdf(file_bytes)
                st.session_state.extracted_doc = doc
                st.session_state.document_name = "National_Merit_Scholarship_2026.pdf"
                st.session_state.explanation = ""
                st.session_state.audio_bytes = None
                st.session_state.chat_history = []
                st.rerun()

    with col_s2:
        if st.button("🎓 Admissions", use_container_width=True, help="PG Admissions Circular 2026"):
            sample_path = os.path.join("sample_docs", "University_Admission_Notice_2026.pdf")
            if os.path.exists(sample_path):
                with open(sample_path, "rb") as f:
                    file_bytes = f.read()
                doc = extract_text_from_pdf(file_bytes)
                st.session_state.extracted_doc = doc
                st.session_state.document_name = "University_Admission_Notice_2026.pdf"
                st.session_state.explanation = ""
                st.session_state.audio_bytes = None
                st.session_state.chat_history = []
                st.rerun()

    st.divider()

    # Engine & Grounding Information
    st.markdown("### 🛡️ Grounding Safeguards")
    st.markdown(
        """
        - **Strict Grounding:** Every answer is sourced solely from the uploaded PDF.
        - **Zero Hallucination Policy:** If a date, fee, or condition is absent, FormSaathi explicitly reports it as missing.
        - **Data Integrity:** Document contents are treated as untrusted text, guarding against prompt injection.
        """
    )
    st.caption("Built with Sarvam AI `sarvam-105b` & `bulbul` TTS.")


# --- MAIN HEADER ---
st.markdown(
    """
    <div class="saathi-header">
        <div class="saathi-title">
            <span>📄</span> FormSaathi
        </div>
        <div class="saathi-tagline">"Every document. Clearly understood."</div>
        <p class="saathi-desc">
            Understand official documents, discover important requirements, deadlines, fees, and get answers in your preferred language using Sarvam AI.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- STEP 1: DOCUMENT UPLOAD & STATUS ---
upload_col1, upload_col2 = st.columns([2, 1])

with upload_col1:
    uploaded_file = st.file_uploader(
        "Upload Official Document (PDF only, max 20MB)",
        type=["pdf"],
        help="Upload government schemes, scholarship circulars, admission notices, or examination instructions.",
    )

    if uploaded_file is not None:
        # Check if this is a newly uploaded file
        if st.session_state.document_name != uploaded_file.name:
            # Validate size (max 20MB)
            if uploaded_file.size > 20 * 1024 * 1024:
                st.error("Uploaded file exceeds maximum allowed limit of 20MB. Please upload a smaller file.")
            else:
                with st.spinner("Extracting selectable text from PDF..."):
                    extracted = extract_text_from_pdf(uploaded_file)
                    st.session_state.extracted_doc = extracted
                    st.session_state.document_name = uploaded_file.name
                    st.session_state.explanation = ""
                    st.session_state.audio_bytes = None
                    st.session_state.chat_history = []
                st.rerun()

with upload_col2:
    st.markdown('<div class="saathi-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📊 Document Status</div>', unsafe_allow_html=True)

    curr_doc: Optional[ExtractedDocument] = st.session_state.extracted_doc
    if curr_doc is not None:
        if curr_doc.is_scanned_or_empty:
            st.markdown('<span class="badge badge-amber">⚠️ Scanned / Empty PDF</span>', unsafe_allow_html=True)
            st.error(curr_doc.error_message or "No selectable text found. OCR is required.")
        else:
            st.markdown('<span class="badge badge-green">✓ Text Extracted</span>', unsafe_allow_html=True)
            st.write(f"**File:** `{st.session_state.document_name}`")
            st.write(f"**Pages:** {curr_doc.page_count} | **Words:** {curr_doc.total_words:,}")
            st.caption(f"Engine: {curr_doc.extractor_engine} | Chars: {curr_doc.total_chars:,}")

            if curr_doc.is_truncated:
                st.warning(curr_doc.truncation_note)
    else:
        st.info("No document loaded yet. Upload a PDF or select a demo sample from the sidebar.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- PREVIEW EXTRACTED TEXT ---
if st.session_state.extracted_doc and not st.session_state.extracted_doc.is_scanned_or_empty:
    with st.expander("🔍 View Extracted Document Text Preview"):
        st.caption("This is the exact readable text extracted from your PDF that is sent to Sarvam AI:")
        st.text_area(
            "Extracted Text",
            value=st.session_state.extracted_doc.full_text,
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )


# --- STEP 2: EXPLAIN DOCUMENT ACTION ---
st.markdown("<br>", unsafe_allow_html=True)
action_col1, action_col2, action_col3 = st.columns([1.5, 1.5, 3])

with action_col1:
    explain_disabled = (
        st.session_state.extracted_doc is None
        or st.session_state.extracted_doc.is_scanned_or_empty
    )
    explain_clicked = st.button(
        "✨ Explain Document",
        type="primary",
        disabled=explain_disabled,
        use_container_width=True,
    )

with action_col2:
    if st.session_state.extracted_doc and not st.session_state.extracted_doc.is_scanned_or_empty:
        st.markdown(
            f'<div style="padding-top: 0.5rem;"><span class="badge badge-blue">Language: {SUPPORTED_LANGUAGES[selected_language]["display"]}</span></div>',
            unsafe_allow_html=True,
        )

# Trigger Explanation API Call
if explain_clicked:
    if not client.is_configured():
        st.error(
            "SARVAM_API_KEY is not configured. Please add your key to `.env` or enter it in the sidebar to proceed."
        )
    else:
        with st.spinner(f"Analyzing document in {SUPPORTED_LANGUAGES[selected_language]['display']} using Sarvam-105b..."):
            try:
                explanation_result = client.explain_document(
                    document_text=st.session_state.extracted_doc.full_text,
                    language_name=selected_language,
                    model=DEFAULT_MODEL,
                )
                st.session_state.explanation = explanation_result
                st.session_state.explanation_language = selected_language
                st.session_state.audio_bytes = None  # Reset TTS for new explanation
                st.toast("Document explained successfully!", icon="✅")
            except SarvamAPIError as api_err:
                st.error(f"Sarvam AI Error: {str(api_err)}")
            except Exception as e:
                st.error(f"Unexpected error during explanation: {str(e)}")


# --- STEP 3: STRUCTURED EXPLANATION PANEL ---
if st.session_state.explanation:
    st.divider()
    expl_header_col1, expl_header_col2 = st.columns([3, 1])

    with expl_header_col1:
        st.markdown(
            f"### 📋 Document Explanation ({SUPPORTED_LANGUAGES[st.session_state.explanation_language]['display']})"
        )
    with expl_header_col2:
        # TTS Audio Trigger
        tts_button = st.button("🔊 Read Summary Aloud (Bulbul TTS)", use_container_width=True)
        if tts_button:
            if not client.is_configured():
                st.warning("Please configure your SARVAM_API_KEY to generate speech.")
            else:
                with st.spinner("Synthesizing voice audio with Sarvam Bulbul TTS..."):
                    audio_res = client.generate_speech(
                        text=st.session_state.explanation[:600],
                        language_name=st.session_state.explanation_language,
                    )
                    if audio_res:
                        st.session_state.audio_bytes = audio_res
                    else:
                        st.info("Bulbul TTS audio is currently unavailable for this text. Check API status or credentials.")

    # Audio Player if audio has been generated
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/wav")

    # Render Explanation Content Card
    st.markdown(
        f"""
        <div class="explanation-container">
            {st.session_state.explanation}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Download summary button
    st.download_button(
        label="📥 Download Explanation (.txt)",
        data=st.session_state.explanation,
        file_name=f"FormSaathi_Explanation_{st.session_state.document_name}.txt",
        mime="text/plain",
    )


# --- STEP 4: FOLLOW-UP QUESTION ANSWERING ---
if st.session_state.extracted_doc and not st.session_state.extracted_doc.is_scanned_or_empty:
    st.divider()
    st.markdown("### 💬 Ask Follow-Up Questions About This Document")
    st.caption("Ask specific questions about dates, eligibility, documents, or exceptions. Every answer is strictly grounded in the document.")

    # Demonstration Quick-Question Chips (Localized to chosen script)
    sq = SUGGESTED_QUESTIONS.get(selected_language, SUGGESTED_QUESTIONS["English"])
    st.markdown(f"**Suggested Questions ({SUPPORTED_LANGUAGES[selected_language]['display']}):**")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    with q_col1:
        if st.button(sq["dates_btn"], use_container_width=True):
            st.session_state.pending_question = sq["dates_q"]

    with q_col2:
        if st.button(sq["docs_btn"], use_container_width=True):
            st.session_state.pending_question = sq["docs_q"]

    with q_col3:
        if st.button(sq["elig_btn"], use_container_width=True):
            st.session_state.pending_question = sq["elig_q"]

    with q_col4:
        # Designed to test strict zero-hallucination grounding!
        if st.button(sq["miss_btn"], use_container_width=True):
            st.session_state.pending_question = sq["miss_q"]

    # Chat history display
    for turn in st.session_state.chat_history:
        role = turn.get("role")
        content = turn.get("content", "")
        lang_used = turn.get("lang", selected_language)

        if role == "user":
            st.markdown(
                f"""
                <div class="chat-user">
                    <div class="chat-role-label label-user">You Asked ({lang_used} Script):</div>
                    <div>{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="chat-bot">
                    <div class="chat-role-label label-bot">FormSaathi Answer ({lang_used} Script):</div>
                    <div>{content}</div>
                    <div class="grounding-notice">
                        🔒 Grounded in uploaded document. Script matched to input query.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Input Form for Custom Follow-Up Question
    with st.form(key="qa_form", clear_on_submit=True):
        default_val = st.session_state.pending_question
        user_query = st.text_input(
            "Type your question (in any Indian language or English):",
            value=default_val,
            placeholder="e.g. దరఖాస్తు చివరి తేదీ ఎప్పుడు? / आवेदन की अंतिम तिथि? / What is the last date?",
        )
        submit_qa = st.form_submit_button("Ask FormSaathi 🚀", type="primary")

    if submit_qa and user_query.strip():
        # Clear pending suggestion
        st.session_state.pending_question = ""

        if not client.is_configured():
            st.error("SARVAM_API_KEY is not configured. Please configure your key in the sidebar or `.env`.")
        else:
            # Detect script of input query so answer script matches input script
            input_script = detect_script(user_query.strip()) or selected_language

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_query.strip(),
                "lang": input_script,
            })

            with st.spinner(f"Finding answer in document using Sarvam AI (Matching {input_script} script)..."):
                try:
                    answer = client.answer_question(
                        document_text=st.session_state.extracted_doc.full_text,
                        question=user_query.strip(),
                        language_name=input_script,
                        chat_history=st.session_state.chat_history,
                        model=DEFAULT_MODEL,
                    )

                    ans_script = detect_script(answer) or input_script

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "lang": ans_script,
                    })
                    st.rerun()

                except SarvamAPIError as api_err:
                    st.error(f"Sarvam AI Error: {str(api_err)}")
                except Exception as e:
                    st.error(f"Failed to generate answer: {str(e)}")


# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1rem 0;">
        <strong>FormSaathi</strong> — Powered by <strong>Sarvam AI</strong> (<code>sarvam-105b</code> & <code>bulbul</code>)
        <br>
        <em>Disclaimer: FormSaathi provides AI-assisted comprehension of documents. It does not issue official government decisions.</em>
    </div>
    """,
    unsafe_allow_html=True,
)
