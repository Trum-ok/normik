import os
from errno import ENOSPC
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


def test_inserted_line_takes_the_crlf_of_the_file(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_bytes("первая\r\nвторая\r\n".encode())

    write(plan([finding(path, Region.at(path, 2, 1), "\\newpage\n")]))

    assert path.read_bytes() == "первая\r\n\\newpage\r\nвторая\r\n".encode()


def test_multiline_replacement_takes_the_crlf_of_the_file(tmp_path: Path) -> None:
    path = tmp_path / "report.tex"
    path.write_bytes("\\caption{Схема\r\n  установки}\r\nхвост\r\n".encode())
    region = Region(path, Position(1, 1), Position(2, 13))

    write(plan([finding(path, region, "\\caption{Схема\n  УСТАНОВКИ}")]))

    assert path.read_bytes() == "\\caption{Схема\r\n  УСТАНОВКИ}\r\nхвост\r\n".encode()


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


def test_file_mode_survives_the_write(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    path.chmod(0o640)

    write(plan([finding(path, Region.in_line(path, 1, 1, 17), "\\caption{Схема}")]))

    assert path.stat().st_mode & 0o777 == 0o640


def test_write_leaves_no_temporary_files(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")

    write(plan([finding(path, Region.in_line(path, 1, 1, 17), "\\caption{Схема}")]))

    assert [item.name for item in tmp_path.iterdir()] == [path.name]


def test_symlink_stays_a_symlink(tmp_path: Path) -> None:
    target = write_source(tmp_path, "\\caption{Схема.}\n", name="target.tex")
    link = tmp_path / "report.tex"
    link.symlink_to(target)

    write(plan([finding(link, Region.in_line(link, 1, 1, 17), "\\caption{Схема}")]))

    assert link.is_symlink()
    assert target.read_text(encoding="utf-8") == "\\caption{Схема}\n"


def test_original_survives_a_failed_write(tmp_path: Path, monkeypatch) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    prepared = plan([finding(path, Region.in_line(path, 1, 1, 17), "\\caption{Схема}")])

    def fail(source: object, destination: object) -> None:
        raise OSError(ENOSPC, "нет места на устройстве")

    monkeypatch.setattr(os, "replace", fail)
    written = write(prepared)

    assert written.applied == 0
    assert [item[0] for item in written.failed] == [path]
    assert path.read_text(encoding="utf-8") == "\\caption{Схема.}\n"
    assert [item.name for item in tmp_path.iterdir()] == [path.name]


def test_write_protected_file_is_reported_not_changed(tmp_path: Path) -> None:
    path = write_source(tmp_path, "\\caption{Схема.}\n")
    prepared = plan([finding(path, Region.in_line(path, 1, 1, 17), "\\caption{Схема}")])
    path.chmod(0o444)

    written = write(prepared)

    assert written.applied == 0
    assert [item[0] for item in written.failed] == [path]
    assert path.read_text(encoding="utf-8") == "\\caption{Схема.}\n"


def test_failure_on_one_file_leaves_the_others_written(tmp_path: Path) -> None:
    good = write_source(tmp_path, "\\caption{Схема.}\n", name="good.tex")
    bad = write_source(tmp_path, "\\caption{Схема.}\n", name="bad.tex")
    prepared = plan(
        [
            finding(good, Region.in_line(good, 1, 1, 17), "\\caption{Схема}"),
            finding(bad, Region.in_line(bad, 1, 1, 17), "\\caption{Схема}"),
        ]
    )
    bad.chmod(0o444)

    written = write(prepared)

    assert written.applied == 1
    assert [item[0] for item in written.failed] == [bad]
    assert good.read_text(encoding="utf-8") == "\\caption{Схема}\n"


def test_column_past_the_end_of_the_line_is_dropped(tmp_path: Path) -> None:
    path = write_source(tmp_path, "первая\nвторая\n")

    assert plan([finding(path, Region.in_line(path, 1, 1, 99), "нет")]).edits == ()
