import json
import logging
import os
import re
import sys
from time import perf_counter, sleep

from parsers.sonarqube import Sonarqube
from rich import print
from rich.console import Console

from src.cli.jsonReader import folder_reader
from src.cli.utils import (
    make_progress_bar,
    print_error,
    print_info,
    print_panel,
    print_rule,
    print_warn,
)

logger = logging.getLogger("msgram")
console = Console()


def command_extract(args):
    time_init = perf_counter()
    try:
        output_origin = args["output_origin"]
        extracted_path = args["extracted_path"]
        data_path = args["data_path"]
        language_extension = args["language_extension"]

    except Exception as e:
        logger.error(f"KeyError: args[{e}] - non-existent parameters")
        print_warn(f"KeyError: args[{e}] - non-existent parameters")
        exit(1)

    console.clear()
    print_rule("Extract metrics")

    if not os.path.isdir(extracted_path):
        print_error(f"The file or dir was not found: [blue]{extracted_path}[/]")

        print_panel(
            title="Tips",
            menssage="[yellow]➤[/] To initialize config file and dir that are used in the following commands:\n"
            "[yellow]$[/] [#008080]msgram init -cp [purple]<config_path>[/]",
        )
        sys.exit(1)

    logger.debug(f"output_origin: {output_origin}")
    logger.debug(f"data_path: {data_path}")
    logger.debug(f"language_extension: {language_extension}")

    files = list(data_path.glob("*.json"))
    parser = Sonarqube() if output_origin == "sonarqube" else None

    print_info(f"\n[yellow]➤[/] [black]Extract and save metrics [[blue ]{output_origin}[/]]:\n")

    with make_progress_bar() as progress_bar:
        task_request = progress_bar.add_task("[#A9A9A9]Extracting files: ", total=len(files))
        status = progress_bar.tasks[task_request]
        valid_files = 0
        first_request = True

        for json_data, filename in folder_reader(data_path, "json"):
            if json_data is not None:
                file_path = f"{extracted_path}/{filename}.msgram"
                result = parser.extract_supported_metrics(json_data, first_request)

                with open(file_path, "w") as f:
                    f.write(json.dumps(result, indent=4))
                    print(f"[dark_green]Save   :[/] [black]{filename}.msgram[/]\n")
                    valid_files += 1

                first_request = False
            progress_bar.update(
                task_request,
                advance=1,
                description=f"[white]Extracting files ([red]{status.completed + 1}[/]|[blue]{status.total}[/]) ",
            )
            sleep(0.1)

        time_extract = perf_counter() - time_init
        print_info(
            f"\n\nMetrics successfully extracted! [black][[blue]{valid_files}[/]/[blue]{status.total}[/] "
            f"- [white]{time_extract:0.1f}s[/]]"
        )
    print_panel(
        "[yellow]➤[/] Calculate quality of extracted files and export as (CSV or JSON):\n"
        "[yellow]$[/] [#008080]msgram calculate all -ep [purple]<extracted_path>[/]"
        "-cp [purple]<config_path>[/] -o [purple]<output_origin>"
    )

