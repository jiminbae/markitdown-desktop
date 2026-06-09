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
    embedded_line_number_penalty = len(
        re.findall(r"\b[a-z]{1,4}\s+\d{1,4}\s+[a-z]{3,}", markdown)
    )
    dangling_fragment_penalty = len(re.findall(r"\b[a-z]\s+[a-z]{5,}", markdown))
    visual_noise_lines = sum(1 for line in lines if is_pdf_visual_noise_line(line))

    return sum(
        (
            markdown.count("\x00") * 20,
            markdown.count("(cid:") * 25,
            long_no_space_lines * 8,
            table_ratio_penalty,
            embedded_line_number_penalty * 12,
            dangling_fragment_penalty * 3,
            visual_noise_lines * 15,
        )
    )


def looks_like_broken_pdf_markdown(markdown: str) -> bool:
    return markdown_quality_penalty(markdown) >= 100


COMMON_PDF_LINE_SPLIT_PREFIXES = {
    "archi",
    "cal",
    "cate",
    "com",
    "compo",
    "consis",
    "dynami",
    "effi",
    "forma",
    "improv",
    "improve",
    "diverg",
    "in",
    "informa",
    "informatio",
    "mech",
    "opera",
    "paramet",
    "repre",
    "seman",
    "sent",
    "tec",
    "train",
}

VISUAL_NOISE_RE = re.compile(r"(?:\b[A-Za-z]\b\s+){6,}\b[A-Za-z]\b")
FOOTER_RE = re.compile(r"submitted\s*to.*donotdistribute", re.IGNORECASE)


def should_join_pdf_line_number_split(left: str, right: str) -> bool:
    lower_left = left.lower()
    lower_right = right.lower()
    if lower_left in COMMON_PDF_LINE_SPLIT_PREFIXES:
        return True
    if lower_left.endswith(("s", "ed", "ing")):
        return False
    if lower_left in {"high", "low", "global", "local", "model", "visual"}:
        return False
    return len(lower_left) <= 3 and len(lower_right) >= 5


def remove_embedded_pdf_line_numbers(line: str) -> str:
    def replace_split(match: re.Match[str]) -> str:
        left, _number, right = match.groups()
        separator = "" if should_join_pdf_line_number_split(left, right) else " "
        return f"{left}{separator}{right}"

    line = re.sub(r"\b([A-Za-z]{2,})(\d{1,4})\s+([a-z]{3,})\b", replace_split, line)
    line = re.sub(r"\b([A-Za-z]{3,})(\d{1,4})\b", r"\1", line)
    line = re.sub(r"(?<=[,.;:)\]])\s+[1-9]\d{0,3}\s+(?=[a-z])", " ", line)
    line = re.sub(r"(?<=[A-Za-z\]\)])\s+[2-9]\d{0,3}\s+(?=[a-z])", " ", line)
    line = re.sub(
        r"\b(a|an|as|for|in|of|on|that|the|to|while|with)\s+[1-9]\d{0,3}\s+(?=[a-z])",
        r"\1 ",
        line,
    )
    line = re.sub(
        r"\b([A-Za-z]{4,})\s+[1-9]\d{0,3}\s+(?=(?:and|but|or|that|the|versus|we|when|where|which|while)\b)",
        r"\1 ",
        line,
    )
    return line


def strip_pdf_line_number(line: str) -> str:
    line = re.sub(r"^\s*\d{1,4}\s+(?=\S)", "", line)
    line = re.sub(r"(?<=\D)\s+\d{1,4}\s*$", "", line)
    return line.strip()


def is_pdf_visual_noise_line(line: str) -> bool:
    compact = re.sub(r"\s+", "", line)
    if FOOTER_RE.search(compact):
        return True
    if line.lstrip().startswith(("Figure ", "Table ")):
        return False

    alpha_tokens = re.findall(r"[A-Za-z]+", line)
    if not alpha_tokens:
        return False

    single_letter_tokens = sum(1 for token in alpha_tokens if len(token) == 1)
    if VISUAL_NOISE_RE.search(line) and single_letter_tokens >= 8:
        return True
    if len(alpha_tokens) >= 12 and single_letter_tokens / len(alpha_tokens) > 0.45:
        return True
    return False


