import os
import re
import sys
import shutil
import subprocess
import argparse
import fitz
from PIL import Image


def print_quick_help():
    print("""
PDF Tool - Usage

Commands:
  compress   Compress PDF
  export     Export PDF pages as images
  both       Compress PDF and export pages

Examples:
  py pdf_tool.py compress input\\revista.pdf
  py pdf_tool.py export input\\revista.pdf --pages 1,3-5
  py pdf_tool.py both input\\revista.pdf
  py pdf_tool.py both --batch
  py pdf_tool.py export --batch --pages 1,3

Use --help after any command for more details.
""")


def find_ghostscript():
    candidates = [
        "gswin64c",
        r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.07.0\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe",
    ]

    for candidate in candidates:
        if candidate == "gswin64c":
            if shutil.which(candidate):
                return candidate
        elif os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "No se encontró Ghostscript. Instalalo o ajustá la función find_ghostscript() con la ruta correcta."
    )


def compress_pdf(input_path, output_path, quality="screen"):
    gs = find_ghostscript()

    command = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path,
    ]

    subprocess.run(command, check=True)


def parse_pages(pages_str, total_pages):
    if not pages_str:
        return [1]

    pages = set()
    parts = pages_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            if not re.fullmatch(r"\d+-\d+", part):
                raise ValueError(f"Rango inválido: {part}")

            start_str, end_str = part.split("-")
            start = int(start_str)
            end = int(end_str)

            if start > end:
                raise ValueError(f"Rango inválido: {part}")

            for p in range(start, end + 1):
                if 1 <= p <= total_pages:
                    pages.add(p)
        else:
            if not part.isdigit():
                raise ValueError(f"Página inválida: {part}")

            p = int(part)
            if 1 <= p <= total_pages:
                pages.add(p)

    result = sorted(pages)

    if not result:
        raise ValueError("No quedó ninguna página válida dentro del rango del PDF.")

    return result


def export_pages_as_images(input_pdf, output_dir, pages_str="1", image_format="webp", dpi=150, quality=80):
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(input_pdf)
    total_pages = len(doc)

    pages = parse_pages(pages_str, total_pages)
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]

    image_format = image_format.lower()
    if image_format not in ("webp", "jpeg", "jpg"):
        doc.close()
        raise ValueError("Formato de imagen no soportado. Usá 'webp', 'jpeg' o 'jpg'.")

    ext = "jpg" if image_format in ("jpeg", "jpg") else "webp"
    outputs = []

    for page_number in pages:
        page = doc.load_page(page_number - 1)
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        output_image = os.path.join(output_dir, f"{base_name}-p{page_number}.{ext}")

        if ext == "webp":
            img.save(output_image, "WEBP", quality=quality, method=6)
        else:
            img.save(output_image, "JPEG", quality=quality, optimize=True)

        outputs.append(output_image)

    doc.close()
    return outputs


def print_file_size(label, path):
    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)
    size_kb = size_bytes / 1024

    if size_mb >= 1:
        print(f"{label}: {size_mb:.2f} MB")
    else:
        print(f"{label}: {size_kb:.0f} KB")


def get_pdf_files_from_input_dir(input_dir="input"):
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"No existe la carpeta: {input_dir}")

    pdf_files = []
    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(input_dir, file_name))

    pdf_files.sort()
    return pdf_files


def resolve_input_files(input_pdf=None, batch=False, input_dir="input"):
    if batch:
        files = get_pdf_files_from_input_dir(input_dir)
        if not files:
            raise FileNotFoundError(f"No se encontraron PDFs en la carpeta: {input_dir}")
        return files

    if input_pdf:
        if not os.path.exists(input_pdf):
            raise FileNotFoundError(f"No existe el archivo: {input_pdf}")
        return [input_pdf]

    raise ValueError("Debés indicar un archivo PDF o usar --batch.")


