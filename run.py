"""YLSY Atlas native desktop entry point.

Windows: genuine Qt window / Windows taskbar icon, not an Edge/Chrome app-mode
window with a separate temporary browser process. Backend remains localhost.
--no-browser remains supported for API/CI tests.
--legacy-browser is an optional troubleshooting fallback, not the default.
"""
from __future__ import annotations
import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from server import create_server
from desktop_update import check_for_windows_update

ROOT = Path(__file__).resolve().parent
ICON = ROOT / 'assets' / 'icon.png'


def _single_instance(wait_ms=30000):
    """Keep the scheduled sync job away from an active SQLite workspace."""
    if sys.platform != 'win32':
        return None
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.restype = ctypes.c_bool
    handle = kernel.CreateMutexW(None, True, 'Local\\YLSYAtlasWorkspace')
    if not handle:
        raise OSError('YLSY Atlas çalışma kilidi oluşturulamadı')
    if ctypes.get_last_error() == 183:
        # A scheduled offline-sync run may briefly own the same workspace
        # mutex. Wait for that work to finish so a normal launch is not lost.
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.FindWindowW.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p)
        user32.FindWindowW.restype = ctypes.c_void_p
        user32.ShowWindow.argtypes = (ctypes.c_void_p, ctypes.c_int)
        user32.SetForegroundWindow.argtypes = (ctypes.c_void_p,)
        existing = user32.FindWindowW(None, 'YLSY Atlas — Başvuru ve Hazırlık Platformu')
        if existing:
            user32.ShowWindow(existing, 9)  # SW_RESTORE
            user32.SetForegroundWindow(existing)
            kernel.CloseHandle(handle)
            return None
        kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        kernel.WaitForSingleObject.restype = ctypes.c_uint32
        waited = kernel.WaitForSingleObject(handle, max(0, int(wait_ms)))
        if waited not in (0, 0x80):  # WAIT_OBJECT_0 / WAIT_ABANDONED
            kernel.CloseHandle(handle)
            return False
    return handle


def _release_instance(handle):
    if handle:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
        kernel.CloseHandle.restype = ctypes.c_bool
        kernel.CloseHandle(handle)


def sync_pending(root):
    """Scheduled, headless upload of offline edits after the UI has closed."""
    from storage import Store, data_dir
    from drive_sync import CloudController
    data_root = Path(root or data_dir())
    config_path = data_root / 'cloud-connection.json'
    if not config_path.is_file():
        return
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if config.get('mode') != 'oauth' or not config.get('dirty'):
        return
    store = Store(data_root)
    cloud = CloudController(store, ROOT / 'resources', start_worker=False)
    try:
        cloud.sync_once()
    finally:
        cloud.close()
    cloud.purge_verified_local_data()


def _browser_binary():
    choices=[]
    if os.name=='nt':
        for base in (os.environ.get('PROGRAMFILES',''), os.environ.get('PROGRAMFILES(X86)',''), os.environ.get('LOCALAPPDATA','')):
            if base:
                choices.extend((Path(base)/'Microsoft/Edge/Application/msedge.exe',Path(base)/'Google/Chrome/Application/chrome.exe'))
    for name in ('msedge','msedge.exe','chrome','google-chrome','chromium','chromium-browser'):
        found=shutil.which(name)
        if found: choices.append(Path(found))
    return next((str(x) for x in choices if x.is_file()),None)


def legacy_browser_window(url):
    """Opt-in troubleshooting fallback. Its taskbar icon is browser-managed."""
    binary=_browser_binary()
    if binary:
        with tempfile.TemporaryDirectory(prefix='YLSYAtlas-Window-') as profile:
            args=[binary, f'--app={url}', '--new-window', f'--user-data-dir={profile}',
                  '--disable-background-mode','--no-first-run','--window-size=1500,940']
            subprocess.Popen(args).wait()
    else:
        webbrowser.open(url)
        while True:time.sleep(.2)


