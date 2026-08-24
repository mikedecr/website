from pathlib import Path
from logging import getLogger

log = getLogger(__name__)


def link_dir(source: Path, dest: Path, include: list[str] | None = None):
    source = source.resolve()
    dest.mkdir(parents=True, exist_ok=True)

    wanted = set()
    index_md = source / "index.md"
    if index_md.is_file():
        wanted.add(index_md)
    else:
        log.warning(f"no index.md found in {source}")
    for pattern in include or []:
        for match in source.glob(pattern):
            if match.is_file():
                wanted.add(match.resolve())

    for src_file in sorted(wanted):
        rel_path = src_file.relative_to(source)
        link_path = dest / rel_path
        link_path.parent.mkdir(parents=True, exist_ok=True)

        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        link_path.hardlink_to(src_file)
        log.info(f"linked {link_path} -> {src_file}")

    for stale in _find_stale(dest, source):
        stale.unlink()
        log.info(f"removed stale link {stale}")


def _find_stale(dest: Path, source: Path):
    stale = []
    for path in dest.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if not (source / path.relative_to(dest)).is_file():
            stale.append(path)
    return stale
