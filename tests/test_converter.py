from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from markitdown_desktop.converter import (
    ConversionEngine,
    ConversionJob,
    build_jobs,
    default_output_path,
    extract_markdown,
    should_use_research_pdf_engine,
    convert_job,
)


class ConverterTests(unittest.TestCase):
    def test_default_output_path_replaces_suffix(self) -> None:
        self.assertEqual(default_output_path(Path("paper.pdf")), Path("paper.md"))

    def test_build_jobs_uses_source_folder_by_default(self) -> None:
        jobs = build_jobs([Path("docs/paper.pdf")], None)
        self.assertEqual(jobs[0].output_path, Path("docs/paper.md"))
        self.assertEqual(jobs[0].engine, ConversionEngine.GENERAL)

    def test_build_jobs_uses_selected_output_folder(self) -> None:
        jobs = build_jobs(
            [Path("docs/slides.pptx")],
            Path("out"),
            ConversionEngine.RESEARCH_PAPER,
        )
        self.assertEqual(jobs[0].output_path, Path("out/slides.md"))
        self.assertEqual(jobs[0].engine, ConversionEngine.RESEARCH_PAPER)

    def test_extract_markdown_accepts_current_and_older_result_fields(self) -> None:
        self.assertEqual(extract_markdown(SimpleNamespace(markdown="new")), "new")
        self.assertEqual(extract_markdown(SimpleNamespace(text_content="old")), "old")

    def test_research_pdf_engine_only_applies_to_pdfs(self) -> None:
        pdf_job = ConversionJob(
            Path("paper.pdf"),
            Path("paper.md"),
            ConversionEngine.RESEARCH_PAPER,
        )
        pptx_job = ConversionJob(
            Path("slides.pptx"),
            Path("slides.md"),
            ConversionEngine.RESEARCH_PAPER,
        )
        self.assertTrue(should_use_research_pdf_engine(pdf_job))
        self.assertFalse(should_use_research_pdf_engine(pptx_job))

    def test_convert_job_uses_research_pdf_engine_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")

            with patch(
                "markitdown_desktop.converter.convert_research_pdf",
                return_value="paper markdown",
            ):
                result = convert_job(
                    ConversionJob(
                        input_path,
                        output_path,
                        ConversionEngine.RESEARCH_PAPER,
                    )
                )

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "paper markdown")
            self.assertIn("Docling", result.message)

    def test_convert_job_falls_back_to_markitdown_for_non_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "slides.pptx"
            output_path = Path(temp_dir) / "slides.md"
            input_path.write_bytes(b"pptx test")

            with patch(
                "markitdown_desktop.converter.convert_with_markitdown",
                return_value="slides markdown",
            ):
                result = convert_job(
                    ConversionJob(
                        input_path,
                        output_path,
                        ConversionEngine.RESEARCH_PAPER,
                    )
                )

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "slides markdown")
            self.assertIn("MarkItDown", result.message)


if __name__ == "__main__":
    unittest.main()
