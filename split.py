import fitz  # PyMuPDF
import os
import json
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ModuleNotFoundError:
    import sys, platform
    msg = (
        "tkinter is not available in your Python installation.\n\n"
        "Fix:\n"
    )
    if platform.system() == "Darwin":
        import re
        ver = re.match(r"(\d+\.\d+)", sys.version).group(1)
        msg += f"  brew install python-tk@{ver}\n"
    elif platform.system() == "Linux":
        msg += "  sudo apt install python3-tk   # Debian/Ubuntu\n"
        msg += "  sudo dnf install python3-tkinter  # Fedora/RHEL\n"
    else:
        msg += "  Re-install Python from https://python.org and check 'tcl/tk' during setup.\n"
    print(msg)
    sys.exit(1)
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import RectangleSelector
import numpy as np

COORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coords.json")


def _read_store():
    if not os.path.exists(COORDS_FILE):
        return {}
    with open(COORDS_FILE, "r") as f:
        return json.load(f)


def _write_store(data):
    with open(COORDS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_coords(key):
    return _read_store().get(key)


def save_coords(key, boxes):
    data = _read_store()
    data[key] = [[b.x0, b.y0, b.x1, b.y1] for b in boxes]
    _write_store(data)


def load_last_dir(key):
    return _read_store().get(key, os.path.expanduser("~"))


def save_last_dir(key, path):
    data = _read_store()
    data[key] = path
    _write_store(data)


# ── Input / output selection dialog ─────────────────────────────────────────

def ask_paths():
    """Show a small dialog to pick a single PDF or a folder, plus an optional output folder."""
    root = tk.Tk()
    root.title("PDF Splitter – Setup")
    root.resizable(False, False)

    # Center the window
    root.update_idletasks()
    w, h = 520, 410
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    result = {"input": None, "output": None, "mode": None, "save_coords": False, "use_coords": False, "overwrite": True}

    # ── Input row ────────────────────────────────────────────────────────────
    input_var = tk.StringVar()
    mode_var = tk.StringVar(value="file")  # "file" or "folder"

    tk.Label(root, text="Input Path", font=("Helvetica", 11, "bold")).grid(
        row=0, column=0, sticky="w", padx=14, pady=(18, 0)
    )

    mode_frame = tk.Frame(root)
    mode_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(2, 4))
    tk.Radiobutton(mode_frame, text="Single PDF", variable=mode_var, value="file").pack(side="left")
    tk.Radiobutton(mode_frame, text="Folder", variable=mode_var, value="folder").pack(side="left", padx=8)

    last_input_dir = load_last_dir("__last_input_dir__")
    last_output_dir = load_last_dir("__last_output_dir__")

    def browse_input():
        nonlocal last_input_dir
        if mode_var.get() == "file":
            path = filedialog.askopenfilename(
                title="Select a PDF",
                filetypes=[("PDF files", "*.pdf")],
                initialdir=last_input_dir,
            )
        else:
            path = filedialog.askdirectory(
                title="Select input folder",
                initialdir=last_input_dir,
            )
        if path:
            input_var.set(path)
            last_input_dir = os.path.dirname(path) if os.path.isfile(path) else path
            save_last_dir("__last_input_dir__", last_input_dir)

    input_row = tk.Frame(root)
    input_row.grid(row=2, column=0, columnspan=3, padx=12, pady=2, sticky="ew")
    input_row.columnconfigure(0, weight=1)
    input_entry = tk.Entry(input_row, textvariable=input_var, width=42)
    input_entry.grid(row=0, column=0, sticky="nsew")
    tk.Button(input_row, text="Browse…", command=browse_input).grid(row=0, column=1, padx=(4, 0), sticky="nsew")

    # ── Output row ───────────────────────────────────────────────────────────
    output_var = tk.StringVar()

    tk.Label(root, text="Output Path", font=("Helvetica", 11, "bold")).grid(
        row=3, column=0, sticky="w", padx=14, pady=(14, 0)
    )
    tk.Label(root, text="optional – defaults to output_pdfs/ next to input", fg="grey").grid(
        row=4, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 4)
    )

    def browse_output():
        nonlocal last_output_dir
        path = filedialog.askdirectory(title="Select output folder", initialdir=last_output_dir)
        if path:
            output_var.set(path)
            last_output_dir = path
            save_last_dir("__last_output_dir__", path)

    output_row = tk.Frame(root)
    output_row.grid(row=5, column=0, columnspan=3, padx=12, pady=2, sticky="ew")
    output_row.columnconfigure(0, weight=1)
    output_entry = tk.Entry(output_row, textvariable=output_var, width=42)
    output_entry.grid(row=0, column=0, sticky="nsew")
    tk.Button(output_row, text="Browse…", command=browse_output).grid(row=0, column=1, padx=(4, 0), sticky="nsew")

    # ── Coordinates options ───────────────────────────────────────────────────
    coords_mode_var = tk.StringVar(value="draw")

    coords_frame = tk.Frame(root)
    coords_frame.grid(row=6, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 0))
    tk.Label(coords_frame, text="Coordinates:", font=("Helvetica", 10, "bold")).pack(side="left")
    tk.Radiobutton(coords_frame, text="Draw", variable=coords_mode_var, value="draw").pack(side="left", padx=(8, 0))
    tk.Radiobutton(coords_frame, text="Draw & save", variable=coords_mode_var, value="save").pack(side="left", padx=8)
    tk.Radiobutton(coords_frame, text="Use saved", variable=coords_mode_var, value="use").pack(side="left")

    # ── Output mode ───────────────────────────────────────────────────────────
    overwrite_var = tk.StringVar(value="overwrite")

    out_mode_frame = tk.Frame(root)
    out_mode_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=14, pady=(8, 0))
    tk.Label(out_mode_frame, text="Output:", font=("Helvetica", 10, "bold")).pack(side="left")
    tk.Radiobutton(out_mode_frame, text="Overwrite all", variable=overwrite_var, value="overwrite").pack(side="left", padx=(8, 0))
    tk.Radiobutton(out_mode_frame, text="Add new files only", variable=overwrite_var, value="add").pack(side="left", padx=8)

    # ── OK / Cancel ──────────────────────────────────────────────────────────
    def on_ok():
        inp = input_var.get().strip()
        if not inp:
            messagebox.showerror("Missing input", "Please choose a PDF file or folder.")
            return
        if not os.path.exists(inp):
            messagebox.showerror("Not found", f"Path does not exist:\n{inp}")
            return
        result["input"] = inp
        result["mode"] = mode_var.get()
        result["save_coords"] = coords_mode_var.get() == "save"
        result["use_coords"] = coords_mode_var.get() == "use"
        result["overwrite"] = overwrite_var.get() == "overwrite"

        out = output_var.get().strip()
        if out:
            result["output"] = out
        else:
            # Default: output_pdfs/ next to the input file/folder
            parent = os.path.dirname(inp) if mode_var.get() == "file" else os.path.dirname(inp.rstrip("/\\"))
            result["output"] = os.path.join(parent, "output_pdfs")

        root.destroy()

    def on_cancel():
        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=8, column=0, columnspan=3, pady=18)
    tk.Button(btn_frame, text="  OK  ", command=on_ok, default="active", width=10).pack(side="left", padx=8)
    tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=8)
    root.bind("<Return>", lambda _: on_ok())

    root.mainloop()
    return result


