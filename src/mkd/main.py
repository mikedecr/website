from pathlib import Path
from logging import getLogger

from typer import Context

from .app import app
from .links import link_md_files

log = getLogger(__name__)


@app.command()
def link(context: Context):
    links = context.obj.get("links", {})
    if not links:
        log.warning("no [links] section found in config")
        return

    for dest_str, src_str in links.items():
        source = Path(src_str)
        dest = Path(dest_str)
        link_md_files(source, dest)
