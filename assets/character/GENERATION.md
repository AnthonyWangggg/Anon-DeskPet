# 角色资源生成记录

模式：内置 image_gen 工具。原图仅用作角色与画风参考。

第一版工具输出将棋盘格烘焙进 RGB 图片，因此未直接作为透明资源交付。第二次编辑生成纯绿色背景，然后 tools/extract-atlas.cjs 转换色键与边缘 alpha，输出 RGBA 图集和八张独立 PNG。没有使用 CLI/API key 生成路径。

## 初次生成提示词

Use case: stylized-concept / background-extraction.
Asset type: production transparent PNG sprite atlas for the provided Chihaya Anon desktop pet.
Input image is the sole character identity and art-style reference. Extract/reconstruct the FRONT VIEW chibi character (front turnaround near bottom) faithfully: pastel pink very long straight hair with pointed faceted locks, side swept bangs, grey-blue eyes, light grey school blazer with white edge trim and gold buttons, dark green striped tie, dark green plaid pleated skirt, dark knee socks, brown loafers. Preserve the pastel flat low-poly angular shading, chibi proportions, and original school outfit.
Create ONE precisely aligned 4 columns by 2 rows sprite sheet on REAL transparent alpha background, ideally 2048 x 1536. Each of the 8 equal cells contains exactly one full-body front-facing character at identical size and identical position, standing upright, arms at sides, feet both fully visible. Character occupies 80% of cell height and 76% width; clear transparent gutters between cells. No pose changes or body/hair silhouette changes between cells, only facial expression changes.
Reading order left to right top to bottom:
1 neutral half-lidded eyes, small neutral mouth (idle);
2 both eyes completely closed, small neutral mouth (blink);
3 closed happy arc eyes and open smiling mouth (happy);
4 inward angled angry eyebrows, half-lidded eyes, tiny pout (angry);
5 spiral eyes, tiny unsettled mouth (dizzy);
6 blushing closed happy eyes, sweet small smile (love);
7 round wide open grey-blue eyes and small O mouth (surprised);
8 one eye closed in wink, other half open, small smile (wink).
Do not add floating symbols, words, labels, frames, checkerboard, shadows, props, backgrounds, grids or lettering. Each character completely isolated on alpha. This is a real usable game sprite atlas, not a presentation sheet. Same visual identity and geometry in all eight cells.

## 背景修正提示词

Edit the supplied sprite atlas with one precise change: remove EVERY grey/white checkerboard background pixel and replace the entire background including all gaps between hair strands, arms and legs with perfectly uniform solid RGB(0,255,0), hex #00FF00. No checkerboard, no gradients, no shadow, no green light on character. Preserve all 8 characters, their faces, clothes, colors, outlines, positions, dimensions, and 4-column 2-row grid EXACTLY. Do not redraw, resize or move any character. Preserve grey blazer and green skirt. This is a chroma-key asset, so background must be exactly pure bright green everywhere outside the character silhouettes.

