from pathlib import Path
import tomllib
from typing import Dict

from typer import Typer, Context, Option


def read_toml(file: Path) -> Dict:
    io = open(file, "rb")
    return tomllib.load(io)


app = Typer(name="mkd")


@app.callback()
def _callback(context: Context,
               config_file: str = Option("mkd.toml", "-f", "--file")):
    toml_data: Dict = read_toml(Path(config_file))
    context.obj = toml_data
    return context
