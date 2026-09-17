# 爱音 Live2D 表情模型

已在 Cubism Editor 5.3.04 FREE 完成网格和表情绑定，以 SDK 5.0 导出真实 MOC3。

- 工程：assets/live2d/authoring/Anon_Expression_Starter.cmo3
- 最新运行模型：assets/live2d/Anon/Anon.model3.json
- 单张 2048×2048 纹理，8 个整身 ArtMesh。
- ParamExpression：0 日常、1 开心、2 生气、3 晕眩、4 喜欢、5 惊讶、6 wink。
- ParamEyeLOpen：日常状态下 0 闭眼、1 睁眼。

默认桌宠加载爱音 Live2D，设置中可切换图片模式或导入其他模型。
Live2D 模式现支持整体待机起伏、鼠标跟随摆动、开心/惊讶弹跳、生气轻抖和晕眩摇摆；动作预留边距，暂停后保持姿态。以上是运行时整体变换，不是头发或身体部位的独立绑定。
重新导出到 assets/live2d/Anon/Anon.moc3 后，运行 tools/prepare_anon_runtime.py 补齐表情描述和 EyeBlink 参数组，再运行 tests/anon_model_smoke.py 验证。
导出选 SDK 5.0，勾选导出隐藏的图形网格。继续编辑请打开 cmo3，不要重新导入 PSD 覆盖绑定。

当前为根据设定图重绘素材制作的整身表情切换模型，没有独立头发物理、眼球跟随、口型或身体呼吸绑定；贴图边缘有少量色键残色。PSD 是初始整身表情素材，不是身体部位拆层。authoring 中的旧运行导出仅用于早期眨眼验证，正式程序使用 Anon 目录。
