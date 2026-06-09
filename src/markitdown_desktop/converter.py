from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionJob:
    input_path: Path
    output_path: Path


@dataclass(frozen=True)
class ConversionResult:
    job: ConversionJob
    succeeded: bool
    message: str


def default_output_path(input_path: Path) -> Path:
    return input_path.with_suffix(".md")


def build_jobs(input_paths: list[Path], output_directory: Path | None) -> list[ConversionJob]:
    jobs: list[ConversionJob] = []
    for input_path in input_paths:
        if output_directory is None:
            output_path = default_output_path(input_path)
        else:
            output_path = output_directory / f"{input_path.stem}.md"
        jobs.append(ConversionJob(input_path=input_path, output_path=output_path))
    return jobs


def extract_markdown(result: object) -> str:
    for attribute in ("markdown", "text_content"):
        value = getattr(result, attribute, None)
        if isinstance(value, str):
            return value
    raise TypeError("MarkItDown returned a result without markdown text content.")


def convert_job(job: ConversionJob) -> ConversionResult:
    from markitdown import MarkItDown

    try:
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        result = MarkItDown().convert(str(job.input_path))
        markdown = extract_markdown(result)
        job.output_path.write_text(markdown, encoding="utf-8")
    except Exception as exc:
        return ConversionResult(job=job, succeeded=False, message=str(exc))

    return ConversionResult(job=job, succeeded=True, message=f"Wrote {job.output_path}")
