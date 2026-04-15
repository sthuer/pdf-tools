# pdf-tools
Simple Python tool to compress  PDFs (Ghostscript) and exportpages as images

Simple Python tool to:

- Compress PDF files using Ghostscript
- Export PDF pages as images (WebP or JPEG)

## Requirements

- Python 3.x
- Ghostscript installed

## Installation

```bash
pip install pymupdf pillow
```

## Usage

Compress PDF
py pdf_tool.py compress input\\file.pdf

Export pages
py pdf_tool.py export input\\file.pdf --pages 1,3-5

Compress + export
py pdf_tool.py both input\\file.pdf

Options
--pages → page selection (e.g. 2, 2,5,7, 2-10)
--format → webp (default) or jpeg
--pdf-quality → screen, ebook, etc.