from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re


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


def markdown_quality_penalty(markdown: str) -> int:
    lines = markdown.splitlines()
    if not markdown.strip():
        return 1_000_000

    line_count = max(len(lines), 1)
    pipe_lines = sum(1 for line in lines if "|" in line)
    long_no_space_lines = sum(1 for line in lines if len(line) > 60 and " " not in line)
    table_ratio_penalty = int(200 * max(0, pipe_lines / line_count - 0.20))

    return sum(
        (
            markdown.count("\x00") * 20,
            markdown.count("(cid:") * 25,
            long_no_space_lines * 8,
            table_ratio_penalty,
        )
    )


def looks_like_broken_pdf_markdown(markdown: str) -> bool:
    return markdown_quality_penalty(markdown) >= 100


def cleanup_pdf_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)(?=[a-z0-9,(])", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdfplumber_text(page: object) -> str:
    return page.extract_text(  # type: ignore[attr-defined]
        x_tolerance=2,
        x_tolerance_ratio=0.18,
        y_tolerance=4,
        layout=False,
    ) or ""


def convert_with_pdf_layout_repair(input_path: Path) -> str:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(str(input_path)) as pdf:
        for page_number, page in enumerate(pdf.pages):
            width = float(page.width)
            height = float(page.height)
            split_x = width / 2
            top = height * 0.08
            bottom = height * 0.94
            page_parts: list[str] = []

            if page_number == 0:
                top_band_bottom = height * 0.34
                page_parts.append(
                    extract_pdfplumber_text(page.crop((0, top, width, top_band_bottom)))
                )
                top = top_band_bottom

            gutter = width * 0.025
            left = page.crop((0, top, split_x - gutter, bottom))
            right = page.crop((split_x + gutter, top, width, bottom))
            page_parts.extend((extract_pdfplumber_text(left), extract_pdfplumber_text(right)))
            pages.append(cleanup_pdf_text("\n\n".join(part for part in page_parts if part)))

    markdown = "\n\n".join(page for page in pages if page)
    if not markdown.strip():
        raise ValueError("pdfplumber did not extract any text from the PDF.")
    return markdown


def better_markdown(candidate: str, baseline: str) -> bool:
    return markdown_quality_penalty(candidate) < markdown_quality_penalty(baseline)


def convert_auto(job: ConversionJob) -> tuple[str, str]:
    markdown = convert_with_markitdown(job.input_path)
    if is_pdf(job.input_path) and looks_like_broken_pdf_markdown(markdown):
        fallback_errors: list[str] = []
        try:
            repaired = convert_with_pdf_layout_repair(job.input_path)
            if better_markdown(repaired, markdown):
                return repaired, "Auto: PDF layout repair"
            fallback_errors.append("PDF layout repair was not better")
        except Exception as exc:
            fallback_errors.append(f"PDF layout repair failed: {exc}")

        try:
            return convert_with_docling(job.input_path), "Auto: Docling fallback"
        except Exception as exc:
            fallback_errors.append(f"Docling fallback failed: {exc}")
            return markdown, "Auto: MarkItDown; " + "; ".join(fallback_errors)
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