def main():
    if len(sys.argv) == 1 or "?" in sys.argv:
        print_quick_help()
        return

    parser = argparse.ArgumentParser(
        description="Compress PDF and/or export PDF pages as images."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # compress
    compress_parser = subparsers.add_parser("compress", help="Compress PDF only")
    compress_parser.add_argument("input_pdf", nargs="?", help="Path to input PDF")
    compress_parser.add_argument("--batch", action="store_true", help="Process all PDF files in input directory")
    compress_parser.add_argument("--input-dir", default="input", help="Input directory for batch mode")
    compress_parser.add_argument("--output-dir", default="output", help="Output directory")
    compress_parser.add_argument(
        "--pdf-quality",
        default="screen",
        choices=["screen", "ebook", "printer", "prepress", "default"],
        help="Ghostscript PDF quality preset"
    )

    # export
    export_parser = subparsers.add_parser("export", help="Export PDF pages as images")
    export_parser.add_argument("input_pdf", nargs="?", help="Path to input PDF")
    export_parser.add_argument("--batch", action="store_true", help="Process all PDF files in input directory")
    export_parser.add_argument("--input-dir", default="input", help="Input directory for batch mode")
    export_parser.add_argument("--output-dir", default="output", help="Output directory")
    export_parser.add_argument("--pages", default="1", help="Pages to export, e.g. 2 or 2,5,7 or 2-10")
    export_parser.add_argument("--format", default="webp", choices=["webp", "jpeg", "jpg"], help="Image format")
    export_parser.add_argument("--dpi", type=int, default=150, help="Image DPI")
    export_parser.add_argument("--image-quality", type=int, default=80, help="Image quality")

    # both
    both_parser = subparsers.add_parser("both", help="Compress PDF and export pages as images")
    both_parser.add_argument("input_pdf", nargs="?", help="Path to input PDF")
    both_parser.add_argument("--batch", action="store_true", help="Process all PDF files in input directory")
    both_parser.add_argument("--input-dir", default="input", help="Input directory for batch mode")
    both_parser.add_argument("--output-dir", default="output", help="Output directory")
    both_parser.add_argument(
        "--pdf-quality",
        default="screen",
        choices=["screen", "ebook", "printer", "prepress", "default"],
        help="Ghostscript PDF quality preset"
    )
    both_parser.add_argument("--pages", default="1", help="Pages to export, e.g. 2 or 2,5,7 or 2-10")
    both_parser.add_argument("--format", default="webp", choices=["webp", "jpeg", "jpg"], help="Image format")
    both_parser.add_argument("--dpi", type=int, default=150, help="Image DPI")
    both_parser.add_argument("--image-quality", type=int, default=80, help="Image quality")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.command == "compress":
        input_files = resolve_input_files(args.input_pdf, args.batch, args.input_dir)

        for input_file in input_files:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            optimized_pdf = os.path.join(args.output_dir, f"{base_name}-optimized.pdf")

            print(f"\nProcessing: {input_file}")
            print("1) Compressing PDF...")
            compress_pdf(input_file, optimized_pdf, quality=args.pdf_quality)

            print("Done.")
            print_file_size("Original PDF", input_file)
            print_file_size("Compressed PDF", optimized_pdf)
            print(f"Output: {optimized_pdf}")

    elif args.command == "export":
        input_files = resolve_input_files(args.input_pdf, args.batch, args.input_dir)

        for input_file in input_files:
            print(f"\nProcessing: {input_file}")
            print("1) Exporting page(s) as image...")

            outputs = export_pages_as_images(
                input_file,
                args.output_dir,
                pages_str=args.pages,
                image_format=args.format,
                dpi=args.dpi,
                quality=args.image_quality,
            )

            print("Done.")
            for output in outputs:
                print_file_size("Image", output)
                print(f"Output: {output}")

    elif args.command == "both":
        input_files = resolve_input_files(args.input_pdf, args.batch, args.input_dir)

        for input_file in input_files:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            optimized_pdf = os.path.join(args.output_dir, f"{base_name}-optimized.pdf")

            print(f"\nProcessing: {input_file}")
            print("1) Compressing PDF...")
            compress_pdf(input_file, optimized_pdf, quality=args.pdf_quality)

            print("2) Exporting page(s) as image...")
            outputs = export_pages_as_images(
                optimized_pdf,
                args.output_dir,
                pages_str=args.pages,
                image_format=args.format,
                dpi=args.dpi,
                quality=args.image_quality,
            )

            print("Done.")
            print_file_size("Original PDF", input_file)
            print_file_size("Compressed PDF", optimized_pdf)
            print(f"Output PDF: {optimized_pdf}")

            for output in outputs:
                print_file_size("Image", output)
                print(f"Output image: {output}")


if __name__ == "__main__":
    main()