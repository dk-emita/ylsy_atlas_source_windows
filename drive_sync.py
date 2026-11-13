"""YLSY Atlas 4.0.0: snapshot synchronization, preserving offline changes.

The OAuth application's client metadata belongs to the software publisher. A user
never supplies client IDs, private keys or passwords to Atlas; Google owns login.
This module does NOT claim to provide server-confirmed sync through the local
Google Drive for Desktop folder: only API mode can prove server confirmation.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone

from ylsy_atlas_drive.google_drive import GoogleAuth, GoogleDrive, make_service

APP_KEY = 'atlas-workspace.zip'


def _write_json_atomic(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


class CloudController:
    def __init__(self, store, resources: Path, start_worker: bool = True, secret_store=None):
        self.store = store
        self.resources = Path(resources)
        self.secret_store = secret_store
        self.conf_path = store.root / 'cloud-connection.json'
        self.queue_path = store.root / 'offline_sync_queue.sqlite3'
        self._queue_init()
        try:
            self.config = json.loads(self.conf_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, ValueError):
            self.config = {}
        self.lock = threading.RLock()
        self.wakeup = threading.Event()
        self.stop_event = threading.Event()
        self.credentials = None
        self.auth = None
        self.error = ''
        self.synced = False
        self.dirty = bool(self.config.get('dirty', False))
        self.gener = self._queue_max_revision()
        self.status_text = 'Bağlı değil'
        self.mode = self.config.get('mode', 'none')
        self.connected = bool(self.config.get('folder_id') if self.mode == 'oauth' else self.config.get('local_path'))
        self.last_remote = self.config.get('remote_md5', '')
        self.last_local = ''
        self.thread = None
        self.login_thread = None
        self.change_number = 0
        self.initialized = False
        self.conflict_blocked = bool(self.config.get('conflict_blocked'))
        self.edit_lease_until = 0.0
        self.drive_folder_root = None
        self.store.on_change = self.mark_dirty
        if self.connected:
            self.status_text = 'Bağlantı denetleniyor'
            if start_worker:
                self._start_worker()

    def configured(self):
        path = self.resources / 'google_oauth_client.json'
        if not path.is_file():
            return False
        try:
            o = json.loads(path.read_text(encoding='utf-8'))
            return bool(o.get('installed', {}).get('client_id', '').endswith('.apps.googleusercontent.com'))
        except (ValueError, OSError):
            return False

    def current(self):
        with self.lock:
            return {
                'mode': self.mode, 'connected': self.connected,
                'configured': self.configured(),
                'authorization_ready': self.credentials is not None or (self.mode == 'oauth' and self.connected),
                'conflict_blocked': self.conflict_blocked,
                'startup_shown': bool(self.config.get('startup_shown')),
                'status': self.status_text, 'error': self.error[:240],
                'dirty': self.dirty, 'synchronized': self.synced,
                'change_number': self.change_number,
                'pending_changes': self._queue_count(),
                'folder': self.config.get('folder_id') if self.mode == 'oauth' else self.config.get('local_path', ''),
            }

    def mark_dirty(self):
        with self.lock:
            self.gener += 1
            self.dirty = True
            self.synced = False
            self.status_text = 'Değişiklikler senkronizasyon bekliyor' if self.connected else 'Yerel kayıt'
            self.change_number += 1
            self.config['dirty'] = True
            _write_json_atomic(self.conf_path, self.config)
            self._queue_add(self.gener)
        self.wakeup.set()

    def _queue_init(self):
        """Durable FIFO journal; the SQLite workspace itself is the local buffer."""
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.queue_path, timeout=20) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA synchronous=FULL')
            db.execute('''CREATE TABLE IF NOT EXISTS offline_sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                revision INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending'
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_offline_queue_state_id ON offline_sync_queue(state,id)')

    def _queue_add(self, revision):
        with sqlite3.connect(self.queue_path, timeout=20) as db:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('INSERT INTO offline_sync_queue(revision,created_at,state) VALUES(?,?,\'pending\')',
                       (revision, datetime.now(timezone.utc).isoformat(timespec='seconds')))

    def _queue_count(self):
        try:
            with sqlite3.connect(self.queue_path, timeout=5) as db:
                return db.execute("SELECT COUNT(*) FROM offline_sync_queue WHERE state='pending'").fetchone()[0]
        except sqlite3.Error:
            return 0

    def _queue_max_revision(self):
        try:
            with sqlite3.connect(self.queue_path, timeout=5) as db:
                return int(db.execute('SELECT COALESCE(MAX(revision),0) FROM offline_sync_queue').fetchone()[0])
        except sqlite3.Error:
            return 0

    def _queue_ack(self, revision):
        """Delete FIFO entries only after the corresponding cloud snapshot is confirmed."""
        with sqlite3.connect(self.queue_path, timeout=20) as db:
            db.execute("DELETE FROM offline_sync_queue WHERE state='pending' AND revision<=?", (revision,))

    def editor_active(self, is_active):
        # Prevent another machine's snapshot from replacing the database while
        # a document or form contains unsaved edits in the UI. Lease expires
        # automatically after a window crash or network interruption.
        with self.lock:
            self.edit_lease_until = time.monotonic() + 9 if is_active else 0.0
        return {'ok': True}

    def mark_startup_shown(self):
        with self.lock:
            self.config['startup_shown'] = True
            _write_json_atomic(self.conf_path, self.config)
        return self.current()

    def _start_worker(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._loop, name='YLSY-Drive-Sync', daemon=True)
        self.thread.start()

    def oauth_login(self):
        if not self.configured():
            raise ValueError('Google Client ID ayarı bulunamadı; uygulama paketini güncelleyin.')
        with self.lock:
            if self.login_thread and self.login_thread.is_alive():
                return self.current()
            self.status_text = 'Google giriş sayfası açılıyor'
            self.error = ''
            self.change_number += 1
        def login():
            try:
                auth = GoogleAuth(self.resources / 'google_oauth_client.json', secret_store=self.secret_store)
                creds = auth.authorize(interactive=True, force_account_choice=True)
                with self.lock:
                    self.auth, self.credentials = auth, creds
                    # A newly selected Google account must explicitly choose
                    # its folder before any snapshot is uploaded.
                    self.connected = False
                    self.mode = 'none'
                    self.config.update(mode='none')
                    self.config.pop('folder_id', None)
                    self.config.pop('local_path', None)
                    self.initialized = False
                    _write_json_atomic(self.conf_path, self.config)
                    self.status_text = 'Google hesabı doğrulandı; Drive klasörü seçiniz'
                    self.change_number += 1
            except Exception as exc:
                with self.lock:
                    self.status_text = 'Google hesabına bağlanılamadı'
                    self.error = str(exc)[:240]
                    self.change_number += 1
        self.login_thread = threading.Thread(target=login, name='YLSY-Google-OAuth', daemon=True)
        self.login_thread.start()
        return self.current()

    def _drive(self, folder_id=None):
        if not self.configured():
            raise ValueError('Google OAuth bağlantısı bu uygulama paketinde etkin değil')
        if not self.auth:
            self.auth = GoogleAuth(self.resources / 'google_oauth_client.json', secret_store=self.secret_store)
        creds = self.auth.authorize(interactive=False)
        with self.lock:
            self.credentials = creds
        return GoogleDrive(make_service(creds), folder_id)

    def folders(self, parent_id='root'):
        if not self.credentials and not self.connected:
            raise ValueError('Önce Google hesabını bağlayın.')
        if not parent_id or len(parent_id) > 150:
            raise ValueError('Drive klasörü geçersiz')
        try:
            return self._drive().folders_in(parent_id)
        except Exception as exc:
            from googleapiclient.errors import HttpError
            from google.auth.exceptions import RefreshError, TransportError
            if isinstance(exc, (RefreshError, TransportError)):
                raise ValueError('Google oturumu yenilenemedi. Hesabı yeniden bağlayın.') from exc
            if isinstance(exc, HttpError):
                status = exc.resp.status
                if status == 401:
                    raise ValueError('Google oturumunun süresi doldu. Hesabı yeniden bağlayın.') from exc
                if status == 403:
                    raise ValueError('Drive klasörlerine erişim reddedildi. Google Drive API ve uygulama izinlerini kontrol edin.') from exc
                if status == 404:
                    raise ValueError('Bu Drive klasörü artık bulunamıyor. Ana klasöre dönün.') from exc
                if status == 429 or status >= 500:
                    raise ValueError('Google Drive şu anda yanıt vermiyor. Biraz sonra yeniden deneyin.') from exc
            raise

    def select_google_folder(self, parent_id='root'):
        if not self.credentials and not (self.connected and self.mode == 'oauth'):
            raise ValueError('Google hesabı bağlantısı tamamlanmadı')
        drive = self._drive()
        folder = drive.get_or_create_app_folder(parent_id)
        with self.lock:
            self.config.update(mode='oauth', folder_id=folder, conflict_blocked=False)
            self.conflict_blocked = False
            self.config.pop('local_path', None)
            self.mode, self.connected = 'oauth', True
            self.initialized = False
            self.last_remote = ''
            self.config.pop('remote_md5', None)
            self.dirty = self._has_records()
            self.config['dirty'] = self.dirty
            self.status_text = 'Drive klasörü ayarlandı; ilk senkronizasyon başlıyor'
            self.change_number += 1
            _write_json_atomic(self.conf_path, self.config)
        self._start_worker()
        self.wakeup.set()
        return self.current()

    def connect_local_drive(self, path):
        # This mode requires Drive for Desktop to be signed in and syncing the
        # selected folder. The program cannot verify Google's server receipt.
        if not path or not isinstance(path, str):
            raise ValueError('Google Drive masaüstü klasörünü seçin')
        base = Path(path).expanduser().resolve()
        if not base.is_dir():
            raise ValueError('Seçilen klasör bulunamadı')
        app = base / 'YLSY Atlas'
        app.mkdir(exist_ok=True)
        test = app / ('.atlas-write-test-' + secrets.token_hex(5))
        try:
            test.write_bytes(b'ok')
        finally:
            test.unlink(missing_ok=True)
        with self.lock:
            self.config.update(mode='desktop-folder', local_path=str(app), conflict_blocked=False)
            self.conflict_blocked = False
            self.config.pop('folder_id', None)
            self.mode, self.connected = 'desktop-folder', True
            self.initialized = False
            self.last_remote = ''
            self.config.pop('remote_md5', None)
            self.dirty = self._has_records()
            self.config['dirty'] = self.dirty
            self.status_text = 'Drive masaüstü klasörü seçildi (bulut onayı bilinmiyor)'
            self.change_number += 1
            _write_json_atomic(self.conf_path, self.config)
        self._start_worker()
        self.wakeup.set()
        return self.current()

    def disconnect(self):
        # Local edits remain safe and usable; disconnect never deletes them.
        with self.lock:
            self.mode = 'none'
            self.connected = False
            self.config.pop('folder_id', None)
            self.config.pop('local_path', None)
            self.config['mode'] = 'none'
            self.config['conflict_blocked'] = False
            self.conflict_blocked = False
            self.initialized = False
            self.status_text = 'Hesap ayrıldı; yerel kayıt etkin'
            self.change_number += 1
            _write_json_atomic(self.conf_path, self.config)
        if self.auth:
            self.auth.disconnect()
        self.wakeup.set()
        return self.current()

    def _has_records(self):
        # Empty SQLite tables and default settings do not count as user content.
        with self.store.lock, self.store.connect() as c:
            tables = ('universities','programs','advisors','tasks','documents','ielts_sessions',
                      'vocabulary','events','notes','resources','attachments')
            return any(c.execute('SELECT EXISTS(SELECT 1 FROM '+t+' LIMIT 1)').fetchone()[0] for t in tables)

    def _remote(self):
        if self.mode == 'desktop-folder':
            path = Path(self.config['local_path']) / APP_KEY
            if not path.is_file():
                return None, None, None
            b = path.read_bytes()
            return {'md5Checksum': hashlib.md5(b).hexdigest(), 'id': 'local'}, b, None
        d = self._drive(self.config['folder_id'])
        info = d.list_docs().get(APP_KEY)
        return info, None, d

    def _upload(self, contents, remote, drive):
        md5 = hashlib.md5(contents).hexdigest()
        if self.mode == 'desktop-folder':
            path = Path(self.config['local_path']) / APP_KEY
            tmp = path.with_suffix('.tmp')
            with tmp.open('wb') as f:
                f.write(contents)
                f.flush();os.fsync(f.fileno())
            os.replace(tmp, path)
            if hashlib.md5(path.read_bytes()).hexdigest() != md5:
                raise RuntimeError('Google Drive masaüstü klasörü dosya doğrulaması başarısız')
        else:
            info = drive.put_doc(APP_KEY, contents, remote['id'] if remote else None)
            confirmed = drive.doc_info(info['id'])
            if not confirmed or confirmed.get('md5Checksum') != md5:
                raise RuntimeError('Google Drive sunucusu dosya bütünlüğünü doğrulamadı')
        return md5

    def _download(self, remote, b, drive):
        blob = b if b is not None else drive.get_doc(remote['id'])
        if hashlib.md5(blob).hexdigest() != remote.get('md5Checksum'):
            raise RuntimeError('Uzak dosyanın MD5 değeri uyuşmuyor')
        return blob

    def _conflict(self, contents, drive):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        key = 'atlas-conflict-' + stamp + '-' + secrets.token_hex(3) + '.zip'
        if self.mode == 'desktop-folder':
            dest = Path(self.config['local_path']) / key
            dest.write_bytes(contents)
        else:
            drive.put_doc(key, contents, None)
        with self.lock:
            self.status_text = 'Çakışma: yerel kayıt ayrı bir kopyada korundu; birleştirme gerekli'
            self.conflict_blocked = True
            self.config['conflict_blocked'] = True
            self.config['dirty'] = True
            self.error = key
            self.change_number += 1
            _write_json_atomic(self.conf_path, self.config)
        return key

    def sync_once(self):
        with self.lock:
            if not self.connected or self.conflict_blocked:
                return
            dirty, generation, was_initialized = self.dirty, self.gener, self.initialized
        remote, raw, drive = self._remote()
        remote_md5 = remote['md5Checksum'] if remote else ''
        if (self.mode == 'oauth' and self.config.get('local_purged') and
                self.dirty and remote and self._has_records()):
            # Only records created since the last cloud-only cleanup exist
            # locally. Merge them into the downloaded cloud workspace before
            # uploading; a plain snapshot upload would erase older cloud rows.
            from cloud_merge import merge_new_records
            with self.lock, self.store.lock:
                offline = self.store.backup()
                merged = merge_new_records(self._download(remote, raw, drive), offline)
                current = drive.doc_info(remote['id'])
                if not current or current.get('md5Checksum') != remote_md5:
                    raise RuntimeError('Drive verisi bu sırada değişti; birleştirme yeniden denenecek')
                uploaded_md5 = self._upload(merged, remote, drive)
                self.store.restore(merged, keep_previous=False, notify=False)
                self.last_remote = uploaded_md5
                self.config.update(remote_md5=uploaded_md5, dirty=False, local_purged=False)
                self.dirty = False
                self.initialized = True
                self.synced = True
                self.error = ''
                self.status_text = 'Çevrimdışı kayıtlar Drive verileriyle birleştirildi'
                self.change_number += 1
                _write_json_atomic(self.conf_path, self.config)
                self._queue_ack(generation)
            return
        # First login on a second PC: fetch its workspace before touching anything.
        if not was_initialized:
            if remote and not self._has_records():
                self.store.restore(self._download(remote, raw, drive), keep_previous=False, notify=False)
                with self.lock:
                    self.last_remote = remote_md5
                    self.config['remote_md5'] = remote_md5
                    self.dirty = False
                    self.config['dirty'] = False
                    self.config['local_purged'] = False
                    self.initialized = True
                    self.synced = self.mode == 'oauth'
                    self.status_text = 'Drive verileri indirildi; arayüzü yenileyin' if self.mode == 'oauth' else 'Drive klasöründeki kayıtlar alındı'
                    self.change_number += 1
                    _write_json_atomic(self.conf_path, self.config)
                    self._queue_ack(generation)
                return
            if remote and self._has_records() and remote_md5 == self.last_remote:
                with self.lock:
                    self.initialized = True
                    self.synced = (self.mode == 'oauth') and not self.dirty
                    self.status_text = ('Değişiklikler buluta gönderilmeyi bekliyor' if self.dirty else
                                        'Google Drive sunucusunda doğrulandı' if self.synced else 'Drive masaüstü klasörü bağlı')
                return
            if remote and self._has_records():
                if not self.dirty and self.last_remote:
                    # Last known cloud version was synchronized before exit.
                    # Another device updated it: safely restore its newer copy.
                    with self.lock:
                        if time.monotonic() < self.edit_lease_until:
                            self.status_text = 'Bulutta yeni kayıtlar var; düzenleme bittikten sonra alınacak'
                            return
                        if self.dirty or self.gener != generation:
                            return
                        self.store.restore(self._download(remote, raw, drive), keep_previous=False, notify=False)
                        self.last_remote = remote_md5
                        self.config['remote_md5'] = remote_md5
                        self.config['dirty'] = False
                        self.config['local_purged'] = False
                        self.initialized = True
                        self.synced = self.mode == 'oauth'
                        self.status_text = 'Drive değişiklikleri alındı; ekranı yenileyin'
                        self.change_number += 1
                        _write_json_atomic(self.conf_path, self.config)
                        self._queue_ack(generation)
                    return
                # Local changes or a previously unsynced database: never overwrite.
                contents = self.store.backup()
                if hashlib.md5(contents).hexdigest() != remote_md5:
                    self._conflict(contents, drive)
                    with self.lock: self.initialized = True
                    return
            with self.lock:
                self.initialized = True
                self.last_remote = remote_md5
                self.dirty = True if not remote else self.dirty
                dirty = self.dirty
        if remote and remote_md5 != self.last_remote:
            if not dirty:
                with self.lock:
                    if time.monotonic() < self.edit_lease_until:
                        self.status_text = 'Yeni Drive verisi var; açık düzenleme tamamlanınca alınacak'
                        return
                self.store.restore(self._download(remote, raw, drive), keep_previous=False, notify=False)
                with self.lock:
                    self.last_remote = remote_md5
                    self.config['remote_md5'] = remote_md5
                    self.config['dirty'] = False
                    self.config['local_purged'] = False
                    self.synced = self.mode == 'oauth'
                    self.status_text = 'Drive değişiklikleri alındı; ekranı yenileyin'
                    self.change_number += 1
                    _write_json_atomic(self.conf_path, self.config)
                    self._queue_ack(generation)
                return
            # A different computer also edited; don't clobber either copy.
            self._conflict(self.store.backup(), drive)
            return
        if not dirty:
            self._queue_ack(generation)
            return
        contents = self.store.backup()
        if remote and remote_md5 == hashlib.md5(contents).hexdigest():
            uploaded_md5 = remote_md5
        else:
            uploaded_md5 = self._upload(contents, remote, drive)
        with self.lock:
            self.last_remote = uploaded_md5
            self.config['remote_md5'] = uploaded_md5
            if generation == self.gener:
                self.dirty = False
                self.synced = self.mode == 'oauth'
                self.status_text = ('Google Drive sunucusunda doğrulandı' if self.synced else 'Drive masaüstü klasörüne yazıldı; Google sunucu onayı bekleniyor')
            self.config['dirty'] = self.dirty
            if not self.dirty:
                self.config['local_purged'] = False
                self._queue_ack(generation)
            self.error = ''
            self.change_number += 1
            _write_json_atomic(self.conf_path, self.config)

    def _loop(self):
        while not self.stop_event.is_set():
            try:
                if self.connected:
                    self.sync_once()
            except Exception as exc:
                with self.lock:
                    self.status_text = 'Çevrimdışı: değişiklikler yerelde güvenle saklanıyor'
                    self.error = str(exc)[:240]
                    self.change_number += 1
            self.wakeup.wait(4.0)
            self.wakeup.clear()

    def close(self):
        self.stop_event.set()
        self.wakeup.set()
        if self.thread:
            self.thread.join(timeout=8)

    def purge_verified_local_data(self):
        """Remove the working copy only after Google confirms the cloud copy."""
        if self.thread and self.thread.is_alive():
            return False
        with self.lock, self.store.lock:
            if (self.mode != 'oauth' or not self.connected or self.dirty or
                    self.conflict_blocked or not self.last_remote or not self.synced):
                return False
            try:
                remote, _, _ = self._remote()
            except Exception:
                return False
            if not remote or remote.get('md5Checksum') != self.last_remote:
                return False
            self.store.db_path.unlink(missing_ok=True)
            for suffix in ('-wal', '-shm', '-journal'):
                Path(str(self.store.db_path) + suffix).unlink(missing_ok=True)
            shutil.rmtree(self.store.uploads)
            (self.store.root / 'before-restore.zip').unlink(missing_ok=True)
            self.config['local_purged'] = True
            _write_json_atomic(self.conf_path, self.config)
            return True
