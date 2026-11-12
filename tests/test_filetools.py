from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from campos import Workspace
from filetools import FileTools

class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.ws=Workspace(self.root,approve=lambda _: True)
        self.trash=self.root/'fake-trash';self.trash.mkdir()
        def backend(src):
            dst=self.trash/src.name;src.rename(dst);return dst
        self.tools=FileTools(self.ws,self.root/'state.sqlite',backend)
        self.p=self.root/'file.txt';self.p.write_text('original')
    def tearDown(self):self.tmp.cleanup()
    def test_rename_move_restore_roundtrip(self):
        self.tools.execute({'action':'rename','path':'file.txt','name':'new.txt'})
        (self.root/'folder').mkdir()
        self.tools.execute({'action':'move','path':'new.txt','destination':'folder/new.txt'})
        self.tools.execute({'action':'trash','path':'folder/new.txt'})
        import json
        item=json.loads(self.tools.execute({'action':'trash_list'}))[0]['id']
        self.tools.execute({'action':'restore','id':item})
        self.assertEqual((self.root/'folder/new.txt').read_text(),'original')
        self.assertEqual(self.tools.execute({'action':'trash_list'}),'[]')
    def test_denials_preserve_file(self):
        self.ws.approve=lambda _:False
        for a in [{'action':'rename','path':'file.txt','name':'new.txt'}, {'action':'move','path':'file.txt','destination':'new.txt'}, {'action':'trash','path':'file.txt'}]:
            self.assertIn('recusada',self.tools.execute(a))
            self.assertEqual(self.p.read_text(),'original')
    def test_no_overwrite(self):
        (self.root/'other').write_text('other')
        with self.assertRaises(ValueError):self.tools.execute({'action':'move','path':'file.txt','destination':'other'})
        self.assertEqual(self.p.read_text(),'original')
    def test_restore_conflict_and_missing(self):
        import json
        self.tools.execute({'action':'trash','path':'file.txt'})
        item=json.loads(self.tools.execute({'action':'trash_list'}))[0]['id']
        self.p.write_text('new')
        with self.assertRaises(ValueError):self.tools.execute({'action':'restore','id':item})
        self.p.unlink();(self.trash/'file.txt').unlink()
        with self.assertRaises(ValueError):self.tools.execute({'action':'restore','id':item})
    def test_trash_failure_never_unlinks(self):
        def failed(_):raise OSError('denied')
        self.tools.trash_backend=failed
        with self.assertRaises(ValueError):self.tools.execute({'action':'trash','path':'file.txt'})
        self.assertTrue(self.p.exists())
    def test_links_directory_and_escape_rejected(self):
        (self.root/'link').symlink_to(self.p)
        for path in ['link','fake-trash','../outside']:
            with self.assertRaises(ValueError):self.tools.execute({'action':'trash','path':path})
    def test_readonly_all_mutations(self):
        self.ws.readonly=True
        for action in ['rename','move','trash','restore']:
            self.assertIn('Recusado',self.tools.execute({'action':action}))
    def test_other_workspace_cannot_restore(self):
        import json
        self.tools.execute({'action':'trash','path':'file.txt'})
        item=json.loads(self.tools.execute({'action':'trash_list'}))[0]['id']
        other=self.root/'other';other.mkdir()
        tools=FileTools(Workspace(other),self.root/'state.sqlite')
        with self.assertRaises(ValueError):tools.execute({'action':'restore','id':item})
    def test_changed_during_approval(self):
        def approval(_):self.p.write_text('changed');return True
        self.ws.approve=approval
        with self.assertRaises(ValueError):self.tools.execute({'action':'trash','path':'file.txt'})
        self.assertEqual(self.p.read_text(),'changed')
    def test_native_adapter_arguments(self):
        from filetools import native_trash
        import subprocess
        with patch('filetools.platform.system',return_value='Darwin'), patch('filetools.subprocess.run',return_value=subprocess.CompletedProcess([],0,'/tmp/trash/file.txt\n','')) as run:
            self.assertEqual(native_trash(Path('/tmp/a "quoted".txt')),Path('/tmp/trash/file.txt'))
            self.assertEqual(run.call_args.args[0][-1],'/tmp/a "quoted".txt')
    def test_changed_trash_not_restored(self):
        import json
        self.tools.execute({'action':'trash','path':'file.txt'})
        item=json.loads(self.tools.execute({'action':'trash_list'}))[0]['id']
        (self.trash/'file.txt').write_text('tampered')
        with self.assertRaises(ValueError):self.tools.execute({'action':'restore','id':item})
    def test_corrupt_state_reported_and_file_kept(self):
        (self.root/'state.sqlite').write_bytes(b'nao e sqlite'*100)
        for a in [{'action':'trash_list'},{'action':'trash','path':'file.txt'},{'action':'restore','id':'x'}]:
            with self.assertRaisesRegex(ValueError,'Registro da Lixeira'):self.tools.execute(a)
        self.assertEqual(self.p.read_text(),'original')
    def test_state_connection_closed_on_error(self):
        import sqlite3
        from unittest.mock import MagicMock
        conn=MagicMock();conn.execute.side_effect=sqlite3.DatabaseError('file is not a database')
        with patch('filetools.sqlite3.connect',return_value=conn):
            with self.assertRaises(ValueError):self.tools.execute({'action':'trash_list'})
        conn.close.assert_called_once()
    def test_restore_reports_record_failure_after_move(self):
        import json
        self.tools.execute({'action':'trash','path':'file.txt'})
        item=json.loads(self.tools.execute({'action':'trash_list'}))[0]['id']
        def approval(_):(self.root/'state.sqlite').write_bytes(b'nao e sqlite'*100);return True
        self.ws.approve=approval
        with self.assertRaisesRegex(ValueError,'Arquivo restaurado'):self.tools.execute({'action':'restore','id':item})
        self.assertEqual(self.p.read_text(),'original')
