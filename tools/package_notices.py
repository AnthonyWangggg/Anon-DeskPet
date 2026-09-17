"""Copy dependency license files and local usage instructions into the build."""
from importlib import metadata
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
package = root / 'dist' / 'AnonDeskPet'
if not (package / 'AnonDeskPet.exe').exists():
    raise SystemExit('Build the executable before copying notices.')
licenses = package / 'licenses'
licenses.mkdir(parents=True, exist_ok=True)
for name in ('PySide6', 'shiboken6', 'psutil', 'nvidia-ml-py', 'live2d-py', 'PyOpenGL', 'numpy', 'Pillow'):
    distribution = metadata.distribution(name)
    for file in distribution.files or []:
        if any(term in str(file).lower() for term in ('license', 'copying', 'notice')):
            source = Path(distribution.locate_file(file))
            if source.is_file() and '.dist-info' in str(file):
                destination = licenses / name / Path(str(file).split('.dist-info/', 1)[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
shutil.copy2(root / 'README.md', package / 'README.md')
(package / 'START-HERE.txt').write_text(
    '千早爱音桌宠\n\n双击 AnonDeskPet.exe 启动。请保留同目录的 _internal 文件夹。\n'
    '左键互动，拖动移动，右键设置，Ctrl + 滚轮缩放。\n'
    '默认使用爱音 Cubism 模型：七种整身表情与自动眨眼。\n'
    '当前没有独立头发物理、眼球跟随及口型；设置中可切换图片模式。\n'
    '设置中可导入已有的标准 Live2D 模型。\n', encoding='utf-8')
print('Copied usage instructions and available dependency licenses.')
