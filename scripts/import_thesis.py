#!/usr/bin/env python3
"""Extract thesis evidence locally without modifying originals or publishing full text."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from docx import Document
from pypdf import PdfReader


def extract(docx,pdf,output):
    output=Path(output)
    if output.exists():
        raise ValueError('证据目录已存在，请使用新目录')
    word=Document(docx)
    text='\n'.join(p.text for p in word.paragraphs if p.text.strip())
    text+='\n'+'\n'.join(' | '.join(c.text for c in r.cells) for t in word.tables for r in t.rows)
    headings=[p.text.strip() for p in word.paragraphs if p.style and ('Heading' in p.style.name or '标题' in p.style.name) and p.text.strip()]
    reader=PdfReader(pdf)
    pages=[p.extract_text() or '' for p in reader.pages]
    ptext='\n'.join(f'[PDF page {i+1}]\n{p}' for i,p in enumerate(pages))
    if not any(p.strip() for p in pages):
        raise ValueError('PDF 无可提取文字，请先通过 OCR 检查，不能声称核对完成')
    normalize=lambda s: re.sub(r'\s+','',s)
    # A diagnostic only: output must be read, not auto-accepted as matching finals.
    snippets=[normalize(p.text) for p in word.paragraphs if len(p.text.strip())>30]
    pdfnorm=normalize(ptext)
    matched=sum(s in pdfnorm for s in snippets)
    sources=[{'format':f,'filename':Path(p).name,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()} for f,p in [('Word',docx),('PDF',pdf)]]
    metadata={'sources':sources,'pdf_pages':len(pages),'word_paragraphs':len(word.paragraphs),'word_tables':len(word.tables),
       'headings':headings,'paragraph_exact_coverage':matched/len(snippets) if snippets else None,
       'status':'extracted_for_review','note':'文本重合率仅用于定位差异，不自动认定两份文件为相同最终版；需核对正文、表格、公式与图注。'}
    output.mkdir(parents=True)
    (output/'word.txt').write_text(text,encoding='utf-8'); (output/'pdf.txt').write_text(ptext,encoding='utf-8')
    (output/'evidence.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    return {k:v for k,v in metadata.items() if k!='headings'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='导入最终版 Word 和 PDF，生成仅供本地核对的证据')
    parser.add_argument('--docx',required=True); parser.add_argument('--pdf',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(extract(args.docx,args.pdf,args.output),ensure_ascii=False,indent=2))
