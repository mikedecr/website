from pathlib import Path
from logging import getLogger

log = getLogger(__name__)


def link_md_files(source: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)

    for md_file in source.glob("index.md"):
        link_path = dest / md_file.name

        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        link_path.hardlink_to(md_file.resolve())
        log.info(f"linked {link_path} -> {md_file}")
