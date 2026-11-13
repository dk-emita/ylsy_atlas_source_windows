"""YLSY Atlas local-first SQLite storage. No cloud, accounts or tracking."""
from __future__ import annotations

import base64
import csv
import io
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import uuid
import zipfile
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

from guide import GUIDE, TEMPLATES


def now():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def data_dir():
    if os.environ.get('ATLAS_DATA_DIR'):
        return Path(os.environ['ATLAS_DATA_DIR'])
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'YLSYAtlas2'
    return Path.home() / '.local' / 'share' / 'YLSYAtlas2'


SCHEMAS = {
    'universities': '''CREATE TABLE IF NOT EXISTS universities (
       id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, short TEXT NOT NULL UNIQUE,
       country TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '', url TEXT NOT NULL DEFAULT '',
       ylsy_status TEXT NOT NULL DEFAULT 'Doğrulanmadı', rank INTEGER NOT NULL DEFAULT 99,
       note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'programs': '''CREATE TABLE IF NOT EXISTS programs (
       id INTEGER PRIMARY KEY, university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
       name TEXT NOT NULL, laboratory TEXT NOT NULL DEFAULT '', research TEXT NOT NULL DEFAULT '',
       deadline TEXT NOT NULL DEFAULT '', deadline_verified INTEGER NOT NULL DEFAULT 0,
       stage TEXT NOT NULL DEFAULT 'Araştırılıyor', url TEXT NOT NULL DEFAULT '',
       note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'advisors': '''CREATE TABLE IF NOT EXISTS advisors (
       id INTEGER PRIMARY KEY, university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
       program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
       name TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '',
       url TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Araştırılıyor',
       last_contact TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'tasks': '''CREATE TABLE IF NOT EXISTS tasks (
       id INTEGER PRIMARY KEY, guide_key TEXT NOT NULL DEFAULT '', title TEXT NOT NULL,
       group_name TEXT NOT NULL DEFAULT 'Genel', track TEXT NOT NULL DEFAULT 'Rehber',
       status TEXT NOT NULL DEFAULT 'todo', due_date TEXT NOT NULL DEFAULT '',
       priority TEXT NOT NULL DEFAULT 'Normal', source_page INTEGER NOT NULL DEFAULT 0,
       note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'documents': '''CREATE TABLE IF NOT EXISTS documents (
       id INTEGER PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Genel',
       html TEXT NOT NULL DEFAULT '', ref_key TEXT NOT NULL DEFAULT '', source_page INTEGER NOT NULL DEFAULT 0,
       updated_at TEXT NOT NULL DEFAULT '')''',
    'ielts_sessions': '''CREATE TABLE IF NOT EXISTS ielts_sessions (
       id INTEGER PRIMARY KEY, date TEXT NOT NULL, skill TEXT NOT NULL, minutes INTEGER NOT NULL DEFAULT 30,
       score TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'vocabulary': '''CREATE TABLE IF NOT EXISTS vocabulary (
       id INTEGER PRIMARY KEY, word TEXT NOT NULL, meaning TEXT NOT NULL,
       example TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '',
       created_at TEXT NOT NULL DEFAULT '', review_count INTEGER NOT NULL DEFAULT 0,
       known_count INTEGER NOT NULL DEFAULT 0, last_reviewed_at TEXT NOT NULL DEFAULT '',
       updated_at TEXT NOT NULL DEFAULT '')''',
    'events': '''CREATE TABLE IF NOT EXISTS events (
       id INTEGER PRIMARY KEY, date TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Genel',
       note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'attachments': '''CREATE TABLE IF NOT EXISTS attachments (
       id INTEGER PRIMARY KEY, owner_type TEXT NOT NULL, owner_id INTEGER NOT NULL,
       original_name TEXT NOT NULL, stored_name TEXT NOT NULL UNIQUE, mime TEXT NOT NULL DEFAULT 'application/octet-stream',
       size INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT '')''',
    'notes': '''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT 'Genel', updated_at TEXT NOT NULL DEFAULT '')''',
    'resources': '''CREATE TABLE IF NOT EXISTS resources (id INTEGER PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL DEFAULT '', kind TEXT NOT NULL DEFAULT 'Makale', note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT '')''',
    'settings': '''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)'''
}

EDITABLE = {
    'universities': ['name','short','country','city','url','ylsy_status','rank','note'],
    'programs': ['university_id','name','laboratory','research','deadline','deadline_verified','stage','url','note'],
    'advisors': ['university_id','program_id','name','topic','email','url','status','last_contact','note'],
    'tasks': ['guide_key','title','group_name','track','status','due_date','priority','source_page','note'],
    'documents': ['title','kind','html','ref_key','source_page'],
    'ielts_sessions': ['date','skill','minutes','score','note'],
    'vocabulary': ['word','meaning','example','note','tags'],
    'events': ['date','title','kind','note'],
    'notes': ['title','body','category'],
    'resources': ['title','url','kind','note'],
}


class Store:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or data_dir())
        self.root.mkdir(parents=True, exist_ok=True)
        self.uploads = self.root / 'uploads'
        self.uploads.mkdir(exist_ok=True)
        self.db_path = self.root / 'atlas.sqlite3'
        self.lock = threading.RLock()
        self._setup()
        self.on_change = None

    def _changed(self):
        cb = self.on_change
        if cb is not None: cb()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=20000')
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _setup(self):
        with self.lock, self.connect() as c:
            for statement in SCHEMAS.values():
                c.execute(statement)
            c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status, track)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_advisors_school ON advisors(university_id)')
            # A genuinely empty personal workspace on first launch.
            # Reference guide and writing templates are available from read-only
            # catalog endpoints, never written into user records by default.
            # In particular no schools, advisors, tasks, IELTS sessions,
            # documents, events or personal profile data are seeded here.
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('accent','cyan')")
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('sidebar_collapsed','false')")

    def get_settings(self):
        with self.lock, self.connect() as c:
            return {r['key']:r['value'] for r in c.execute('SELECT key,value FROM settings')}

    def set_settings(self, vals):
        if not isinstance(vals,dict):
            raise ValueError('Geçersiz ayarlar')
        approved={'cefr','ielts_target','course_end','accent','sidebar_collapsed','external_browser','research_focus','research_tags'}
        with self.lock, self.connect() as c:
            for k,v in vals.items():
                if k in approved:
                    c.execute('INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                              (k,str(v)[:250]))
        self._changed()
        return self.get_settings()

    def all(self, table):
        if table not in EDITABLE and table != 'attachments':
            raise ValueError('Bilinmeyen tablo')
        with self.lock, self.connect() as c:
            if table=='universities':
                sql='SELECT *, (SELECT COUNT(*) FROM programs p WHERE p.university_id=u.id) AS program_count FROM universities u ORDER BY rank,name'
            elif table=='programs':
                sql='SELECT p.*,u.short AS university,u.name AS university_name FROM programs p JOIN universities u ON u.id=p.university_id ORDER BY u.rank,p.name'
            elif table=='advisors':
                sql='SELECT a.*,u.short AS university FROM advisors a JOIN universities u ON u.id=a.university_id ORDER BY u.rank,a.name'
            else:
                col={'tasks':'CASE status WHEN \'doing\' THEN 0 WHEN \'todo\' THEN 1 ELSE 2 END, CASE WHEN due_date=\'\' THEN 1 ELSE 0 END, due_date, id',
                     'documents':'updated_at DESC,id', 'ielts_sessions':'date DESC,id DESC','vocabulary':'created_at DESC,id DESC','events':'date,id','notes':'updated_at DESC,id DESC','resources':'updated_at DESC,id DESC','attachments':'id DESC'}.get(table,'id')
                sql=f'SELECT * FROM {table} ORDER BY {col}'
            return [dict(r) for r in c.execute(sql)]

    def one(self, table, item_id):
        if table not in EDITABLE and table!='attachments': raise ValueError('Bilinmeyen tablo')
        with self.lock, self.connect() as c:
            r=c.execute(f'SELECT * FROM {table} WHERE id=?',(int(item_id),)).fetchone()
            if r is None: raise KeyError('Kayıt bulunamadı')
            return dict(r)

    def save(self, table, data, item_id=None):
        if table not in EDITABLE: raise ValueError('Bu kayıt tipi düzenlenemez')
        if not isinstance(data,dict):raise ValueError('Geçersiz kayıt')
        payload={k:self._value(k,v) for k,v in data.items() if k in EDITABLE[table]}
        if table=='tasks' and payload.get('status') not in (None,'todo','doing','done'):raise ValueError('Görev durumu geçersiz')
        if table=='programs' and payload.get('stage') not in (None,'Araştırılıyor','Danışman iletişimi','Başvuru hazırlanıyor','Başvuru gönderildi','Bekleme listesi','Kabul','Ret','Vazgeçildi'):
            raise ValueError('Başvuru aşaması geçersiz')
        if table=='vocabulary' and item_id is None and (not payload.get('word','').strip() or not payload.get('meaning','').strip()):
            raise ValueError('Kelime ve anlam alanları gerekli')
        if not payload:raise ValueError('Düzenlenecek alan bulunamadı')
        with self.lock, self.connect() as c:
            payload['updated_at']=now()
            if item_id is None:
                if table in ('programs','advisors') and 'university_id' not in payload:raise ValueError('Üniversite seçilmeli')
                if table=='tasks' and 'title' not in payload: raise ValueError('Görev adı gerekli')
                if table=='documents' and 'title' not in payload: raise ValueError('Belge başlığı gerekli')
                if table=='vocabulary': payload['created_at']=now()
                cols=list(payload); marks=','.join('?' for _ in cols)
                cur=c.execute(f'INSERT INTO {table} ({",".join(cols)}) VALUES({marks})',tuple(payload.values()))
                item_id=cur.lastrowid
            else:
                item_id=int(item_id)
                if not c.execute(f'SELECT 1 FROM {table} WHERE id=?',(item_id,)).fetchone():raise KeyError('Kayıt bulunamadı')
                cols=list(payload)
                c.execute(f'UPDATE {table} SET {",".join(f"{k}=?" for k in cols)} WHERE id=?',(*payload.values(),item_id))
        self._changed()
        return self.one(table,item_id)

    def review_vocabulary(self, item_id, known):
        with self.lock, self.connect() as c:
            cur=c.execute('''UPDATE vocabulary SET review_count=review_count+1,
                known_count=known_count+?, last_reviewed_at=?, updated_at=? WHERE id=?''',
                (1 if known else 0, now(), now(), int(item_id)))
            if not cur.rowcount: raise KeyError('Kelime kaydı bulunamadı')
        self._changed()
        return self.one('vocabulary', item_id)

    @staticmethod
    def _value(key,v):
        if key in ('university_id','program_id','rank','source_page','deadline_verified','minutes'):
            return None if v in ('',None) and key=='program_id' else int(v or 0)
        return str(v if v is not None else '')[:400000 if key in ('html','note') else 1200]

    def remove(self,table,item_id):
        if table not in EDITABLE: raise ValueError('Silinemez')
        with self.lock, self.connect() as c:
            cur=c.execute(f'DELETE FROM {table} WHERE id=?',(int(item_id),))
            if not cur.rowcount:raise KeyError('Kayıt bulunamadı')
        self._changed()
        return {'ok':True}

    def overview(self):
        with self.lock,self.connect() as c:
            tasks=c.execute('SELECT status,COUNT(*) n FROM tasks GROUP BY status').fetchall()
            by={x['status']:x['n'] for x in tasks}
            total=sum(by.values());done=by.get('done',0)
            nuni=c.execute('SELECT COUNT(*) FROM universities').fetchone()[0]
            nprog=c.execute('SELECT COUNT(*) FROM programs').fetchone()[0]
            nadv=c.execute('SELECT COUNT(*) FROM advisors').fetchone()[0]
            submitted=c.execute("SELECT COUNT(*) FROM programs WHERE stage IN ('Başvuru gönderildi','Bekleme listesi','Kabul')").fetchone()[0]
            accepted=c.execute("SELECT COUNT(*) FROM programs WHERE stage='Kabul'").fetchone()[0]
            # 90 day upcoming; don't hide overdue tasks.
            tasks_due=[dict(r) for r in c.execute("SELECT id,title,due_date,status,track FROM tasks WHERE due_date<>'' AND status!='done' ORDER BY due_date LIMIT 10")]
            schools_due=[dict(r) for r in c.execute("SELECT p.id,p.name,p.deadline,p.deadline_verified,u.short AS university FROM programs p JOIN universities u ON u.id=p.university_id WHERE p.deadline<>'' ORDER BY p.deadline LIMIT 10")]
            sessions=[dict(r) for r in c.execute('SELECT * FROM ielts_sessions ORDER BY date DESC,id DESC LIMIT 8')]
            activity=[dict(r) for r in c.execute("SELECT id,title,status,track,guide_key FROM tasks WHERE status!='done' ORDER BY CASE WHEN status='doing' THEN 0 ELSE 1 END,id LIMIT 6")]
            return dict(total=total,done=done,doing=by.get('doing',0),completion=round(done*100/total) if total else 0,
                        university_count=nuni,program_count=nprog,advisor_count=nadv,submitted=submitted,accepted=accepted,
                        tasks_due=tasks_due,programs_due=schools_due,sessions=sessions,next_tasks=activity)

    def search(self,q):
        q=str(q).strip()[:100]
        if not q:return []
        term=f'%{q}%';out=[]
        with self.lock,self.connect() as c:
            for r in c.execute('SELECT id,short title,name subtitle FROM universities WHERE name LIKE ? OR short LIKE ? LIMIT 5',(term,term)):
                out.append({'type':'universities',**dict(r)})
            for r in c.execute('SELECT id,title,group_name subtitle FROM tasks WHERE title LIKE ? OR note LIKE ? LIMIT 8',(term,term)):
                out.append({'type':'tasks',**dict(r)})
            for r in c.execute('SELECT id,name title,topic subtitle FROM advisors WHERE name LIKE ? OR topic LIKE ? LIMIT 5',(term,term)):
                out.append({'type':'advisors',**dict(r)})
            for r in c.execute('SELECT id,title,kind subtitle FROM documents WHERE title LIKE ? LIMIT 5',(term,)):
                out.append({'type':'documents',**dict(r)})
            for r in c.execute('SELECT id,word title,meaning subtitle FROM vocabulary WHERE word LIKE ? OR meaning LIKE ? LIMIT 8',(term,term)):
                out.append({'type':'vocabulary',**dict(r)})
        return out

    def save_attachment(self,data):
        name=Path(str(data.get('name','belge'))).name[:180]
        if not name or name.startswith('.'):raise ValueError('Geçersiz dosya adı')
        content=base64.b64decode(data.get('content',''),validate=True)
        if len(content)>20*1024*1024:raise ValueError('En fazla 20 MB dosya yükleyebilirsiniz')
        owner_type=str(data.get('owner_type','general'))[:32]
        if owner_type not in ('general','university','program','advisor','task','document'):
            raise ValueError('Geçersiz belge bağlantısı')
        owner_id=int(data.get('owner_id',0))
        file_id=uuid.uuid4().hex
        storage_name=f'{file_id}{Path(name).suffix.lower()[:12]}'
        (self.uploads/storage_name).write_bytes(content)
        mime=str(data.get('mime') or 'application/octet-stream')[:120]
        with self.lock,self.connect() as c:
            cur=c.execute('INSERT INTO attachments(owner_type,owner_id,original_name,stored_name,mime,size,updated_at) VALUES(?,?,?,?,?,?,?)',
                          (owner_type,owner_id,name,storage_name,mime,len(content),now()))
            result = dict(c.execute('SELECT * FROM attachments WHERE id=?',(cur.lastrowid,)).fetchone())
        self._changed()
        return result

    def delete_attachment(self,item_id):
        a=self.one('attachments',item_id)
        with self.lock,self.connect() as c:
            c.execute('DELETE FROM attachments WHERE id=?',(int(item_id),))
        (self.uploads/a['stored_name']).unlink(missing_ok=True)
        self._changed()
        return {'ok':True}

    def backup(self)->bytes:
        """Portable ZIP containing consistent SQLite snapshot plus user attachments."""
        with self.lock:
            tmp=sqlite3.connect(':memory:')
            with self.connect() as src:src.backup(tmp)
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'atlas.sqlite3'
                dst=sqlite3.connect(path)
                tmp.backup(dst)
                dst.close();tmp.close()
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
                    z.write(path,'atlas.sqlite3')
                    for f in self.uploads.iterdir():
                        if f.is_file():z.write(f,f'uploads/{f.name}')
                    z.writestr('backup-info.json',json.dumps({'created':now(),'schema':1},ensure_ascii=False))
                return stream.getvalue()

    def restore(self,contents:bytes, keep_previous=True, notify=True):
        if len(contents)>150*1024*1024:raise ValueError('Yedek çok büyük')
        with self.lock:
            with tempfile.TemporaryDirectory() as d:
                temp=Path(d)
                with zipfile.ZipFile(io.BytesIO(contents)) as z:
                    names=z.namelist()
                    if 'atlas.sqlite3' not in names:raise ValueError('Bu bir Atlas yedeği değil')
                    if len(names)>1000 or sum(x.file_size for x in z.infolist())>250*1024*1024:raise ValueError('Yedek boyutu güvenli sınırı aşıyor')
                    (temp/'atlas.sqlite3').write_bytes(z.read('atlas.sqlite3'))
                    upload_names=[n for n in names if n.startswith('uploads/') and not n.endswith('/')]
                    for n in upload_names:
                        if Path(n).name!=n.split('/',1)[1] or '..' in n:raise ValueError('Geçersiz yedek içeriği')
                        (temp/Path(n).name).write_bytes(z.read(n))
                test=sqlite3.connect(temp/'atlas.sqlite3')
                try:
                    result=test.execute('PRAGMA integrity_check').fetchone()[0]
                    if result!='ok':raise ValueError('Veritabanı bütünlük kontrolü başarısız')
                    for table in SCHEMAS:
                        test.execute(f'SELECT 1 FROM {table} LIMIT 1')
                finally:test.close()
                # Automatic rollback archive before replacement.
                if keep_previous:
                    before=self.root/'before-restore.zip'
                    before.write_bytes(self.backup())
                os.replace(temp/'atlas.sqlite3',self.db_path)
                shutil.rmtree(self.uploads)
                self.uploads.mkdir()
                for n in upload_names:
                    os.replace(temp/Path(n).name,self.uploads/Path(n).name)
        if notify: self._changed()
        return {'ok':True,'message':'Yedek geri yüklendi.'}

    def tasks_csv(self):
        rows=self.all('tasks')
        output=io.StringIO(); w=csv.DictWriter(output,fieldnames=['id','guide_key','title','group_name','track','status','due_date','priority','note'])
        w.writeheader()
        for r in rows:w.writerow({k:r.get(k,'') for k in w.fieldnames})
        return '\ufeff'+output.getvalue()
