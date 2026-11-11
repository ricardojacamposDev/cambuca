import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import campos

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ws = campos.Workspace(self.root, approve=lambda _: True)
    def tearDown(self):
        self.tmp.cleanup()
    def test_escape_and_secrets(self):
        for name in ['../outside', '.env', '.git/config', 'secret.pem']:
            with self.assertRaises(ValueError): self.ws.path(name)
        (self.root/'link').symlink_to('/tmp')
        with self.assertRaises(ValueError): self.ws.path('link/outside')
    def test_denial_does_not_write(self):
        self.ws.approve = lambda _: False
        self.ws.execute({'action':'write','path':'x','content':'hello'})
        self.assertFalse((self.root/'x').exists())
    def test_write_read_search(self):
        self.ws.execute({'action':'write','path':'src/x.py','content':'hello\nworld\n'})
        self.assertIn('2: world', self.ws.execute({'action':'read','path':'src/x.py','start':2}))
        self.assertIn('src/x.py:1:', self.ws.execute({'action':'search','text':'hello'}))
    def test_readonly(self):
        self.ws.readonly = True
        self.assertIn('Recusado', self.ws.execute({'action':'write'}))
        self.assertIn('Recusado', self.ws.execute({'action':'run'}))
    def test_conflicting_edit(self):
        p = self.root/'a'
        p.write_text('old')
        def approval(_):
            p.write_text('external edit')
            return True
        self.ws.approve = approval
        with self.assertRaises(ValueError):
            self.ws.execute({'action':'write','path':'a','content':'new'})
        self.assertEqual(p.read_text(), 'external edit')
    def test_command_denied(self):
        self.ws.approve = lambda _: False
        self.ws.execute({'action':'run','argv':[sys.executable,'-c',"open('bad','w').write('x')"]})
        self.assertFalse((self.root/'bad').exists())
    def test_command_timeout_and_output_bound(self):
        result = campos.run_command([sys.executable,'-c','import time; time.sleep(10)'], self.root, .1)
        self.assertIn('tempo limite', result)
        result = campos.run_command([sys.executable,'-c',"print('x'*100000)"], self.root)
        self.assertLess(len(result), campos.LIMIT + 100)
    def test_protocol(self):
        self.assertEqual(campos.parse_action('```json\n{"action":"final","text":"ok"}\n```')['text'],'ok')
        for bad in ['[]','{"action":"delete"}','not json']:
            with self.assertRaises(ValueError): campos.parse_action(bad)
    def test_http_agent_loop(self):
        (self.root/'demo.txt').write_text('conteúdo local')
        seen = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(inner):
                payload = json.loads(inner.rfile.read(int(inner.headers['Content-Length'])))
                seen.append(payload)
                action = {'action':'read','path':'demo.txt'} if len(seen)==1 else {'action':'final','text':'Concluído'}
                raw = json.dumps({'choices':[{'message':{'content':json.dumps(action)},'finish_reason':'stop'}]}).encode()
                inner.send_response(200)
                inner.end_headers()
                inner.wfile.write(raw)
            def log_message(self, *a): pass
        server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            history = [{'role':'system','content':campos.SYSTEM}]
            campos.turn(history, 'leia demo', self.ws, server.server_port)
            self.assertEqual(len(seen),2)
            self.assertIn('conteúdo local',seen[1]['messages'][-1]['content'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    def test_truncated_action_is_not_executed(self):
        response = {'choices':[{'message':{'content':'{"action":"write","path":"bad","content":"x"}'},'finish_reason':'length'}]}
        with patch.object(campos,'request',return_value=response):
            campos.turn([], 'write', self.ws, 8080)
        self.assertFalse((self.root/'bad').exists())

if __name__ == '__main__': unittest.main()
