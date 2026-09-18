import configparser
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import bidsify


CONFIG = """[task_restingtask]
keywords = rest
description = Eyes closed.

[run_1]
keywords = block1
description = First run.

[DATASET_DESCRIPTION]
Name = ExampleDataset
Authors = Alice, Bob
"""


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        previous_directory = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous_directory)

        self.input_path = self.root / "raw recordings"
        self.input_path.mkdir()
        self.config_file = self.input_path / "bids_configurator.txt"
        self.config_file.write_text(CONFIG, encoding="utf-8")
        self.output_path = self.root / "converted data" / "bids dataset"
        self.arguments = [
            "--input", str(self.input_path), "--output", str(self.output_path)
        ]

    def run_main(self, arguments=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = bidsify.main(self.arguments if arguments is None else arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_config_without_paths_preserves_metadata_and_rules(self):
        config = bidsify.read_config(self.config_file)

        self.assertIsInstance(config, configparser.ConfigParser)
        self.assertEqual(config.defaults(), {})
        self.assertEqual(config["DATASET_DESCRIPTION"]["Name"], "ExampleDataset")
        self.assertIn("Authors", config["DATASET_DESCRIPTION"])
        self.assertNotIn("name", config["DATASET_DESCRIPTION"])
        self.assertEqual(config["task_restingtask"]["keywords"], "rest")
        self.assertEqual(config["run_1"]["description"], "First run.")

    def test_cli_forwards_paths_containing_spaces(self):
        with patch.object(bidsify, "create_bids_structure") as convert:
            status, _, stderr = self.run_main()

        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        convert.assert_called_once()
        input_path, output_path, config = convert.call_args.args
        self.assertEqual(input_path, str(self.input_path))
        self.assertEqual(output_path, str(self.output_path))
        self.assertEqual(config["DATASET_DESCRIPTION"]["Name"], "ExampleDataset")

    def test_each_path_option_is_required(self):
        cases = [
            ([], ("--input", "--output")),
            (["--input", str(self.input_path)], ("--output",)),
            (["--output", str(self.output_path)], ("--input",)),
        ]
        for arguments, missing in cases:
            with self.subTest(arguments=arguments):
                stderr = io.StringIO()
                with redirect_stderr(stderr), patch.object(bidsify, "read_config") as read:
                    with self.assertRaises(SystemExit) as raised:
                        bidsify.main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("required", stderr.getvalue())
                for option in missing:
                    self.assertIn(option, stderr.getvalue())
                read.assert_not_called()

    def test_dataset_configuration_is_used_over_working_directory(self):
        (self.root / "bids_configurator.txt").write_text(
            CONFIG.replace("ExampleDataset", "WrongDataset"), encoding="utf-8"
        )
        with patch.object(bidsify, "create_bids_structure") as convert:
            status, _, stderr = self.run_main()

        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        convert.assert_called_once()
        self.assertEqual(
            convert.call_args.args[2]["DATASET_DESCRIPTION"]["Name"], "ExampleDataset"
        )

    def test_help_succeeds_without_configuration(self):
        self.config_file.unlink()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                bidsify.main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("--input", stdout.getvalue())
        self.assertIn("--output", stdout.getvalue())
        self.assertIn("bids_configurator.txt", stdout.getvalue())
        self.assertIn("input directory", stdout.getvalue())
        self.assertFalse(self.output_path.exists())

    def test_missing_dataset_configuration_does_not_use_working_directory(self):
        self.config_file.unlink()
        (self.root / "bids_configurator.txt").write_text(CONFIG, encoding="utf-8")
        with patch.object(bidsify, "create_bids_structure") as convert:
            status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(str(self.config_file), stderr)
        convert.assert_not_called()
        self.assertFalse(self.output_path.exists())

    def test_unreadable_configuration_fails_clearly(self):
        error = PermissionError(13, "Permission denied", str(self.config_file))
        with patch("builtins.open", side_effect=error):
            status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn("Permission denied", stderr)
        self.assertIn(str(self.config_file), stderr)
        self.assertFalse(self.output_path.exists())

    def test_malformed_configuration_fails_before_output_creation(self):
        self.config_file.write_text("not a configuration section", encoding="utf-8")

        status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(str(self.config_file), stderr)
        self.assertFalse(self.output_path.exists())

    def test_invalid_config_encoding_reports_dataset_config_path(self):
        self.config_file.write_bytes(b"\xff\xfe")

        status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(str(self.config_file), stderr)
        self.assertFalse(self.output_path.exists())

    def test_nonexistent_input_fails_before_output_creation(self):
        self.config_file.unlink()
        self.input_path.rmdir()

        with patch.object(bidsify, "read_config") as read:
            status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(f"Input path '{self.input_path}' not found", stderr)
        read.assert_not_called()
        self.assertFalse(self.output_path.exists())

    def test_input_file_is_rejected_before_output_creation(self):
        self.config_file.unlink()
        self.input_path.rmdir()
        self.input_path.write_text("not a directory", encoding="utf-8")

        with patch.object(bidsify, "read_config") as read:
            status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(f"Input path '{self.input_path}' is not a directory", stderr)
        read.assert_not_called()
        self.assertFalse(self.output_path.exists())

    def test_conversion_function_still_validates_input_directory(self):
        config = bidsify.read_config(self.config_file)
        self.config_file.unlink()
        self.input_path.rmdir()
        with self.assertRaises(FileNotFoundError):
            bidsify.create_bids_structure(self.input_path, self.output_path, config)
        self.assertFalse(self.output_path.exists())

        self.input_path.write_text("not a directory", encoding="utf-8")
        with self.assertRaises(NotADirectoryError):
            bidsify.create_bids_structure(self.input_path, self.output_path, config)
        self.assertFalse(self.output_path.exists())

    def test_output_file_is_rejected_and_preserved(self):
        self.output_path.parent.mkdir()
        self.output_path.write_text("keep this file", encoding="utf-8")

        status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn(f"Output path '{self.output_path}' is not a directory", stderr)
        self.assertEqual(self.output_path.read_text(encoding="utf-8"), "keep this file")

    def test_new_output_lists_only_participants_and_excludes_configuration(self):
        (self.input_path / "participant_002").mkdir()
        (self.input_path / "participant_001").mkdir()

        status, _, stderr = self.run_main()

        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            (self.output_path / "participants.tsv").read_text(),
            "participant_id\toriginal_folder\n"
            "sub-01\tparticipant_001\n"
            "sub-02\tparticipant_002\n",
        )

    def test_legacy_defaults_do_not_override_cli_or_leak_into_metadata(self):
        self.config_file.write_text(
            "[DEFAULT]\ninput_path = old raw\noutput_path = old bids\n"
            "InstitutionName = Example Institute\n\n" + CONFIG,
            encoding="utf-8",
        )
        self.output_path.mkdir(parents=True)
        description_file = self.output_path / "dataset_description.json"
        description_file.write_text('{"BIDSVersion": "1.8.0"}', encoding="utf-8")

        status, _, stderr = self.run_main()

        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertTrue((self.output_path / "participants.tsv").is_file())
        self.assertFalse((self.root / "old bids").exists())
        self.assertEqual(
            json.loads(description_file.read_text()),
            {
                "BIDSVersion": "1.8.0",
                "Name": "ExampleDataset",
                "Authors": ["Alice", "Bob"],
                "InstitutionName": "Example Institute",
            },
        )

    def test_conversion_failure_returns_nonzero_status(self):
        with patch.object(bidsify, "create_bids_structure", side_effect=RuntimeError("Cannot read BDF")):
            status, _, stderr = self.run_main()

        self.assertEqual(status, 1)
        self.assertIn("Cannot read BDF", stderr)

    def test_script_exit_status_and_relative_paths(self):
        script = str(Path(bidsify.__file__).resolve())
        arguments = ["--input", "raw recordings", "--output", "relative bids"]
        success = subprocess.run(
            [sys.executable, script, *arguments],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertTrue((self.root / "relative bids" / "participants.tsv").is_file())

        self.config_file.unlink()
        failure = subprocess.run(
            [sys.executable, script, *arguments],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(failure.returncode, 1)
        self.assertIn("bids_configurator.txt", failure.stderr)

    def test_script_does_not_fall_back_to_code_directory(self):
        self.config_file.unlink()
        code_directory = self.root / "code directory"
        code_directory.mkdir()
        script = code_directory / "bidsify.py"
        shutil.copyfile(bidsify.__file__, script)
        (code_directory / "bids_configurator.txt").write_text(CONFIG, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(script), *self.arguments],
            cwd=self.root, capture_output=True, text=True, check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn(str(self.config_file), result.stderr)
        self.assertFalse(self.output_path.exists())


if __name__ == "__main__":
    unittest.main()