# ── Interactive box drawing ──────────────────────────────────────────────────

def pick_boxes_interactively(pdf_path):
    """Display the first page of a PDF and let the user draw crop boxes."""
    doc = fitz.open(pdf_path)
    page = doc[0]

    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]

    page_w, page_h = page.rect.width, page.rect.height
    doc.close()

    boxes = []
    current_rect = [None]

    plt.rcParams['toolbar'] = 'None'
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.imshow(img, extent=[0, page_w, page_h, 0])
    ax.set_title(
        "Draw boxes by clicking and dragging.\n"
        "ENTER=confirm box   BACKSPACE=undo last   ESCAPE=done",
        fontsize=10,
    )
    ax.set_xlim(0, page_w)
    ax.set_ylim(page_h, 0)

    drawn_patches = []

    def on_select(eclick, erelease):
        x1 = min(eclick.xdata, erelease.xdata)
        y1 = min(eclick.ydata, erelease.ydata)
        x2 = max(eclick.xdata, erelease.xdata)
        y2 = max(eclick.ydata, erelease.ydata)
        current_rect[0] = (x1, y1, x2, y2)
        if on_select._preview:
            on_select._preview.remove()
        on_select._preview = ax.add_patch(patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=1.5, edgecolor="yellow", facecolor="none", linestyle="--"
        ))
        fig.canvas.draw_idle()

    on_select._preview = None

    def on_key(event):
        if event.key == "enter" and current_rect[0]:
            x1, y1, x2, y2 = current_rect[0]
            boxes.append(fitz.Rect(x1, y1, x2, y2))
            if on_select._preview:
                on_select._preview.remove()
                on_select._preview = None
            drawn_patches.append(ax.add_patch(patches.Rectangle(
                (x1, y1), x2 - x1, y2 - y1,
                linewidth=2, edgecolor="lime", facecolor=(0, 1, 0, 0.1)
            )))
            ax.set_title(
                f"{len(boxes)} box(es) confirmed. Draw another or press ESCAPE to finish.\n"
                "ENTER=confirm   BACKSPACE=undo last   ESCAPE=done",
                fontsize=10,
            )
            current_rect[0] = None
            fig.canvas.draw_idle()

        elif event.key == "backspace" and boxes:
            boxes.pop()
            if drawn_patches:
                drawn_patches.pop().remove()
            ax.set_title(
                f"{len(boxes)} box(es) confirmed. Draw another or press ESCAPE to finish.\n"
                "ENTER=confirm   BACKSPACE=undo last   ESCAPE=done",
                fontsize=10,
            )
            fig.canvas.draw_idle()

        elif event.key == "escape":
            plt.close(fig)

    selector = RectangleSelector(
        ax, on_select,
        useblit=True,
        button=[1],
        minspanx=5, minspany=5,
        spancoords="data",
        interactive=False,
    )

    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.tight_layout()
    plt.show()
    _ = selector  # keep alive

    return boxes


