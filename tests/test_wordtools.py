import json
from pathlib import Path
import tempfile
import unittest
from docx import Document
from docx.oxml import OxmlElement
from campos import Workspace
import wordtools

class WordTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.ws=Workspace(self.root,approve=lambda _:True)
        self.p=self.root/'sample.docx'
        doc=Document();p=doc.add_paragraph();p.add_run('Olá ').bold=True;p.add_run('Ricardo').italic=True
        doc.add_table(rows=1,cols=1).cell(0,0).text='Ricardo'
        doc.sections[0].header.paragraphs[0].text='Cabeçalho'
        doc.save(self.p)
    def tearDown(self):self.tmp.cleanup()
    def test_read_body_table_header(self):
        result=json.loads(self.ws.execute({'action':'word_read','path':'sample.docx'}))
        text=str(result)
        self.assertIn('Olá Ricardo',text);self.assertIn('Cabeçalho',text);self.assertIn('/t',text)
    def test_replace_across_runs_preserves_style_and_backup(self):
        before=self.p.read_bytes()
        self.ws.execute({'action':'word_replace','path':'sample.docx','old':'Olá Ricardo','new':'Bom dia','expected_count':1})
        doc=Document(self.p)
        self.assertEqual(doc.paragraphs[0].text,'Bom dia');self.assertTrue(doc.paragraphs[0].runs[0].bold)
        self.assertEqual(doc.tables[0].cell(0,0).text,'Ricardo')
        backup=list((self.root/'.campos/word-backups').iterdir())[0]
        self.assertEqual(backup.read_bytes(),before)
    def test_replace_in_table(self):
        self.ws.execute({'action':'word_replace','path':'sample.docx','old':'Ricardo','new':'Maria','expected_count':2})
        self.assertEqual(Document(self.p).tables[0].cell(0,0).text,'Maria')
    def test_count_mismatch_no_write(self):
        before=self.p.read_bytes()
        with self.assertRaises(ValueError):self.ws.execute({'action':'word_replace','path':'sample.docx','old':'Ricardo','new':'Maria','expected_count':1})
        self.assertEqual(self.p.read_bytes(),before)
    def test_denial_and_readonly(self):
        before=self.p.read_bytes();self.ws.approve=lambda _:False
        self.ws.execute({'action':'word_append','path':'sample.docx','blocks':[{'text':'new'}]})
        self.assertEqual(self.p.read_bytes(),before)
        self.ws.readonly=True
        for action in ['word_create','word_append','word_replace']:
            self.assertIn('Recusado',self.ws.execute({'action':action,'path':'sample.docx'}))
    def test_complex_paragraph_rejected(self):
        doc=Document(self.p);r=doc.paragraphs[0].runs[0];r._r.append(OxmlElement('w:fldChar'));doc.save(self.p)
        before=self.p.read_bytes()
        with self.assertRaises(ValueError):self.ws.execute({'action':'word_replace','path':'sample.docx','old':'Olá','new':'Oi','expected_count':1})
        self.assertEqual(self.p.read_bytes(),before)
    def test_create_and_append(self):
        self.ws.execute({'action':'word_create','path':'new.docx','blocks':[{'type':'title','text':'Título'},{'type':'table','rows':[['A','B'],['1','2']]}]})
        self.ws.execute({'action':'word_append','path':'new.docx','blocks':[{'text':'Final'}]})
        doc=Document(self.root/'new.docx');self.assertEqual(doc.paragraphs[-1].text,'Final');self.assertEqual(len(doc.tables),1)
        with self.assertRaises(ValueError):self.ws.execute({'action':'word_create','path':'new.docx','blocks':[{'text':'overwrite'}]})
    def test_plain_write_word_blocked(self):
        with self.assertRaises(ValueError):self.ws.execute({'action':'write','path':'bad.docx','content':'not a docx'})
    def test_concurrent_change_preserved(self):
        def approval(_):self.p.write_bytes(b'external');return True
        self.ws.approve=approval
        with self.assertRaises(ValueError):self.ws.execute({'action':'word_append','path':'sample.docx','blocks':[{'text':'new'}]})
        self.assertEqual(self.p.read_bytes(),b'external')
    def test_multi_replacement_same_run(self):
        doc=Document();p=doc.add_paragraph('a-a-a');wordtools.replace_runs(p,'a','long')
        self.assertEqual(p.text,'long-long-long')
