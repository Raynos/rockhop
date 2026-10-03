"""Build the standalone, editable reading copy from the authoritative Markdown.
Uses only stdlib and immutable existing screenshots; it does not render riders.
"""
from pathlib import Path
import base64, hashlib, html, json, re

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
MD = HERE / 'README.md'
references = []

def inline(text):
    text = html.escape(text)
    def link(match):
        label, target = match.groups()
        if target.startswith('https://'):
            return f'<a href="{target}">{label}</a>'
        path = (HERE / html.unescape(target)).resolve().relative_to(ROOT)
        references.append(str(path))
        return f'{label}<sup><a href="#ref-{len(references)}">[{len(references)}]</a></sup>'
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', link, text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text

lines = MD.read_text().splitlines(); result = []; i = 0; headings = []
while i < len(lines):
    line = lines[i]
    if not line.strip():
        i += 1; continue
    if line.startswith('#'):
        level = len(line) - len(line.lstrip('#')); title = line[level:].strip()
        slug = re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')
        result.append(f'<h{level} id="{slug}">{inline(title)}</h{level}>')
        if level == 2: headings.append((slug, title))
        i += 1; continue
    if line.startswith('|'):
        rows=[]
        while i < len(lines) and lines[i].startswith('|'):
            cells=[c.strip() for c in lines[i].strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',c) for c in cells): rows.append(cells)
            i += 1
        header=rows.pop(0)
        result.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in header)+'</tr></thead><tbody>')
        for row in rows:
            assert len(row)==len(header),(row,header)
            result.append('<tr>'+''.join('<td data-label="'+html.escape(h,quote=True)+'">'+inline(c)+'</td>' for h,c in zip(header,row))+'</tr>')
        result.append('</tbody></table></div>');continue
    if re.match(r'^\d+\. ',line):
        result.append('<ol>')
        while i < len(lines) and re.match(r'^\d+\. ',lines[i]):
            item=re.sub(r'^\d+\. ','',lines[i]);i+=1
            while i < len(lines) and lines[i].startswith('   '):item+=' '+lines[i].strip();i+=1
            result.append('<li>'+inline(item)+'</li>')
        result.append('</ol>');continue
    para=[]
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')) and not re.match(r'^\d+\. ',lines[i]):
        para.append(lines[i].strip());i+=1
    result.append('<p>'+inline(' '.join(para))+'</p>')

