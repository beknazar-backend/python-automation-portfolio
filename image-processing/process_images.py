#!/usr/bin/env python3
"""Пакетная обработка изображений для e-commerce:

- Изменяет размер до квадрата (по умолчанию 1000x1000)
- Обрезает по центру
- Переименовывает по шаблону (product_001.jpg)
- Сохраняет оптимизированные JPEG/PNG

Использование: python process_images.py -i input_dir -o output_dir
"""
import argparse
from pathlib import Path
from PIL import Image, ImageOps
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Пакетная обработка изображений для e-commerce")
    p.add_argument("-i", "--input", default="input", help="Папка с входными изображениями (по умолчанию ./input)")
    p.add_argument("-o", "--output", default="output", help="Папка для сохранения результатов (по умолчанию ./output)")
    p.add_argument("-s", "--size", type=int, default=1000, help="Целевая размерность (квадрат), по умолчанию 1000")
    p.add_argument("--mode", choices=("crop","fit"), default="crop", help="crop: заполнить и обрезать по центру, fit: вписать и добавить поля")
    p.add_argument("--template", default="product_{:03d}", help="Шаблон имени файла; используйте один целочисленный заполнител, по умолчанию 'product_{:03d}'")
    p.add_argument("--format", choices=("jpeg","png"), default=None, help="Выходной формат; по умолчанию сохраняет оригинал или jpeg для RGB")
    p.add_argument("--quality", type=int, default=95, help="Качество JPEG (только для jpeg), по умолчанию 95")
    p.add_argument("--recursive", action="store_true", help="Обрабатывать папки рекурсивно")
    p.add_argument("--dry-run", action="store_true", help="Показать действия без записи файлов")
    return p.parse_args()


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def iter_images(input_path: Path, recursive: bool):
    if recursive:
        for p in input_path.rglob("*"):
            if p.suffix.lower() in IMAGE_EXTS and p.is_file():
                yield p
    else:
        for p in input_path.iterdir():
            if p.suffix.lower() in IMAGE_EXTS and p.is_file():
                yield p


def process_image(path: Path, out_path: Path, size: int, mode: str, out_format: str, quality: int):
    with Image.open(path) as im:
        if mode == "crop":
            im = ImageOps.exif_transpose(im)
            im_ratio = im.width / im.height
            target_ratio = 1.0
            if im_ratio > target_ratio:
                new_height = size
                new_width = int(im.width * (size / im.height))
            else:
                new_width = size
                new_height = int(im.height * (size / im.width))
            im = im.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - size) // 2
            top = (new_height - size) // 2
            im = im.crop((left, top, left + size, top + size))
        else:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((size, size), Image.LANCZOS)
            background = Image.new("RGBA", (size, size), (255, 255, 255, 0))
            x = (size - im.width) // 2
            y = (size - im.height) // 2
            background.paste(im, (x, y))
            im = background.convert("RGB") if out_format == "jpeg" else background

        if out_format == "jpeg" or (out_format is None and path.suffix.lower() in {".jpg", ".jpeg"}):
            save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True, "progressive": True}
            if im.mode in ("RGBA", "LA"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert("RGB")
        else:
            save_kwargs = {"format": "PNG", "optimize": True}

        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_path, **save_kwargs)


def main():
    args = parse_args()
    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists() or not inp.is_dir():
        print("Input folder does not exist or is not a directory", file=sys.stderr)
        sys.exit(1)

    images = list(iter_images(inp, args.recursive))
    if not images:
        print("No images found in input folder", file=sys.stderr)
        sys.exit(1)

    counter = 1
    for src in images:
        name = args.template.format(counter)
        ext = ".jpg" if args.format == "jpeg" else (src.suffix if args.format is None else ".png")
        dest = out / f"{name}{ext}"
        print(f"{src} -> {dest}")
        if not args.dry_run:
            process_image(src, dest, args.size, args.mode, args.format, args.quality)
        counter += 1


if __name__ == "__main__":
    main()
