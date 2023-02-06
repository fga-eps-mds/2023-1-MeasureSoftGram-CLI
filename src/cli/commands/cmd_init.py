import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from staticfiles import DEFAULT_PRE_CONFIG

from src.cli.utils import print_error, print_info, print_panel, print_rule, print_warn
from src.config.settings import FILE_CONFIG

logger = logging.getLogger("msgram")


def command_init(args):
    try:
        config_path: Path = args["config_path"]

    except Exception as e:
        logger.error(f"KeyError: args[{e}] - non-existent parameters")
        print_error(f"KeyError: args[{e}] - non-existent parameters")
        sys.exit(1)

    logger.debug(config_path)
    file_path = config_path / FILE_CONFIG

    console = Console()
    console.clear()
    print_rule("MSGram", "[#708090]Init to set config file[/]:")

    if not config_path.exists():
        print_info(f"[yellow]➤[/] [#4F4F4F]Created directory:[/] {config_path}")
        config_path.mkdir()

    replace = True

    if file_path.exists():
        print_info(
            f"[yellow]➤[/][#4F4F4F] MSGram config file [yellow]{FILE_CONFIG}[/] exists already!"
        )
        replace = Confirm.ask("[yellow]➤[/][#4F4F4F] Do you want to replace?")

    if replace:
        try:
            with file_path.open("w") as f:
                f.write(json.dumps(DEFAULT_PRE_CONFIG, indent=4))
        except OSError:
            console.line(2)
            print_error("Error opening or writing to file")
        print_info(
            f"[yellow]➤[/][#4F4F4F] The config file:[blue] {FILE_CONFIG}[/] was[/] created successfully."
        )

    else:
        print_warn(
            f"[yellow]➤[/][#4F4F4F] The config file:[/][blue] {FILE_CONFIG}[/] has not been changed..."
        )

    print_panel(
        "[yellow]➤[/] Extract supported metrics:\n"
        "[yellow]$[/] [#099880]msgram extract -o sonarqube -dp [purple]<data_path>[/] -ep [purple]<extract_path>[/][/]"
    )
