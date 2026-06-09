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
    best_page_candidate,
    better_markdown,
    cleanup_pdf_text,
    is_pdf_visual_noise_line,
    looks_like_broken_pdf_markdown,
    remove_embedded_pdf_line_numbers,
    page_candidate_penalty,
    strip_pdf_line_number,
    text_from_pdf_words,
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

    def test_strip_pdf_line_number_removes_neurips_line_numbers(self) -> None:
        self.assertEqual(
            strip_pdf_line_number("42 This is paper text"),
            "This is paper text",
        )
        self.assertEqual(strip_pdf_line_number("Figure 1: Caption"), "Figure 1: Caption")
        self.assertEqual(strip_pdf_line_number("Readable sentence. 68 2"), "Readable sentence.")

    def test_text_from_pdf_words_groups_by_y_then_x(self) -> None:
        words = [
            {"text": "right", "x0": 60, "top": 20},
            {"text": "1", "x0": 0, "top": 10},
            {"text": "left", "x0": 20, "top": 10},
            {"text": "line", "x0": 55, "top": 10},
        ]
        self.assertEqual(text_from_pdf_words(words), "left line\nright")

    def test_best_page_candidate_avoids_embedded_line_number_fragments(self) -> None:
        mixed = "Spiking Transformers merge the e 2 sentational power"
        clean = "Spiking Transformers merge the representational power"
        self.assertGreater(page_candidate_penalty(mixed), page_candidate_penalty(clean))
        self.assertEqual(best_page_candidate([mixed, clean]), clean)

    def test_page_candidate_penalty_discourages_visual_noise_lines(self) -> None:
        noisy = "Readable text\nP o s it i ve P o s i ti v e N e g a ti v e"
        clean = "Readable text\nMore readable paper text"
        self.assertGreater(page_candidate_penalty(noisy), page_candidate_penalty(clean))

    def test_remove_embedded_pdf_line_numbers_repairs_neurips_line_numbers(self) -> None:
        self.assertEqual(
            remove_embedded_pdf_line_numbers(
                "repre1 sentational power and high2 performance persists 3 versus"
            ),
            "representational power and high performance persists versus",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("of17 fering readable text"),
            "offering readable text",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("activations, 4 we reveal SCA) 8 paradigm"),
            "activations, we reveal SCA) paradigm",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("which equals 1 for v and 0 otherwise"),
            "which equals 1 for v and 0 otherwise",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("spiking 40 neurons and otherwise 79 equals"),
            "spiking neurons and otherwise equals",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("Fig. 5 and 10 show CIFAR100 with OSTrack256"),
            "Fig. 5 and 10 show CIFAR100 with OSTrack256",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("Table 3 shows Eq. 10 and Theorem 3.5"),
            "Table 3 shows Eq. 10 and Theorem 3.5",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("Figure 8 explains Fig.8(a) and ImageNet-1K"),
            "Figure 8 explains Fig.8(a) and ImageNet-1K",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("com ponents Diverg ing informa tion improve ments"),
            "components Diverging information improvements",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("In this work, we show in the paper"),
            "In this work, we show in the paper",
        )
        self.assertEqual(
            remove_embedded_pdf_line_numbers("in10 formation remains useful"),
            "information remains useful",
        )

    def test_cleanup_pdf_text_drops_visual_noise_and_footer_lines(self) -> None:
        text = "\n".join(
            [
                "This is readable paper text.",
                "P o s it i ve P o s i ti v e N e g a ti v e",
                "Figure 3: Useful caption",
                "Submittedto40thConferenceonNeuralInformationProcessingSystems(NeurIPS2026). Donotdistribute.",
                "More readable paper text.",
            ]
        )
        cleaned = cleanup_pdf_text(text)
        self.assertIn("This is readable paper text.", cleaned)
        self.assertIn("Figure 3: Useful caption", cleaned)
        self.assertIn("More readable paper text.", cleaned)
        self.assertNotIn("P o s it", cleaned)
        self.assertNotIn("Donotdistribute", cleaned)

    def test_cleanup_pdf_text_trims_visual_noise_after_caption(self) -> None:
        text = "Figure 1: The description of spectral bias. w i t h S N N c h a r a c t e r s"
        self.assertEqual(
            cleanup_pdf_text(text),
            "Figure 1: The description of spectral bias.",
        )

    def test_is_pdf_visual_noise_line_keeps_captions(self) -> None:
        self.assertTrue(is_pdf_visual_noise_line("P o s it i ve P o s i ti v e N e g a ti v e"))
        self.assertFalse(is_pdf_visual_noise_line("Figure 3: Useful caption"))

    def test_cleanup_pdf_text_repairs_common_line_breaks(self) -> None:
        text = "high-\nfrequency\ncomponents\n\nNext paragraph"
        self.assertEqual(
            cleanup_pdf_text(text),
            "highfrequency components\n\nNext paragraph",
        )

    def test_better_markdown_prefers_lower_penalty_candidate(self) -> None:
        broken = "\n".join(["| --- | --- |"] * 60 + ["(cid:32)"] * 5)
        repaired = "# Title\n\nThis is readable paper text."
        self.assertTrue(better_markdown(repaired, broken))

    def test_auto_uses_pdf_layout_repair_before_docling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "paper.pdf"
            output_path = Path(temp_dir) / "paper.md"
            input_path.write_bytes(b"%PDF test")
            broken = "\n".join(["| --- | --- |"] * 60 + ["(cid:32)"] * 5)
            repaired = "# Repaired paper\n\nReadable text."

            with (
                patch(
                    "markitdown_desktop.converter.convert_with_markitdown",
                    return_value=broken,
                ),
                patch(
                    "markitdown_desktop.converter.convert_with_pdf_layout_repair",
                    return_value=repaired,
                ) as repair,
                patch("markitdown_desktop.converter.convert_with_docling") as docling,
            ):
                result = convert_job(ConversionJob(input_path, output_path))

            self.assertTrue(result.succeeded)
            self.assertEqual(output_path.read_text(encoding="utf-8"), repaired)
            self.assertIn("Auto: PDF layout repair", result.message)
            repair.assert_called_once()
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
                    "markitdown_desktop.converter.convert_with_pdf_layout_repair",
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
                    "markitdown_desktop.converter.convert_with_pdf_layout_repair",
                    side_effect=RuntimeError("repair failed"),
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
