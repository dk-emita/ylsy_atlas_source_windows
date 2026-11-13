"""Google Drive API ve Desktop OAuth 2.0 (PKCE).

Mevcut herhangi bir Drive klasörünü listeleyebilmek için geniş `drive` kapsamı
kullanılır. Dağıtımdan önce Google OAuth uygulama doğrulaması gerekebilir.
"""
from __future__ import annotations
import io
import json
from pathlib import Path
import re
import mimetypes
import hashlib

# NOT: İhtiyaç duyulan paketler requirements.txt içinde; modül geç yüklenir.
SCOPES = ['https://www.googleapis.com/auth/drive']
OAUTH_SERVICE = 'YLSY Atlas Desktop'
OAUTH_ACCOUNT = 'google-drive-oauth-v1'
APP_FOLDER_NAME = 'YLSY Atlas'


def _quote_q(x: str) -> str:
    return x.replace('\\', '\\\\').replace("'", "\\'")


class GoogleAuth:
    """Desktop OAuth: system browser + loopback callback + PKCE.

    Access/refresh tokens live in the OS credential vault via keyring, never in
    program files, a cloud snapshot, the bundled client JSON or the SQLite DB.
    """
    def __init__(self, client_config_path: Path, secret_store=None):
        self.client_config_path = Path(client_config_path)
        if secret_store is None:
            import keyring
            secret_store = keyring
        self.secret_store = secret_store
        info = json.loads(self.client_config_path.read_text(encoding='utf-8')).get('installed', {})
        self.client_id = info.get('client_id', '')
        self.client_secret = str(info.get('client_secret') or '')
        if not re.fullmatch(r'[0-9]+-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com', self.client_id):
            raise ValueError('Google Desktop Client ID eksik veya geçersiz.')
        self.account_key = self.client_id

    @staticmethod
    def _auth_url(client_id, redirect_uri, challenge, state):
        from urllib.parse import urlencode
        query = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(SCOPES),
            'access_type': 'offline',
            'prompt': 'select_account consent',
            'code_challenge': challenge,
            'code_challenge_method': 'S256',
            'state': state,
        }
        return 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(query)

    def _browser_login(self):
        import base64
        from datetime import datetime, timedelta, timezone
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from urllib.parse import urlparse, parse_qs
        import secrets
        import threading
        import webbrowser
        import requests
        from google.oauth2.credentials import Credentials

        verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode('ascii').rstrip('=')
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).decode('ascii').rstrip('=')
        expected_state = secrets.token_urlsafe(32)
        client_id = self.client_id
        client_secret = self.client_secret
        captured = {}
        completed = threading.Event()

        def callback_page(success, message):
            title = 'Google hesabı bağlandı' if success else 'Google bağlantısı tamamlanamadı'
            close_script = "<script>window.close();</script>" if success else ''
            safe_message = (message or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return (f'<!doctype html><html lang="tr"><meta charset="utf-8"><title>{title}</title>'
                    '<body style="font:16px sans-serif;margin:3rem">'
                    f'<h1>{title}</h1><p>{safe_message}</p>'
                    '<p>Bu sekme otomatik kapanmazsa kapatıp YLSY Atlas uygulamasına dönün.</p>'
                    f'{close_script}</body></html>').encode('utf-8')

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass   # OAuth callback path may contain sensitive information

            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path != '/':
                    self.send_error(404)
                    return
                params = parse_qs(parsed.query)
                if params.get('state', [''])[0] != expected_state:
                    self.send_error(400, 'Invalid OAuth state')
                    return
                oauth_error = params.get('error', [''])[0]
                if oauth_error:
                    captured['error'] = 'Google hesabı izin vermedi: ' + oauth_error
                    page = callback_page(False, captured['error'])
                else:
                    code = params.get('code', [''])[0]
                    if not code:
                        captured['error'] = 'Google girişinden yetkilendirme kodu alınamadı.'
                        page = callback_page(False, captured['error'])
                    else:
                        try:
                            token_request = {
                                'client_id': client_id,
                                'code': code,
                                'code_verifier': verifier,
                                'redirect_uri': redirect_uri,
                                'grant_type': 'authorization_code',
                            }
                            if client_secret:
                                token_request['client_secret'] = client_secret
                            resp = requests.post('https://oauth2.googleapis.com/token', data=token_request, timeout=25)
                            if not resp.ok:
                                try:
                                    error = resp.json()
                                    reason = error.get('error', 'unknown_error')
                                    description = error.get('error_description', '')
                                except ValueError:
                                    reason, description = str(resp.status_code), ''
                                if (reason == 'invalid_request' and 'client_secret' in description.lower()
                                        and not client_secret):
                                    raise RuntimeError(
                                        'Google OAuth yapılandırmasında client_secret eksik. '
                                        'resources/google_oauth_client.json dosyasını Google Cloud Console’dan '
                                        'aynı OAuth istemcisine ait indirilen Desktop uygulama JSON dosyasıyla güncelleyin.'
                                    )
                                detail = f'{reason}: {description}' if description else str(reason)
                                raise RuntimeError('Google token alışverişi başarısız: ' + detail)
                            payload = resp.json()
                            if not payload.get('access_token'):
                                raise RuntimeError('Google erişim belirteci alınamadı.')
                            captured['credentials'] = Credentials(
                                token=payload['access_token'],
                                refresh_token=payload.get('refresh_token'),
                                token_uri='https://oauth2.googleapis.com/token',
                                client_id=client_id,
                                client_secret=client_secret or None,
                                scopes=SCOPES,
                                expiry=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=max(1,int(payload.get('expires_in', 3599))-30)),
                            )
                            page = callback_page(True, 'Yetkilendirme tamamlandı. YLSY Atlas uygulamasına dönün.')
                        except Exception as exc:
                            captured['error'] = str(exc)
                            page = callback_page(False, captured['error'])
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
                self.end_headers()
                try:
                    self.wfile.write(page)
                except OSError:
                    pass
                completed.set()

        # Desktop client loopback redirects are supported by Google. Dynamic
        # port avoids collisions with another running program.
        with HTTPServer(('127.0.0.1', 0), Handler) as server:
            server.timeout = 0.5
            # Google Desktop loopback redirect uses the port URL without a trailing slash.
            redirect_uri = f'http://127.0.0.1:{server.server_port}'
            url = self._auth_url(self.client_id, redirect_uri, challenge, expected_state)
            if not webbrowser.open(url, new=2):
                raise RuntimeError('Varsayılan tarayıcı açılamadı. Windows varsayılan tarayıcı ayarını kontrol edin.')
            from time import monotonic
            deadline = monotonic() + 180
            while not completed.is_set() and monotonic() < deadline:
                server.handle_request()
            if not completed.is_set():
                raise TimeoutError('Google giriş ekranı üç dakika içinde tamamlanmadı.')
        if captured.get('error'):
            raise RuntimeError(captured['error'])
        creds = captured.get('credentials')
        if not creds:
            raise RuntimeError('Google girişinden yetkilendirme kodu alınamadı.')
        return creds

    def authorize(self, interactive: bool = True, force_account_choice: bool = False):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        saved = self.secret_store.get_password(OAUTH_SERVICE, self.account_key)
        creds = None
        if saved and not force_account_choice:
            saved_info = json.loads(saved)
            if self.client_secret:
                # Credentials.client_secret is read-only. Recreate the object
                # with the current publisher config before refreshing a token.
                saved_info['client_secret'] = self.client_secret
            creds = Credentials.from_authorized_user_info(saved_info, scopes=SCOPES)
            if creds.client_id != self.client_id:
                creds = None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            if not interactive:
                raise RuntimeError('Google oturumu yenilenemiyor. Kullanıcı simgesinden hesabı tekrar bağlayın.')
            creds = self._browser_login()
            if not creds.refresh_token:
                raise RuntimeError('Google uzun süreli erişim izni vermedi; tekrar bağlanmayı deneyin.')
        self.secret_store.set_password(OAUTH_SERVICE, self.account_key, creds.to_json())
        return creds

    def disconnect(self):
        try:
            self.secret_store.delete_password(OAUTH_SERVICE, self.account_key)
        except Exception:
            pass

