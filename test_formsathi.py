"""
FormSaathi - Test Suite
Tests PDF extraction, language mappings, prompt structure, and Sarvam client integration.
"""

import unittest
import os
import io
from pdf_extractor import extract_text_from_pdf, ExtractedDocument
from sarvam_client import (
    SarvamClient,
    SarvamAPIError,
    SUPPORTED_LANGUAGES,
    DEFAULT_MODEL,
    detect_script,
)
from generate_sample_pdf import create_pdf


class TestFormSaathi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_pdf = os.path.join("sample_docs", "National_Merit_Scholarship_2026.pdf")
        if not os.path.exists(cls.sample_pdf):
            from generate_sample_pdf import make_samples
            make_samples()

    @classmethod
    def tearDownClass(cls):
        empty_pdf_path = os.path.join("sample_docs", "empty_test.pdf")
        if os.path.exists(empty_pdf_path):
            try:
                os.remove(empty_pdf_path)
            except OSError:
                pass

    def test_pdf_extraction_valid(self):
        """Test extraction on standard text PDF."""
        doc = extract_text_from_pdf(self.sample_pdf)
        self.assertFalse(doc.is_scanned_or_empty)
        self.assertGreater(doc.total_chars, 500)
        self.assertGreater(doc.total_words, 50)
        self.assertEqual(doc.page_count, 1)
        self.assertIn("NATIONAL MERIT-CUM-MEANS SCHOLARSHIP", doc.full_text)
        self.assertIn("November 30, 2026", doc.full_text)

    def test_scanned_or_empty_detection(self):
        """Test that empty or near-empty PDFs trigger the scanned/OCR warning."""
        empty_pdf_path = os.path.join("sample_docs", "empty_test.pdf")
        create_pdf(empty_pdf_path, "", [])
        doc = extract_text_from_pdf(empty_pdf_path)
        self.assertTrue(doc.is_scanned_or_empty)
        self.assertIn("Scanned or image-only document detected", doc.error_message)

    def test_truncation_threshold(self):
        """Test that very long documents trigger context threshold warning."""
        doc = extract_text_from_pdf(self.sample_pdf, max_chars=100)
        self.assertTrue(doc.is_truncated)
        self.assertIn("Notice: Document is long", doc.truncation_note)

    def test_supported_languages(self):
        """Verify all required Indian languages are configured with TTS codes."""
        required_langs = [
            "English", "Telugu", "Hindi", "Tamil",
            "Kannada", "Malayalam", "Bengali", "Marathi"
        ]
        for lang in required_langs:
            self.assertIn(lang, SUPPORTED_LANGUAGES)
            self.assertTrue(bool(SUPPORTED_LANGUAGES[lang].get("tts_code")))
            self.assertTrue(bool(SUPPORTED_LANGUAGES[lang].get("native")))

    def test_sarvam_client_unconfigured_error(self):
        """Verify unconfigured client raises clear SarvamAPIError."""
        client = SarvamClient(api_key="")
        self.assertFalse(client.is_configured())
        with self.assertRaises(SarvamAPIError):
            client.explain_document("Some document text", "English")

    def test_prompt_structure_8_sections(self):
        """Verify that the explanation prompt contains all 8 required sections."""
        client = SarvamClient(api_key="test_dummy_key_12345")
        
        # We can inspect the method's constructed system prompt by mocking _call_chat_completion
        recorded_messages = []
        def dummy_call(messages, model, temperature):
            recorded_messages.extend(messages)
            return "OK"

        client._call_chat_completion = dummy_call
        client.explain_document("Sample document content", "Telugu")

        self.assertGreater(len(recorded_messages), 0)
        sys_prompt = recorded_messages[0]["content"]

        # Check required 8 sections
        expected_sections = [
            "1. Simple Summary",
            "2. Important Dates",
            "3. Eligibility Criteria",
            "4. Required Documents & Certificates",
            "5. Fees and Financial Details",
            "6. What You Need to Do",
            "7. Important Warnings & Penalties",
            "8. Unclear or Missing Information",
        ]
        for sec in expected_sections:
            self.assertIn(sec, sys_prompt)

        # Check Telugu language instruction is embedded
        self.assertIn("Telugu", sys_prompt)
        self.assertIn("తెలుగు", sys_prompt)

    def test_qa_grounding_prompt(self):
        """Verify follow-up Q&A includes strict zero-hallucination grounding."""
        client = SarvamClient(api_key="test_dummy_key_12345")
        recorded_messages = []
        def dummy_call(messages, model, temperature):
            recorded_messages.extend(messages)
            return "OK"

        client._call_chat_completion = dummy_call
        client.answer_question(
            document_text="The deadline is Nov 30.",
            question="What is the deadline?",
            language_name="Hindi",
        )

        sys_prompt = recorded_messages[0]["content"]
        self.assertIn("This information was not found in the uploaded document", sys_prompt)
        self.assertIn("Never invent, extrapolate, or guess", sys_prompt)

    def test_script_detection_and_matching(self):
        """Verify detect_script detects native Indian scripts and English accurately."""
        self.assertEqual(detect_script("దరఖాస్తు చివరి తేదీ ఏమిటి?"), "Telugu")
        self.assertEqual(detect_script("आवेदन की अंतिम तिथि क्या है?"), "Hindi")
        self.assertEqual(detect_script("விண்ணப்பிக்க கடைசி தேதி என்ன?"), "Tamil")
        self.assertEqual(detect_script("ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ ಯಾವುದು?"), "Kannada")
        self.assertEqual(detect_script("What is the last date to apply?"), "English")

        # Verify answer_question enforces script matching in prompt
        client = SarvamClient(api_key="test_dummy_key_12345")
        recorded_messages = []
        def dummy_call(messages, model, temperature):
            recorded_messages.extend(messages)
            return "OK"

        client._call_chat_completion = dummy_call
        client.answer_question(
            document_text="The deadline is Nov 30.",
            question="చివరి తేదీ ఎప్పుడు?",
            language_name="English",  # Even if default is English, input script is Telugu!
        )

        sys_prompt = recorded_messages[0]["content"]
        self.assertIn("CRITICAL SCRIPT MATCHING REQUIREMENT", sys_prompt)
        self.assertIn("Telugu", sys_prompt)
        self.assertIn("తెలుగు", sys_prompt)


if __name__ == "__main__":
    unittest.main()
