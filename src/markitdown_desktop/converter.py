from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ConversionEngine(str, Enum):
    GENERAL = "general"
    RESEARCH_PAPER = "research-paper"

    @property
    def label(self) -> str:
        if self is ConversionEngine.RESEARCH_PAPER:
            return "Research paper PDFs"
        return "General documents"


@dataclass(frozen=True)
class ConversionJob:
    input_path: Path
    output_path: Path
    engine: ConversionEngine = ConversionEngine.GENERAL


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
    engine: ConversionEngine = ConversionEngine.GENERAL,
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


def convert_research_pdf(input_path: Path) -> str:
    from docling.document_converter import DocumentConverter

    result = DocumentConverter().convert(str(input_path))
    markdown = result.document.export_to_markdown()
    if isinstance(markdown, str):
        return markdown
    raise TypeError("Docling returned an unsupported Markdown result.")


def should_use_research_pdf_engine(job: ConversionJob) -> bool:
    return (
        job.engine is ConversionEngine.RESEARCH_PAPER
        and job.input_path.suffix.lower() == ".pdf"
    )


def convert_job(job: ConversionJob) -> ConversionResult:
    try:
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        if should_use_research_pdf_engine(job):
            markdown = convert_research_pdf(job.input_path)
            engine_name = "Docling"
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
