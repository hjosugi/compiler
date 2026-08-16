from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

from kofumini import __version__

ROOT = Path(__file__).resolve().parents[1]


class ProjectMetadataTests(unittest.TestCase):
    def test_package_and_project_versions_match(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], __version__)
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn(f"VERSION ?= v{__version__}", makefile)

    def test_mit_license_metadata_and_text_are_consistent(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertEqual(project["project"]["license"], "MIT")
        self.assertEqual(project["project"]["license-files"], ["LICENSE"])
        self.assertEqual(project["project"]["authors"], [{"name": "hjosugi"}])
        self.assertIn("setuptools>=77.0.3", project["build-system"]["requires"])
        self.assertIn("Copyright (c) 2026 hjosugi", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)

    def test_toolchain_snapshot_has_stable_and_prerelease_separated(self) -> None:
        lock = json.loads((ROOT / "toolchain.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["schema"], "compiler-atlas.toolchain/v1")
        self.assertEqual(lock["snapshot_date"], "2026-08-16")
        self.assertEqual(lock["llvm_recommended_stable"], "22.1.8")
        self.assertEqual(lock["llvm_current_release_candidate"], "23.1.0-rc3")

    def test_llvm_repository_snapshot_count_matches_manifest(self) -> None:
        manifest = json.loads(
            (ROOT / "data" / "snapshot-manifest.json").read_text(encoding="utf-8")
        )
        rows = [
            line
            for line in (ROOT / "data" / "llvm_org_repositories_2026-08-16.tsv")
            .read_text(encoding="utf-8")
            .splitlines()[1:]
            if line
        ]
        self.assertEqual(len(rows), manifest["llvm_organization"]["repository_count"])
        self.assertFalse(manifest["llvm_releases"]["stable"]["prerelease"])
        self.assertTrue(manifest["llvm_releases"]["candidate"]["prerelease"])


if __name__ == "__main__":
    unittest.main()
