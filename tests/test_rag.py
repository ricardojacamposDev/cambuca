from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import rag

class RagTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.folder=self.root/'conhecimento';self.folder.mkdir()
        self.kb=rag.Knowledge(self.folder)
    def tearDown(self):self.tmp.cleanup()
    def test_chunks_follow_sections_and_lines(self):
        text='# Férias\n'+'Trinta dias por ano.\n'*80+'\n## Reembolso\nNotas em até 5 dias.\n'
        out=rag.chunks(text)
        self.assertEqual(out[0][0],1);self.assertTrue(out[0][1].startswith('# Férias'))
        self.assertTrue(all(body.startswith('#') for _,body in out))  # continuação repete o título
        self.assertTrue(all(len(body)<=rag.CHUNK*2 for _,body in out))
        self.assertEqual(out[-1],(83,'## Reembolso\nNotas em até 5 dias.'))
        self.assertEqual(len(rag.chunks('x'*3000)),3)
    def test_search_ignores_accents_and_inflection(self):
        (self.folder/'ferias.md').write_text('# Política de férias\nCada pessoa tem 30 dias de férias por ano.')
        (self.folder/'lixeira.txt').write_text('A restauração devolve o arquivo ao local original.')
        (self.folder/'outro.md').write_text('Receita de bolo de cenoura.')
        text,sources=self.kb.context('Quantos dias de FERIAS eu tenho?',5000)
        self.assertEqual(sources,['ferias.md']);self.assertIn('30 dias',text);self.assertIn('[ferias.md, linha 1]',text)
        self.assertEqual(self.kb.context('como restaurar um arquivo',5000)[1],['lixeira.txt'])
        self.assertEqual(self.kb.context('olá, tudo bem?',5000),('',[]))
    def test_refresh_tracks_added_changed_and_removed_files(self):
        (self.folder/'a.md').write_text('alfa')
        self.assertEqual(self.kb.refresh(),1)
        (self.folder/'sub').mkdir();(self.folder/'sub/b.txt').write_text('bravo charlie')
        (self.folder/'a.md').write_text('delta modificado')
        self.assertEqual(self.kb.refresh(),2)
        self.assertEqual(self.kb.context('alfa',5000),('',[]))
        self.assertEqual(self.kb.context('delta',5000)[1],['a.md'])
        self.assertEqual(self.kb.context('bravo',5000)[1],['sub/b.txt'])
        (self.folder/'a.md').unlink()
        self.assertEqual(self.kb.refresh(),1);self.assertEqual(self.kb.context('delta',5000),('',[]))
    def test_only_visible_md_txt_with_limits(self):
        (self.folder/'velho.txt').write_bytes('Ação judicial'.encode('cp1252'))
        (self.folder/'doc.pdf').write_text('acao');(self.folder/'.oculto.md').write_text('acao')
        (self.folder/'.git').mkdir();(self.folder/'.git/x.md').write_text('acao')
        (self.folder/'grande.md').write_text('acao '*100)
        with patch.object(rag,'MAX_FILE',200):
            self.assertEqual(self.kb.refresh(),1);self.assertEqual(self.kb.skipped,1)
            self.assertIn('Ação judicial',self.kb.context('acao',5000)[0])
    def test_symlink_loop_is_scanned_once(self):
        (self.folder/'nota.md').write_text('eco')
        (self.folder/'volta').symlink_to(self.folder)
        self.assertEqual(list(rag.scan(self.folder)[0]),['nota.md'])
    def test_budget_limits_excerpts(self):
        for i in range(6):(self.folder/f'n{i}.md').write_text(f'contrato numero {i} '+'clausula '*100)
        text,sources=self.kb.context('contrato clausula',1500)
        self.assertLessEqual(len(text),1500+100);self.assertEqual(len(sources),1)
    def test_prompt_file(self):
        p=self.root/'prompt.md'
        self.assertEqual(rag.load_prompt(p,100),('',''))
        p.write_text('  Responda de forma breve.\n');self.assertEqual(rag.load_prompt(p,100),('Responda de forma breve.',''))
        p.write_bytes('Você é útil.'.encode('cp1252'));self.assertEqual(rag.load_prompt(p,100)[0],'Você é útil.')
        p.write_text('x'*101);text,warning=rag.load_prompt(p,100)
        self.assertEqual(text,'');self.assertIn('passa de 100',warning)

if __name__ == '__main__': unittest.main()
