import json
import math
from pathlib import Path
import re
from copy import deepcopy

import rich.progress
from rich import print

from src.cli.exceptions import exceptions

REQUIRED_SONAR_JSON_KEYS = ["paging", "baseComponent", "components"]
REQUIRED_SONAR_BASE_COMPONENT_KEYS = ["id", "key", "name", "qualifier", "measures"]
REQUIRED_TRK_MEASURES = ["test_failures", "test_errors", "files", "ncloc"]
REQUIRED_UTS_MEASURES = ["tests", "test_execution_time"]
REQUIRED_FIL_MEASURES = [
    "coverage",
    "complexity",
    "functions",
    "comment_lines_density",
    "duplicated_lines_density",
]



def read_mult_files(directory: Path, pattern: str):
    for path_file in directory.glob(f"*.{pattern}"):
        try:
            yield open_json_file(path_file), path_file.name
        except exceptions.MeasureSoftGramCLIException:
            print(f"[red]Error calculating {path_file.name}: Failed to decode the JSON file.\n")


def folder_reader(dir_path, pattern):
    if not list(dir_path.glob(f"*.{pattern}")):
        raise exceptions.MeasureSoftGramCLIException(f"No files .{pattern} found inside folder.")

    for path_file in dir_path.glob(f"*.{pattern}"):
        print(f"[green]Reading:[/] [black]{path_file.name}[/]")

        components = None
        filename = get_filename_fixed(path_file.stem)

        try:
            validade_infos_from_name(filename)
            json_data = open_json_file(path_file, True)
            check_sonar_format(json_data)
            check_metrics_values(json_data)

        except exceptions.MeasureSoftGramCLIException as error:
            print(f"[red]Error  : {error}\n")
            components = None

        else:
            components = json_data["components"]
            components.append(json_data["baseComponent"])
            filename = "-".join(filename)
        finally:
            yield components, filename



def open_json_file(path_file: Path, disable=False):
    try:
        with rich.progress.open(
            path_file,
            "rb",
            description=path_file.name,
            disable=disable,
            style="bar.back",
            complete_style="bar.complete",
            finished_style="bar.finished",
            pulse_style="bar.pulse",
        ) as file:
            return json.load(file)

    except FileNotFoundError:
        raise exceptions.FileNotFound("The file was not found")
    except IsADirectoryError:
        raise exceptions.UnableToOpenFile(f"File {path_file.name} is a directory")
    except json.JSONDecodeError as error:
        raise exceptions.InvalidMetricsJsonFile(f"Failed to decode the JSON file. {error}")


def get_missing_keys_str(attrs, required_attrs):
    missing_keys = [req_key for req_key in required_attrs if req_key not in attrs]
    return ", ".join(missing_keys)



