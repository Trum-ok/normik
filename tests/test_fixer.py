from pathlib import Path

from nk.core.finding import Finding, Fix, Severity
from nk.core.fixer import diff, plan, write
from nk.core.position import Position, Region


def finding(path: Path, region: Region, replacement: str, rule_id: str = "G732-a") -> Finding:
    return Finding(
        rule_id=rule_id,
        clause="6.5.7",
        severity=Severity.ERROR,
        message="сообщение",
        requirement="требование",
        path=path,
        lineno=region.start.lineno,
        fix=Fix(region=region, replacement=replacement),
    )


def write_source(tmp_path: Path, text: str, name: str = "report.tex") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_single_replacement(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    region = Region.in_line(path, 1, 1, 17)

    result = plan([finding(path, region, "\\caption{Схема}")])
    write(result)

    assert path.read_text(encoding="utf-8") == "\\caption{Схема}\n"
    assert result.applied == 1


def test_several_edits_in_one_line_do_not_shift_each_other(tmp_path: Path) -> None:
    path = write_source(tmp_path, "аа бб вв\n")

    result = plan(
        [
            finding(path, Region.in_line(path, 1, 1, 3), "ААА", rule_id="G732-a"),
            finding(path, Region.in_line(path, 1, 7, 9), "В", rule_id="G732-b"),
        ]
    )
    write(result)

    assert path.read_text(encoding="utf-8") == "ААА бб В\n"


def test_multiline_region(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема\n  установки.}\nхвост\n")
    region = Region(path, Position(1, 1), Position(2, 14))

    write(plan([finding(path, region, "\\caption{Схема установки}")]))

    assert path.read_text(encoding="utf-8") == "\\caption{Схема установки}\nхвост\n"


def test_overlapping_edits_are_applied_one_per_pass(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    region = Region.in_line(path, 1, 1, 17)

    result = plan(
        [
            finding(path, region, "\\caption{Схема}", rule_id="G732-a"),
            finding(path, region, "\\caption{СХЕМА.}", rule_id="G732-b"),
        ]
    )

    assert result.applied == 1


def test_insertion_at_a_point(tmp_path: Path) -> None:
    path = write_source(tmp_path, "текст\nформула\n")

    write(plan([finding(path, Region.at(path, 2, 1), "\n")]))

    assert path.read_text(encoding="utf-8") == "текст\n\nформула\n"


def test_findings_without_a_fix_are_skipped(tmp_path: Path) -> None:
    path = write_source(tmp_path, "текст\n")
    plain = Finding(
        rule_id="G732-a",
        clause="6.5.7",
        severity=Severity.ERROR,
        message="m",
        requirement="r",
        path=path,
        lineno=1,
    )

    assert plan([plain]).edits == ()


def test_edits_beyond_the_file_are_dropped(tmp_path: Path) -> None:
    path = write_source(tmp_path, "текст\n")

    assert plan([finding(path, Region.in_line(path, 99, 1, 5), "нет")]).edits == ()


def test_non_utf8_file_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_bytes("\\caption{Схема.}\n".encode("cp1251"))

    result = plan([finding(path, Region.in_line(path, 1, 1, 17), "\\caption{Схема}")])

    assert result.edits == ()
    assert result.skipped == (path,)


def test_crlf_line_endings_survive(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_bytes("первая\r\n\\caption{Схема.}\r\nтретья\r\n".encode())

    write(plan([finding(path, Region.in_line(path, 2, 1, 17), "\\caption{Схема}")]))

    assert path.read_bytes() == "первая\r\n\\caption{Схема}\r\nтретья\r\n".encode()


def test_overlay_replaces_the_file_content(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    overlay = {path: "\\caption{Другая.}\n"}

    result = plan([finding(path, Region.in_line(path, 1, 1, 18), "\\caption{Другая}")], overlay)

    assert result.edits[0].text == "\\caption{Другая}\n"
    assert path.read_text(encoding="utf-8") == "\\caption{Схема.}\n"


def test_diff_compares_against_the_file_on_disk(tmp_path: Path) -> None:
    path = write_source(tmp_path, "первая\nвторая\n")

    text = diff({path: "первая\nтретья\n"})

    assert "-вторая" in text
    assert "+третья" in text
