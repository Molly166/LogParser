"""
Tkinter 可视化界面 - 日志解析器

运行方式：
  python src/gui.py
"""

from __future__ import annotations

import threading
import traceback
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, Iterator, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from log_parser import LogParser


SUPPORTED_EXTS = (".log", ".txt", ".json")


@dataclass
class RunConfig:
    mode: str  # "single" | "batch"
    input_file: Optional[Path]
    logs_dir: Optional[Path]
    output_dir: Path
    output_file: Optional[Path]
    fmt: str  # "json" | "csv" | "txt"
    stream: bool


def find_log_files(directory: Path) -> List[Path]:
    files: List[Path] = []
    for ext in SUPPORTED_EXTS:
        files.extend(directory.glob(f"*{ext}"))
    return sorted(set(files))


def chunked(items: List[Dict[str, Any]], chunk_size: int = 300) -> Iterator[List[Dict[str, Any]]]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("日志解析器 - 可视化界面")
        self.geometry("980x700")
        self.minsize(900, 620)

        self.parser = LogParser()
        self._worker: Optional[threading.Thread] = None
        self._preview_queue: Deque[Dict[str, Any]] = deque()
        self._preview_polling = False

        self.var_mode = tk.StringVar(value="single")
        self.var_input_file = tk.StringVar(value="")
        self.var_logs_dir = tk.StringVar(value=str((Path(__file__).parent.parent / "logs").resolve()))
        self.var_output_dir = tk.StringVar(value=str((Path(__file__).parent.parent / "output").resolve()))
        self.var_output_file = tk.StringVar(value="")
        self.var_format = tk.StringVar(value="json")
        self.var_stream = tk.BooleanVar(value=False)

        self._build_ui()
        self._on_mode_change()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        mode_row = ttk.Frame(top)
        mode_row.pack(fill="x")

        ttk.Label(mode_row, text="处理模式：").pack(side="left")
        ttk.Radiobutton(mode_row, text="单文件", value="single", variable=self.var_mode, command=self._on_mode_change).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(mode_row, text="批量目录", value="batch", variable=self.var_mode, command=self._on_mode_change).pack(side="left")

        # Single file row
        self.single_row = ttk.Frame(top)
        self.single_row.pack(fill="x", pady=(10, 0))
        ttk.Label(self.single_row, text="输入文件：").pack(side="left")
        self.entry_input_file = ttk.Entry(self.single_row, textvariable=self.var_input_file)
        self.entry_input_file.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(self.single_row, text="选择...", command=self._pick_input_file).pack(side="left")

        # Batch dir row
        self.batch_row = ttk.Frame(top)
        self.batch_row.pack(fill="x", pady=(10, 0))
        ttk.Label(self.batch_row, text="日志目录：").pack(side="left")
        self.entry_logs_dir = ttk.Entry(self.batch_row, textvariable=self.var_logs_dir)
        self.entry_logs_dir.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(self.batch_row, text="选择...", command=self._pick_logs_dir).pack(side="left")

        # Output row
        out_row = ttk.Frame(top)
        out_row.pack(fill="x", pady=(10, 0))
        ttk.Label(out_row, text="输出目录：").pack(side="left")
        self.entry_output_dir = ttk.Entry(out_row, textvariable=self.var_output_dir)
        self.entry_output_dir.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(out_row, text="选择...", command=self._pick_output_dir).pack(side="left")

        # Optional output file (single mode only)
        self.outfile_row = ttk.Frame(top)
        self.outfile_row.pack(fill="x", pady=(10, 0))
        ttk.Label(self.outfile_row, text="输出文件(可选)：").pack(side="left")
        self.entry_output_file = ttk.Entry(self.outfile_row, textvariable=self.var_output_file)
        self.entry_output_file.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(self.outfile_row, text="选择...", command=self._pick_output_file).pack(side="left")

        # Options row
        opt_row = ttk.Frame(top)
        opt_row.pack(fill="x", pady=(10, 0))
        ttk.Label(opt_row, text="输出格式：").pack(side="left")
        ttk.OptionMenu(opt_row, self.var_format, self.var_format.get(), "json", "csv", "txt").pack(side="left", padx=(8, 16))
        ttk.Checkbutton(opt_row, text="流式处理（适合大文件）", variable=self.var_stream).pack(side="left")

        # Actions
        action_row = ttk.Frame(top)
        action_row.pack(fill="x", pady=(12, 0))
        self.btn_run = ttk.Button(action_row, text="开始解析", command=self._run_clicked)
        self.btn_run.pack(side="left")
        ttk.Button(action_row, text="清空日志", command=self._clear_log).pack(side="left", padx=8)

        # Main area: log + preview
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        log_frame = ttk.Labelframe(main, text="运行日志")
        preview_frame = ttk.Labelframe(main, text="结果预览（同步追加展示）")
        main.add(log_frame, weight=1)
        main.add(preview_frame, weight=1)

        self.txt_log = tk.Text(log_frame, height=20, wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=8)

        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.preview_tree = ttk.Treeview(preview_container, columns=("query", "bill_info", "reply"), show="headings")
        self.preview_tree.heading("query", text="query")
        self.preview_tree.heading("bill_info", text="bill_info")
        self.preview_tree.heading("reply", text="reply")
        self.preview_tree.column("query", width=220, anchor="w")
        self.preview_tree.column("bill_info", width=280, anchor="w")
        self.preview_tree.column("reply", width=320, anchor="w")
        vsb = ttk.Scrollbar(preview_container, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=vsb.set)
        self.preview_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tip = ttk.Label(self, text="提示：批量目录模式会扫描 *.log / *.txt / *.json，并把结果输出到指定输出目录。", anchor="w")
        tip.pack(fill="x", padx=12, pady=(0, 10))

    def _on_mode_change(self) -> None:
        mode = self.var_mode.get()
        if mode == "single":
            self.single_row.pack(fill="x", pady=(10, 0))
            self.outfile_row.pack(fill="x", pady=(10, 0))
            self.batch_row.forget()
        else:
            self.batch_row.pack(fill="x", pady=(10, 0))
            self.single_row.forget()
            self.outfile_row.forget()

    def _pick_input_file(self) -> None:
        path = filedialog.askopenfilename(title="选择日志文件", filetypes=[("Log files", "*.log *.txt *.json"), ("All files", "*.*")])
        if path:
            self.var_input_file.set(path)

    def _pick_logs_dir(self) -> None:
        path = filedialog.askdirectory(title="选择日志目录")
        if path:
            self.var_logs_dir.set(path)

    def _pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.var_output_dir.set(path)

    def _pick_output_file(self) -> None:
        fmt = self.var_format.get()
        path = filedialog.asksaveasfilename(
            title="选择输出文件",
            defaultextension=f".{fmt}",
            filetypes=[(fmt.upper(), f"*.{fmt}"), ("All files", "*.*")],
        )
        if path:
            self.var_output_file.set(path)

    def _clear_log(self) -> None:
        self.txt_log.delete("1.0", "end")
        self._clear_preview()

    def _clear_preview(self) -> None:
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self._preview_queue.clear()

    def _log(self, msg: str) -> None:
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.btn_run.configure(state=state)

    def _validate_config(self) -> Optional[RunConfig]:
        try:
            output_dir = Path(self.var_output_dir.get().strip()).expanduser().resolve()
        except Exception:
            messagebox.showerror("错误", "输出目录不合法")
            return None

        fmt = self.var_format.get().strip().lower()
        if fmt not in ("json", "csv", "txt"):
            messagebox.showerror("错误", "输出格式不合法")
            return None

        mode = self.var_mode.get()
        if mode == "single":
            input_file_str = self.var_input_file.get().strip()
            if not input_file_str:
                messagebox.showerror("错误", "请选择输入文件")
                return None
            input_file = Path(input_file_str).expanduser().resolve()
            if not input_file.exists():
                messagebox.showerror("错误", f"输入文件不存在：{input_file}")
                return None
            if input_file.suffix.lower() not in SUPPORTED_EXTS:
                messagebox.showwarning("提示", f"文件扩展名不在支持列表中：{SUPPORTED_EXTS}")

            output_file_str = self.var_output_file.get().strip()
            output_file = Path(output_file_str).expanduser().resolve() if output_file_str else None
            return RunConfig(
                mode="single",
                input_file=input_file,
                logs_dir=None,
                output_dir=output_dir,
                output_file=output_file,
                fmt=fmt,
                stream=bool(self.var_stream.get()),
            )

        # batch
        logs_dir_str = self.var_logs_dir.get().strip()
        if not logs_dir_str:
            messagebox.showerror("错误", "请选择日志目录")
            return None
        logs_dir = Path(logs_dir_str).expanduser().resolve()
        if not logs_dir.exists():
            messagebox.showerror("错误", f"日志目录不存在：{logs_dir}")
            return None
        return RunConfig(
            mode="batch",
            input_file=None,
            logs_dir=logs_dir,
            output_dir=output_dir,
            output_file=None,
            fmt=fmt,
            stream=bool(self.var_stream.get()),
        )

    def _run_clicked(self) -> None:
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("提示", "任务正在运行中，请稍等。")
            return

        cfg = self._validate_config()
        if not cfg:
            return

        self._set_running(True)
        self._log("=" * 80)
        self._log("开始解析...")
        self._clear_preview()
        self._start_preview_polling()

        self._worker = threading.Thread(target=self._run_job_safe, args=(cfg,), daemon=True)
        self._worker.start()

    def _run_job_safe(self, cfg: RunConfig) -> None:
        try:
            self._run_job(cfg)
            self.after(0, lambda: self._log("完成。"))
        except Exception:
            err = traceback.format_exc()
            self.after(0, lambda: self._log(err))
            self.after(0, lambda: messagebox.showerror("运行失败", "解析过程中发生异常，详情请查看日志。"))
        finally:
            self.after(0, lambda: self._set_running(False))
            self.after(0, self._stop_preview_polling)

    def _render_preview(self, results: List[Dict[str, Any]]) -> None:
        self._clear_preview()
        self._append_preview_batch(results)

    def _append_preview_batch(self, results: List[Dict[str, Any]]) -> None:
        if not results:
            return
        for r in results:
            q = (r.get("query") or "")[:240]
            b = (r.get("bill_info") or "")[:400]
            rep = (r.get("reply") or "")[:500]
            self.preview_tree.insert("", "end", values=(q, b, rep))
        children = self.preview_tree.get_children()
        if children:
            self.preview_tree.see(children[-1])

    def _enqueue_preview(self, item: Dict[str, Any]) -> None:
        self._preview_queue.append(item)

    def _start_preview_polling(self) -> None:
        if self._preview_polling:
            return
        self._preview_polling = True
        self.after(80, self._poll_preview_queue)

    def _stop_preview_polling(self) -> None:
        self._preview_polling = False

    def _poll_preview_queue(self) -> None:
        if not self._preview_polling:
            return
        batch: List[Dict[str, Any]] = []
        while self._preview_queue and len(batch) < 200:
            batch.append(self._preview_queue.popleft())
        if batch:
            self._append_preview_batch(batch)
        self.after(80, self._poll_preview_queue)

    def _stream_with_preview(self, stream: Iterator[Dict[str, Any]], ui_flush_every: int = 50) -> Iterator[Dict[str, Any]]:
        buffered: List[Dict[str, Any]] = []
        for item in stream:
            buffered.append(item)
            if len(buffered) >= ui_flush_every:
                for x in buffered:
                    self._enqueue_preview(x)
                buffered.clear()
            yield item
        if buffered:
            for x in buffered:
                self._enqueue_preview(x)

    def _run_job(self, cfg: RunConfig) -> None:
        cfg.output_dir.mkdir(parents=True, exist_ok=True)

        if cfg.mode == "single":
            assert cfg.input_file is not None
            in_path = cfg.input_file
            out_path = cfg.output_file or (cfg.output_dir / f"{in_path.stem}_result.{cfg.fmt}")

            self.after(0, lambda: self._log(f"模式：单文件"))
            self.after(0, lambda: self._log(f"输入：{in_path}"))
            self.after(0, lambda: self._log(f"输出：{out_path}"))
            self.after(0, lambda: self._log(f"格式：{cfg.fmt}  流式：{cfg.stream}"))

            if cfg.stream:
                stream = self.parser.parse_log_file_stream(in_path)
                wrapped = self._stream_with_preview(stream)
                self.parser.save_results_stream(wrapped, out_path, format=cfg.fmt)
            else:
                results = self.parser.parse_log_file(in_path)
                self.parser.save_results(results, out_path, format=cfg.fmt)
                for ch in chunked(results, chunk_size=300):
                    self.after(0, lambda c=ch: self._append_preview_batch(c))

            self.after(0, lambda: self._log(f"✅ 输出完成：{out_path}"))
            return

        # batch
        assert cfg.logs_dir is not None
        files = find_log_files(cfg.logs_dir)
        self.after(0, lambda: self._log(f"模式：批量目录"))
        self.after(0, lambda: self._log(f"目录：{cfg.logs_dir}"))
        self.after(0, lambda: self._log(f"输出目录：{cfg.output_dir}"))
        self.after(0, lambda: self._log(f"找到文件数：{len(files)}"))
        self.after(0, lambda: self._log(f"格式：{cfg.fmt}  流式：{cfg.stream}"))

        if not files:
            self.after(0, lambda: messagebox.showinfo("提示", f"目录下未找到日志文件（支持：{SUPPORTED_EXTS}）"))
            return

        success = 0
        fail = 0
        total_records = 0

        for idx, in_path in enumerate(files, 1):
            out_path = cfg.output_dir / f"{in_path.stem}_result.{cfg.fmt}"
            self.after(0, lambda p=in_path, i=idx, n=len(files): self._log(f"[{i}/{n}] {p.name}"))
            try:
                if cfg.stream:
                    stream = self.parser.parse_log_file_stream(in_path)
                    wrapped = self._stream_with_preview(stream)
                    self.parser.save_results_stream(wrapped, out_path, format=cfg.fmt)
                    success += 1
                else:
                    results = self.parser.parse_log_file(in_path)
                    self.parser.save_results(results, out_path, format=cfg.fmt)
                    total_records += len(results)
                    success += 1
                    # 批量模式默认仅预览第一个文件，避免混杂
                    if idx == 1 and results:
                        for ch in chunked(results, chunk_size=300):
                            self.after(0, lambda c=ch: self._append_preview_batch(c))

                self.after(0, lambda p=out_path: self._log(f"  ✅ 输出：{p.name}"))
            except Exception as e:
                fail += 1
                self.after(0, lambda ee=e: self._log(f"  ❌ 失败：{ee}"))

        self.after(0, lambda: self._log("-" * 80))
        self.after(0, lambda: self._log(f"完成：成功 {success}，失败 {fail}"))
        if not cfg.stream:
            self.after(0, lambda: self._log(f"总记录数：{total_records}"))


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

