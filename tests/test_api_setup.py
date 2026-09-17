from types import SimpleNamespace
import unittest
from unittest.mock import patch
from flask import Flask, render_template
from api_setup import setup_message


class ApiSetupTests(unittest.TestCase):
    def test_missing_key_does_not_capture_or_create_error_history(self):
        import scan_pipeline
        service = SimpleNamespace(last_activity={}, queue_count=0)
        with patch('config.GEMINI_API_KEY', ''), patch('config.COMPANION_SETTINGS', {'lang':'en'}), \
                patch.object(scan_pipeline, 'begin') as history, patch.object(scan_pipeline, 'process_image') as model:
            scan_pipeline.run_capture(service)
        history.assert_not_called()
        model.assert_not_called()
        self.assertEqual(service.last_activity['state'], 'setup')
        self.assertEqual(service.last_activity['message'], setup_message('en'))
        self.assertIn('aistudio.google.com', service.last_activity['setup_url'])

    def test_onboarding_and_update_controls_in_both_languages(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        app = Flask(__name__, template_folder=str(root/'templates'))
        for lang, label, update in [('pl', 'Podłącz Gemini API', 'Sprawdź aktualizacje'),
                                    ('en', 'Connect Gemini API', 'Check for updates')]:
            with app.test_request_context(), self.subTest(lang=lang):
                html = render_template('api-onboarding.html', lang=lang, api_configured=False) + render_template('app-status.html', lang=lang)
                self.assertIn(label, html)
                self.assertIn(update, html)
                self.assertIn('https://aistudio.google.com/apikey', html)
                self.assertNotIn('id="api-onboarding" hidden', html)
