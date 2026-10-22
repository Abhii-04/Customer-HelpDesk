"""HTTP integration checks; isolate inference so these run offline."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from backend.app import app


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_home_and_assets(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        for asset in ('chat.js', 'styles.css'):
            self.assertEqual(self.client.get('/static/' + asset).status_code, 200)

    def test_order_request_reaches_agent(self):
        from agent.nodes.handlers import handle
        with patch('backend.app.classify', new_callable=AsyncMock) as classify:
            classify.return_value = SimpleNamespace(intent='order-status', intent_confidence=1, wants_human=0, complexity=0)
            with patch('backend.app.handle', wraps=handle) as handler:
                response = self.client.post('/start-agent', data={'user_input': '  kh-1042  '})
                self.assertEqual(response.status_code, 200)
                self.assertIn('KH-1042', response.json()['response'])
                handler.assert_awaited_once_with('tool', 'What is the status of order KH-1042?')

    def test_invalid_input_does_not_call_agent(self):
        with patch('backend.app.run_agent', new_callable=AsyncMock) as agent:
            for data in ({}, {'user_input': '   '}, {'user_input': 'x' * 4001}):
                self.assertEqual(self.client.post('/start-agent', data=data).status_code, 422)
            agent.assert_not_awaited()

    def test_generated_response_is_checked(self):
        for accepted in (True, False):
            with self.subTest(accepted=accepted), patch('backend.app.classify', new_callable=AsyncMock) as classify, patch('backend.app.handle', new_callable=AsyncMock) as handle, patch('backend.app.check_reply', new_callable=AsyncMock) as check:
                classify.return_value = SimpleNamespace(intent='product-question', intent_confidence=1, wants_human=0, complexity=0)
                handle.return_value = ('Catalog answer', 'Catalog', 0)
                check.return_value = SimpleNamespace(send=accepted)
                response = self.client.post('/start-agent', data={'user_input': 'Product question'})
                self.assertEqual(response.json()['response'], 'Catalog answer' if accepted else 'Reply needs human review.')
                check.assert_awaited_once_with('Product question', 'Catalog answer', 'Catalog')

    def test_failure_does_not_expose_internal_error(self):
        with patch('backend.app.run_agent', side_effect=RuntimeError('secret-token')):
            response = self.client.post('/start-agent', data={'user_input': 'hello'})
            self.assertEqual(response.status_code, 500)
            self.assertNotIn('secret-token', response.text)


if __name__ == '__main__':
    unittest.main()
