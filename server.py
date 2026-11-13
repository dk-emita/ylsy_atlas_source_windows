"""Local-only HTTP bridge for the YLSY Atlas offline desktop UI."""
from __future__ import annotations
import base64
import io
import json
import mimetypes
import os
import re
import secrets
import threading
import webbrowser
import shutil
import subprocess
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs,quote

from guide import GUIDE, TEMPLATES
from storage import Store
from drive_sync import CloudController

ROOT=Path(__file__).resolve().parent
WEB=ROOT/'web'
ASSETS=ROOT/'assets'
PDF=ROOT/'resources'/'ylsy_us_graduate_application_guide.pdf'
PDF_NAME='ylsy_us_graduate_application_guide.pdf'
LEGACY_PDF_NAME='YLSY_ABD_Lisansustu_Basvuru_Rehberi.pdf'

def guide_pdf_path(store):
    """Prefer the per-user imported file, then a bundled or EXE-adjacent resource."""
    import sys
    candidates=[store.root/'guide'/PDF_NAME,store.root/'guide'/LEGACY_PDF_NAME,PDF]
    if getattr(sys,'frozen',False):
        candidates.append(Path(sys.executable).resolve().parent/'resources'/PDF_NAME)
    candidates.append(ROOT.parent/'resources'/PDF_NAME)
    for f in candidates:
        if f.is_file() and f.stat().st_size>8 and f.open('rb').read(5)==b'%PDF-':
            return f
    return None



