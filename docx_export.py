"""Generate portable Word documents from Atlas editor HTML (safe basic formatting)."""
import io
from html.parser import HTMLParser

from docx import Document
from docx.shared import Cm, Pt, RGBColor


class DocBuilder(HTMLParser):
    def __init__(self,doc):
        super().__init__(convert_charrefs=True)
        self.doc=doc
        self.p=None
        self.bold=0; self.italic=0
        self.list_type=[]
        self.pending_heading=None

    def handle_starttag(self,tag,attrs):
        if tag in ('h1','h2','h3','p','div','blockquote','li'):
            if tag.startswith('h'):
                level={'h1':1,'h2':2,'h3':3}[tag]
                self.p=self.doc.add_paragraph(style=f'Heading {level}')
            elif tag=='li':
                self.p=self.doc.add_paragraph(style='List Number' if self.list_type and self.list_type[-1]=='ol' else 'List Bullet')
            elif tag=='blockquote':
                self.p=self.doc.add_paragraph(style='Quote')
            else:
                self.p=self.doc.add_paragraph()
        elif tag=='br':
            if not self.p:self.p=self.doc.add_paragraph()
            self.p.add_run().add_break()
        elif tag in ('strong','b'):self.bold+=1
        elif tag in ('em','i'):self.italic+=1
        elif tag in ('ul','ol'):self.list_type.append(tag)

    def handle_endtag(self,tag):
        if tag in ('strong','b'):self.bold=max(self.bold-1,0)
        elif tag in ('em','i'):self.italic=max(self.italic-1,0)
        elif tag in ('ul','ol') and self.list_type:self.list_type.pop()
        elif tag in ('p','div','li','h1','h2','h3','blockquote'):self.p=None

    def handle_data(self,data):
        if not data:return
        if self.p is None:self.p=self.doc.add_paragraph()
        run=self.p.add_run(data)
        run.bold=self.bold>0
        run.italic=self.italic>0


def export_docx(title,html):
    d=Document()
    sec=d.sections[0]
    sec.top_margin=Cm(2.3);sec.bottom_margin=Cm(2.3)
    sec.left_margin=Cm(2.5);sec.right_margin=Cm(2.5)
    normal=d.styles['Normal']
    normal.font.name='Aptos';normal.font.size=Pt(10.5)
    normal.paragraph_format.space_after=Pt(7)
    for n,size in [('Heading 1',17),('Heading 2',12.5),('Heading 3',11)]:
        s=d.styles[n];s.font.name='Aptos Display';s.font.size=Pt(size);s.font.color.rgb=RGBColor(20,79,117)
    parser=DocBuilder(d)
    parser.feed(str(html))
    if not any(p.text.strip() for p in d.paragraphs):d.add_paragraph(title)
    b=io.BytesIO();d.save(b);return b.getvalue()
