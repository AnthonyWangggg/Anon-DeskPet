import json
import tempfile
import unittest
from pathlib import Path

from deskpet.animation import Animator
from deskpet.cubism import validate_model
from deskpet.metrics import rate
from deskpet.settings import Settings


class AnimationTests(unittest.TestCase):
    def test_expression_returns_to_idle(self):
        animation = Animator(seed=1)
        animation.trigger('happy', .3)
        self.assertEqual(animation.pose().frame, 'happy')
        for _ in range(10):
            animation.advance(.05)
        self.assertEqual(animation.expression, 'idle')

    def test_blink_is_brief_and_repeats(self):
        animation = Animator(seed=0)
        frames = [animation.advance(.02).frame for _ in range(600)]
        self.assertGreater(frames.count('blink'), 0)
        self.assertLess(frames.count('blink'), 40)

    def test_animation_is_bounded_and_pauses(self):
        animation = Animator(seed=0)
        animation.set_pointer(1000, -1000)
        poses = [animation.advance(.1) for _ in range(6000)]
        self.assertLessEqual(max(abs(p.bounce) for p in poses), 1.6)
        self.assertLessEqual(animation.pointer_x, 1)
        self.assertGreaterEqual(animation.pointer_y, -1)
        animation.paused = True
        before = animation.pose()
        self.assertEqual(before, animation.advance(.1))


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'settings.json'

    def test_legacy_migration_and_roundtrip(self):
        old = {'scale': 70, 'pos': [100, 200], 'apps': [{'path': 'C:/app.exe', 'name': '应用'}]}
        self.path.with_name('deskpet.json').write_text(json.dumps(old), encoding='utf8')
        settings = Settings(self.path)
        self.assertEqual(settings.config.position, [100, 200])
        self.assertEqual(settings.config.scale_percent, 70)
        settings.save()
        self.assertEqual(Settings(self.path).config, settings.config)
        self.assertTrue(self.path.with_name('deskpet.json').exists())

    def test_broken_json_and_wrong_shape(self):
        for raw in ('{', 'null', '[]', '{"apps": null}', '{"position": ["bad", 3]}'):
            self.path.write_text(raw)
            self.assertEqual(Settings(self.path).config.version, 2)

    def test_clamps_size_and_deduplicates_apps(self):
        self.path.write_text('{"scale_percent": 9000}')
        settings = Settings(self.path)
        self.assertEqual(settings.config.scale_percent, 150)
        settings.add_app(str(Path(self.temp.name) / 'test.exe'))
        settings.add_app(str(Path(self.temp.name) / 'test.exe'))
        self.assertEqual(len(settings.config.apps), 1)
        settings.remove_app(-1)
        self.assertEqual(len(settings.config.apps), 1)
        settings.remove_app(0)
        self.assertEqual(len(Settings(self.path).config.apps), 0)


class CubismTests(unittest.TestCase):
    def test_rejects_missing_moc_and_fake_moc(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'Anon.model3.json'
            path.write_text(json.dumps({'Version': 3, 'FileReferences': {'Moc': 'Anon.moc3', 'Textures': ['texture.png']}}))
            with self.assertRaisesRegex(ValueError, '缺失'):
                validate_model(path)
            (root / 'Anon.moc3').write_bytes(b'NOT A MODEL')
            (root / 'texture.png').write_bytes(b'placeholder')
            with self.assertRaisesRegex(ValueError, '文件头'):
                validate_model(path)

    def test_rejects_sprite_manifest(self):
        with self.assertRaises(ValueError):
            validate_model('assets/character/anon.sprite.json')

    def test_rate(self):
        self.assertEqual(rate(-10), '0.0 B/s')
        self.assertEqual(rate(2048), '2.0 KB/s')


if __name__ == '__main__':
    unittest.main()
