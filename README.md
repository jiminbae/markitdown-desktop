# MarkItDown Desktop

Unofficial desktop app for converting documents to Markdown with
[Microsoft MarkItDown](https://github.com/microsoft/markitdown).

MarkItDown Desktop gives you a simple desktop interface for files such as
PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, images, audio, ZIP files, and other
formats supported by MarkItDown.

> This project is not affiliated with, endorsed by, sponsored by, or maintained
> by Microsoft. "Microsoft" and "MarkItDown" are referenced only to identify the
> upstream open-source library used by this app.

## Features

- Choose one or more files with a normal file picker
- Convert files to `.md` next to the original file
- Optionally write all outputs to a selected folder
- See conversion progress and errors in the app window
- Package a Windows build with GitHub Actions and PyInstaller

## Download

Download the latest Windows `.zip` from the
[GitHub Releases](https://github.com/jiminbae/markitdown-desktop/releases) page.

After downloading:

1. Unzip the file.
2. Run `MarkItDown Desktop.exe`.
3. Click `Choose Files`.
4. Select documents to convert.
5. Click `Convert`.

## Supported Files

MarkItDown Desktop delegates conversion to Microsoft MarkItDown, so format
support depends on the installed MarkItDown package and its optional
dependencies. The packaged app is configured to install `markitdown[all]`.

Common supported inputs include:

- PDF
- PowerPoint files (`.pptx`)
- Word files (`.docx`)
- Excel files (`.xlsx`, `.xls`)
- HTML
- CSV, JSON, XML
- Images
- Audio
- ZIP
- EPUB

Some advanced conversions may require system tools or online services depending
on the upstream MarkItDown converter being used.

## Development

Requirements:

- Python 3.10 or newer
- Windows, macOS, or Linux for development
- Windows for the release build workflow

Create a virtual environment and install the app:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Run the app:

```bash
python -m markitdown_desktop
```

Build locally with PyInstaller:

```bash
pyinstaller packaging/markitdown-desktop.spec --noconfirm --clean
```

The Windows build output is created under `dist/MarkItDown Desktop`.

## GitHub Releases

The workflow in `.github/workflows/build-windows.yml` builds a Windows
application bundle whenever a tag starting with `v` is pushed:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow uploads a zipped Windows app to the GitHub Release. The UI uses
Python's standard-library Tkinter toolkit, so the main third-party license
surface is MarkItDown and its conversion dependencies.

## Relationship To Microsoft MarkItDown

This app is a desktop wrapper around the open-source
[microsoft/markitdown](https://github.com/microsoft/markitdown) Python package.
It does not copy or vendor MarkItDown source code into this repository. The
application depends on MarkItDown as a third-party package.

Microsoft MarkItDown is distributed under the MIT License with copyright held by
Microsoft Corporation. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for
credit and license details.

The name "MarkItDown Desktop" is used descriptively to communicate that this is
a desktop interface for MarkItDown. This project is unofficial and independent.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