def native_window(url, check_report=None, cloud=None):
    """Run the app as a genuine Windows/Qt window with an explicit taskbar icon."""
    from PySide6.QtCore import QUrl, Qt, QStandardPaths, QTimer, qVersion
    from PySide6.QtGui import QIcon, QDesktopServices
    from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings

    if sys.platform=='win32':
        # Assign the taskbar the identity of Atlas, not that of Edge or Chrome.
        try:ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('YLSY.Atlas.Desktop.236')
        except (AttributeError,OSError):pass

    app=QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName('YLSY Atlas')
    app.setOrganizationName('YLSY Atlas')
    app.setApplicationDisplayName('YLSY Atlas — Başvuru ve Hazırlık Platformu')
    # Give Qt the full-resolution approved image so it rasterizes each window
    # and taskbar size from the master PNG instead of reusing a tiny ICO frame.
    app_icon=QIcon(str(ICON))
    if app_icon.isNull():
        app_icon=QIcon(str(ROOT/'assets'/'atlas-icon.ico'))
    app.setWindowIcon(app_icon)

    check_done = False

    def complete_check(ok, **details):
        nonlocal check_done
        if check_report is None or check_done:
            return
        check_done = True
        result = {
            'ok': ok, 'backend': 'Qt', 'qt': qVersion(),
            'pid': os.getpid(), 'hwnd': int(window.winId()),
            'icon_source': str(ICON), 'icon_null': app_icon.isNull(),
            'ui_loaded': ok,
            **details,
        }
        def finish():
            if ok:
                window.grab().save(str(check_report.with_suffix('.png')))
            check_report.write_text(json.dumps(result), encoding='utf-8')
            QTimer.singleShot(100, app.quit)
        # DOM readiness precedes Chromium's next composited frame.
        QTimer.singleShot(750 if ok else 0, finish)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('YLSY Atlas — Başvuru ve Hazırlık Platformu')
            self.setWindowIcon(app_icon)
            self.setMinimumSize(950,670)
            self.resize(1500,940)
            self.web=QWebEngineView(self)
            self.setCentralWidget(self.web)
            self.web.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled,True)
            self.web.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,True)
            self.web.page().newWindowRequested.connect(self._external_window)
            self.web.page().profile().downloadRequested.connect(self._download)
            self._first_load=True
            self.web.loadFinished.connect(self._on_load)
            self.web.page().renderProcessTerminated.connect(self._renderer_terminated)
            self.web.load(QUrl(url))

        def _on_load(self, ok):
            if check_report is not None:
                if not ok:
                    complete_check(False, error='The application page failed to load.')
                else:
                    self._check_ui()
                return
            if self._first_load:
                self._first_load=False
                if not ok:
                    QMessageBox.warning(self,'YLSY Atlas','Uygulama arayüzü yüklenemedi. Yerel sunucu çalışıyor mu?')

        def _renderer_terminated(self, status, code):
            if check_report is not None:
                complete_check(False, error=f'Renderer stopped: {status}, code {code}')

        def _check_ui(self):
            if check_done:
                return
            script = """JSON.stringify({
                ready: typeof state !== 'undefined' && state.overview !== null,
                heading: document.querySelector('#main h1')?.textContent || '',
                navigation: document.querySelectorAll('#sidebar [data-nav]').length,
                loading: !!document.querySelector('#main .loading-screen'),
                background: getComputedStyle(document.body).backgroundColor
            })"""
            def inspect(value):
                if check_done:
                    return
                try:
                    snapshot = json.loads(value or '{}')
                except (ValueError, TypeError):
                    snapshot = {}
                if (snapshot.get('ready') and snapshot.get('heading')
                        and snapshot.get('navigation', 0) >= 10
                        and not snapshot.get('loading')
                        and snapshot.get('background') not in ('', 'rgba(0, 0, 0, 0)')):
                    complete_check(True, **snapshot)
                else:
                    QTimer.singleShot(250, self._check_ui)
            self.web.page().runJavaScript(script, inspect)

        def _external_window(self,req):
            address=req.requestedUrl()
            # Opening REBUS is handled by server in the user's normal browser.
            # Other window.open links (PDF/source links) also use normal browser.
            if address.scheme() in ('http','https'):
                QDesktopServices.openUrl(address)

        def _download(self,download):
            home=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            suggested=download.downloadFileName() or 'YLSY-Atlas-Dosya'
            from pathlib import Path
            target,_=QFileDialog.getSaveFileName(self,'Dosyayı kaydet',str(Path(home)/suggested))
            if target:
                dest=Path(target)
                download.setDownloadDirectory(str(dest.parent))
                download.setDownloadFileName(dest.name)
                download.accept()
            else:
                download.cancel()

    window=MainWindow()
    window.show()
    # Refresh icon once Windows has created the native HWND.
    window.setWindowIcon(app_icon)
    if cloud is not None:
        def return_from_google():
            if not cloud.login_completed.is_set():
                return
            cloud.login_completed.clear()
            window.showNormal()
            window.raise_()
            window.activateWindow()
            if sys.platform == 'win32':
                ctypes.windll.user32.SetForegroundWindow(int(window.winId()))
        login_return_timer = QTimer(window)
        login_return_timer.timeout.connect(return_from_google)
        login_return_timer.start(250)
    if check_report is not None:
        QTimer.singleShot(30000, lambda: complete_check(False, error='Application UI did not become ready in 30 seconds.'))
    return app.exec()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--no-browser',action='store_true',help='Start local API for tests only')
    p.add_argument('--legacy-browser',action='store_true',help='Opt in to old Edge/Chrome app-mode window')
    p.add_argument('--port',type=int,default=0)
    p.add_argument('--data-dir',type=Path,default=None)
    p.add_argument('--sync-pending',action='store_true',help='Upload offline changes without opening the UI')
    p.add_argument('--check-native-window',type=Path,help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.check_native_window:
        # Load the real page, CSS, JS and bootstrap API using an isolated empty
        # workspace; no user account, data, updater or Drive worker is opened.
        try:
            with tempfile.TemporaryDirectory(prefix='YLSYAtlas-UI-Check-', ignore_cleanup_errors=True) as check_dir:
                check_server=create_server(root=Path(check_dir), start_cloud_worker=False)
                threading.Thread(target=check_server.serve_forever, daemon=True).start()
                try:
                    native_window(check_server.atlas_url, check_report=args.check_native_window)
                finally:
                    check_server.shutdown()
                    check_server.server_close()
                    check_server.atlas_cloud.close()
                    import gc
                    gc.collect()
        except Exception as exc:
            args.check_native_window.write_text(json.dumps({
                'ok': False, 'error': str(exc)
            }), encoding='utf-8')
        return
    instance = _single_instance(0 if args.sync_pending else 30000)
    if instance is None:
        return
    if instance is False:
        if not args.sync_pending and sys.platform == 'win32':
            ctypes.windll.user32.MessageBoxW(None,
                'YLSY Atlas arka plan eşitlemesini tamamlıyor. Biraz sonra yeniden açın.',
                'YLSY Atlas', 0x40)
        return
    if args.sync_pending:
        try:
            sync_pending(args.data_dir)
        finally:
            _release_instance(instance)
        return
    if not args.no_browser and not check_for_windows_update():
        _release_instance(instance)
        return
    server=create_server(root=args.data_dir,port=args.port,start_cloud_worker=False)
    if server.atlas_cloud.config.get('local_purged'):
        try:
            server.atlas_cloud.sync_once()
        except Exception as exc:
            server.atlas_cloud.status_text = 'Çevrimdışı: yeni kayıtlar geçici olarak bu bilgisayarda saklanır'
            server.atlas_cloud.error = str(exc)[:240]
    if server.atlas_cloud.connected:
        server.atlas_cloud._start_worker()
    worker=threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    try:
        if args.no_browser:
            print(server.atlas_url,flush=True)
            while True:time.sleep(.2)
        elif args.legacy_browser:
            legacy_browser_window(server.atlas_url)
        else:
            try:
                native_window(server.atlas_url, cloud=server.atlas_cloud)
            except Exception as exc:
                import traceback
                from storage import data_dir
                log = Path(data_dir()) / 'logs' / 'startup.log'
                log.parent.mkdir(parents=True, exist_ok=True)
                detail = traceback.format_exc()
                log.write_text(detail + '\nQt penceresi açılamadı; uygulama penceresi için tarayıcı uygulama kipine geçiliyor.\n', encoding='utf-8')
                try:
                    legacy_browser_window(server.atlas_url)
                except Exception as browser_exc:
                    with log.open('a',encoding='utf-8') as f:
                        f.write('\nTarayıcı yedeği de açılamadı: ' + repr(browser_exc) + '\n')
                    if sys.platform == 'win32':
                        ctypes.windll.user32.MessageBoxW(None,
                            'YLSY Atlas açılamadı. Hata kaydı burada:\n' + str(log) + '\n\n' + str(browser_exc),
                            'YLSY Atlas başlatma hatası', 0x10)
                    raise
    except KeyboardInterrupt:pass
    finally:
        server.shutdown()
        server.server_close()
        server.atlas_cloud.close()
        server.atlas_cloud.purge_verified_local_data()
        _release_instance(instance)

if __name__=='__main__':main()
