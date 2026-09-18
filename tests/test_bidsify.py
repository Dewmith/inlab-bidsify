"""Configuration and conversion-flow tests without recording dependencies."""

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import tomlkit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
mne_stub = types.ModuleType("mne")
mne_stub.io = types.SimpleNamespace(read_raw_bdf=Mock())
mne_bids_stub = types.ModuleType("mne_bids")
mne_bids_stub.BIDSPath = Mock()
mne_bids_stub.write_raw_bids = Mock()
spec = importlib.util.spec_from_file_location("bidsify_under_test", PROJECT_ROOT / "bidsify.py")
bidsify = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"mne": mne_stub, "mne_bids": mne_bids_stub}):
    spec.loader.exec_module(bidsify)


VALID_CONFIG = '''
[DATASET_DESCRIPTION]
Name = "ExampleDataset"
Authors = ["Alice Dupont", "John Smith"]
InstitutionAddress = "City, Country"
DatasetType = " raw "
ParticipantCount = 2
Score = 1.5
Public = true

[task_restingtask]
keywords = [" rest ", "baseline"]
description = "Rest, with eyes closed."

[run_1]
keywords = [" block1 ", "run1"]
description = "First run, before break."

[run_2]
keywords = ["block2", "run2"]
description = "Second run."
'''


class BidsifyTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.input = self.root / "raw recordings"
        self.input.mkdir()
        self.output = self.root / "bids dataset"
        self.config_path = self.input / "bids_configurator.toml"
        self.config_path.write_text(VALID_CONFIG, encoding="utf-8")

        reader_patch = patch.object(bidsify.mne.io, "read_raw_bdf")
        self.reader = reader_patch.start()
        self.addCleanup(reader_patch.stop)
        writer_patch = patch.object(bidsify, "write_raw_bids")
        self.writer = writer_patch.start()
        self.addCleanup(writer_patch.stop)
        path_patch = patch.object(bidsify, "BIDSPath")
        self.bids_path = path_patch.start()
        self.addCleanup(path_patch.stop)

    def run_cli(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status = bidsify.main(["--input", str(self.input), "--output", str(self.output)])
        return status, stderr.getvalue()

    def add_recordings(self, *filenames):
        participant = self.input / "participant_001"
        participant.mkdir()
        for filename in filenames:
            recording = participant / filename
            recording.touch()
            os.utime(recording, (1700000000, 1700000000))

    def mock_recording_output(self):
        def make_bids_path(**values):
            path = Mock()
            filename = (
                f"sub-{values['subject']}_ses-{values['session']}_"
                f"task-{values['task']}_run-{values['run']}_eeg.json"
            )
            path.copy.return_value.update.return_value.fpath = Path(values["root"]) / filename
            return path

        def write_recording(raw, path, overwrite):
            sidecar = path.copy().update(extension=".json").fpath
            sidecar.write_text('{"SamplingFrequency": 512}', encoding="utf-8")
            (self.output / "dataset_description.json").write_text(
                '{"Name": "Generated", "BIDSVersion": "1.8.0"}', encoding="utf-8"
            )

        self.bids_path.side_effect = make_bids_path
        self.writer.side_effect = write_recording

    def test_reads_native_values_and_normalizes_keywords(self):
        config = bidsify.read_config(self.config_path)
        self.assertIs(type(config), dict)
        self.assertIs(type(config["DATASET_DESCRIPTION"]), dict)
        self.assertIs(type(config["DATASET_DESCRIPTION"]["Authors"]), list)
        self.assertEqual(config["task_restingtask"]["keywords"], ["rest", "baseline"])
        self.assertEqual(config["DATASET_DESCRIPTION"]["InstitutionAddress"], "City, Country")
        self.assertIs(type(config["DATASET_DESCRIPTION"]["ParticipantCount"]), int)
        self.assertIs(type(config["DATASET_DESCRIPTION"]["Score"]), float)
        self.assertIs(config["DATASET_DESCRIPTION"]["Public"], True)

    def test_shipped_example_is_valid(self):
        config = bidsify.read_config(PROJECT_ROOT / "bids_configurator.example.toml")
        self.assertEqual(config["task_NbackRolling"]["keywords"], ["rolling"])
        self.assertIsInstance(config["DATASET_DESCRIPTION"]["Authors"], list)
        self.assertIsInstance(config["DATASET_DESCRIPTION"]["InstitutionAddress"], str)

    def test_readme_toml_examples_are_valid(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        examples = readme.split("```toml\n")[1:]
        self.assertTrue(examples)
        for example in examples:
            bidsify.validate_config(tomlkit.parse(example.split("```", 1)[0]).unwrap())

    def test_rejects_unsupported_extensions_even_with_valid_toml(self):
        for name in ("settings.ini", "settings.cfg", "settings.toml.bak", "settings"):
            with self.subTest(name=name):
                path = self.root / name
                path.write_text(VALID_CONFIG, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, r"\.toml extension"):
                    bidsify.read_config(path)

    def test_missing_configuration_fails_without_output(self):
        self.config_path.unlink()
        status, error = self.run_cli()
        self.assertEqual(status, 1)
        self.assertIn("bids_configurator.toml", error)
        self.assertIn("Cannot read configuration file", error)
        self.assertFalse(self.output.exists())
        self.reader.assert_not_called()

    def test_missing_input_fails_without_output(self):
        self.input = self.root / "missing"
        status, error = self.run_cli()
        self.assertEqual(status, 1)
        self.assertIn("not found", error)
        self.assertFalse(self.output.exists())

    def test_input_must_be_directory(self):
        self.input = self.config_path
        status, error = self.run_cli()
        self.assertEqual(status, 1)
        self.assertIn("not a directory", error)
        self.assertFalse(self.output.exists())

    def test_configuration_must_be_readable_utf8_file(self):
        self.config_path.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(ValueError, "Cannot read configuration file"):
            bidsify.read_config(self.config_path)
        self.config_path.unlink()
        self.config_path.mkdir()
        with self.assertRaisesRegex(ValueError, "Cannot read configuration file"):
            bidsify.read_config(self.config_path)

    def test_invalid_toml_fails_without_output(self):
        for contents in ('[task_rest]\nkeywords = ["rest"', '[DATASET_DESCRIPTION]\nName = unquoted'):
            with self.subTest(contents=contents):
                self.config_path.write_text(contents, encoding="utf-8")
                status, error = self.run_cli()
                self.assertEqual(status, 1)
                self.assertIn("Cannot read configuration file", error)
                self.assertFalse(self.output.exists())
                self.reader.assert_not_called()

    def test_requires_keyword_arrays_of_nonblank_strings(self):
        invalid_values = ('"rest, baseline"', '"rest"', '[]', '[""]', '["  "]', '["rest", 2]', 'true')
        for section in ("task_rest", "run_1"):
            for value in invalid_values:
                with self.subTest(section=section, value=value):
                    self.config_path.write_text(f"[{section}]\nkeywords = {value}\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "nonempty TOML array of nonblank strings"):
                        bidsify.read_config(self.config_path)
            self.config_path.write_text(f'[{section}]\ndescription = "Description"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "keywords"):
                bidsify.read_config(self.config_path)

    def test_requires_tables_and_string_descriptions(self):
        invalid_configs = (
            'DATASET_DESCRIPTION = "metadata"',
            'task_rest = ["rest"]',
            'run_1 = "first"',
            '[task_rest]\nkeywords = ["rest"]\ndescription = 2',
            '[run_1]\nkeywords = ["block1"]\ndescription = ["First"]',
        )
        for contents in invalid_configs:
            with self.subTest(contents=contents):
                self.config_path.write_text(contents, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "must be a (TOML table|string)"):
                    bidsify.read_config(self.config_path)

    def test_keyword_conflicts_include_trimmed_values_and_runs(self):
        for other_section in ("task_other", "run_1"):
            with self.subTest(other_section=other_section):
                config = {"task_rest": {"keywords": [" rest "]}, other_section: {"keywords": ["rest"]}}
                with self.assertRaisesRegex(ValueError, "Keyword 'rest' found in both"):
                    bidsify.validate_config(config)
        with self.assertRaisesRegex(ValueError, "Keyword 'rest' found in both"):
            bidsify.validate_config({"task_rest": {"keywords": ["rest", " rest "]}})

    def test_keyword_conflicts_are_case_sensitive(self):
        bidsify.validate_config({"task_rest": {"keywords": ["rest", "REST"]}})

    def test_run_names_and_numbering(self):
        for names in (("run_0",), ("run_2",), ("run_1", "run_3"), ("run_01",), ("run_first",), ("run_1_extra",)):
            with self.subTest(names=names):
                with self.assertRaisesRegex(ValueError, "Run (table names|numbers)"):
                    bidsify.validate_config({name: {"keywords": [name]} for name in names})
        bidsify.validate_config({"run_2": {"keywords": ["second"]}, "run_1": {"keywords": ["first"]}})

    def test_dataset_type_defaults_and_trims_strings(self):
        for config in ({}, {"DATASET_DESCRIPTION": {}}, {"DATASET_DESCRIPTION": {"DatasetType": " raw "}}):
            with self.subTest(config=config):
                self.assertEqual(bidsify.validate_dataset_type(config), "raw")

    def test_rejects_invalid_dataset_type(self):
        for value in ("", " ", "derivative", "study", "RAW", '"raw"', 1, True, ["raw"]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Invalid DatasetType"):
                    bidsify.validate_config({"DATASET_DESCRIPTION": {"DatasetType": value}})

    def test_rejects_metadata_incompatible_with_json(self):
        for value in ("2026-09-18", "2026-09-18T12:00:00Z", "12:00:00", "inf", "nan", "[1, nan]", "{ date = 2026-09-18 }"):
            with self.subTest(value=value):
                self.config_path.write_text(f"[DATASET_DESCRIPTION]\nCustom = {value}\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "compatible with JSON"):
                    bidsify.read_config(self.config_path)

    def test_invalid_configuration_never_changes_output_or_reads_recordings(self):
        self.add_recordings("rest.bdf")
        invalid_configs = (
            {"task_rest": {"keywords": "rest"}},
            {"task_rest": {"keywords": ["rest"], "description": 42}},
            {"task_rest": {"keywords": ["rest"]}, "run_1": {"keywords": ["rest"]}},
            {"run_2": {"keywords": ["block2"]}},
            {"DATASET_DESCRIPTION": {"DatasetType": "derivative"}},
            {"DATASET_DESCRIPTION": {"Custom": float("nan")}},
        )
        for config in invalid_configs:
            with self.subTest(config=config, output_exists=False):
                with self.assertRaises(ValueError):
                    bidsify.create_bids_structure(self.input, self.output, config)
                self.assertFalse(self.output.exists())

        self.output.mkdir()
        for filename in ("participants.tsv", "dataset_description.json", "recording_eeg.json"):
            (self.output / filename).write_bytes(b"existing content\n")
        original = {path.name: path.read_bytes() for path in self.output.iterdir()}
        for config in invalid_configs:
            with self.subTest(config=config, output_exists=True):
                with self.assertRaises(ValueError):
                    bidsify.create_bids_structure(self.input, self.output, config)
                self.assertEqual({path.name: path.read_bytes() for path in self.output.iterdir()}, original)
        self.reader.assert_not_called()
        self.writer.assert_not_called()

    def test_validation_does_not_mutate_supplied_dictionary(self):
        config = {"task_rest": {"keywords": [" rest "]}}
        original = copy.deepcopy(config)
        normalized = bidsify.validate_config(config)
        self.assertEqual(config, original)
        self.assertEqual(normalized["task_rest"]["keywords"], ["rest"])

    def test_cli_uses_only_exact_input_configuration(self):
        self.config_path.unlink()
        (self.input / "other.toml").write_text(VALID_CONFIG, encoding="utf-8")
        (self.input / "bids_configurator.cfg").write_text(VALID_CONFIG, encoding="utf-8")
        working_directory = self.root / "working directory"
        working_directory.mkdir()
        (working_directory / "bids_configurator.toml").write_text(VALID_CONFIG, encoding="utf-8")
        original_cwd = Path.cwd()
        try:
            os.chdir(working_directory)
            status, error = self.run_cli()
            self.assertEqual(status, 1)
            self.assertIn(str(self.config_path), error)
            self.assertFalse(self.output.exists())

            self.config_path.write_text(VALID_CONFIG, encoding="utf-8")
            with patch.object(bidsify, "create_bids_structure") as convert:
                status, error = self.run_cli()
            self.assertEqual((status, error), (0, ""))
            self.assertEqual(convert.call_args.args[2]["task_restingtask"]["keywords"], ["rest", "baseline"])
        finally:
            os.chdir(original_cwd)

    def test_cli_reports_validation_errors(self):
        self.config_path.write_text('[task_rest]\nkeywords = "rest"\n', encoding="utf-8")
        status, error = self.run_cli()
        self.assertEqual(status, 1)
        self.assertIn("Invalid configuration file", error)
        self.assertIn("[task_rest].keywords", error)
        self.assertFalse(self.output.exists())

    def test_cli_help_describes_toml_and_required_paths(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit) as exit_context:
            bidsify.main(["--help"])
        self.assertEqual(exit_context.exception.code, 0)
        self.assertIn("bids_configurator.toml", stdout.getvalue())
        self.assertIn("--input", stdout.getvalue())
        self.assertIn("--output", stdout.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit_context:
            bidsify.main([])
        self.assertEqual(exit_context.exception.code, 2)

    def test_conversion_matches_arrays_and_preserves_metadata(self):
        self.add_recordings("baseline_block2.bdf")
        self.mock_recording_output()
        status, error = self.run_cli()
        self.assertEqual((status, error), (0, ""))
        self.reader.assert_called_once_with(str(self.input / "participant_001" / "baseline_block2.bdf"), preload=False)
        path_values = self.bids_path.call_args.kwargs
        self.assertEqual((path_values["subject"], path_values["session"], path_values["task"], path_values["run"]),
                         ("01", "01", "restingtask", "02"))
        self.assertTrue(self.writer.call_args.kwargs["overwrite"])
        sidecar = json.loads((self.output / "sub-01_ses-01_task-restingtask_run-02_eeg.json").read_text())
        self.assertEqual(sidecar["OriginalFilename"], "baseline_block2.bdf")
        self.assertEqual(sidecar["TaskDescription"], "Rest, with eyes closed.")
        self.assertEqual(sidecar["RunDescription"], "Second run.")
        self.assertEqual(sidecar["SamplingFrequency"], 512)
        metadata = json.loads((self.output / "dataset_description.json").read_text())
        self.assertEqual(metadata["Authors"], ["Alice Dupont", "John Smith"])
        self.assertEqual(metadata["InstitutionAddress"], "City, Country")
        self.assertEqual(metadata["DatasetType"], "raw")
        self.assertEqual(metadata["BIDSVersion"], "1.8.0")
        self.assertEqual(metadata["ParticipantCount"], 2)
        self.assertEqual(metadata["Score"], 1.5)
        self.assertIs(metadata["Public"], True)
        self.assertEqual((self.output / "participants.tsv").read_text(),
                         "participant_id\toriginal_folder\nsub-01\tparticipant_001\n")

    def test_conversion_uses_trimmed_keywords(self):
        self.add_recordings("rest_block1.bdf")
        self.mock_recording_output()
        status, error = self.run_cli()
        self.assertEqual((status, error), (0, ""))
        path_values = self.bids_path.call_args.kwargs
        self.assertEqual((path_values["task"], path_values["run"]), ("restingtask", "01"))
        sidecar = json.loads((self.output / "sub-01_ses-01_task-restingtask_run-01_eeg.json").read_text())
        self.assertEqual(sidecar["RunDescription"], "First run, before break.")

    def test_case_sensitive_matching_and_automatic_runs(self):
        self.add_recordings("REST_BLOCK1.bdf", "REST_BLOCK2.bdf")
        self.mock_recording_output()
        status, error = self.run_cli()
        self.assertEqual((status, error), (0, ""))
        values = [call.kwargs for call in self.bids_path.call_args_list]
        self.assertEqual([(value["task"], value["run"]) for value in values], [("task", "01"), ("task", "02")])
        for path in self.output.glob("*_eeg.json"):
            metadata = json.loads(path.read_text())
            self.assertNotIn("TaskDescription", metadata)
            self.assertNotIn("RunDescription", metadata)

    def test_descriptions_and_dataset_metadata_are_optional(self):
        self.config_path.write_text('[task_rest]\nkeywords = ["rest"]\n[run_1]\nkeywords = ["block1"]', encoding="utf-8")
        self.add_recordings("rest_block1.bdf")
        self.mock_recording_output()
        status, error = self.run_cli()
        self.assertEqual((status, error), (0, ""))
        sidecar = json.loads((self.output / "sub-01_ses-01_task-rest_run-01_eeg.json").read_text())
        self.assertNotIn("TaskDescription", sidecar)
        self.assertNotIn("RunDescription", sidecar)
        metadata = json.loads((self.output / "dataset_description.json").read_text())
        self.assertEqual(metadata["DatasetType"], "raw")
        self.assertEqual(metadata["Name"], "Generated")

    def test_missing_dataset_description_is_not_created(self):
        self.output.mkdir()
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            bidsify.update_dataset_description(self.output, {})
        self.assertIn("Skipping update", stdout.getvalue())
        self.assertFalse((self.output / "dataset_description.json").exists())


if __name__ == "__main__":
    unittest.main()
