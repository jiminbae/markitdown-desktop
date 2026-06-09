from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from markitdown_desktop.converter import (
    ConversionEngine,
    ConversionJob,
    build_jobs,
    convert_job,
    default_output_path,
    extract_markdown,
    looks_like_broken_pdf_markdown,
)


class ConverterTests(unittest.TestCase):
    def test_default_output_path_replaces_suffix(self) -> None:
        self.assertEqual(default_output_path(Path("paper.pdf")), Path("paper.md"))

    def test_build_jobs_uses_source_folder_by_default(self) -> None:
        jobs = build_jobs([Path("docs/paper.pdf")], None)
        self.assertEqual(jobs[0].output_path, Path("docs/paper.md"))
        self.assertEqual(jobs[0].engine, ConversionEngine.AUTO)

    def test_build_jobs_uses_selected_output_folder(self) -> None:
        jobs = build_jobs([Path("docs/slides.pptx")], Path("out"), ConversionEngine.DOCLING)
        self.assertEqual(jobs[0].output_path, Path("out/slides.md"))
        self.assertEqual(jobs[0].engine, ConversionEngine.DOCLING)

    def test_extract_markdown_accepts_current_and_older_result_fields(self) -> None:
        self.assertEqual(extract_markdown(SimpleNamespace(markdown="new")), "new")
        self.assertEqual(extract_markdown(SimpleNamespace(text_content="old")), "old")

    def test_pdf_quality_heuristic_detects_common_markitdown_failures(self) -> None:
        broken = "\n".join(
            ["| --- | --- |"] * 60
            + ["word" * 30] * 8
            + ["(cid:32)"] * 5
        )
        clean = "# Title\n\nThis is a readable paragraph with normal spacing."
        self.assertTrue(looks_like_broken_pdf_markdown(broken))
        self.assertFalse(looks_like_broken_pdf_markdown(clean))

    def test_auto_uses_markitdown_for_clean_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value="# Clean paper\n\nReadable text.",
                ) as markitdown,
                patch("markitdown_desktop.converter.convert_with_docling") as docling,
            ):
                result = convert_job(ConversionJob(input_path, output_path))

            expected = "# Clean paper\n\nReadable text."
            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), expected)
            self.assertIn("Auto: MarkItDown", result.message)
            markitdown.assert_called_once()
            docling.assert_not_called()

    def test_auto_retries_broken_pdf_with_docling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")
            broken = "\n".join(["| --- | --- |"] * 60 + ["(cid:32)"] * 5)

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value=broken,
                ),
                patch(
                    "markitdown_desktop.converter.convert_with_docling",
                    return_value="docling markdown",
                ) as docling,
            ):
                result = convert_job(ConversionJob(input_path, output_path))

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "docling markdown")
            self.assertIn("Auto: Docling fallback", result.message)
            docling.assert_called_once()

    def test_auto_keeps_markitdown_when_docling_fallback_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")
            broken = "\n".join(["| --- | --- |"] * 60 + ["(cid:32)"] * 5)

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value=broken,
                ),
                patch(
                    "markitdown_desktop.converter.convert_with_docling",
                    side_effect=RuntimeError("Input document paper.pdf is not valid."),
                ) as docling,
            ):
                result = convert_job(ConversionJob(input_path, output_path))

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), broken)
            self.assertIn("Auto: MarkItDown", result.message)
            self.assertIn("Docling fallback failed", result.message)
            docling.assert_called_once()

    def test_auto_uses_markitdown_for_non_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "slides.pptx"
            output_path = Path(temp_dir) / "slides.md"
            input_path.write_bytes(b"pptx test")

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value="slides markdown",
                ),
                patch("markitdown_desktop.converter.convert_with_docling") as docling,
            ):
                result = convert_job(ConversionJob(input_path, output_path))

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "slides markdown")
            self.assertIn("Auto: MarkItDown", result.message)
            docling.assert_not_called()

    def test_markitdown_mode_always_uses_markitdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value="markitdown markdown",
                ) as markitdown,
                patch("markitdown_desktop.converter.convert_with_docling") as docling,
            ):
                result = convert_job(
                    ConversionJob(input_path, output_path, ConversionEngine.MARKITDOWN)
                )

            self.assertTrue(result.succeeded)
            self.assertIn("MarkItDown", result.message)
            markitdown.assert_called_once()
            docling.assert_not_called()

    def test_docling_mode_falls_back_to_markitdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "slides.pptx"
            output_path = Path(temp_dir) / "slides.md"
            input_path.write_bytes(b"pptx test")

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_docling",
                    side_effect=RuntimeError("unsupported"),
                ),
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value="slides markdown",
                ),
            ):
                result = convert_job(
                    ConversionJob(input_path, output_path, ConversionEngine.DOCLING)
                )

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "slides markdown")
            self.assertIn("Docling fallback: MarkItDown", result.message)


if __name__ == "__main__":
    unittest.main()
