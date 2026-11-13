"""Merge records created offline after a verified cloud-only cleanup."""
from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from storage import Store


def merge_new_records(remote_backup: bytes, offline_backup: bytes) -> bytes:
    """Add locally created rows to the remote workspace with new IDs.

    A purged workspace has no old records to edit while offline. Consequently
    every local row is new; remapping IDs preserves its relationships.
    """
    with tempfile.TemporaryDirectory(prefix='atlas-cloud-merge-') as directory:
        base = Path(directory)
        remote = Store(base / 'remote')
        offline = Store(base / 'offline')
        remote.restore(remote_backup, keep_previous=False, notify=False)
        offline.restore(offline_backup, keep_previous=False, notify=False)
        tables = ('universities', 'programs', 'advisors', 'tasks', 'documents',
                  'ielts_sessions', 'vocabulary', 'events', 'notes', 'resources', 'attachments')
        mapping = {}
        with offline.connect() as source, remote.connect() as target:
            for table in tables:
                mapping[table] = {}
                for original in source.execute(f'SELECT * FROM {table} ORDER BY id'):
                    row = dict(original)
                    old_id = row.pop('id')
                    if table in ('programs', 'advisors'):
                        row['university_id'] = mapping['universities'][row['university_id']]
                    if table == 'advisors' and row['program_id'] is not None:
                        row['program_id'] = mapping['programs'][row['program_id']]
                    if table == 'attachments':
                        parent_table = {'university': 'universities', 'program': 'programs',
                                        'advisor': 'advisors', 'task': 'tasks',
                                        'document': 'documents'}.get(row['owner_type'])
                        if parent_table and row['owner_id']:
                            parent_id = mapping[parent_table].get(row['owner_id'])
                            if parent_id is None:
                                row['owner_type'], row['owner_id'] = 'general', 0
                            else:
                                row['owner_id'] = parent_id
                        old_name = row['stored_name']
                        new_name = uuid.uuid4().hex + Path(old_name).suffix
                        shutil.copy2(offline.uploads / old_name, remote.uploads / new_name)
                        row['stored_name'] = new_name
                    columns = tuple(row)
                    marks = ','.join('?' for _ in columns)
                    new_id = target.execute(
                        f'INSERT INTO {table} ({",".join(columns)}) VALUES ({marks})',
                        tuple(row.values()),
                    ).lastrowid
                    mapping[table][old_id] = new_id
            for key, value in source.execute('SELECT key,value FROM settings'):
                target.execute('INSERT INTO settings(key,value) VALUES (?,?) '
                               'ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))
        return remote.backup()
