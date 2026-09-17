"""Smoke-test the frozen executable with isolated settings and a time limit."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
exe = ROOT / 'dist/AnonDeskPet/AnonDeskPet.exe'
output = ROOT / 'output/package-validation'
output.mkdir(parents=True, exist_ok=True)


def run(arguments):
    process = subprocess.run([str(exe), *map(str, arguments)], cwd=ROOT, timeout=25,
                             capture_output=True)
    if process.returncode:
        raise RuntimeError(f'Executable failed ({process.returncode}): {process.stderr!r}')


run(['--preview', output / 'preview.png'])
assert (output / 'preview.png').stat().st_size > 10000
report = {'frozen_preview': 'passed'}
for mode in ('sprite', 'cubism', 'anon'):
    folder = output / mode
    folder.mkdir(exist_ok=True)
    config = folder / 'settings.json'
    data = {'show_metrics': False}
    if mode == 'sprite':
        data['live2d_model'] = 'sprite'
    if mode == 'cubism':
        data['live2d_model'] = str(ROOT / 'output/validation-model/Haru/Haru.model3.json')
    config.write_text(json.dumps(data), encoding='utf8')
    log = folder / 'deskpet.log'
    if log.exists():
        log.write_text('', encoding='utf8')
    run(['--smoke-test', '--settings', config])
    contents = log.read_text(encoding='utf8')
    assert 'ERROR' not in contents and 'WARNING' not in contents, contents
    assert 'sprite atlas ready' in contents, contents
    if mode in ('cubism', 'anon'):
        assert 'Cubism loaded:' in contents, contents
    report[f'frozen_{mode}_startup'] = 'passed'
(output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report, indent=2))
