"""Exercise the build sync route without importing desktop/capture dependencies."""
import ast
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class MarketBuildSyncTests(unittest.TestCase):
    def test_build_sync_payload_sent_to_market(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_build_online_sync')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = {
            'server_url': 'https://market.d2app.xyz',
            'api_token': 'test_token_123',
            'title': 'Hammerdin — Paladin',
            'class_name': 'paladin',
            'level': 90,
            'description': 'Gear details',
            'skills': [{'name': 'Blessed Hammer', 'points': 20}],
            'html_content': '<!doctype html><html><body>Test Build</body></html>'
        }
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","id":"build_abc","url":"/builds/build_abc"}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch('urllib.request.urlopen', return_value=response) as send:
            result = scope['api_build_online_sync']()

        req = send.call_args.args[0]
        self.assertEqual(req.full_url, 'https://market.d2app.xyz/api/marketplace/builds/publish')
        self.assertEqual(req.headers.get('X-api-key'), 'test_token_123')
        payload = json.loads(req.data.decode('utf-8'))
        self.assertEqual(payload['title'], 'Hammerdin — Paladin')
        self.assertEqual(payload['class_name'], 'paladin')
        self.assertIn('Test Build', payload['html_content'])
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['id'], 'build_abc')

    def test_build_sync_default_server_url(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_build_online_sync')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = {
            'api_token': 'test_token_123',
            'title': 'Hammerdin',
            'html_content': '<html></html>'
        }
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","id":"build_def","url":"/builds/build_def"}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch('urllib.request.urlopen', return_value=response) as send:
            scope['api_build_online_sync']()

        req = send.call_args.args[0]
        self.assertEqual(req.full_url, 'https://market.d2app.xyz/api/marketplace/builds/publish')


if __name__ == '__main__':
    unittest.main()
