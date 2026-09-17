"""Exercise the sync route without importing desktop/capture dependencies."""
import ast
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class MarketListSyncTests(unittest.TestCase):
    def test_selected_list_is_read_and_sent(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_trade_online_sync')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = dict(list_name='Runy', item_ids=['item2'], api_token='test')
        db = Mock()
        db.get_trade_items.return_value = [dict(id='item2', trade_list_name='Runy', trade_price='Ist')]
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","count":1}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch.dict(sys.modules, {'db':db}), patch('urllib.request.urlopen', return_value=response) as send:
            result = scope['api_trade_online_sync']()
        db.get_trade_items.assert_called_once_with('Runy')
        payload = json.loads(send.call_args.args[0].data)
        self.assertEqual(payload['list_name'], 'Runy')
        self.assertEqual(payload['items'][0]['trade_price'], 'Ist')
        self.assertEqual(result['count'], 1)

    def test_anonymous_list_sync(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_trade_anonymous_sync')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = dict(
            list_name='Runy',
            title='Moja Anonimowa Lista',
            description='Opis w textarea',
            password='secret_password',
            item_ids=['item2'],
            realm_sc_hc='sc',
            realm_ladder='ladder',
            realm_expansion='lod'
        )
        db = Mock()
        db.get_trade_items.return_value = [dict(id='item2', trade_list_name='Runy', trade_price='Ist')]
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","id":"anon123","url":"/shared-list/anon123","count":1}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch.dict(sys.modules, {'db': db}), patch('urllib.request.urlopen', return_value=response) as send:
            result = scope['api_trade_anonymous_sync']()
        db.get_trade_items.assert_called_once_with('Runy')
        payload = json.loads(send.call_args.args[0].data)
        self.assertEqual(payload['title'], 'Moja Anonimowa Lista')
        self.assertEqual(payload['description'], 'Opis w textarea')
        self.assertEqual(payload['password'], 'secret_password')
        self.assertEqual(payload['items'][0]['trade_price'], 'Ist')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['url'], '/shared-list/anon123')

    def test_anonymous_list_update(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_trade_anonymous_update')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = dict(
            list_id='anon123',
            password='secret_password',
            title='Zaktualizowana Lista',
            description='Nowy opis',
            update_items=True,
            list_name='Runy',
            item_ids=['item2']
        )
        db = Mock()
        db.get_trade_items.return_value = [dict(id='item2', trade_list_name='Runy', trade_price='Vex')]
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","message":"Lista zostala zaktualizowana.","url":"/shared-list/anon123","count":1}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch.dict(sys.modules, {'db': db}), patch('urllib.request.urlopen', return_value=response) as send:
            result = scope['api_trade_anonymous_update']()
        req = send.call_args.args[0]
        self.assertIn('/api/marketplace/anonymous-list/anon123/edit', req.full_url)
        payload = json.loads(req.data.decode('utf-8'))
        self.assertEqual(payload['title'], 'Zaktualizowana Lista')
        self.assertEqual(payload['password'], 'secret_password')
        self.assertEqual(result['status'], 'success')

    def test_anonymous_list_delete(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'api_trade_anonymous_delete')
        route.decorator_list = []
        request = Mock()
        request.get_json.return_value = dict(
            list_id='anon123',
            password='secret_password'
        )
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"status":"success","message":"Anonimowa lista zostala usunieta."}'
        scope = dict(request=request, json=json, jsonify=lambda value=None, **kw: value or kw)
        exec(compile(ast.Module(body=[route], type_ignores=[]), '<sync-route>', 'exec'), scope)
        with patch('urllib.request.urlopen', return_value=response) as send:
            result = scope['api_trade_anonymous_delete']()
        req = send.call_args.args[0]
        self.assertIn('/api/marketplace/anonymous-list/anon123/delete', req.full_url)
        payload = json.loads(req.data.decode('utf-8'))
        self.assertEqual(payload['password'], 'secret_password')
        self.assertEqual(result['status'], 'success')


if __name__ == '__main__':
    unittest.main()