def check_sonar_format(json_data):
    components = json_data.get("components")

    if isinstance(components, type(None)):
        raise exceptions.InvalidMetricsJsonFile("Json sonar components do not exist.")

    if len(components) == 0:
        raise exceptions.InvalidMetricsJsonFile("Json sonar components TRK and FIL empty.")

    base_component = json_data["baseComponent"]
    if len(base_component) == 0:
        raise exceptions.InvalidMetricsJsonFile("Json sonar baseComponent TRK empty.")

    attributes = list(json_data.keys())
    missing_keys = get_missing_keys_str(attributes, REQUIRED_SONAR_JSON_KEYS)
    if len(missing_keys) > 0:
        raise exceptions.InvalidMetricsJsonFile(
            f"Invalid Sonar JSON keys. Missing keys are: {missing_keys}"
        )

    base_component_attrs = list(base_component.keys())
    missing_keys = get_missing_keys_str(base_component_attrs, REQUIRED_SONAR_BASE_COMPONENT_KEYS)

    if len(missing_keys) > 0:
        raise exceptions.InvalidMetricsJsonFile(
            f"Invalid Sonar baseComponent keys. Missing keys are: {missing_keys}"
        )

    base_component_measures = base_component["measures"]
    base_component_measures_attrs = [bc["metric"] for bc in base_component_measures]
    missing_keys = get_missing_keys_str(base_component_measures_attrs, REQUIRED_TRK_MEASURES)

    if len(missing_keys) > 0:
        raise exceptions.InvalidMetricsJsonFile(
            f"Invalid Sonar baseComponent TRK measures. Missing keys: {missing_keys}"
        )

    required_fil_measure = deepcopy(REQUIRED_FIL_MEASURES)
    for component in components:
        if component["qualifier"] == "FIL":
            for measure in component["measures"]:
                if measure["metric"] in required_fil_measure:
                    required_fil_measure.remove(measure["metric"])

    if len(required_fil_measure) > 0:
        raise exceptions.InvalidMetricsJsonFile(
            f"Invalid Sonar components FIL measures. Missing keys: {required_fil_measure}"
        )

    required_uts_measure = deepcopy(REQUIRED_UTS_MEASURES)
    for component in components:
        if component["qualifier"] == "UTS":
            for measure in component["measures"]:
                if measure["metric"] in required_uts_measure:
                    required_uts_measure.remove(measure["metric"])

    if len(required_uts_measure) > 0:
        raise exceptions.InvalidMetricsJsonFile(
            f"Invalid Sonar components UTS measures. Missing keys: {required_uts_measure}"
        )


def check_file_extension(file_name):
    if file_name.split(".")[-1] != "json":
        raise exceptions.InvalidMetricsJsonFile("Only JSON files are accepted.")


def raise_invalid_metric(key, metric):
    raise exceptions.InvalidMetricException(
        f'Invalid metric value in "{key}" component for the "{metric}" metric'
    )


def check_metrics_values(json_data):
    try:
        for component in json_data["components"]:
            for measure in component["measures"]:
                value = measure["value"]

                try:
                    if value is None or math.isnan(float(value)):
                        raise_invalid_metric(component["key"], measure["metric"])
                except (ValueError, TypeError):
                    raise_invalid_metric(component["key"], measure["metric"])
    except KeyError as e:
        raise exceptions.InvalidMetricsJsonFile(
            "Failed to validate Sonar JSON metrics. Please check if the file is a valid Sonar JSON"
        ) from e


def validate_metrics_post(response_status):
    if 200 <= response_status <= 299:
        return "OK: Metrics uploaded successfully"

    return f"FAIL: The host service server returned a {response_status} error. Trying again"


def get_filename_fixed(filename):
    re_filename = re.sub("[^a-zA-Z0-9\s]", "-", filename)
    re_filename = re_filename.replace(" ", "")

    try:
        version = re.search(r"\d{1,2}-\d{1,2}-\d{4}-\d{1,2}-\d{1,2}-\d{1,2}", re_filename)[0]
        repository = re_filename.split(version)[0][:-1]

    except Exception:
        return ["repository", "version"]

    return [repository, version]


def validade_infos_from_name(filename):
    """
    Formato valido: MM-DD-YYYY-HH-MM-SS ou DD-MM-YYYY-HH-MM-SS  (dia e mes pode ter um ou dois digtos)
    """

    regex1 = "^([1-9]|0[1-9]|1\d|2\d|3[01])\-(0[1-9]|[1-9]|1[0-2])\-(19|20)\d{2}\-([0-1]?\d|2[0-3])-([0-5]?\d)-([0-5]?\d)$"
    regex2 = "^(0[1-9]|[1-9]|1[0-2])\-([1-9]|0[1-9]|1\d|2\d|3[01])\-(19|20)\d{2}\-([0-1]?\d|2[0-3])-([0-5]?\d)-([0-5]?\d)$"

    if len(filename[0]) < 2:
        raise exceptions.NameFileFormatInvalid("Unable to extract repository name from file name.")

    if not (re.match(regex1, filename[1]) or re.match(regex2, filename[1])):
        raise exceptions.NameFileFormatInvalid(
            "Unable to extract valid creation date from file name."
        )
