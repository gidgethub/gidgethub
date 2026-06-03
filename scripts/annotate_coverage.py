"""Emit GitHub Actions annotations for uncovered lines in coverage.py JSON."""

import json
import pathlib
import sys
from typing import Sequence, TextIO, Union


def annotate_coverage(
    coverage_report: Union[str, pathlib.Path] = "coverage.json",
    *,
    output: TextIO = sys.stdout,
) -> int:
    coverage_json = pathlib.Path(coverage_report)
    if not coverage_json.is_file():
        print(
            f"::warning::{coverage_report} not found; "
            "this is expected if tests did not complete successfully",
            file=output,
        )
        return 0

    coverage = json.loads(coverage_json.read_text())
    files = coverage.get("files")
    if not isinstance(files, dict):
        print(f"::warning::{coverage_report} has no file coverage data", file=output)
        return 0

    for filename, report in files.items():
        for line in report.get("missing_lines", ()):
            print(
                f"::warning file={filename},line={line}::"
                f"Line {line} is not covered by tests",
                file=output,
            )
        for branch in report.get("missing_branches", ()):
            message = (
                f"Branch from line {branch[0]} to line {branch[1]} "
                "is not covered by tests"
            )
            print(f"::warning file={filename},line={branch[0]}::{message}", file=output)
    return 0


def main(argv: Sequence[str]) -> int:
    coverage_report = argv[0] if argv else "coverage.json"
    return annotate_coverage(coverage_report)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
