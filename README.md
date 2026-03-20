# PDF Box Splitter

A desktop tool that lets you visually draw crop regions on a PDF page and extract those regions across an entire document (or batch of documents) into a new PDF.

## Features

- GUI file picker — choose a single PDF or a whole folder
- Optional output folder selection (defaults to `output_pdfs/` next to your input)
- Remembers the last used input and output directories across sessions
- Interactive crop-box drawing directly on a rendered PDF page
- Supports any number of boxes per page
- Processes all pages of every selected PDF automatically
- Save and reuse crop coordinates — draw once, reuse on future runs
- Output mode control — overwrite existing files or skip files that already exist

## Requirements

- Python 3.8+
- `tkinter` — part of the standard library, but **not bundled** with Homebrew Python on macOS. Install it separately before creating your venv:

  ```bash
  # macOS (Homebrew) — match the version you use, e.g. 3.14
  brew install python-tk@3.14

  # Linux (Debian/Ubuntu)
  sudo apt install python3-tk

  # Linux (Fedora/RHEL)
  sudo dnf install python3-tkinter

  # Windows — tkinter is included; no extra step needed
  ```

  > If you skip this step the script will print a clear error with the exact command to run.

Create and activate a virtual environment, then install the remaining dependencies:

```bash
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
python split.py
```

1. **Input** — select a single PDF file or a folder containing multiple PDFs. Use the radio buttons to switch between modes.
2. **Output folder** — optionally choose where the processed PDFs are saved. If left blank, an `output_pdfs/` folder is created next to your input.
3. **Coordinates** — choose how crop boxes are sourced:
   - **Draw** — draw boxes interactively every time (default)
   - **Draw & save** — draw boxes and save them to `coords.json` for future reuse
   - **Use saved** — skip drawing and load previously saved coordinates for the current input path. If no saved coordinates are found, you will be prompted to draw them manually (with an option to save).
4. **Output mode** — choose what happens when an output file already exists:
   - **Overwrite all** — always overwrite (default)
   - **Add new files only** — skip files that already exist in the output folder
5. **Draw boxes** — if drawing is required, the first page of your PDF opens in an interactive window. Click and drag to draw a crop region.
   - `Enter` — confirm the current box (turns green)
   - `Backspace` — undo the last confirmed box
   - `Escape` — finish and start processing
6. Processed PDFs are saved to the output folder. Each original page produces one output page per box, in the order the boxes were drawn.

## Pre-built executables

Download the latest release for your platform from the [Releases](../../releases) page — no Python installation needed.

| Platform | File |
|----------|------|
| Windows  | `PDF-Box-Splitter-windows.exe` |
| macOS    | `PDF-Box-Splitter-macos` |
| Linux    | `PDF-Box-Splitter-linux` |

**macOS note:** The app is unsigned, so Gatekeeper will block it on first launch. To open it anyway, right-click (or Control-click) the file and choose **Open**, then confirm in the dialog. You only need to do this once.

**Linux note:** You may need to mark the file as executable before running it:
```bash
chmod +x PDF-Box-Splitter-linux
./PDF-Box-Splitter-linux
```

## Output structure

For each input PDF, each page is split into N output pages (one per box), in drawing order. The output file keeps the same filename as the input.

```
input_pdfs/
  lecture01.pdf   →   output_pdfs/lecture01.pdf
  lecture02.pdf   →   output_pdfs/lecture02.pdf
```
