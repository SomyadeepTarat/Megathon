from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pypdfium2 as pdfium
pdfmetrics.registerFont(TTFont('Report','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ReportBold','C:/Windows/Fonts/arialbd.ttf'))
text=Path('C:/Users/hp/.codex/attachments/af80ca98-daa0-4839-931f-1661662857db/Pasted text.txt').read_text(encoding='utf-8-sig')
text=text[text.index('M2 Progress Report'):].split('Also rename project name')[0].replace('GreenPrint AI','Kew').replace('—','-').replace('–','-')
body=ParagraphStyle('body',fontName='Report',fontSize=9,leading=12,spaceAfter=6,textColor=colors.HexColor('#242424'))
heading=ParagraphStyle('heading',parent=body,fontName='ReportBold',fontSize=11,leading=14,spaceBefore=9,spaceAfter=6)
sub=ParagraphStyle('sub',parent=body,fontName='ReportBold',fontSize=9.5,leading=12,spaceBefore=5)
title=ParagraphStyle('title',parent=body,fontName='ReportBold',fontSize=18,leading=22,spaceAfter=5)
story=[]
lines=text.splitlines();i=0
while i<len(lines):
 line=lines[i].strip();i+=1
 if not line or line=='Page 1':continue
 if line=='Page 2':story.append(PageBreak());continue
 if '\t' in line:
  rows=[line.split('\t')]
  while i<len(lines) and '\t' in lines[i]:rows.append(lines[i].strip().split('\t'));i+=1
  table=Table([[Paragraph(escape(c), sub if r==0 else body) for c in row] for r,row in enumerate(rows)],colWidths=[340,159])
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeeb')),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#aaaaaa')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),2)]));story += [table,Spacer(1,7)];continue
 style=title if line.startswith('M2 Progress') else heading if line[:2] in ['1.','2.','3.','4.'] and ('Current approach' in line or 'Experiments' in line or 'Progress on' in line or 'Plan for' in line) else sub if line in ['Property-value model','Held-out energy and recommendation evaluation','Software and integration verification','Local LLM evaluation'] or line.startswith('Kew:') else body
 story.append(Paragraph(escape(line),style))
def footer(c,d):
 c.setFont('Report',8);c.setFillColor(colors.HexColor('#777777'));c.drawString(48,26,'Team 254 | Kew');c.drawRightString(A4[0]-48,26,str(d.page))
out='output/pdf/Kew-M2-Progress-Report.pdf'
SimpleDocTemplate(out,pagesize=A4,rightMargin=48,leftMargin=48,topMargin=35,bottomMargin=40,title='M2 Progress Report - Team 254 - Kew',author='Team 254').build(story,onFirstPage=footer,onLaterPages=footer)
doc=pdfium.PdfDocument(out)
print('Pages:',len(doc))
for i,p in enumerate(doc):p.render(scale=1.2).to_pil().save(f'tmp/pdfs/report-{i+1}.png')