pictures = [
 ('Approved target', 'harness/out/local-cloud-reconcile-2026-10-03/storyboard/Rockhop-rider-concept-overview.png', 'Approved storyboard overview. A target image, not a generated model render.'),
 ('Preferred generated assembly', 'docs/evidence/hero-remaster/one-rider-v2/parent-assembly/white-target02/target-left-actual-right.png', 'Historical nine-view comparison: target LEFT, actual generated assembly RIGHT. Body7.2/face7.5 historical parent judgment; no final acceptance.'),
 ('Actual preferred rider sitting frames', 'harness/out/local-cloud-reconcile-2026-10-03/photos/Preferred-body11-standing-to-sit-actual24frames.jpg', 'Decoded actual body11 side clip,24ordered frames. Seated compression/support remains unresolved. Play the Library film before judging motion.'),
 ('Newer structural fallback', 'harness/out/local-cloud-reconcile-2026-10-03/photos/Local-finite208-unrigged-gray-front.png', 'Actual finite208 gray front. Unrigged structural fallback, not preferred PBR appearance and not a moving anatomy pass.'),
]
figures=[];image_pins=[]
for title,path,caption in pictures:
    data=(ROOT/path).read_bytes();mime='image/jpeg' if path.endswith('.jpg') else 'image/png'
    figures.append(f'<figure><h3>{html.escape(title)}</h3><img alt="{html.escape(title)}" src="data:{mime};base64,{base64.b64encode(data).decode()}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    image_pins.append({'title':title,'repo_path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
source_index='<section id="source-index"><h2>Repository evidence index</h2><p>These paths require the Rockhop checkout; the document is readable without it.</p><ol>'+''.join(f'<li id="ref-{n}"><code>{html.escape(p)}</code></li>' for n,p in enumerate(references,1))+'</ol></section>'
nav='<details><summary>Contents and evidence</summary><nav aria-label="Contents">'+''.join(f'<a href="#{slug}">{html.escape(title)}</a>' for slug,title in headings)+'</nav></details>'
css='''body{margin:0;background:#f2f1ee;color:#191919;font:17px/1.6 system-ui,-apple-system,sans-serif}main{max-width:1160px;margin:auto;background:white;padding:40px 48px}h1,h2,h3{color:#000;line-height:1.25}h1{font-size:38px;margin:0 0 24px}h2{font-size:27px;margin:48px 0 20px;scroll-margin-top:30px}h3{font-size:20px}p{max-width:94ch}a{color:#174d85;text-decoration:underline}code{font-size:.83em;overflow-wrap:anywhere}sup{font-size:.66em;margin-left:3px}table{width:100%;border-collapse:collapse;font-size:15px;line-height:1.55}th,td{vertical-align:top;text-align:left;border:1px solid #d5d5d5;padding:14px;overflow-wrap:anywhere}th{background:#efefec;color:#000}td:first-child{width:25%}td{min-width:0}figure{margin:28px 0;padding:20px;border:1px solid #d5d5d5;break-inside:avoid}img{display:block;max-width:100%;height:auto;margin:12px auto}figcaption{font-size:14px;color:#444}nav{display:flex;gap:10px 20px;flex-wrap:wrap;padding:20px 0;border-bottom:1px solid #ddd}button{background:#222;color:white;font:inherit;padding:10px 15px;border:0;border-radius:5px;cursor:pointer}.note{font-size:14px;color:#444}.table{margin:22px 0}li{margin:12px 0}[contenteditable]:focus{outline:2px solid #bbb}#source-index code{font-size:13px}@media(max-width:650px){main{padding:24px 16px}h1{font-size:29px}h2{font-size:24px}table,tbody,tr,td{display:block;width:auto}thead{display:none}tr{margin-bottom:16px;border:1px solid #ccc}td,td:first-child{width:auto;border:0;border-bottom:1px solid #eee}td:before{content:attr(data-label);display:block;font-weight:650;margin-bottom:6px}figure{padding:12px}nav{font-size:14px}}@media print{body{background:white}main{padding:0;max-width:none}nav,button{display:none}h2{break-after:avoid}tr{break-inside:avoid}a{color:black}}'''
script='''document.querySelector('#save').onclick=()=>{const copy=document.documentElement.cloneNode(true);copy.querySelector('#save').textContent='Save edited copy';const blob=new Blob(['<!doctype html>\\n'+copy.outerHTML],{type:'text/html;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='Rockhop-rider-next-agent-handoff-edited.html';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000)};'''
content='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Rockhop rider next-agent handoff</title><style>'+css+'</style></head><body><main><button id="save">Save edited copy</button><p class="note">Editable offline copy · 2026-10-03. Click the text to edit, then save. Repository Markdown is authoritative. All four images are embedded.</p>'+nav+'<article contenteditable="true" spellcheck="false">'+''.join(result)+'<section id="reference-images"><h2>Reference images</h2><p>Source identity and diagnostic stills only. Actual films remain linked in the catalogue; stills cannot establish motion acceptance.</p>'+''.join(figures)+'</section>'+source_index+'</article></main><script>'+script+'</script></body></html>'
(HERE/'Rockhop-rider-next-agent-handoff.html').write_text(content)
(HERE/'reading-copy-provenance.json').write_text(json.dumps({'markdown_sha256':hashlib.sha256(MD.read_bytes()).hexdigest(),'embedded_images':image_pins,'source_reference_count':len(references),'html_sha256':hashlib.sha256(content.encode()).hexdigest(),'html_bytes':len(content.encode()),'limits':'Reading-copy render is document QA, not rider/game/animation acceptance.'},indent=2)+'\n')
print(json.dumps({'html_bytes':len(content.encode()),'images':len(image_pins),'source_references':len(references)}))
