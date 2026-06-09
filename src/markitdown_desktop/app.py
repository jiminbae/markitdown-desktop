from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .converter import ConversionJob, ConversionResult, build_jobs, convert_job


class MarkItDownDesktop(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MarkItDown Desktop")
        self.geometry("860x640")
        self.minsize(760, 560)

        self._files: list[Path] = []
        self._selected_output_dir: Path | None = None
        self._use_output_dir = tk.BooleanVar(value=False)
        self._messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker_thread: threading.Thread | None = None

        self._configure_style()
        self._build_layout()
        self._refresh_file_list()

    def _configure_style(self) -> None:
        self.configure(bg="#f6f7f9")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f7f9")
        style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#f6f7f9", foreground="#1f2933")
        style.configure("Muted.TLabel", background="#f6f7f9", foreground="#667085")
        style.configure(
            "Title.TLabel",
            background="#f6f7f9",
            foreground="#111827",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background="#f6f7f9",
            foreground="#344054",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.configure("TCheckbutton", background="#f6f7f9", foreground="#344054")

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=24)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X)

        title_block = ttk.Frame(header)
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(title_block, text="MarkItDown Desktop", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_block,
            text="Convert documents to Markdown without using a terminal",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(header, text=f"v{__version__}", style="Muted.TLabel").pack(
            side=tk.RIGHT,
            anchor=tk.N,
        )

        panel = ttk.Frame(root, style="Panel.TFrame", padding=18)
        panel.pack(fill=tk.X, pady=(20, 16))

        ttk.Label(
            panel,
            text="Add PDF, PPTX, DOCX, XLSX, HTML, CSV, JSON, images, ZIP, and more.",
            background="#ffffff",
            foreground="#344054",
            font=("Segoe UI", 12, "bold"),
            wraplength=720,
        ).pack(anchor=tk.W)
        ttk.Label(
            panel,
            text="Choose files, pick an optional output folder, then convert them to Markdown.",
            background="#ffffff",
            foreground="#667085",
            wraplength=720,
        ).pack(anchor=tk.W, pady=(6, 0))

        actions = ttk.Frame(root)
        actions.pack(fill=tk.X, pady=(0, 12))

        self._choose_button = ttk.Button(actions, text="Choose Files", command=self.choose_files)
        self._choose_button.pack(side=tk.LEFT)

        self._remove_button = ttk.Button(
            actions,
            text="Remove Selected",
            command=self.remove_selected,
        )
        self._remove_button.pack(side=tk.LEFT, padx=(8, 0))

        self._clear_button = ttk.Button(actions, text="Clear", command=self.clear_files)
        self._clear_button.pack(side=tk.LEFT, padx=(8, 0))

        self._convert_button = ttk.Button(
            actions,
            text="Convert",
            style="Primary.TButton",
            command=self.start_conversion,
        )
        self._convert_button.pack(side=tk.RIGHT)

        output = ttk.Frame(root)
        output.pack(fill=tk.X, pady=(0, 16))

        self._output_toggle = ttk.Checkbutton(
            output,
            text="Use selected output folder",
            variable=self._use_output_dir,
            command=self._update_output_controls,
        )
        self._output_toggle.pack(side=tk.LEFT)

        self._output_label = ttk.Label(output, text="Original file folders", style="Muted.TLabel")
        self._output_label.pack(side=tk.LEFT, padx=(12, 12), fill=tk.X, expand=True)

        self._output_button = ttk.Button(
            output,
            text="Choose Folder",
            command=self.choose_output_folder,
        )
        self._output_button.pack(side=tk.RIGHT)

        ttk.Label(root, text="Files", style="Section.TLabel").pack(anchor=tk.W)
        file_frame = ttk.Frame(root)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 14))

        file_scroll = ttk.Scrollbar(file_frame, orient=tk.VERTICAL)
        self._file_list = tk.Listbox(
            file_frame,
            selectmode=tk.EXTENDED,
            activestyle="none",
            bg="#ffffff",
            fg="#1f2937",
            selectbackground="#dbeafe",
            selectforeground="#111827",
            relief=tk.SOLID,
            highlightthickness=0,
            yscrollcommand=file_scroll.set,
            font=("Segoe UI", 10),
        )
        file_scroll.configure(command=self._file_list.yview)
        self._file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(root, text="Activity", style="Section.TLabel").pack(anchor=tk.W)
        log_frame = ttk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 12))

        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        self._log = tk.Text(
            log_frame,
            height=7,
            bg="#ffffff",
            fg="#1f2937",
            relief=tk.SOLID,
            highlightthickness=0,
            yscrollcommand=log_scroll.set,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        log_scroll.configure(command=self._log.yview)
        self._log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._log.configure(state=tk.DISABLED)

        self._status_label = ttk.Label(root, text="Ready", style="Muted.TLabel")
        self._status_label.pack(anchor=tk.W)

    def choose_files(self) -> None:
        files = filedialog.askopenfilenames(title="Choose files to convert")
        self.add_files([Path(path) for path in files])

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self._selected_output_dir = Path(folder)
            self._output_label.configure(text=str(self._selected_output_dir))

    def add_files(self, paths: list[Path]) -> None:
        existing = {path.resolve() for path in self._files}
        added = 0
        for path in paths:
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved not in existing:
                self._files.append(resolved)
                existing.add(resolved)
                added += 1
        if added:
            self._refresh_file_list()
            self._append_log(f"Added {added} file(s)")

    def remove_selected(self) -> None:
        for row in reversed(self._file_list.curselection()):
            self._files.pop(row)
        self._refresh_file_list()

    def clear_files(self) -> None:
        self._files.clear()
        self._refresh_file_list()
        self._append_log("Cleared file list")

    def _refresh_file_list(self) -> None:
        self._file_list.delete(0, tk.END)
        for path in self._files:
            self._file_list.insert(tk.END, str(path))
        self._convert_button.configure(
            state=tk.NORMAL if self._files and not self._worker_thread else tk.DISABLED
        )
        self._status_label.configure(text=f"{len(self._files)} file(s) ready")

    def _update_output_controls(self) -> None:
        if self._use_output_dir.get():
            self._output_button.configure(state=tk.NORMAL)
            label = (
                str(self._selected_output_dir)
                if self._selected_output_dir
                else "No output folder selected"
            )
            self._output_label.configure(text=label)
        else:
            self._output_button.configure(state=tk.DISABLED)
            self._output_label.configure(text="Original file folders")

    def start_conversion(self) -> None:
        if not self._files:
            return

        output_directory = None
        if self._use_output_dir.get():
            if self._selected_output_dir is None:
                self.choose_output_folder()
            if self._selected_output_dir is None:
                return
            output_directory = self._selected_output_dir

        jobs = build_jobs(self._files, output_directory)
        self._set_busy(True)
        self._append_log(f"Starting {len(jobs)} conversion(s)")
        self._worker_thread = threading.Thread(
            target=self._run_conversion,
            args=(jobs,),
            daemon=True,
        )
        self._worker_thread.start()
        self.after(100, self._poll_messages)

    def _run_conversion(self, jobs: list[ConversionJob]) -> None:
        total = len(jobs)
        for index, job in enumerate(jobs, start=1):
            self._messages.put(("progress", (index, total, job.input_path.name)))
            self._messages.put(("result", convert_job(job)))
        self._messages.put(("finished", None))

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self._messages.get_nowait()
                if kind == "progress":
                    index, total, filename = payload  # type: ignore[misc]
                    status = f"Converting {index}/{total}: {filename}"
                    self._status_label.configure(text=status)
                elif kind == "result":
                    result = payload
                    if isinstance(result, ConversionResult):
                        prefix = "OK" if result.succeeded else "Failed"
                        log_message = (
                            f"{prefix}: {result.job.input_path.name} -> {result.message}"
                        )
                        self._append_log(log_message)
                elif kind == "finished":
                    self._worker_thread = None
                    self._set_busy(False)
                    self._status_label.configure(text="Done")
                    self._append_log("Finished")
                    messagebox.showinfo("MarkItDown Desktop", "Conversion finished.")
        except queue.Empty:
            pass

        if self._worker_thread is not None:
            self.after(100, self._poll_messages)

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self._choose_button.configure(state=state)
        self._remove_button.configure(state=state)
        self._clear_button.configure(state=state)
        self._output_toggle.configure(state=state)
        self._output_button.configure(
            state=tk.NORMAL if not busy and self._use_output_dir.get() else tk.DISABLED
        )
        convert_state = tk.DISABLED if busy or not self._files else tk.NORMAL
        self._convert_button.configure(state=convert_state)

    def _append_log(self, message: str) -> None:
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, message + "\n")
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)


def main() -> int:
    app = MarkItDownDesktop()
    app.mainloop()
    return 0
