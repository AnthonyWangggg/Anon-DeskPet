"""Add expression descriptors to the genuine Cubism Editor export."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
folder = ROOT / 'assets/live2d/Anon'
path = folder / 'Anon.model3.json'
data = json.loads(path.read_text(encoding='utf-8-sig'))
assert (folder / data['FileReferences']['Moc']).read_bytes()[:4] == b'MOC3'
expressions = []
for value, name in enumerate(['idle', 'happy', 'angry', 'dizzy', 'love', 'surprised', 'wink']):
    relative = f'expressions/{name}.exp3.json'
    target = folder / relative
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'Type': 'Live2D Expression', 'FadeInTime': 0,
        'FadeOutTime': 0, 'Parameters': [
            {'Id': 'ParamExpression', 'Value': value, 'Blend': 'Overwrite'}
        ]}, indent=2), encoding='utf8')
    expressions.append({'Name': name, 'File': relative})
data['FileReferences']['Expressions'] = expressions
data['Groups'] = [{'Target': 'Parameter', 'Name': 'EyeBlink', 'Ids': ['ParamEyeLOpen']}]
data['DeskPet'] = {'WholeBodyMotion': True, 'DiscreteExpressions': {e['Name']: i for i, e in enumerate(expressions)},
                   'ExpressionParameter': 'ParamExpression'}
path.write_text(json.dumps(data, indent=2), encoding='utf8')
print(path)
