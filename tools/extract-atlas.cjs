// Convert the image-generator chroma-key output into real alpha and PNG frames.
// Usage: node tools/extract-atlas.cjs [sharp-module-directory]
const fs = require('node:fs');
const path = require('node:path');
const sharp = require(process.argv[2] || 'sharp');
const root = path.resolve(__dirname, '..');

async function main() {
  const source = path.join(root, 'assets/reference/anon-chroma.png');
  const target = path.join(root, 'assets/character');
  const {data, info} = await sharp(source).removeAlpha().raw().toBuffer({resolveWithObject:true});
  const rgba = Buffer.alloc(info.width * info.height * 4);
  for (let p = 0; p < info.width * info.height; p++) {
    const [r,g,b] = data.subarray(p*3,p*3+3);
    const excess = g - Math.max(r,b);
    // Green plaid is dark/desaturated and remains opaque. Only vivid key-green
    // and mixed edge pixels lose opacity; remove green spill at those edges.
    const alpha = Math.max(0, Math.min(1, 1 - (excess - 20) / 190));
    let red = r, green = g, blue = b;
    if (alpha < 1 && alpha > .02) {
      red = Math.min(255, r / alpha);
      green = Math.max(0, Math.min(255, (g - (1-alpha)*250) / alpha));
      blue = Math.min(255, b / alpha);
    }
    rgba[p*4] = alpha <= .02 ? 0 : Math.round(red);
    rgba[p*4+1] = alpha <= .02 ? 0 : Math.round(green);
    rgba[p*4+2] = alpha <= .02 ? 0 : Math.round(blue);
    rgba[p*4+3] = alpha <= .02 ? 0 : Math.round(alpha*255);
  }
  fs.mkdirSync(target,{recursive:true});
  const raw = {width:info.width,height:info.height,channels:4};
  const atlas = await sharp(rgba,{raw}).png().toBuffer();
  fs.writeFileSync(path.join(target,'anon-atlas.png'),atlas);
  const manifest = JSON.parse(fs.readFileSync(path.join(target,'anon.sprite.json'),'utf8'));
  const width = Math.floor(info.width/4), height = Math.floor(info.height/2);
  for (const [name,index] of Object.entries(manifest.frames)) {
    await sharp(atlas).extract({left:(index%4)*width,top:Math.floor(index/4)*height,width,height})
      .png().toFile(path.join(target,`${name}.png`));
  }
  await sharp(path.join(target,'idle.png')).extract({left:Math.round(width*.14),top:Math.round(height*.04),width:Math.round(width*.72),height:Math.round(height*.47)})
    .resize(256,256,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}})
    .png().toFile(path.join(target,'icon.png'));
  console.log(`Exported RGBA atlas ${info.width}x${info.height}, 8 frames ${width}x${height}, and icon.png`);
}
main().catch(error=>{console.error(error);process.exitCode=1});
