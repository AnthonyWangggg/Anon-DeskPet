"""Download the official Haru sample ONLY to output/ for runtime validation."""
import concurrent.futures
import json
import urllib.request
from pathlib import Path

BASE = 'https://raw.githubusercontent.com/Live2D/CubismWebSamples/develop/Samples/Resources/Haru/'
ROOT = Path(__file__).resolve().parent.parent / 'output' / 'validation-model' / 'Haru'


def fetch(name):
    target = ROOT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(BASE + name, timeout=40) as response:
            target.write_bytes(response.read())
    return target


if __name__ == '__main__':
    model = json.loads(fetch('Haru.model3.json').read_text())
    refs = model['FileReferences']
    names = [refs['Moc'], *refs['Textures']]
    names += [refs[k] for k in ('Physics', 'Pose', 'UserData', 'DisplayInfo') if k in refs]
    names += [e['File'] for e in refs['Expressions']]
    for group in refs['Motions'].values():
        for motion in group:
            names.append(motion['File'])
            if motion.get('Sound'):
                names.append(motion['Sound'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for target in pool.map(fetch, names):
            print(target.relative_to(ROOT))
    print('Official sample downloaded for validation only; not the Anon character.')
