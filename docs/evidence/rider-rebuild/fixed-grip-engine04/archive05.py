"""Archive exact completed played reports; derive unaccepted movie review frames."""
import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = ROOT / 'harness/out/rider-rebuild/fixed-grip-engine04'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(name):
    report_path = OUT / name / 'report.json'
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    guard_path = EVIDENCE / (name + '-guard/guard.json')
    guard = json.loads(guard_path.read_text())
    assert guard['exitCode'] == 0 and guard['status'] == 'worker returned; review pending'
    assert report['captureChecksCompleted'] and not report.get('failure') and not report['errors']
    assert report['encoding']['exitCode'] == 0
    assert report['presence']['invalidFrames'] == 0
    assert report['source']['sha256'] == '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef'
    assert report['source']['bytes'] == 74833728
    summary_path = EVIDENCE / (name + '-summary05.json')
    compressed_path = EVIDENCE / (name + '-report05.json.gz')
    assert not summary_path.exists() and not compressed_path.exists(), 'Never overwrite evidence'
    movie_path = Path(report['encoding']['encodedPath'])
    metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-show_entries', 'stream=width,height,codec_type:format=duration', '-of', 'json', str(movie_path)]))
    assert not any(s['codec_type'] == 'audio' for s in metadata['streams'])
    duration = float(metadata['format']['duration'])
    summary = {key: report[key] for key in ['accepted', 'status', 'mode', 'bike', 'source',
        'contract', 'runtimeMetadata', 'requestedGripProfileSHA256', 'profileDriverIdentity',
        'sourcePinsAtCapture', 'sourcePinScope', 'browser', 'audio', 'method', 'limits', 'presence',
        'videoRates', 'encoding']}
    summary['reviewLimits'] = 'Unaccepted checkpoint. Parent judges played movie. Socket/joint invariants do not establish finger, thumb, cuff or hoodie surface acceptance. Mac submissions and encoded cadence do not establish iPhone FPS.'
    summary['exactReport'] = {'path': str(report_path.relative_to(ROOT)),
        'sha256': hashlib.sha256(report_bytes).hexdigest(), 'bytes': len(report_bytes),
        'compressedArchive': str(compressed_path.relative_to(ROOT))}
    summary['movies'] = [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p), 'bytes': p.stat().st_size}
        for p in [Path(report['rawVideoPath']), movie_path]]
    if report['mode'] == 'lean':
        samples = report['played']['motionSamples']
        assert len(samples) == 241 and len(report['played']['inputs']) == 1200
        assert all(s['tick'] == i * 5 and len(s['joints']) == 75 and s['debug']['allBoneFinite']
            and s['debug']['physicalPose'] and s['debug']['stageClip'] is None for i, s in enumerate(samples))
        assert all(len(s['debug']['forearmPronation']) == 2 and all(math.isfinite(p['radians'])
            and not p['singular'] for p in s['debug']['forearmPronation']) for s in samples)
        cursor = 0
        phases = []
        for phase in report['played']['phases']:
            end = cursor + phase['wallSeconds']
            phases.append({'name': phase['name'], 'endTick': phase['state']['tick'],
                'stateHash': phase['hash'], 'faults': phase['faults'],
                'approximatePresentationSeconds': [cursor, end]})
            cursor = end
        summary['played'] = {'ticks': report['played']['ticks'], 'nativeSamples': len(samples),
            'nativeJointsPerSample': 75, 'finalHash': report['played']['finalHash'], 'phases': phases,
            'timelineLimit': 'Wall windows approximate movie time; visible phase label and timer remain authoritative. Each movie is separately paced.'}
        summary['played']['wristErrMaximumMeters'] = max(x for s in samples for x in s['debug']['wristErr'])
        summary['played']['gripAngleErrMaximumRadians'] = max(x for s in samples for x in s['debug']['gripAngleErr'])
        summary['played']['bothHandOnGripSamples'] = sum(all(s['debug']['handOnGrip']) for s in samples)
        times = [0.4, 1.8, 3.8, 5.8, 7.8, 9.8, min(11.8, duration - 0.08)]
    else:
        summary['orbit'] = report['orbit']
        summary['garageEnd'] = {'forearmPronation': report['garageEnd']['debug']['forearmPronation']}
        times = [duration * f for f in [.05, .2, .35, .5, .65, .8, .95]]
    frame_dir = OUT / 'review05' / name
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for seconds in times:
        full_path = frame_dir / ('frame-%07.3f.png' % seconds)
        if not full_path.exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-ss', str(seconds),
                '-i', str(movie_path), '-frames:v', '1', '-threads', '1', str(full_path)], check=True)
        row = {'presentationSeconds': seconds, 'full': str(full_path.relative_to(ROOT)), 'sha256': digest(full_path)}
        if report['mode'] == 'lean':
            # Source pixels only. Fixed screen rectangles do not identify an anatomical side.
            for region, box in [('screen-left', '430:370:330:380'), ('screen-right', '440:370:860:250')]:
                crop_path = frame_dir / ('frame-%07.3f-%s.png' % (seconds, region))
                assert not crop_path.exists(), 'Never overwrite a derived crop'
                subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(full_path),
                    '-vf', 'crop=' + box, '-frames:v', '1', '-threads', '1', str(crop_path)], check=True)
                row[region] = {'path': str(crop_path.relative_to(ROOT)), 'sha256': digest(crop_path), 'cropWHXY': box}
        frames.append(row)
    summary['chronologicalMovieFrames'] = frames
    compressed_path.write_bytes(gzip.compress(report_bytes, mtime=0))
    assert gzip.decompress(compressed_path.read_bytes()) == report_bytes
    summary['exactReport']['compressedSHA256'] = digest(compressed_path)
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'accepted': False, 'summary': str(summary_path), 'frames': len(frames),
        'compressedBytes': compressed_path.stat().st_size}))


if __name__ == '__main__':
    assert len(sys.argv) == 2
    archive(sys.argv[1])
