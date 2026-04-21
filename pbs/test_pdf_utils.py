import tempfile
import os

from django.test import SimpleTestCase
from django.test.utils import override_settings

from pbs.utils.pdf import (
    copy_pdflatex_artifacts,
    get_latex_file_references,
    get_missing_latex_file_references,
    get_missing_latex_file_references_from_log,
)


class PdfUtilityTests(SimpleTestCase):
    @override_settings(BASE_DIR='/tmp/pbs-test-base-dir')
    def test_copy_pdflatex_artifacts_updates_existing_log_dir(self):
        with tempfile.TemporaryDirectory() as base_dir:
            with tempfile.TemporaryDirectory() as source_dir:
                with tempfile.TemporaryDirectory() as preexisting_base_dir:
                    old_base_dir = '/tmp/pbs-test-base-dir'
                    target_dir = os.path.join(
                        old_base_dir,
                        'logs',
                        'pdf',
                        'ALB_091',
                        'archive-run',
                    )

                    os.makedirs(target_dir)
                    with open(os.path.join(target_dir, 'pfp.log'), 'w') as handle:
                        handle.write('old log content')

                    with open(os.path.join(source_dir, 'pfp.log'), 'w') as handle:
                        handle.write('new log content')

                    with open(os.path.join(source_dir, 'pfp.aux'), 'w') as handle:
                        handle.write('aux data')

                    with override_settings(BASE_DIR=preexisting_base_dir):
                        copied_log = copy_pdflatex_artifacts(
                            source_dir,
                            'ALB_091',
                            'archive-run.pdf',
                            'pfp.log',
                        )

                    self.assertEqual(
                        copied_log,
                        os.path.join(preexisting_base_dir, 'logs', 'pdf', 'ALB_091', 'archive-run', 'pfp.log')
                    )
                    with open(copied_log, 'r') as handle:
                        self.assertEqual(handle.read(), 'new log content')
                    self.assertTrue(
                        os.path.exists(
                            os.path.join(preexisting_base_dir, 'logs', 'pdf', 'ALB_091', 'archive-run', 'pfp.aux')
                        )
                    )

    def test_get_latex_file_references_extracts_distinct_paths(self):
        rendered_tex = r"""
        \includegraphics[scale=0.6]{/tmp/static/logo.png}
        \includepdf[pages=-]{/tmp/uploads/burn-map.pdf}
        \includepdf[pages=-]{/tmp/uploads/burn-map.pdf}
        """

        self.assertEqual(
            get_latex_file_references(rendered_tex),
            ['/tmp/static/logo.png', '/tmp/uploads/burn-map.pdf']
        )

    def test_get_latex_file_references_handles_nested_braces_and_multiline_options(self):
        rendered_tex = r"""
        \includegraphics{{/tmp/static/logo.png}}
        \includepdf[pages=-,
        scale=1,fitpaper=true]{/tmp/uploads/burn-map.pdf}
        """

        self.assertEqual(
            get_latex_file_references(rendered_tex),
            ['/tmp/static/logo.png', '/tmp/uploads/burn-map.pdf']
        )

    def test_get_missing_latex_file_references_returns_only_missing_paths(self):
        with tempfile.NamedTemporaryFile() as existing_file:
            rendered_tex = r"""
            \includegraphics{{{0}}}
            \includepdf{{/tmp/does-not-exist.pdf}}
            """.format(existing_file.name)

            self.assertEqual(
                get_missing_latex_file_references(rendered_tex),
                ['/tmp/does-not-exist.pdf']
            )

    def test_get_missing_latex_file_references_from_log_handles_wrapped_paths(self):
        log_output = """
Including PDF:/data/data/projects/pbs_django_3/media/uploads/2025_2026/2025_202
6_ALB_091_Operations_Map_2025-11-20.pdf with dimensions 0 0

/tmp/pbs_pdflatexflxnbuay/pfp.tex:1644: Package pdfpages Error: Cannot find fil
e `/data/data/projects/pbs_django_3/media/uploads/2025_2026/2025_2026_ALB_091_O
perations_Map_2025-11-20.pdf'.
        """

        self.assertEqual(
            get_missing_latex_file_references_from_log(log_output),
            ['/data/data/projects/pbs_django_3/media/uploads/2025_2026/2025_2026_ALB_091_Operations_Map_2025-11-20.pdf']
        )