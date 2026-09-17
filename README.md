# 千早爱音 · DeskPet

根据用户提供的 `anon_temp.png` 制作的 Windows 桌宠。保留粉色长发、灰色校服、绿色格裙和设定图中的表情。

## 当前交付状态

- **可以使用：** 内置爱音的透明 PNG 图集、七种表情和自动眨眼帧，呼吸、摆动、鼠标跟随、点击互动、拖动、对话气泡、托盘、应用快捷入口、系统监测、设置保存。
- **可以导入：** 标准 Cubism `*.model3.json` + `.moc3` + 纹理及相关文件。使用 `live2d-py` 和 OpenGL 实际渲染，已用官方 Haru 模型验证。
- **已交付：爱音 Cubism cmo3 / moc3 表情模型。** 默认使用真实 Cubism 渲染，支持七种整身表情与自动眨眼。尚无独立眼球跟随、头发物理、口型及身体呼吸绑定；设置中可切换原图片动画模式。

## 启动

本机直接双击 `Start-DeskPet.bat`。优先使用 `dist/AnonDeskPet/AnonDeskPet.exe`，无需另装 Python。

分发时请复制整个 `dist/AnonDeskPet` 文件夹，保留 `_internal`；不要只复制 exe。

从源码运行：安装 Python 3.11+，双击 `setup.bat`，再双击 `Start-DeskPet.bat`。也可以运行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## 操作

| 操作 | 结果 |
| --- | --- |
| 左键点击 | 开心 → 眨眼 → 喜欢 → 生气，随后恢复日常 |
| 左键拖动 | 移动桌宠，显示惊讶 / 晕乎乎反馈，并保存位置 |
| 右键 | 表情、应用、系统信息、暂停、设置、退出 |
| Ctrl + 滚轮 | 调整大小（30%～150%） |
| 单击托盘图标 | 显示桌宠并取消鼠标穿透 |
| 托盘右键 → 回到屏幕右下角 | 找回移到屏幕外的角色 |

大小、应用列表、置顶、气泡、鼠标跟随、帧率、位置存储在 `%APPDATA%/DeskPet/settings.json`。旧版 `deskpet.json` 在尚无新版配置时自动读取；旧文件保留。诊断日志在同目录的 `deskpet.log`。

GPU 信息需要 NVIDIA 驱动 / NVML；其他显卡显示“不可用”。桌宠不上传系统监测数据。气泡是预设台词，没有联网聊天或语音功能。

## 角色资源

| 位置 | 内容 |
| --- | --- |
| `assets/reference/anon-reference.png` | 用户提供的原始设定图 |
| `assets/reference/anon-chroma.png` | 图像生成工具输出的纯色背景中间资源 |
| `assets/character/anon-atlas.png` | 1448×1086 RGBA 图集，4 列 × 2 行 |
| `assets/character/idle.png` 等 | 8 张 362×543 的独立透明表情帧 |
| `assets/character/anon.sprite.json` | 本项目图集描述文件，**不是 model3.json** |
| `assets/character/GENERATION.md` | 生成方式与完整提示词 |
| `output/anon-preview.png` | 程序实际渲染的表情总览 |

资源由内置图像生成工具参考设定图重绘，再通过色键转换得到真正的 alpha。它们不是对原图的无损逐像素裁切，也不是已拆层的 PSD。`tools/extract-atlas.cjs` 可使用 Node.js 和 `sharp` 重建 RGBA 图集与独立 PNG。

## 标准 Live2D

在设置中选择“导入 Live2D 模型…”，选择导出的 `角色名.model3.json`。程序检查 MOC3 文件头及所有引用资源是否齐全；加载失败则保留或恢复内置图集。模型自带表情会出现在“模型表情”菜单中。

爱音工程位于 `assets/live2d/authoring/Anon_Expression_Starter.cmo3`，最新运行模型位于 `assets/live2d/Anon/Anon.model3.json`。已在 Cubism Editor 5.3.04 FREE 中绑定，以 SDK 5.0 导出。重新导出后运行 `tools/prepare_anon_runtime.py`，再运行 `tests/anon_model_smoke.py` 验证。详细限制与编辑说明见 `assets/live2d/README.md`。

运行库说明：[live2d-py 源码](https://github.com/EasyLive2D/relive2d)。模型文件说明：[Live2D 官方导出文档](https://docs.live2d.com/zh-CHS/cubism-editor-manual/export-moc3-motion3-files/)。官方 Haru 示例仅在 `output/validation-model` 用于验证，不作为爱音资源，也不打入运行包。

## 开发与验证

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py --preview output\anon-preview.png
.\.venv\Scripts\python.exe main.py --smoke-test --settings output\test-settings\settings.json
# 原生窗口测试（使用独立配置并自动关闭）
.\.venv\Scripts\python.exe tests\gui_smoke.py
# 下载官方模型后测试真正的 Cubism 路径
.\.venv\Scripts\python.exe tools\fetch_validation_model.py
.\.venv\Scripts\python.exe tests\gui_smoke.py --cubism
```

`deskpet/animation.py` 管理表情、眨眼及时间；`rendering.py` 绘制内置图集；`cubism.py` 负责标准 Live2D；`settings.py` 负责配置验证和原子保存；`metrics.py` 负责系统监测；`app.py` 负责窗口和交互。

双击 `build.bat` 生成独立运行包，或使用 `python -m PyInstaller --noconfirm AnonDeskPet.spec`。可选运行库及图集都通过 spec 收集；模型验证资源不会被打包。