# ── Progress window ──────────────────────────────────────────────────────────

def run_with_progress(pdf_files, boxes, output_folder, overwrite):
    root = tk.Tk()
    root.title("PDF Splitter – Processing")
    root.resizable(False, False)

    root.update_idletasks()
    w, h = 500, 340
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text="Processing files…", font=("Helvetica", 11, "bold")).pack(pady=(16, 6))

    log_box = scrolledtext.ScrolledText(root, width=60, height=12, state="disabled", font=("Courier", 10))
    log_box.pack(padx=14, pady=4)

    ok_btn = tk.Button(root, text="OK", width=10, state="disabled", command=root.destroy)
    ok_btn.pack(pady=(6, 14))

    def log(msg):
        log_box.config(state="normal")
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        log_box.config(state="disabled")
        root.update()

    def process():
        processed = 0
        skipped = 0

        for pdf_path in pdf_files:
            basename = os.path.basename(pdf_path)
            out_path = os.path.join(output_folder, basename)

            if not overwrite and os.path.exists(out_path):
                log(f"Skipped (already exists): {basename}")
                skipped += 1
                continue

            log(f"Processing: {basename}")

            doc = fitz.open(pdf_path)
            out = fitz.open()

            for page in doc:
                for b in boxes:
                    new_page = out.new_page(width=b.width, height=b.height)
                    new_page.show_pdf_page(new_page.rect, doc, page.number, clip=b)

            out.save(out_path)
            out.close()
            doc.close()
            processed += 1

        summary = f"\nDone! {processed} file(s) processed"
        if skipped:
            summary += f", {skipped} skipped"
        summary += f".\nOutput folder: {output_folder}"
        log(summary)

        ok_btn.config(state="normal")
        root.title("PDF Splitter – Done")

    root.after(100, process)
    root.mainloop()


# ── Main ─────────────────────────────────────────────────────────────────────

paths = ask_paths()

if not paths["input"]:
    exit(0)

input_path = paths["input"]
output_folder = paths["output"]
mode = paths["mode"]

os.makedirs(output_folder, exist_ok=True)

# Collect the list of PDFs to process and pick a preview file
if mode == "file":
    pdf_files = [input_path]
    preview_pdf = input_path
else:
    all_files = sorted(f for f in os.listdir(input_path) if f.lower().endswith(".pdf"))
    if not all_files:
        messagebox.showerror("No PDFs found", f"No PDF files found in:\n{input_path}")
        exit(1)
    pdf_files = [os.path.join(input_path, f) for f in all_files]
    preview_pdf = pdf_files[0]

# ── Coordinates: load or draw ─────────────────────────────────────────────────
coords_key = os.path.normpath(input_path)

if paths["use_coords"]:
    saved = load_coords(coords_key)
    if saved:
        boxes = [fitz.Rect(*c) for c in saved]
    else:
        dlg = tk.Tk()
        dlg.title("No Saved Coordinates")
        dlg.resizable(False, False)
        dlg.update_idletasks()
        dw, dh = 400, 175
        dlg.geometry(f"{dw}x{dh}+{(dlg.winfo_screenwidth()-dw)//2}+{(dlg.winfo_screenheight()-dh)//2}")

        tk.Label(
            dlg,
            text="No saved coordinates were found for this input path.\nYou will be asked to draw the boxes manually.",
            justify="left", wraplength=360,
        ).pack(padx=20, pady=(18, 8))

        fallback_save_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="Save coordinates after drawing", variable=fallback_save_var).pack(anchor="w", padx=20)

        def on_dlg_ok():
            paths["save_coords"] = fallback_save_var.get()
            dlg.destroy()

        tk.Button(dlg, text="OK", width=10, command=on_dlg_ok).pack(pady=12)
        dlg.bind("<Return>", lambda _: on_dlg_ok())
        dlg.mainloop()
        paths["use_coords"] = False

if not paths["use_coords"]:
    boxes = pick_boxes_interactively(preview_pdf)

if not boxes:
    messagebox.showwarning("No boxes defined", "No crop boxes were defined. Exiting.")
    exit(0)

if paths["save_coords"]:
    save_coords(coords_key, boxes)

run_with_progress(pdf_files, boxes, output_folder, paths["overwrite"])
