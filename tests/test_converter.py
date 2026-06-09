from pathlib import Path
from types import SimpleNamespace
import unittest

from markitdown_desktop.converter import build_jobs, default_output_path, extract_markdown


class ConverterTests(unittest.TestCase):
    def test_default_output_path_replaces_suffix(self) -> None:
        self.assertEqual(default_output_path(Path("paper.pdf")), Path("paper.md"))

    def test_build_jobs_uses_source_folder_by_default(self) -> None:
        jobs = build_jobs([Path("docs/paper.pdf")], None)
        self.assertEqual(jobs[0].output_path, Path("docs/paper.md"))

    def test_build_jobs_uses_selected_output_folder(self) -> None:
        jobs = build_jobs([Path("docs/slides.pptx")], Path("out"))
        self.assertEqual(jobs[0].output_path, Path("out/slides.md"))

    def test_extract_markdown_accepts_current_and_older_result_fields(self) -> None:
        self.assertEqual(extract_markdown(SimpleNamespace(markdown="new")), "new")
        self.assertEqual(extract_markdown(SimpleNamespace(text_content="old")), "old")


if __name__ == "__main__":
    unittest.main()
