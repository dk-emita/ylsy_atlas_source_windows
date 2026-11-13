"""Mandatory Windows desktop updater for the public GitHub Releases feed."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RELEASE_API = 'https://api.github.com/repos/dk-emita/ylsy_atlas/releases/latest'
USER_AGENT = 'YLSYAtlas-Windows-Updater'


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers = re.findall(r'\d+', str(value or '').lstrip('vV'))
    return tuple(int(part) for part in numbers[:4]) or (0,)


def _current_version() -> str:
    info = ROOT / 'assets' / 'version_info.txt'
    try:
        match = re.search(r"ProductVersion','([^']+)'", info.read_text(encoding='utf-8'))
        if match:
            return match.group(1)
    except OSError:
        pass
    return '4.0.0'


def _latest_windows_release(timeout: float = 3.5):
    request = urllib.request.Request(
        RELEASE_API,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': USER_AGENT,
                 'X-GitHub-Api-Version': '2022-11-28'},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        release = json.loads(response.read().decode('utf-8'))
    tag = str(release.get('tag_name') or '').strip()
    if not tag or _version_tuple(tag) <= _version_tuple(_current_version()):
        return None
    assets = release.get('assets') or []
    asset = next((item for item in assets
                  if str(item.get('name', '')).lower().endswith('-setup.exe')
                  and str(item.get('browser_download_url', '')).startswith('https://github.com/')),
                 None)
    return {'tag': tag, 'asset': asset}


def _message_box(app, icon, title: str, message: str, update_available: bool) -> bool:
    from PySide6.QtWidgets import QMessageBox
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setWindowIcon(icon)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Warning if update_available else QMessageBox.Icon.Critical)
    update_button = box.addButton('Güncelle', QMessageBox.ButtonRole.AcceptRole) if update_available else None
    exit_button = box.addButton('Çıkış', QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(update_button or exit_button)
    box.setEscapeButton(exit_button)
    box.setModal(True)
    box.exec()
    return update_available and box.clickedButton() is update_button


def _download_and_start_installer(asset: dict, version: str, app, icon) -> bool:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog

    url = str(asset.get('browser_download_url') or '')
    if not url.startswith('https://github.com/'):
        return False
    target = Path(tempfile.gettempdir()) / f'YLSY-Atlas-v{version}-Setup.exe'
    expected_size = int(asset.get('size') or 0)
    expected_digest = str(asset.get('digest') or '')
    progress = QProgressDialog('Yeni Windows sürümü indiriliyor…', '', 0, 100)
    progress.setCancelButton(None)
    progress.setWindowTitle('YLSY Atlas güncellemesi')
    progress.setWindowIcon(icon)
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.show()
    QApplication.processEvents()
    part = target.with_suffix('.exe.part')
    digest = hashlib.sha256()
    total = 0
    try:
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(request, timeout=25) as response, part.open('wb') as output:
            length = int(response.headers.get('Content-Length') or expected_size or 0)
            while True:
                chunk = response.read(1024 * 512)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                total += len(chunk)
                if length:
                    progress.setValue(min(99, int(total * 100 / length)))
                progress.setLabelText(f'Yeni Windows sürümü indiriliyor… {total / 1048576:.0f} MB')
                QApplication.processEvents()
            output.flush()
            os.fsync(output.fileno())
        if total < 1024 or (expected_size and total != expected_size):
            raise OSError('İndirilen kurulum dosyasının boyutu doğrulanamadı.')
        if expected_digest.startswith('sha256:') and digest.hexdigest().lower() != expected_digest[7:].lower():
            raise OSError('Kurulum dosyasının SHA-256 doğrulaması başarısız oldu.')
        os.replace(part, target)
        progress.setValue(100)
        progress.close()
        subprocess.Popen([str(target), '/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
                         close_fds=True)
        return True
    except Exception:
        progress.close()
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        _message_box(app, icon, 'Güncelleme tamamlanamadı',
                     'Yeni Windows sürümü indirilemedi veya doğrulanamadı. Güvenliğiniz için Atlas kapatılacak; internet bağlantısını kontrol edip yeniden açın.',
                     False)
        return False


def check_for_windows_update() -> bool:
    """Return False to exit after installing or when a mandatory update fails."""
    import sys
    if sys.platform != 'win32':
        return True
    try:
        release = _latest_windows_release()
    except Exception:
        # Keep the desktop app usable offline or while GitHub is unavailable.
        return True
    if not release:
        return True
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv[:1])
    icon_path = ROOT / 'assets' / 'icon.png'
    icon = QIcon(str(icon_path))
    asset = release.get('asset')
    if not asset:
        _message_box(app, icon, 'YLSY Atlas güncellemesi gerekli',
                     f'{release["tag"]} sürümü yayımlandı ancak Windows kurulum dosyası eklenmemiş. Güncelleme yayımlanana kadar uygulama açılamaz.',
                     False)
        return False
    accepted = _message_box(app, icon, 'YLSY Atlas güncellemesi gerekli',
                            f'Yeni Windows sürümü ({release["tag"]}) yayımlandı. Devam etmek için güncelleme gerekli.',
                            True)
    if not accepted:
        return False
    if _download_and_start_installer(asset, release['tag'], app, icon):
        return False
    return False
