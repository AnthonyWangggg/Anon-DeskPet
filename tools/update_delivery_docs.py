import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
note = '''# 爱音 Live2D 表情模型

已在 Cubism Editor 5.3.04 FREE 完成网格和表情绑定，以 SDK 5.0 导出真实 MOC3。

- 工程：assets/live2d/authoring/Anon_Expression_Starter.cmo3
- 最新运行模型：assets/live2d/Anon/Anon.model3.json
- 单张 2048×2048 纹理，8 个整身 ArtMesh。
- ParamExpression：0 日常、1 开心、2 生气、3 晕眩、4 喜欢、5 惊讶、6 wink。
- ParamEyeLOpen：日常状态下 0 闭眼、1 睁眼。

默认桌宠加载爱音 Live2D，设置中可切换图片模式或导入其他模型。
重新导出到 assets/live2d/Anon/Anon.moc3 后，运行 tools/prepare_anon_runtime.py 补齐表情描述和 EyeBlink 参数组，再运行 tests/anon_model_smoke.py 验证。
导出选 SDK 5.0，勾选导出隐藏的图形网格。继续编辑请打开 cmo3，不要重新导入 PSD 覆盖绑定。

当前为根据设定图重绘素材制作的整身表情切换模型，没有独立头发物理、眼球跟随、口型或身体呼吸绑定；贴图边缘有少量色键残色。PSD 是初始整身表情素材，不是身体部位拆层。authoring 中的旧运行导出仅用于早期眨眼验证，正式程序使用 Anon 目录。
'''
for relative in ['assets/live2d/README.md', 'assets/live2d/authoring/START-HERE.md']:
    (root / relative).write_text(note, encoding='utf8')
path = root / 'README.md'
lines = path.read_text(encoding='utf8').splitlines()
for i, line in enumerate(lines):
    if line.startswith('- **尚未交付：'):
        lines[i] = '- **已交付：爱音 Cubism cmo3 / moc3 表情模型。** 默认使用真实 Cubism 渲染，支持七种整身表情与自动眨眼。尚无独立眼球跟随、头发物理、口型及身体呼吸绑定；设置中可切换原图片动画模式。'
    if line.startswith('爱音标准模型仍需'):
        lines[i] = '爱音工程位于 `assets/live2d/authoring/Anon_Expression_Starter.cmo3`，最新运行模型位于 `assets/live2d/Anon/Anon.model3.json`。已在 Cubism Editor 5.3.04 FREE 中绑定，以 SDK 5.0 导出。重新导出后运行 `tools/prepare_anon_runtime.py`，再运行 `tests/anon_model_smoke.py` 验证。详细限制与编辑说明见 `assets/live2d/README.md`。'
path.write_text('\n'.join(lines) + '\n', encoding='utf8')
path = root / 'assets/live2d/authoring/starter-manifest.json'
data = json.loads(path.read_text(encoding='utf8'))
data['status'] = 'PSD is initial whole-body artwork; cmo3 now has seven expression bindings and blink'
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf8')
report_path = root / 'output/validation-summary.json'
report = json.loads(report_path.read_text(encoding='utf8'))
report['character_backend'] = 'Cubism MOC3 whole-body expression model; sprite fallback available'
report['anon_moc3_created'] = True
report['anon_model'] = json.loads((root / 'output/anon-model-validation/report.json').read_text(encoding='utf8'))
report['frozen_executable'] = json.loads((root / 'output/package-validation/report.json').read_text(encoding='utf8'))
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