def make_service(creds):
    from googleapiclient.discovery import build
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


class GoogleDrive:
    def __init__(self, service, app_folder_id: str | None = None):
        self.service = service
        self.folder_id = app_folder_id

    def folders_in(self, parent_id: str = 'root'):
        q = f"'{_quote_q(parent_id)}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        items, page = [], None
        while True:
            resp = self.service.files().list(q=q, fields='nextPageToken,files(id,name,mimeType,parents)', pageSize=100, pageToken=page).execute()
            items.extend(resp.get('files', []))
            page = resp.get('nextPageToken')
            if not page: break
        return sorted(items, key=lambda f: f['name'].casefold())

    def get_or_create_app_folder(self, selected_parent: str):
        for item in self.folders_in(selected_parent):
            if item['name'] == APP_FOLDER_NAME:
                self.folder_id = item['id']
                return self.folder_id
        created = self.service.files().create(body={'name': APP_FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [selected_parent]},fields='id,name').execute()
        self.folder_id = created['id']
        return self.folder_id

    def _require_folder(self):
        if not self.folder_id:
            raise ValueError('Drive klasörü henüz seçilmedi.')

    def list_docs(self):
        self._require_folder()
        q = f"'{_quote_q(self.folder_id)}' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        result, page = {}, None
        while True:
            resp = self.service.files().list(q=q, fields='nextPageToken,files(id,name,md5Checksum,appProperties,modifiedTime)', pageSize=1000, pageToken=page).execute()
            for f in resp.get('files', []):
                key = f.get('appProperties', {}).get('ylsy_key')
                if key:
                    f['key'] = key
                    result[key] = f
            page = resp.get('nextPageToken')
            if not page: break
        return result

    def put_doc(self, key: str, data: bytes, file_id: str | None):
        from googleapiclient.http import MediaIoBaseUpload
        if len(key.encode('utf-8')) > 110:
            raise ValueError('Drive kayıt anahtarı çok uzun (110 UTF-8 baytı aşamaz).')
        self._require_folder()
        mime = mimetypes.guess_type(key)[0] or 'application/octet-stream'
        basename = key.split('/')[-1].replace('\\', '_')
        safe_name = re.sub(r'[^\w.() -]+', '_', basename, flags=re.UNICODE)[:100] or 'kayit'
        name = f'{safe_name}--{hashlib.sha256(key.encode()).hexdigest()[:10]}'
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime, resumable=True, chunksize=1024 * 1024)
        files = self.service.files()
        if file_id:
            req = files.update(fileId=file_id, media_body=media, fields='id,name,md5Checksum,appProperties')
        else:
            req = files.create(body={'name':name,'parents':[self.folder_id],'mimeType':mime,'appProperties':{'ylsy_key':key}}, media_body=media, fields='id,name,md5Checksum,appProperties')
        # Resumable yüklemeyi tamamlamadan doğrulama ve yerel silme yapılmaz.
        answer = None
        while answer is None:
            _, answer = req.next_chunk(num_retries=3)
        answer['key'] = key
        return answer

    def doc_info(self, file_id, missing_ok=False):
        from googleapiclient.errors import HttpError
        try:
            return self.service.files().get(fileId=file_id, fields='id,name,md5Checksum,appProperties,trashed').execute()
        except HttpError as e:
            if missing_ok and e.resp.status in (404, 410):
                return None
            raise

    def get_doc(self, file_id):
        from googleapiclient.http import MediaIoBaseDownload
        stream = io.BytesIO()
        req = self.service.files().get_media(fileId=file_id)
        download = MediaIoBaseDownload(stream, req)
        finished = False
        while not finished:
            _, finished = download.next_chunk(num_retries=3)
        return stream.getvalue()

    def delete_doc(self, file_id):
        self.service.files().delete(fileId=file_id).execute()
