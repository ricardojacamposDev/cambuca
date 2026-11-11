"""Word .docx: leitura estrutural, criação, acréscimo e substituição conservadora."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import uuid
import zipfile

ACTIONS = {'word_read','word_create','word_replace','word_append'}


def library():
    try:
        from docx import Document
        return Document
    except ImportError as exc:
        raise ValueError('Suporte Word ausente. Execute novamente python3 instalar.py na pasta da versão atual.') from exc


def load(data):
    if len(data) > 20_000_000:
        raise ValueError('DOCX maior que 20 MB não suportado.')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(x.file_size for x in archive.infolist()) > 80_000_000:
            raise ValueError('DOCX expandido excede 80 MB.')
        if any('vbaProject' in x for x in archive.namelist()):
            raise ValueError('Documentos com macros não suportados.')
    return library()(io.BytesIO(data))


def paragraphs(doc):
    # Ordem de documento, tabelas aninhadas, cabeçalhos e rodapés.
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    seen = set()
    def visit(container, prefix):
        for i, block in enumerate(container.iter_inner_content()):
            if isinstance(block, Paragraph):
                yield f'{prefix}/p{i}', block
            elif isinstance(block, Table):
                for r, row in enumerate(block.rows):
                    for c, cell in enumerate(row.cells):
                        if cell._tc in seen:
                            continue
                        seen.add(cell._tc)
                        yield from visit(cell, f'{prefix}/t{i}/r{r}/c{c}')
    yield from visit(doc,'body')
    for i, section in enumerate(doc.sections):
        for kind in ['header','footer','first_page_header','first_page_footer','even_page_header','even_page_footer']:
            part = getattr(section,kind)
            if part.is_linked_to_previous:
                continue
            if part._element in seen:
                continue
            seen.add(part._element)
            yield from visit(part,f'section{i}/{kind}')


def simple(p):
    from docx.oxml.ns import qn
    if any(c.tag not in {qn('w:pPr'),qn('w:r')} for c in p._p):
        return False
    return all(c.tag in {qn('w:rPr'),qn('w:t')} for r in p.runs for c in r._r)


def replace_runs(p, old, new):
    """Preserva propriedades dos runs; texto novo herda formato do início."""
    text = ''.join(r.text for r in p.runs)
    starts = []
    at = 0
    while True:
        at = text.find(old, at)
        if at < 0:
            break
        starts.append(at); at += len(old)
    # Substitui do fim para o início para manter os índices anteriores.
    for start in reversed(starts):
        end = start + len(old)
        offsets = []
        pos = 0
        for run in p.runs:
            offsets.append((pos,pos+len(run.text),run));pos += len(run.text)
        matched = [(lo,hi,r) for lo,hi,r in offsets if hi > start and lo < end]
        for i,(lo,hi,r) in enumerate(matched):
            before = r.text[:max(0,start-lo)] if lo <= start else ''
            after = r.text[max(0,end-lo):] if hi >= end else ''
            r.text = before + (new if i == 0 else '') + after


def add_blocks(doc, blocks):
    if not isinstance(blocks,list) or not blocks or len(blocks)>100:
        raise ValueError('Informe entre 1 e 100 blocos.')
    if len(json.dumps(blocks,ensure_ascii=False))>50000:
        raise ValueError('Conteúdo acima do limite de 50 mil caracteres.')
    for block in blocks:
        kind = block.get('type','paragraph')
        if kind in {'paragraph','heading','title'}:
            text = block['text']
            if not isinstance(text,str):
                raise ValueError('Texto deve ser string.')
            if kind == 'title':
                doc.add_paragraph(text,'Title')
            elif kind == 'heading':
                level = int(block.get('level',1))
                if not 1 <= level <= 3:
                    raise ValueError('Nível deve ser 1, 2 ou 3.')
                doc.add_heading(text,level)
            else:
                doc.add_paragraph(text)
        elif kind == 'table':
            rows = block['rows']
            if not isinstance(rows,list) or not rows or len(rows)>100 or not isinstance(rows[0],list) or not 1<=len(rows[0])<=10:
                raise ValueError('Tabela deve ter 1–100 linhas e 1–10 colunas.')
            width=len(rows[0])
            if any(not isinstance(row,list) or len(row)!=width or not all(isinstance(v,str) for v in row) for row in rows):
                raise ValueError('Todas as linhas precisam do mesmo número de células de texto.')
            table=doc.add_table(rows=0,cols=width)
            table.style='Table Grid'
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            borders=OxmlElement('w:tblBorders')
            for side in ['top','left','bottom','right','insideH','insideV']:
                edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'4');edge.set(qn('w:color'),'D9D9D9');borders.append(edge)
            table._tbl.tblPr.append(borders)
            for i,row in enumerate(rows):
                cells=table.add_row().cells
                for j,value in enumerate(row):
                    cells[j].text=value
                    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
                    cells[j].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    if i==0:
                        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAEAEA');cells[j]._tc.get_or_add_tcPr().append(shade)
                    if i==0:
                        for run in cells[j].paragraphs[0].runs:run.bold=True
        else:
            raise ValueError('Tipo de bloco desconhecido.')


def execute(ws,a):
    from campos import display
    action=a['action']
    if action!='word_read' and ws.readonly:
        return 'Recusado: modo somente leitura.'
    path=ws.path(a['path'])
    if path.suffix.lower()!='.docx':
        raise ValueError('Suporte somente a .docx; .doc e .docm não são aceitos.')
    if action=='word_create':
        if path.exists():
            raise ValueError('Destino já existe; use outro nome ou ferramentas de edição.')
        old=None;doc=library()()
        from docx.shared import RGBColor, Pt
        for name in ['Title','Heading 1','Heading 2','Heading 3']:
            doc.styles[name].font.color.rgb=RGBColor(0,0,0)
        for border in list(doc.styles.element.xpath('.//w:pBdr')):
            border.getparent().remove(border)
        doc.styles['Normal'].font.name='Calibri'
        doc.styles['Normal'].font.size=Pt(11)
    else:
        if path.stat().st_size>20_000_000:
            raise ValueError('DOCX maior que 20 MB.')
        old=path.read_bytes();doc=load(old)
    if action=='word_read':
        start=max(0,int(a.get('start',0)));count=min(100,max(1,int(a.get('count',40))))
        entries=[];size=0;total=0
        for index,(key,p) in enumerate(paragraphs(doc)):
            total=index+1
            if index<start or len(entries)>=count or size>16000:
                continue
            entry={'index':index,'id':key,'text':p.text[:4000],'editable':simple(p)}
            entries.append(entry);size+=len(entry['text'])
        return json.dumps({'sha256':hashlib.sha256(old).hexdigest(),'total':total,'next_start':start+len(entries),
                           'blocks':entries,'scope':'Parágrafos, tabelas, cabeçalhos e rodapés. Caixas de texto, comentários e alterações controladas não são extraídos.'},ensure_ascii=False)
    if action in {'word_create','word_append'}:
        add_blocks(doc,a['blocks'])
        display('Criar documento' if action=='word_create' else 'Acrescentar ao fim do documento')
        display(f'Arquivo: {path}\n'+json.dumps(a['blocks'],ensure_ascii=False,indent=2))
    elif action=='word_replace':
        old_text,new_text=a['old'],a['new']
        if not isinstance(old_text,str) or not old_text or not isinstance(new_text,str) or len(new_text)>50000:
            raise ValueError('Substituição deve ter texto antigo não vazio e texto novo de até 50 mil caracteres.')
        targets=[];n=0
        for key,p in paragraphs(doc):
            if a.get('id') and key!=a['id']:
                continue
            occurrences=p.text.count(old_text)
            if occurrences:
                if not simple(p):
                    raise ValueError(f'Parágrafo {key} contém estrutura complexa. Edite-o no Word para preservar campos e objetos.')
                n+=occurrences;targets.append(p)
        expected=a.get('expected_count')
        if not isinstance(expected,int) or isinstance(expected,bool) or expected<1 or n!=expected:
            raise ValueError(f'Foram encontradas {n} ocorrências; informe expected_count exato após ler o documento.')
        display(f'Arquivo: {path}\nOcorrências: {n}\nDE: {old_text}\nPARA: {new_text}')
        for p in targets:replace_runs(p,old_text,new_text)
    else:
        raise ValueError('Ação Word desconhecida.')
    if not ws.approve('Confirmar gravação do Word? Será criado backup antes de editar.'):
        return 'Alteração recusada.'
    if ws.path(a['path']) != path or (path.read_bytes() if path.exists() else None)!=old:
        raise ValueError('Documento mudou durante a revisão; releia antes de editar.')
    if not path.parent.is_dir():
        raise ValueError('Pasta de destino deve existir.')
    backup=None
    if old is not None:
        backup_dir=ws.root/'.campos'/'word-backups'
        if not backup_dir.resolve().is_relative_to(ws.root) or any(p.is_symlink() for p in [ws.root/'.campos',backup_dir]):
            raise ValueError('Pasta de backup insegura.')
        backup_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
        backup=backup_dir/(uuid.uuid4().hex+'-'+path.name)
        with backup.open('xb') as f:f.write(old)
        backup.chmod(0o600)
    fd,tempname=tempfile.mkstemp(dir=path.parent,prefix='.cambuca-word-',suffix='.docx')
    os.close(fd);temp=Path(tempname)
    try:
        doc.save(temp)
        load(temp.read_bytes())
        if (path.read_bytes() if path.exists() else None)!=old:
            raise ValueError('Arquivo mudou durante a gravação; original preservado.')
        if old is None:
            os.link(temp,path)
        else:
            os.chmod(temp,path.stat().st_mode & 0o777)
            os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)
    return f'Word gravado: {path.relative_to(ws.root)}'+(f'. Backup anterior: {backup}' if backup else '')
