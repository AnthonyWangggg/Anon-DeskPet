"""Native Qt smoke test. Closes its own windows; never changes user settings."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog
from deskpet.app import Pet
from deskpet.settings import Settings


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    directory = ROOT / 'output' / 'gui-validation'
    directory.mkdir(parents=True, exist_ok=True)
    settings = Settings(directory / 'settings.json')
    settings.config.live2d_model = 'sprite'
    settings.config.show_metrics = False
    settings.config.scale_percent = 80
    pet = Pet(settings, enable_tray=False)
    try:
        pet.show()
        QTest.qWait(400)
        anchor = pet.pos()
        QTest.mouseClick(pet, Qt.LeftButton, pos=QPoint(pet.width()//2, pet.height()//2))
        assert pet.animator.expression == 'happy'
        QTest.qWait(1200)
        assert pet.pos() == anchor, 'Animation moved the desktop window'
        assert pet.grab().save(str(directory / 'desktop-pet.png'))
        pet.toggle_metrics(True)
        assert pet.info and 'CPU' in pet.info.text()
        pet.toggle_metrics(False)
        pet.toggle_pause(True)
        phase = pet.animator.time
        QTest.qWait(100)
        assert pet.animator.time == phase
        pet.toggle_pause(False)
        def capture_settings():
            for widget in app.topLevelWidgets():
                if isinstance(widget, QDialog) and widget.isVisible():
                    widget.grab().save(str(directory / 'settings.png'))
                    widget.accept()
        QTimer.singleShot(300, capture_settings)
        pet.show_settings()
        report = {'sprite_window': 'passed', 'click': 'passed', 'no_window_drift': 'passed',
                  'metrics': 'passed', 'pause': 'passed', 'settings_dialog': 'passed'}
        if '--cubism' in sys.argv:
            model_path = ROOT / 'output/validation-model/Haru/Haru.model3.json'
            assert pet.load_cubism(str(model_path))
            QTest.qWait(2000)
            assert pet.cubism is not None and pet.cubism.model is not None, 'Cubism failed to load'
            assert pet.cubism.isValid(), 'No valid OpenGL context'
            assert len(pet.cubism.expression_ids) > 0
            pet.trigger_model_expression(pet.cubism.expression_ids[0])
            QTest.qWait(500)
            image = pet.cubism.grabFramebuffer()
            assert not image.isNull()
            image.save(str(directory / 'cubism-official-sample.png'))
            # Runtime capture must contain BOTH transparent background and model pixels.
            alphas = [image.pixelColor(x, y).alpha() for y in range(0, image.height(), 5)
                      for x in range(0, image.width(), 5)]
            assert max(alphas) > 200 and min(alphas) == 0
            report['cubism_official_haru_model'] = 'passed'
            report['cubism_opengl_alpha'] = 'passed'
            pet.unload_cubism()
            QTest.qWait(100)
            assert pet.cubism is None
            report['cubism_to_sprite_fallback'] = 'passed'
        print(json.dumps(report, indent=2))
        (directory / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    finally:
        settings.config.live2d_model = ''
        pet.shutdown()
        pet.close()


if __name__ == '__main__':
    main()