def cleanup_pdf_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            cleaned_lines.append("")
            continue
        line = strip_pdf_line_number(remove_embedded_pdf_line_numbers(line))
        if line.lstrip().startswith(("Figure ", "Table ")) and VISUAL_NOISE_RE.search(line):
            first_sentence = re.match(r"(.+?\.)\s+", line)
            if first_sentence:
                line = first_sentence.group(1)
        if line and not is_pdf_visual_noise_line(line):
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"(?<!\n)\n(?!\n)(?=[a-z0-9,(])", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def word_value(word: object, key: str, default: object = "") -> object:
    if isinstance(word, dict):
        return word.get(key, default)
    return getattr(word, key, default)


def text_from_pdf_words(words: list[object], y_tolerance: float = 3.0) -> str:
    if not words:
        return ""

    sorted_words = sorted(
        words,
        key=lambda word: (
            round(float(word_value(word, "top", 0.0)) / y_tolerance),
            float(word_value(word, "x0", 0.0)),
        ),
    )
    lines: list[list[object]] = []

    for word in sorted_words:
        top = float(word_value(word, "top", 0.0))
        if not lines:
            lines.append([word])
            continue

        line_top = float(word_value(lines[-1][0], "top", 0.0))
        if abs(top - line_top) <= y_tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])

    text_lines: list[str] = []
    for line_words in lines:
        line = " ".join(
            str(word_value(word, "text", ""))
            for word in sorted(line_words, key=lambda word: float(word_value(word, "x0", 0.0)))
        )
        line = strip_pdf_line_number(line)
        if line:
            text_lines.append(line)
    return "\n".join(text_lines)


def extract_pdfplumber_text(page: object) -> str:
    words = page.extract_words(  # type: ignore[attr-defined]
        x_tolerance=2,
        y_tolerance=4,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    return text_from_pdf_words(words)


def extract_full_width_page(page: object, top: float, bottom: float) -> str:
    return extract_pdfplumber_text(page.crop((0, top, float(page.width), bottom)))


def extract_two_column_page(page: object, top: float, bottom: float) -> str:
    width = float(page.width)
    split_x = width / 2
    gutter = width * 0.025
    left = page.crop((0, top, split_x - gutter, bottom))
    right = page.crop((split_x + gutter, top, width, bottom))
    return "\n\n".join(
        part for part in (extract_pdfplumber_text(left), extract_pdfplumber_text(right)) if part
    )


def page_candidate_penalty(text: str) -> int:
    penalty = markdown_quality_penalty(text)
    penalty += len(re.findall(r"\b[a-z]{1,4}\s+\d{1,4}\s+[a-z]{3,}", text)) * 20
    penalty += len(re.findall(r"\b(?:e|t|o|n|s|r)\s+[a-z]{5,}", text)) * 8
    return penalty


def best_page_candidate(candidates: list[str]) -> str:
    cleaned = [cleanup_pdf_text(candidate) for candidate in candidates if candidate.strip()]
    if not cleaned:
        return ""
    return min(cleaned, key=page_candidate_penalty)


def extract_pdfplumber_page(page: object, page_number: int) -> str:
    height = float(page.height)
    top = height * 0.08
    bottom = height * 0.94

    candidates = [
        extract_full_width_page(page, top, bottom),
        extract_two_column_page(page, top, bottom),
    ]

    if page_number == 0:
        for title_ratio in (0.16, 0.22, 0.28, 0.34):
            title_bottom = height * title_ratio
            candidates.append(
                "\n\n".join(
                    part
                    for part in (
                        extract_full_width_page(page, top, title_bottom),
                        extract_two_column_page(page, title_bottom, bottom),
                    )
                    if part
                )
            )

    return best_page_candidate(candidates)


def convert_with_pdf_layout_repair(input_path: Path) -> str:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(str(input_path)) as pdf:
        for page_number, page in enumerate(pdf.pages):
            page_text = extract_pdfplumber_page(page, page_number)
            if page_text:
                pages.append(page_text)

    markdown = cleanup_pdf_text("\n\n".join(pages))
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
