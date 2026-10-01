"""Push only this private review site's exact main source; credential via stdin."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import termios

site = Path('/Users/raynos/projects/games/rockhop/harness/out/hero-remaster/rider-review-site')
project_id = json.loads((site / '.openai/hosting.json').read_text())['project_id']
if sys.stdin.isatty():
    state = termios.tcgetattr(sys.stdin)
    hidden = list(state)
    hidden[3] &= ~termios.ECHO
    termios.tcsetattr(sys.stdin, termios.TCSANOW, hidden)
else:
    state = None
print('Ready for Site credential JSON on stdin (input is hidden).', flush=True)
try:
    credential = json.loads(sys.stdin.readline())
finally:
    if state is not None:
        termios.tcsetattr(sys.stdin, termios.TCSANOW, state)
assert credential['branch'] == 'main'
assert credential['repository'] == project_id
assert credential['auth_mode'] == 'http_extra_header'
def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=site, env=env, text=True).strip()
if not (site / '.git').exists():
    git('init', '-b', 'main')
    git('config', 'user.name', 'Raynos')
    git('config', 'user.email', 'raynos@users.noreply.github.com')
assert git('branch', '--show-current') == 'main'
git('add', '--', '.openai/hosting.json', 'dist')
if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=site).returncode:
    git('commit', '-m', 'design(rider): publish current multi-angle review gallery',
        '-m', 'Phone access needs hosted video and image files. Preserve current actual renders and label open deformation gates.\n\nValidation: local silent WebKit playback and responsive checks.\n\nAssisted-by: Codex:gpt-6.1-sol')
head = git('rev-parse', 'HEAD')
env = os.environ.copy()
env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.extraHeader',
           GIT_CONFIG_VALUE_0='Authorization: Bearer ' + credential['token'],
           GIT_TERMINAL_PROMPT='0')
# The token stays in process memory. It is never an argument, config, or file.
subprocess.run(['git', 'push', credential['remote_url'], 'HEAD:refs/heads/main'],
               cwd=site, env=env, check=True)
remote_head = git('ls-remote', credential['remote_url'], 'refs/heads/main', env=env).split()[0]
assert remote_head == head
assert not git('status', '--porcelain')
print(json.dumps({'project_id': project_id, 'commit_sha': head, 'remoteVerified': True}), flush=True)
