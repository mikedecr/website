from pathlib import Path
from logging import getLogger

from typer import Context

from .app import app
from .links import link_dir

log = getLogger(__name__)


@app.command()
def link(context: Context):
    links = context.obj.get("links", {})
    if not links:
        log.warning("no [links] section found in config")
        return

    for dest_str, spec in links.items():
        if isinstance(spec, str):
            source, include = Path(spec), []
        elif isinstance(spec, dict):
            if "src" not in spec:
                raise ValueError(f"link entry '{dest_str}' is missing required key 'src'")
            source = Path(spec["src"])
            include = [str(p) for p in spec.get("include", [])]
        else:
            raise ValueError(f"link entry '{dest_str}' must be a string or table")

        link_dir(source, Path(dest_str), include)
