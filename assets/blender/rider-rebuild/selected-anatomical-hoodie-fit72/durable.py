"""Atomic, verified transport spans. No scheduling, retry or geometry policy."""
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''): value.update(chunk)
    return value.hexdigest()


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def atomic_json(path, value):
    """Only a fully fsynced JSON is exposed under its final name."""
    path = Path(path); assert not path.exists()
    descriptor, pending = tempfile.mkstemp(prefix='.pending-json-', dir=path.parent)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(value, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    assert not path.exists(); os.rename(pending, path); sync_directory(path.parent)


class Spans:
    def __init__(self, root, job, np, create=False):
        self.root, self.job, self.np = Path(root).resolve(), job, np
        self.count, self.chunk = job['sourceVertexCount'], job['chunkSize']
        assert self.count > 0 and self.chunk > 0
        if create:
            assert not self.root.exists(); self.root.mkdir(parents=True)
            (self.root/'spans').mkdir(); atomic_json(self.root/'job.json', job)
            sync_directory(self.root.parent)
        assert json.loads((self.root/'job.json').read_text()) == job, 'Wrong executing source or frozen job'
        assert (self.root/'spans').is_dir()
        self.job_sha = sha(self.root/'job.json')

    def pin(self, path, logical=None):
        path = Path(path)
        return {'path': str((Path(logical) if logical else path).relative_to(self.root)), 'sha256': sha(path)}

    def checked(self, row):
        path = (self.root/row['path']).resolve()
        assert path.is_relative_to(self.root) and sha(path) == row['sha256'], row['path']
        return path

    def arrays(self, position, jacobian, count):
        p = self.np.load(position, mmap_mode='r', allow_pickle=False)
        j = self.np.load(jacobian, mmap_mode='r', allow_pickle=False)
        assert p.dtype == j.dtype == self.np.float64
        assert p.shape == (count, 3) and j.shape == (count, 3, 3)
        return p, j

    def source_hash(self, original, start, end):
        assert original.shape == (self.count, 3) and original.dtype == self.np.float32
        return hashlib.sha256(original[start:end].tobytes()).hexdigest()

    def scan(self, original, complete=False):
        """Reject corrupt or gapped sealed spans; ignore only unsealed staging."""
        directories = []
        for path in (self.root/'spans').iterdir():
            if path.name.startswith('.pending-'): continue
            match = re.fullmatch(r'(\d{7})-(\d{7})', path.name)
            assert match and path.is_dir(), ('Unexpected sealed span', str(path))
            directories.append((int(match[1]), int(match[2]), path))
        at = 0; seals = []
        for start, end, path in sorted(directories):
            assert start == at and end == min(start+self.chunk, self.count), ('Noncontiguous or invalid span', start, end, at)
            assert end > start
            assert {p.name for p in path.iterdir()} == {'positions.npy', 'jacobians.npy', 'seal.json'}
            seal = json.loads((path/'seal.json').read_text())
            assert set(seal) == {'status', 'jobSHA256', 'start', 'end', 'originalPointsSHA256', 'positions', 'jacobians'}
            assert seal['status'] == 'SEALED_COMPLETE_SPAN72' and seal['jobSHA256'] == self.job_sha
            assert seal['start'] == start and seal['end'] == end
            assert seal['originalPointsSHA256'] == self.source_hash(original, start, end)
            assert seal['positions']['path'] == str((path/'positions.npy').relative_to(self.root))
            assert seal['jacobians']['path'] == str((path/'jacobians.npy').relative_to(self.root))
            p, j = self.arrays(self.checked(seal['positions']), self.checked(seal['jacobians']), end-start)
            assert self.np.isfinite(p).all() and self.np.isfinite(j).all()
            seals.append({'start': start, 'end': end, 'seal': self.pin(path/'seal.json')}); at = end
        if complete: assert at == self.count, ('Incomplete transport is inadmissible', at, self.count)
        return at, seals

    def seal(self, start, positions, jacobians, original):
        end = min(start+self.chunk, self.count); count = end-start
        assert 0 <= start < self.count and start % self.chunk == 0
        assert positions.shape == (count, 3) and jacobians.shape == (count, 3, 3)
        assert positions.dtype == jacobians.dtype == self.np.float64
        assert self.np.isfinite(positions).all() and self.np.isfinite(jacobians).all()
        final = self.root/'spans'/('%07d-%07d' % (start, end)); assert not final.exists()
        pending = Path(tempfile.mkdtemp(prefix='.pending-span-', dir=final.parent))
        for name, value in (('positions.npy', positions), ('jacobians.npy', jacobians)):
            with (pending/name).open('wb') as stream:
                self.np.save(stream, value, allow_pickle=False); stream.flush(); os.fsync(stream.fileno())
        p, j = self.arrays(pending/'positions.npy', pending/'jacobians.npy', count)
        assert self.np.array_equal(p, positions) and self.np.array_equal(j, jacobians)
        del p, j
        seal = {'status': 'SEALED_COMPLETE_SPAN72', 'jobSHA256': self.job_sha,
            'start': start, 'end': end, 'originalPointsSHA256': self.source_hash(original, start, end),
            'positions': self.pin(pending/'positions.npy', final/'positions.npy'),
            'jacobians': self.pin(pending/'jacobians.npy', final/'jacobians.npy')}
        atomic_json(pending/'seal.json', seal); sync_directory(pending)
        assert not final.exists(); os.rename(pending, final); sync_directory(final.parent)

    def verify_assembly(self, original):
        _, seals = self.scan(original, complete=True)
        final = self.root/'complete'
        assert {p.name for p in final.iterdir()} == {'positions.npy', 'jacobians.npy', 'assembly.json'}
        row = json.loads((final/'assembly.json').read_text())
        assert set(row) == {'status', 'jobSHA256', 'sourceVertexCount', 'spans', 'positions', 'jacobians'}
        assert row['status'] == 'ALL_SEALED_SPANS_ASSEMBLED72' and row['jobSHA256'] == self.job_sha
        assert row['sourceVertexCount'] == self.count and row['spans'] == seals
        assert row['positions']['path'] == 'complete/positions.npy'
        assert row['jacobians']['path'] == 'complete/jacobians.npy'
        p, j = self.arrays(self.checked(row['positions']), self.checked(row['jacobians']), self.count)
        for span in seals:
            seal = json.loads(self.checked(span['seal']).read_text())
            a, b = self.arrays(self.checked(seal['positions']), self.checked(seal['jacobians']), span['end']-span['start'])
            assert self.np.array_equal(p[span['start']:span['end']], a)
            assert self.np.array_equal(j[span['start']:span['end']], b)
        return row

    def assemble(self, original):
        _, seals = self.scan(original, complete=True)
        final = self.root/'complete'
        if final.exists(): return self.verify_assembly(original)
        pending = Path(tempfile.mkdtemp(prefix='.pending-assembly-', dir=self.root))
        p = self.np.lib.format.open_memmap(pending/'positions.npy', mode='w+', dtype=self.np.float64, shape=(self.count, 3))
        j = self.np.lib.format.open_memmap(pending/'jacobians.npy', mode='w+', dtype=self.np.float64, shape=(self.count, 3, 3))
        for span in seals:
            seal = json.loads(self.checked(span['seal']).read_text())
            a, b = self.arrays(self.checked(seal['positions']), self.checked(seal['jacobians']), span['end']-span['start'])
            p[span['start']:span['end']] = a; j[span['start']:span['end']] = b
        p.flush(); j.flush(); del p, j
        for name in ('positions.npy', 'jacobians.npy'):
            with (pending/name).open('rb') as stream: os.fsync(stream.fileno())
        row = {'status': 'ALL_SEALED_SPANS_ASSEMBLED72', 'jobSHA256': self.job_sha,
            'sourceVertexCount': self.count, 'spans': seals,
            'positions': self.pin(pending/'positions.npy', final/'positions.npy'),
            'jacobians': self.pin(pending/'jacobians.npy', final/'jacobians.npy')}
        atomic_json(pending/'assembly.json', row); sync_directory(pending)
        assert not final.exists(); os.rename(pending, final); sync_directory(final.parent)
        return self.verify_assembly(original)
