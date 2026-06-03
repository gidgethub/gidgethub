import importlib.util
import io
import json
import pathlib

script_path = pathlib.Path(__file__).parents[1] / "scripts" / "annotate_coverage.py"
spec = importlib.util.spec_from_file_location("annotate_coverage", script_path)
annotate_coverage = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(annotate_coverage)


def test_missing_coverage_report() -> None:
    output = io.StringIO()

    result = annotate_coverage.annotate_coverage("missing.json", output=output)

    assert result == 0
    assert output.getvalue() == (
        "::warning::missing.json not found; "
        "this is expected if tests did not complete successfully\n"
    )


def test_malformed_coverage_report(tmp_path: pathlib.Path) -> None:
    coverage_report = tmp_path / "coverage.json"
    coverage_report.write_text(json.dumps({"totals": {}}))
    output = io.StringIO()

    result = annotate_coverage.annotate_coverage(coverage_report, output=output)

    assert result == 0
    assert output.getvalue() == (
        f"::warning::{coverage_report} has no file coverage data\n"
    )


def test_missing_lines_and_branches(tmp_path: pathlib.Path) -> None:
    coverage_report = tmp_path / "coverage.json"
    coverage_report.write_text(
        json.dumps(
            {
                "files": {
                    "gidgethub/example.py": {
                        "missing_lines": [3],
                        "missing_branches": [[4, 5]],
                    }
                }
            }
        )
    )
    output = io.StringIO()

    result = annotate_coverage.annotate_coverage(coverage_report, output=output)

    assert result == 0
    line_warning = (
        "::warning file=gidgethub/example.py,line=3::Line 3 is not covered by tests"
    )
    branch_warning = (
        "::warning file=gidgethub/example.py,line=4::"
        "Branch from line 4 to line 5 is not covered by tests"
    )
    assert output.getvalue().splitlines() == [
        line_warning,
        branch_warning,
    ]
