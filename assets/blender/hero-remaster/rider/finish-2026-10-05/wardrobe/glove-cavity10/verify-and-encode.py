"""Frozen render readback, one authorized silent encode, full decode receipt."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


base = Path('docs/evidence/hero-remaster/finish-2026-10-05/wardrobe/glove-cavity10')
render_path = Path('assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/glove-cavity10-render/render.json')
render = json.loads(render_path.read_text())
guard_path = base / 'render-guard/guard.json'
guard = json.loads(guard_path.read_text())
assert guard['exitCode'] == 0 and guard['elapsedSeconds'] < guard['limitSeconds'] == 300
assert render['recipeSHA256'] == 'e6c09d7f334739e54b1ad93277811c448542036ea85475c2d177c64840b0c148'
assert sha('assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/glove-cavity10/render-source-context.py') == render['recipeSHA256']
assert render['source']['sha256'] == sha(render['source']['path']) == '8379004e394bbae110f495c13bfc12a205977061d13cefdcc8ee24c6e5343782'
assert all(sha(pin['path']) == pin['sha256'] for pin in render['maps'].values())
assert render['sourceTrianglesPresent'] == 14543 and render['sourceHiddenTriangles'] == 0
assert render['sourceGeometryBeforeAfterExact'] and render['sourceUVFloat32DisplayReadbackExact']
assert len(render['frames']) == len(render['cameraPaths']) == 60 and render['fps'] == 12
translation_error, aim_error, rotation_error, ortho_error = [], [], [], []
frame_hashes = []
for index, frame in enumerate(render['frames']):
    pose = render['cameraPaths'][index]
    assert frame['index'] == index and frame['assignedSourcePose'] == pose
    matrix = np.array(frame['actualCameraWorld'])
    source_location, source_target = np.array(pose['sourceLocation']), np.array(pose['sourceTarget'])
    location, target = source_location[[0, 2, 1]].copy(), source_target[[0, 2, 1]].copy()
    location[1] *= -1
    target[1] *= -1
    actual_translation_error = float(np.linalg.norm(matrix[:3, 3] - location))
    direction = target - matrix[:3, 3]
    direction /= np.linalg.norm(direction)
    actual_aim_error = float(np.linalg.norm(-matrix[:3, 2] - direction))
    actual_rotation_error = float(abs(np.einsum('ij,ik->jk', matrix[:3, :3], matrix[:3, :3], optimize=False) - np.eye(3)).max())
    actual_ortho_error = abs(frame['actualOrthoScale'] - pose['orthoScale'])
    assert actual_translation_error < 1e-6 and actual_aim_error < 1e-6 and actual_rotation_error < 1e-6 and actual_ortho_error < 1e-6
    translation_error.append(actual_translation_error)
    aim_error.append(actual_aim_error)
    rotation_error.append(actual_rotation_error)
    ortho_error.append(actual_ortho_error)
    for panel in ['plain', 'marked']:
        pin = frame['panels'][panel]
        assert sha(pin['path']) == pin['sha256']
        assert pin['actualCameraWorld'] == frame['actualCameraWorld']
        frame_hashes.append(pin['sha256'])
assert len(frame_hashes) == 120
readback = {'acceptedWearable': False, 'status': 'NATIVE_PAIRED_RENDER_READBACK_PASS_BEFORE_ONE_ENCODE', 'validatorSHA256': sha(__file__), 'renderSHA256': sha(render_path), 'guardSHA256': sha(guard_path), 'workerExitCode': guard['exitCode'], 'renderElapsedSeconds': guard['elapsedSeconds'], 'sourceSHA256After': sha(render['source']['path']), 'cameraTranslationMaxResidualSourceUnits': max(translation_error), 'cameraAimMaxResidual': max(aim_error), 'cameraRotationOrthogonalityMaxResidual': max(rotation_error), 'cameraOrthoMaxResidualSourceUnits': max(ortho_error), 'matchedPlainMarkedActualCameraPoses': 60, 'frameHashesVerified': 120, 'sourceTrianglesPresent': 14543, 'sourceHiddenTriangles': 0, 'nativeSourceGeometryBeforeAfterExact': True, 'nativeUVFloat32DisplayExact': True, 'nativeUVFloat64ToFloat32MaxResidual': render['uvFloat64ToFloat32MaximumResidual'], 'limits': ['Source-context native camera/material/readback only; no cavity/free-volume/source interpretation or wearable acceptance.', 'Parent played review remains pending. No source native-rider/fit/skin/cut operation.']}
(base / 'render-readback.json').write_text(json.dumps(readback, indent=2) + '\n')
shutil.copyfile(render_path, base / 'render.json')
movie = base / 'paired-pbr-source-context.mp4'
assert not movie.exists()
command = ['ffmpeg', '-n', '-loglevel', 'error', '-threads', '2', '-framerate', '12', '-i', str(render_path.parent / 'plain/%03d.png'), '-threads', '2', '-framerate', '12', '-i', str(render_path.parent / 'marked/%03d.png'), '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]', '-map', '[v]', '-c:v', 'libx264', '-threads', '2', '-filter_complex_threads', '2', '-crf', '20', '-pix_fmt', 'yuv420p', '-an', str(movie)]
start = time.monotonic()
encode = subprocess.run(command, capture_output=True, text=True, timeout=60)
encode_receipt = {'acceptedWearable': False, 'status': 'ONE_AUDIOFREE_ENCODE_RETURNED', 'recipeSHA256': sha(__file__), 'command': command, 'exitCode': encode.returncode, 'elapsedSeconds': time.monotonic() - start, 'stdout': encode.stdout, 'stderr': encode.stderr}
(base / 'encode.json').write_text(json.dumps(encode_receipt, indent=2) + '\n')
assert encode.returncode == 0
probe_command = ['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(movie)]
probe = subprocess.run(probe_command, capture_output=True, text=True, timeout=30)
assert probe.returncode == 0
metadata = json.loads(probe.stdout)
streams = metadata['streams']
assert len(streams) == 1 and streams[0]['codec_type'] == 'video' and streams[0]['width'] == 1536 and streams[0]['height'] == 768
assert streams[0]['nb_read_frames'] == '60' and streams[0]['avg_frame_rate'] == '12/1'
assert float(metadata['format']['duration']) == 5
decode_command = ['ffmpeg', '-v', 'error', '-threads', '2', '-i', str(movie), '-map', '0:v:0', '-an', '-f', 'null', '-']
decode = subprocess.run(decode_command, capture_output=True, text=True, timeout=30)
decoder = {'acceptedWearable': False, 'status': 'PAIRED_SOURCE_CONTEXT_MOVIE_FULL_DECODE_PASS_PLAYBACK_PENDING', 'movie': {'path': str(movie), 'sha256': sha(movie), 'bytes': movie.stat().st_size}, 'probeCommand': probe_command, 'probeExitCode': probe.returncode, 'probe': metadata, 'decodeCommand': decode_command, 'decodeExitCode': decode.returncode, 'decodeStderr': decode.stderr, 'audioStreams': 0, 'videoStreams': 1, 'frames': 60, 'fps': 12, 'durationSeconds': 5, 'limits': 'Decoded file integrity only; parent actual silent headless playback and temporal source-context interpretation pending checkpoint41. No cavity/source edit/fit acceptance.'}
(base / 'movie.json').write_text(json.dumps(decoder, indent=2) + '\n')
assert decode.returncode == 0 and not decode.stderr
assert sha(render['source']['path']) == render['source']['sha256']
print(json.dumps({'readback': readback['status'], 'movie': decoder['movie'], 'encodeExit': encode.returncode, 'decodeExit': decode.returncode, 'audioStreams': 0}))
