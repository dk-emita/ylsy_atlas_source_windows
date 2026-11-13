"""Exercise desktop restore and sign-out without touching a real Drive account."""
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drive_sync import CloudController
from storage import Store


class FakeDrive:
    folder_id = 'atlas-folder'

    def __init__(self):
        self.data = {}

    def get_or_create_app_folder(self, parent):
        return self.folder_id

    def list_docs(self):
        return {name: {'id': name, 'md5Checksum': hashlib.md5(blob).hexdigest()}
                for name, blob in self.data.items()}

    def put_doc(self, name, blob, existing):
        self.data[name] = blob
        return self.list_docs()[name]

    def doc_info(self, name):
        return self.list_docs().get(name)

    def get_doc(self, name):
        return self.data[name]


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    drive = FakeDrive()

    first_store = Store(root / 'first')
    first = CloudController(first_store, root / 'resources', start_worker=False)
    first._drive = lambda folder_id=None: drive
    first._start_worker = lambda: None
    first.credentials = object()
    first_store.save('universities', {'name': 'Massachusetts Institute of Technology', 'short': 'MIT'})
    first.select_google_folder('root')
    first.sync_once()
    assert first.synced and not first.dirty

    second_store = Store(root / 'second')
    second = CloudController(second_store, root / 'resources', start_worker=False)
    second._drive = lambda folder_id=None: drive
    second._start_worker = lambda: None
    second.credentials = object()
    second.select_google_folder('root')
    second.sync_once()
    assert second_store.all('universities')[0]['short'] == 'MIT'
    assert second.synced and not second.dirty

    second.auth = type('FakeAuth', (), {'disconnect': lambda self: None})()
    second.disconnect()
    assert second.config['local_purged']
    assert second_store.all('universities') == []
    assert second.credentials is None and not second.current()['authorization_ready']

    second.credentials = object()
    second.select_google_folder('root')
    second.sync_once()
    assert second_store.all('universities')[0]['short'] == 'MIT'
    assert not second.conflict_blocked and not second.dirty

    first.close()
    second.close()

print('PASS: desktop upload, first-login restore, sign-out cleanup, and reconnect restore')
