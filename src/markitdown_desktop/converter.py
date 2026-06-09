from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ConversionEngine(str, Enum):
    AUTO = "auto"
    MARKITDOWN = "markitdown"
    DOCLING = "docling"

    @property
    def label(self) -> str:
        if self is ConversionEngine.DOCLING:
            return "Docling"
        if self is ConversionEngine.MARKITDOWN:
            return "MarkItDown"
        return "Auto"


@dataclass(frozen=True)
class ConversionJob:
    input_path: Path
    output_path: Path
    engine: ConversionEngine = ConversionEngine.AUTO


@dataclass(frozen=True)
class ConversionResult:
    job: ConversionJob
    succeeded: bool
    message: str


def default_output_path(input_path: Path) -> Path:
    return input_path.with_suffix(".md")


def build_jobs(
    input_paths: list[Path],
    output_directory: Path | None,
    engine: ConversionEngine = ConversionEngine.AUTO,
) -> list[ConversionJob]:
    jobs: list[ConversionJob] = []
    for input_path in input_paths:
        if output_directory is None:
            output_path = default_output_path(input_path)
        else:
            output_path = output_directory / f"{input_path.stem}.md"
        jobs.append(
            ConversionJob(input_path=input_path, output_path=output_path, engine=engine)
        )
    return jobs


def extract_markdown(result: object) -> str:
    for attribute in ("markdown", "text_content"):
        value = getattr(result, attribute, None)
        if isinstance(value, str):
            return value
    raise TypeError("MarkItDown returned a result without markdown text content.")


def convert_with_markitdown(input_path: Path) -> str:
    from markitdown import MarkItDown

    result = MarkItDown().convert(str(input_path))
    return extract_markdown(result)


def convert_with_docling(input_path: Path) -> str:
    from docling.document_converter import DocumentConverter

    result = DocumentConverter().convert(str(input_path))
    markdown = result.document.export_to_markdown()
    if isinstance(markdown, str):
        return markdown
    raise TypeError("Docling returned an unsupported Markdown result.")


def is_pdf(input_path: Path) -> bool:
    return input_path.suffix.lower() == ".pdf"


def looks_like_broken_pdf_markdown(markdown: str) -> bool:
    lines = markdown.splitlines()
    if not markdown.strip():
        return True

    line_count = max(len(lines), 1)
    pipe_lines = sum(1 for line in lines if "|" in line)
    long_no_space_lines = sum(1 for line in lines if len(line) > 60 and " " not in line)

    return any(
        (
            "\x00" in markdown,
            markdown.count("(cid:") >= 5,
            long_no_space_lines >= 8,
            pipe_lines >= 50 and pipe_lines / line_count > 0.20,
        )
    )


def convert_auto(job: ConversionJob) -> tuple[str, str]:
    markdown = convert_with_markitdown(job.input_path)
    if is_pdf(job.input_path) and looks_like_broken_pdf_markdown(markdown):
        return convert_with_docling(job.input_path), "Auto: Docling fallback"
    return markdown, "Auto: MarkItDown"


def convert_docling_first(job: ConversionJob) -> tuple[str, str]:
    try:
        return convert_with_docling(job.input_path), "Docling"
    except Exception as docling_error:
        try:
            markdown = convert_with_markitdown(job.input_path)
        except Exception:
            raise docling_error
        return markdown, "Docling fallback: MarkItDown"


def convert_job(job: ConversionJob) -> ConversionResult:
    try:
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        if job.engine is ConversionEngine.AUTO:
            markdown, engine_name = convert_auto(job)
        elif job.engine is ConversionEngine.DOCLING:
            markdown, engine_name = convert_docling_first(job)
        else:
            markdown = convert_with_markitdown(job.input_path)
            engine_name = "MarkItDown"
        job.output_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        return ConversionResult(job=job, succeeded=False, message=str(exc))

    return ConversionResult(
        job=job,
        succeeded=True,
        message=f"Wrote {job.output_path} with {engine_name}",
    )
