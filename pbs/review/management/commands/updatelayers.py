import os
import re
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from pbs.review.models import Layer


class Command(BaseCommand):
    help = "Download updated KB layers and update local layer timestamps."

    API_BASE_URL = "https://kaartdijin-boodja.dbca.wa.gov.au/api/catalogue/layers/submissions2/"
    DOWNLOAD_URL_TEMPLATE = "https://kaartdijin-boodja.dbca.wa.gov.au/api/catalogue/layers/submissions/{submission_id}/file/"

    def add_arguments(self, parser_obj):
        parser_obj.add_argument(
            "--download-dir",
            default=getattr(settings, "BPP_FILE_DOWNLOAD_PATH", "/mnt/fmsb/master_burn_planning_bpp_pbs"),
            help="Directory where downloaded layer payloads are stored.",
        )
        parser_obj.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without downloading or saving.",
        )
        parser_obj.add_argument(
            "--no-kb-auth",
            action="store_true",
            help="Do not use KB_USER/KB_PASSWORD for KB API and download requests.",
        )

    def handle(self, *args, **options):
        download_dir = options["download_dir"]
        dry_run = options["dry_run"]
        no_kb_auth = options["no_kb_auth"]

        timeout = getattr(settings, "REQUEST_TIMEOUT", 60)
        auth = None
        if not no_kb_auth:
            kb_user = (getattr(settings, "KB_USER", "") or "").strip()
            kb_password = (getattr(settings, "KB_PASSWORD", "") or "").strip()
            if not kb_user or not kb_password:
                raise CommandError("KB_USER and KB_PASSWORD must be set in settings, or use --no-kb-auth.")
            auth = (kb_user, kb_password)

        layers = Layer.objects.filter(active=True).order_by("name")
        if not layers.exists():
            self.stdout.write("No active local layers found.")
            return

        if not dry_run:
            self._ensure_download_dir(download_dir)

        updated_count = 0
        skipped_count = 0
        unchanged_count = 0

        for layer in layers:
            if not layer.catalogue_entry_id:
                skipped_count += 1
                self.stderr.write("Skipping layer '{}' with no catalogue_entry_id".format(layer.name))
                continue

            api_url = self._build_shortened_api_url(layer.catalogue_entry_id)

            try:
                submission = self._get_latest_submission(api_url, timeout, auth)
            except Exception as exc:
                raise CommandError("Failed to check latest submission for layer '{}': {}".format(layer.name, exc))

            submission_id = submission.get("id")
            if not submission_id:
                skipped_count += 1
                self.stderr.write("Skipping layer '{}' because submission id is missing.".format(layer.name))
                continue

            submitted_at_raw = submission.get("submitted_at")
            if not submitted_at_raw:
                skipped_count += 1
                self.stderr.write(
                    "Skipping layer '{}' because latest submission has no submitted_at.".format(layer.name)
                )
                continue

            submitted_at = self._parse_submitted_at(submitted_at_raw)

            if layer.modified_at and submitted_at <= layer.modified_at:
                unchanged_count += 1
                self.stdout.write(
                    "No update for '{}' (submitted_at={} <= modified_at={})"
                    .format(layer.name, submitted_at.isoformat(), layer.modified_at.isoformat())
                )
                continue

            download_url = self._build_download_url(submission_id)

            source_file = submission.get("file") or "submission"
            output_filename = os.path.basename(source_file)
            if not output_filename:
                safe_layer_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", layer.name).strip("_") or "layer"
                output_filename = "{}_{}.bin".format(safe_layer_name, submission_id)

            output_path = os.path.join(download_dir, output_filename)

            if dry_run:
                self.stdout.write(
                    "Would download '{}' from {} and set modified_at={}"
                    .format(layer.name, download_url, submitted_at.isoformat())
                )
                if output_path.lower().endswith(".7z"):
                    self.stdout.write(
                        "Dry-run: downloaded 7z archive for '{}' would be extracted to '{}'"
                        .format(layer.name, download_dir)
                    )
                continue

            try:
                self._download_file(download_url, output_path, timeout, auth)
                if output_path.lower().endswith(".7z"):
                    self._extract_7z_file(output_path, download_dir)
                    self.stdout.write("Extraction complete for '{}': {}".format(layer.name, download_dir))

                Layer.objects.filter(pk=layer.pk).update(modified_at=submitted_at)

                updated_count += 1
                self.stdout.write(
                    "Updated '{}' (saved to {}, modified_at={})"
                    .format(layer.name, output_path, submitted_at.isoformat())
                )
            except Exception as exc:
                raise CommandError(
                    "Failed to update layer '{}': {}".format(layer.name, exc)
                )

        self.stdout.write(
            "Layer update complete: {} updated, {} unchanged, {} skipped."
            .format(updated_count, unchanged_count, skipped_count)
        )

    def _build_shortened_api_url(self, catalogue_entry_id):
        query = {
            "catalogue_entry_id": catalogue_entry_id,
            "order[0][column]": 0,
            "order[0][dir]": "desc",
            "start": 0,
            "length": 1,
        }
        return "{}?{}".format(self.API_BASE_URL, urlencode(query))

    def _get_latest_submission(self, api_url, timeout, auth):
        response = requests.get(api_url, timeout=timeout, verify=False, auth=auth)
        response.raise_for_status()

        payload = response.json()
        rows = payload.get("data") or []
        if not rows:
            raise CommandError("Submissions API returned no rows in 'data'.")

        return rows[0]

    def _build_download_url(self, submission_id):
        return self.DOWNLOAD_URL_TEMPLATE.format(submission_id=submission_id)

    def _parse_submitted_at(self, submitted_at_raw):
        try:
            submitted_at = datetime.fromisoformat(submitted_at_raw)
        except ValueError as exc:
            raise CommandError(
                "Unable to parse submitted_at '{}': {}".format(submitted_at_raw, exc)
            )

        if timezone.is_naive(submitted_at):
            submitted_at = timezone.make_aware(submitted_at, timezone.get_current_timezone())

        return submitted_at

    def _ensure_download_dir(self, download_dir):
        try:
            os.makedirs(download_dir, exist_ok=True)
        except PermissionError as exc:
            raise CommandError(
                "Cannot create download directory '{}': {}. "
                "Use --download-dir with a writable path, for example '/tmp/pbs_downloads'.".format(download_dir, exc)
            )
        except OSError as exc:
            raise CommandError("Failed to prepare download directory '{}': {}".format(download_dir, exc))

        if not os.path.isdir(download_dir):
            raise CommandError("Download path '{}' is not a directory.".format(download_dir))

        if not os.access(download_dir, os.W_OK | os.X_OK):
            raise CommandError(
                "Download directory '{}' is not writable. "
                "Use --download-dir with a writable path, for example '/tmp/pbs_downloads'.".format(download_dir)
            )

    def _download_file(self, url, output_path, timeout, auth):
        try:
            self.stderr.write("download url '{}' ".format(url))
            response = requests.get(url, timeout=timeout, verify=False, stream=True, auth=auth)
            response.raise_for_status()

            with open(output_path, "wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)
        except PermissionError as exc:
            raise CommandError("Cannot write downloaded file '{}': {}".format(output_path, exc))
        except Exception as exc:
            raise CommandError("Failed to download file from '{}': {}".format(url, exc))

    def _extract_7z_file(self, archive_path, destination_dir):
        seven_zip_bin = shutil.which("7z") or shutil.which("7za")
        if not seven_zip_bin:
            raise CommandError(
                "Downloaded file is a .7z archive, but no '7z' executable was found on PATH. "
                "Install p7zip and run the command again."
            )

        cmd = [seven_zip_bin, "x", "-y", "-o{}".format(destination_dir), archive_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            details = stderr or stdout or str(exc)
            raise CommandError("Failed to extract archive '{}': {}".format(archive_path, details))
