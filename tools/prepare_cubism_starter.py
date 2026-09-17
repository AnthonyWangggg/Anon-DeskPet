"""Package existing, unmodified PNG pixels into an RGB/8-bit layered PSD.

This is an expression-sheet starter, not an anatomically separated illustration
and not a Cubism model. No image generation or retouching is performed here.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets' / 'character'
OUTPUT = ROOT / 'assets' / 'live2d' / 'authoring'
FRAMES = ['idle', 'blink', 'happy', 'angry', 'dizzy', 'love', 'surprised', 'wink']


def u32(value):
    return struct.pack('>I', value)


def block(data):
    return u32(len(data)) + data


def resource(identifier, data):
    return b'8BIM' + struct.pack('>H', identifier) + b'\0\0' + block(data) + b'\0' * (len(data) % 2)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames = {name: Image.open(SOURCE / f'{name}.png').convert('RGBA') for name in FRAMES}
    width, height = frames['idle'].size
    assert all(image.size == (width, height) for image in frames.values())
    assert len(frames) <= 100 and width * height * len(frames) < 2048 * 2048
    records, pixels, manifest = [], [], []
    # PSD records run from top to bottom. Every alternative has opacity zero,
    # rather than erased alpha, so Cubism can import its complete texture.
    for index, name in reversed(list(enumerate(FRAMES))):
        layer_name = f'{index:02d}_{name}'.encode('ascii')
        pascal = bytes([len(layer_name)]) + layer_name
        pascal += b'\0' * (-len(pascal) % 4)
        unicode_name = u32(len(layer_name)) + layer_name.decode().encode('utf-16-be')
        extra = u32(0) + u32(0) + pascal
        extra += b'8BIMluni' + block(unicode_name)
        extra += b'\0' * (len(unicode_name) % 2)
        extra += b'8BIMlyid' + block(u32(index + 1))
        channels = frames[name].split()
        channel_ids = [0, 1, 2, -1]
        channel_data = list(channels)
        record = struct.pack('>iiiiH', 0, 0, height, width, 4)
        for channel_id in channel_ids:
            record += struct.pack('>hI', channel_id, width * height + 2)
        opacity = 255 if name == 'idle' else 0
        record += b'8BIMnorm' + bytes([opacity, 0, 0, 0]) + block(extra)
        records.append(record)
        pixels.extend(b'\0\0' + channel.tobytes() for channel in channel_data)
        manifest.append({'name': layer_name.decode(), 'expression': name,
                         'opacity': opacity, 'width': width, 'height': height,
                         'kind': 'whole-body-expression-frame'})
    layer_info = struct.pack('>h', -len(FRAMES)) + b''.join(records) + b''.join(pixels)
    layer_info += b'\0' * (len(layer_info) % 2)
    layer_mask_section = block(layer_info) + u32(0)
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    resources = resource(1039, profile)
    header = b'8BPS' + struct.pack('>H6sHIIHH', 1, b'\0' * 6, 4, height, width, 8, 3)
    composite = b'\0\0' + b''.join(channel.tobytes() for channel in frames['idle'].split())
    target = OUTPUT / 'Anon_Expression_Starter.psd'
    target.write_bytes(header + u32(0) + block(resources) + block(layer_mask_section) + composite)

    # Read back with Pillow's independent PSD decoder, including every layer.
    with Image.open(target) as loaded:
        assert loaded.size == (width, height)
        assert loaded.n_frames == len(FRAMES)
        assert loaded.convert('RGBA').tobytes() == frames['idle'].tobytes()
        assert len(loaded.layers) == len(FRAMES)
        names = [layer[0] for layer in loaded.layers]
        assert len(set(names)) == len(FRAMES)
        for layer in loaded.layers:
            expected = frames[layer[0].split('_', 1)[1]]
            # Pillow 12.3 parses layers into an in-memory section: its tile
            # offsets are section-relative. Read those independently parsed
            # channel locations instead of the plugin's incompatible seek().
            with target.open('rb') as stream:
                for tile in layer[3]:
                    assert tile.codec_name == 'raw'
                    stream.seek(loaded._layers_position + tile.offset)
                    actual = stream.read(width * height)
                    assert actual == expected.getchannel(tile.args).tobytes(), layer[0]

    info = {
        'editor': 'Cubism 5.3.04 FREE',
        'target_sdk': 'SDK5.0/Cubism5.0',
        'runtime_core_tested': '5.1.0',
        'psd': target.name,
        'color_mode': 'RGB', 'bits_per_channel': 8, 'color_profile': 'sRGB',
        'canvas': [width, height], 'layers': manifest,
        'status': 'expression starter only; no anatomical separation or Cubism bindings',
        'validation': 'PSD decoded and all 8 layers compared pixel-for-pixel with source PNGs',
        'free_limits': {'artmeshes': 100, 'parameters': 30, 'deformers': 50,
                        'part_folders': 30, 'texture_atlases': 1, 'texture_edge': 2048},
    }
    (OUTPUT / 'starter-manifest.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'Created and verified {target}: {width}x{height}, 8 RGBA layers, RGB/8-bit/sRGB')


if __name__ == '__main__':
    main()
