from pathlib import Path

from nk.core.document import Document, Line
from nk.core.profile import Profile


def make_document(text: str, path: str = "report.tex", profile: Profile | None = None) -> Document:
    """Собрать документ из текста без участия парсера."""
    file_path = Path(path)
    lines = tuple(
        Line(path=file_path, lineno=number, raw=raw, stripped=raw)
        for number, raw in enumerate(text.splitlines(), start=1)
    )
    return Document(
        root=file_path,
        files=(file_path,),
        lines=lines,
        profile=profile or Profile(),
    )
