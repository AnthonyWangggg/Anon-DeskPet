"""Validate the actual Editor-exported Anon model and its eye parameter."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from deskpet.cubism import create_cubism_widget, validate_model
from deskpet.animation import Pose

app = QApplication([])
out = ROOT / 'output/anon-model-validation'
out.mkdir(parents=True, exist_ok=True)
path = ROOT / 'assets/live2d/Anon/Anon.model3.json'
validate_model(path)
host = QWidget()
host.resize(362, 543)
widget = create_cubism_widget(str(path), host)
widget.resize(362, 543)
host.show()
QTest.qWait(1500)
try:
    assert widget.model is not None and widget.isValid(), 'Model/OpenGL load failed'
    widget.paused = True
    widget.model.SetAutoBlinkEnable(False)
    widget.model.SetAutoBreathEnable(False)
    captures = []
    for value, name in [(1.0, 'open'), (0.0, 'closed')]:
        widget.model.SetParameterValue('ParamEyeLOpen', value)
        widget.update()
        QTest.qWait(100)
        picture = widget.grabFramebuffer()
        assert not picture.isNull()
        picture.save(str(out / f'{name}.png'))
        captures.append(bytes(picture.constBits()))
        alphas = [picture.pixelColor(x, y).alpha() for y in range(0, picture.height(), 5)
                  for x in range(0, picture.width(), 5)]
        assert min(alphas) == 0 and max(alphas) > 200, 'Missing transparent model rendering'
    assert captures[0] != captures[1], 'Eye parameter has no rendered effect'
    expressions = ['idle', 'happy', 'angry', 'dizzy', 'love', 'surprised', 'wink']
    rendered = []
    widget.model.SetParameterValue('ParamEyeLOpen', 1)
    for value, name in enumerate(expressions):
        widget.model.SetParameterValue('ParamExpression', value)
        widget.update()
        QTest.qWait(100)
        picture = widget.grabFramebuffer()
        picture.save(str(out / f'{name}.png'))
        alphas = [picture.pixelColor(x, y).alpha() for y in range(0, picture.height(), 5)
                  for x in range(0, picture.width(), 5)]
        assert min(alphas) == 0 and max(alphas) > 200, f'{name} invisible'
        rendered.append(bytes(picture.constBits()))
    assert len(set(rendered)) == 7, 'Expression bindings must produce seven different images'
    widget.paused = False
    for name in [*expressions, 'idle']:
        widget.trigger_expression(name)
        QTest.qWait(200)
        picture = widget.grabFramebuffer()
        assert bytes(picture.constBits()) == rendered[expressions.index(name)], f'{name} expression playback differs'
    widget.model.SetAutoBlinkEnable(True)
    blink_seen = False
    for _ in range(100):
        QTest.qWait(100)
        picture = widget.grabFramebuffer()
        if bytes(picture.constBits()) != rendered[0]:
            blink_seen = True
            break
    assert blink_seen, 'Automatic blink did not change rendering'
    widget.model.SetAutoBlinkEnable(False)
    motion_images = []
    for index, (tilt, bounce, pointer) in enumerate([(-7, -12, -1), (7, 2, 1), (0, 0, 0)]):
        widget.set_pose(Pose('idle', 0, pointer, 0, bounce, tilt))
        QTest.qWait(150)
        picture = widget.grabFramebuffer()
        picture.save(str(out / f'motion-{index}.png'))
        motion_images.append(bytes(picture.constBits()))
        # Every edge should remain transparent even at the largest motion.
        w, h = picture.width(), picture.height()
        edges = [(x, y) for x in range(w) for y in (0, h - 1)]
        edges += [(x, y) for y in range(h) for x in (0, w - 1)]
        assert all(picture.pixelColor(x, y).alpha() == 0 for x, y in edges), 'Motion clipped at viewport edge'
    assert len(set(motion_images)) == 3, 'Whole-body motion not rendered'
    QTest.qWait(200)
    picture = widget.grabFramebuffer()
    assert bytes(picture.constBits()) == motion_images[-1], 'Transforms accumulate across frames'
    widget.paused = True
    widget.set_pose(Pose('idle', 1, 1, 0, -12, 7))
    QTest.qWait(200)
    picture = widget.grabFramebuffer()
    assert bytes(picture.constBits()) == motion_images[-1], 'Pause changed rendered pose'
    report = {'model': str(path), 'moc3_load': 'passed', 'transparent_render': 'passed',
              'eye_parameter_changes_render': 'passed',
              'expressions': expressions,
              'expression_playback_and_reset': 'passed', 'automatic_blink': 'passed',
              'motion_bounds_and_pause': 'passed',
              'scope': 'Whole-body expression prototype; seven expressions and blink.'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))
finally:
    widget.cleanup()
    host.close()