def launch_normal_browser(url: str, preference: str = 'default'):
    """Use user's *normal* browser profile, not Atlas's temporary app-mode profile.
    Browser controls whether it opens a tab or window; Atlas never handles passwords.
    """
    preference = preference if preference in {'default','chrome','edge','firefox'} else 'default'
    if os.name == 'nt' and preference != 'default':
        names = {'chrome': ('chrome.exe', 'Google/Chrome/Application/chrome.exe'),
                 'edge': ('msedge.exe', 'Microsoft/Edge/Application/msedge.exe'),
                 'firefox': ('firefox.exe', 'Mozilla Firefox/firefox.exe')}
        executable, suffix = names[preference]
        candidates = []
        found = shutil.which(executable)
        if found: candidates.append(Path(found))
        for env_key in ('LOCALAPPDATA','PROGRAMFILES','PROGRAMFILES(X86)'):
            base = os.environ.get(env_key)
            if base: candidates.append(Path(base)/suffix)
        binary = next((str(x) for x in candidates if x.is_file()), None)
        if binary is None:
            raise ValueError('Seçilen tarayıcı bu bilgisayarda bulunamadı. Ayarlardan varsayılan tarayıcıyı seçebilirsiniz.')
        args = [binary, url] if preference != 'firefox' else [binary, '-new-tab', url]
        subprocess.Popen(args, close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    if os.name == 'nt':
        try:
            os.startfile(url)  # type: ignore[attr-defined]
        except OSError:
            if not webbrowser.open(url, new=2, autoraise=True):
                raise ValueError('Varsayılan tarayıcı açılamadı')
    elif not webbrowser.open(url, new=2, autoraise=True):
        raise ValueError('Varsayılan tarayıcı açılamadı')


def dictionary_lookup(word):
    """Fetch English definitions, Turkish translations and genuine cited example sentences."""
    import requests
    word=str(word or '').strip().lower()
    if not re.fullmatch(r"[a-z][a-z -]{0,60}",word): raise ValueError('Geçerli bir İngilizce kelime yazın.')
    headers={'User-Agent':'YLSYAtlas/4.0.0 (local vocabulary lookup)'}
    response=requests.get('https://api.dictionaryapi.dev/api/v2/entries/en/'+quote(word,safe=' -'),headers=headers,timeout=7)
    if response.status_code==404:return {'meanings':[],'examples':[],'source_found':False}
    response.raise_for_status(); data=response.json(); definitions=[]; examples=[]
    for entry in data if isinstance(data,list) else []:
        for meaning in entry.get('meanings',[]):
            for item in meaning.get('definitions',[]):
                definition=str(item.get('definition','')).strip()
                if definition and definition not in definitions: definitions.append(definition)
                example=str(item.get('example','')).strip()
                if example and example not in examples: examples.append(example)
    translations=[]
    for definition in definitions[:8]:
        try:
            translated=requests.get('https://api.mymemory.translated.net/get',params={'q':definition[:450],'langpair':'en|tr'},headers=headers,timeout=6).json()
            candidates=[translated.get('responseData',{}).get('translatedText','')]
            candidates += [x.get('translation','') for x in translated.get('matches',[]) if float(x.get('quality',0) or 0)>=70]
            for candidate in candidates:
                candidate=re.sub(r'<[^>]+>','',str(candidate)).strip()
                if candidate and candidate.lower()!=definition.lower() and candidate not in translations: translations.append(candidate)
                if len(translations)>=5: break
        except Exception: continue
        if len(translations)>=5: break
    # Supplement dictionary examples with real, Turkish-translated community sentences.
    if len(examples)<3:
        try:
            corpus=requests.get('https://api.tatoeba.org/v1/sentences',params={'lang':'eng','q':word,'sort':'relevance','trans:lang':'tur','showtrans':'matching','limit':20},headers=headers,timeout=7).json()
            for row in corpus.get('data',[]):
                sentence=str(row.get('text','')).strip()
                if len(sentence.split())<4 or not re.search(r'(?i)(?<![a-z])'+re.escape(word)+r'(?![a-z])',sentence): continue
                if not any(t.get('lang')=='tur' for t in row.get('translations',[])): continue
                if any(re.sub(r'[^a-z]','',sentence.lower())==re.sub(r'[^a-z]','',x.lower().split(' [Tatoeba:',1)[0]) for x in examples): continue
                credit=f" [Tatoeba: {row.get('owner','community')}, CC BY 2.0 FR, https://tatoeba.org/en/sentences/show/{row.get('id')}]"
                examples.append(sentence+credit)
                if len(examples)>=3: break
        except Exception: pass
    return {'meanings':translations,'examples':examples[:3],'source_found':True}

def create_server(root=None,port=0,token=None,start_cloud_worker=True,secret_store=None):
    store=Store(root)
    cloud=CloudController(store, ROOT / "resources", start_worker=start_cloud_worker, secret_store=secret_store)
    token=token or secrets.token_urlsafe(36)
    class Handler(BaseHTTPRequestHandler):
        server_version='YLSYAtlasDesktop/4.0.0'
        protocol_version='HTTP/1.1'

        def log_message(self,format,*args):
            # No personal data or full query strings in access logs.
            if os.environ.get('ATLAS_DEBUG')=='1':super().log_message(format,*args)

        def _send(self,content,status=200,mime='application/json; charset=utf-8',attachment=None):
            if isinstance(content,(dict,list)):
                content=json.dumps(content,ensure_ascii=False).encode('utf-8')
            elif isinstance(content,str):content=content.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(content)))
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Frame-Options','SAMEORIGIN')
            if attachment:
                safe='YLSY-Atlas-'+attachment.split('.')[-1]
                self.send_header('Content-Disposition',f"attachment; filename=\"{safe}\"; filename*=UTF-8''{urllib.parse.quote(attachment)}")
            self.end_headers()
            try:self.wfile.write(content)
            except (BrokenPipeError,ConnectionAbortedError,ConnectionResetError):pass

        def _authorized(self,query):
            provided=self.headers.get('X-Atlas-Token','')
            if not provided and query:
                provided=parse_qs(query).get('token',[''])[0]
            return secrets.compare_digest(provided,token)

        def _method(self):
            u=urlparse(self.path)
            if u.path.startswith('/api/') or u.path=='/pdf':
                if not self._authorized(u.query):return self._send({'error':'Erişim anahtarı gerekli'},403)
            try:
                if self.command=='GET':return self._get(u)
                if self.command=='POST':return self._post(u)
                if self.command=='PUT':return self._put(u)
                if self.command=='DELETE':return self._delete(u)
                return self._send({'error':'Geçersiz işlem'},405)
            except KeyError as e:return self._send({'error':str(e)},404)
            except (ValueError,TypeError,OverflowError,sqlite_error()) as e:return self._send({'error':str(e)},400)
            except Exception as e:
                if os.environ.get('ATLAS_DEBUG')=='1':
                    import traceback;traceback.print_exc()
                return self._send({'error':'İşlem sırasında beklenmeyen bir hata oluştu.'},500)

        def do_GET(self):return self._method()
        def do_POST(self):return self._method()
        def do_PUT(self):return self._method()
        def do_DELETE(self):return self._method()

        def _body(self,max_length=25*1024*1024):
            length=int(self.headers.get('Content-Length','0') or 0)
            if length<0 or length>max_length:raise ValueError('İstek boyutu izin verilen sınırı aşıyor')
            data=self.rfile.read(length)
            return json.loads(data.decode('utf-8')) if data else {}

        def _get(self,u):
            path=u.path
            if path=='/':return self._send((WEB/'index.html').read_bytes(),mime='text/html; charset=utf-8')
            if path=='/cloud.js':return self._send((WEB/'cloud.js').read_bytes(),mime='text/javascript; charset=utf-8')
            if path=='/app.js':return self._send((WEB/'app.js').read_bytes(),mime='text/javascript; charset=utf-8')
            if path=='/styles.css':return self._send((WEB/'styles.css').read_bytes(),mime='text/css; charset=utf-8')
            if path=='/desktop.css':return self._send((WEB/'desktop.css').read_bytes(),mime='text/css; charset=utf-8')
            if path=='/desktop-redesign.css':return self._send((WEB/'desktop-redesign.css').read_bytes(),mime='text/css; charset=utf-8')
            if path=='/desktop.js':return self._send((WEB/'desktop.js').read_bytes(),mime='text/javascript; charset=utf-8')
            if path=='/app-icon.png':return self._send((ASSETS/'atlas-icon-512.png').read_bytes(),mime='image/png')
            if path=='/brand-icon.png':return self._send((ASSETS/'atlas-brand-hires.png').read_bytes(),mime='image/png')
            if path=='/turbine-banner.png':return self._send((ASSETS/'approved-turbine-banner.png').read_bytes(),mime='image/png')
            if path=='/pdf':
                f=guide_pdf_path(store)
                if f is None:
                    return self._send({'error':'MEB rehberi bulunamadı. Rehber ekranındaki “PDF Seç” düğmesini kullanın.'},404)
                return self._send(f.read_bytes(),mime='application/pdf')
            if path=='/api/dictionary':return self._send(dictionary_lookup(parse_qs(u.query).get('word',[''])[0]))
            if path=='/api/cloud/status':return self._send(cloud.current())
            if path=='/api/cloud/folders':
                parent=parse_qs(u.query).get('parent',['root'])[0]
                return self._send(cloud.folders(parent))
            if path=='/api/guide-pdf/status':
                f=guide_pdf_path(store)
                return self._send({'available':bool(f),'size':f.stat().st_size if f else 0,'name':PDF_NAME})
            if path=='/api/guide':
                return self._send([dict(id=k,title=title,page=page,level=level,summary=summary,group=group) for k,title,page,level,summary,group in GUIDE])
            if path=='/api/templates':
                return self._send([dict(title=title,kind=kind,ref_key=ref,page=page,html=html) for title,kind,ref,page,html in TEMPLATES])
            if path=='/api/settings':return self._send(store.get_settings())
            if path=='/api/overview':return self._send(store.overview())
            if path=='/api/search':return self._send(store.search(parse_qs(u.query).get('q',[''])[0]))
            if path=='/api/backup':return self._send(store.backup(),mime='application/zip',attachment='YLSY-Atlas-Yedek.zip')
            if path=='/api/tasks.csv':return self._send(store.tasks_csv(),mime='text/csv; charset=utf-8',attachment='YLSY-Atlas-Gorevler.csv')
            if path.startswith('/api/'):
                parts=path.strip('/').split('/')
                if len(parts)==2:return self._send(store.all(parts[1]))
                if len(parts)==3 and parts[2].isdigit():return self._send(store.one(parts[1],parts[2]))
                if len(parts)==4 and parts[1]=='documents' and parts[2].isdigit() and parts[3]=='export.docx':
                    doc=store.one('documents',parts[2])
                    from docx_export import export_docx
                    b=export_docx(doc['title'],doc['html'])
                    return self._send(b,mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',attachment='YLSY-Atlas-Belge.docx')
                if len(parts)==4 and parts[1]=='attachments' and parts[2].isdigit() and parts[3]=='file':
                    attach=store.one('attachments',parts[2]);f=store.uploads/attach['stored_name']
                    mime=attach['mime']
                    if not (mime=='application/pdf' or mime.startswith('image/')):mime='application/octet-stream'
                    return self._send(f.read_bytes(),mime=mime,attachment=None if mime!='application/octet-stream' else attach['original_name'])
            return self._send({'error':'Dosya bulunamadı'},404)

        def _post(self,u):
            p=u.path
            review_match=re.fullmatch(r'/api/vocabulary/(\d+)/review',p)
            if review_match:
                body=self._body(max_length=512)
                if not isinstance(body.get('known'),bool):raise ValueError('Quiz yanıtı geçersiz')
                return self._send(store.review_vocabulary(review_match.group(1),body['known']))
            if p=='/api/cloud/editor-active':
                return self._send(cloud.editor_active(bool(self._body(max_length=128).get('active'))))
            if p=='/api/cloud/skip':return self._send(cloud.mark_startup_shown())
            if p=='/api/cloud/connect':return self._send(cloud.oauth_login())
            if p=='/api/cloud/select-folder':
                folder=self._body(max_length=4096).get('parent','root')
                return self._send(cloud.select_google_folder(folder))
            if p=='/api/cloud/disconnect':return self._send(cloud.disconnect())
            if p=='/api/cloud/sync-now':
                cloud.wakeup.set();return self._send(cloud.current())
            if p=='/api/guide-pdf/import':
                body=self._body(max_length=65*1024*1024)
                content=base64.b64decode(str(body.get('content','')),validate=True)
                if len(content)>40*1024*1024 or len(content)<100 or not content.startswith(b'%PDF-'):
                    raise ValueError('Geçerli bir PDF seçin (en fazla 40 MB).')
                from pypdf import PdfReader
                try:
                    pdf_doc=PdfReader(io.BytesIO(content))
                    n_pages=len(pdf_doc.pages)
                    cover=''.join((pdf_doc.pages[0].extract_text() or '').upper().split())
                except Exception as exc:
                    raise ValueError('PDF okunamadı. Dosyanın bozuk veya şifreli olmadığını kontrol edin.') from exc
                if n_pages!=60 or '1416' not in cover:
                    raise ValueError(f'Bu dosya beklenen 60 sayfalık 1416’lı MEB ABD rehberi değil (bulunan: {n_pages} sayfa).')
                folder=store.root/'guide'
                folder.mkdir(parents=True,exist_ok=True)
                target=folder/PDF_NAME
                tmp=folder/(PDF_NAME+'.tmp')
                tmp.write_bytes(content)
                os.replace(tmp,target)
                return self._send({'ok':True,'name':PDF_NAME,'size':len(content)})
            if p=='/api/restore':
                obj=self._body(max_length=210*1024*1024)
                data=base64.b64decode(obj.get('content',''),validate=True)
                return self._send(store.restore(data))
            if p=='/api/open-external':
                site=self._body(max_length=1024).get('site')
                allow={'rebus':'https://rebus.meb.gov.tr/','nvi':'https://randevu.nvi.gov.tr/'}
                if site not in allow:raise ValueError('İzin verilmeyen dış bağlantı')
                url=allow[site]
                launch_normal_browser(url, 'default')
                return self._send({'ok':True,'message':'Tarayıcı açıldı.'})
            if p=='/api/settings':return self._send(store.set_settings(self._body()))
            if p=='/api/attachments':return self._send(store.save_attachment(self._body(max_length=32*1024*1024)))
            if p.startswith('/api/') and p.count('/')==2:
                return self._send(store.save(p.split('/')[2],self._body()),201)
            return self._send({'error':'Bilinmeyen işlem'},404)

        def _put(self,u):
            parts=u.path.strip('/').split('/')
            if len(parts)==3 and parts[0]=='api' and parts[2].isdigit():
                return self._send(store.save(parts[1],self._body(),parts[2]))
            return self._send({'error':'Geçersiz kayıt'},404)

        def _delete(self,u):
            parts=u.path.strip('/').split('/')
            if len(parts)==3 and parts[0]=='api' and parts[2].isdigit():
                if parts[1]=='attachments':return self._send(store.delete_attachment(parts[2]))
                return self._send(store.remove(parts[1],parts[2]))
            return self._send({'error':'Geçersiz kayıt'},404)

    # cannot use closures except assigned; standard server cross-platform.
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    server.atlas_store=store
    server.atlas_cloud=cloud
    server.atlas_token=token
    server.atlas_url=f'http://127.0.0.1:{server.server_port}/?token={token}'
    return server


def sqlite_error():
    import sqlite3
    return sqlite3.Error
