import argparse
import sys
from measuresoftgram.jsonReader import file_reader
from urllib import request
import requests
import inquirer
from inquirer.themes import GreenPassion


VALID_WEIGHT_SUM_ADVISE = "the sum of the weights must be 100"
INVALID_WEIGHT_SUM_ERROR = "Invalid weights," + VALID_WEIGHT_SUM_ADVISE

VALID_WEIGHT_ADVISE = "the weight must be between 0 and 100"
INVALID_WEIGHT_VALUE = "Invalid weight, " + VALID_WEIGHT_ADVISE


def define_weight(data_key, data_name):
    while True:
        weights = [
            inquirer.Text(
                data_key,
                message="Enter the weight of "
                + data_name
                + f" ({VALID_WEIGHT_SUM_ADVISE})",
            )
        ]
        defined_weight = inquirer.prompt(weights, theme=GreenPassion())
        if validate_weight_value(int(defined_weight[data_key])):
            break
        print(INVALID_WEIGHT_VALUE)

    return defined_weight


def validate_weight_sum(items):
    sum = 0
    for x in items:
        for k, v in x.items():
            sum += int(v)

    if sum != 100:
        return False
    else:
        return True


def validate_weight_value(weight):
    if weight > 100 or weight <= 0:
        return False
    else:
        return True


def sublevel_cli(level_name, level_alias, sublevels, available_pre_config):
    reverse_sublevel = {v["name"]: k for k, v in available_pre_config.items()}

    sublevels_answer = [
        inquirer.Checkbox(
            "sublevels",
            message="Choose the " + level_alias + " for " + level_name,
            choices=[available_pre_config[x]["name"] for x in sublevels],
        )
    ]
    user_sublevels = inquirer.prompt(sublevels_answer, theme=GreenPassion())

    user_sublevels = [reverse_sublevel[x] for x in user_sublevels["sublevels"]]

    return user_sublevels


def define_characteristic(available_pre_config):
    characteristics = available_pre_config["characteristics"]

    if len(characteristics) == 1:
        user_characteristics = list(characteristics.keys())[0]
        characteristics_weights = [{user_characteristics[0]: 100}]
        return user_characteristics, characteristics_weights

    reversed_characteristics = {v["name"]: k for k, v in characteristics.items()}

    characteristics_answer = [
        inquirer.Checkbox(
            "characteristics",
            message="Choose the characteristics",
            choices=[x["name"] for _, x in characteristics.items()],
        )
    ]

    user_characteristics = inquirer.prompt(characteristics_answer, theme=GreenPassion())

    user_characteristics = [
        reversed_characteristics[x] for x in user_characteristics["characteristics"]
    ]

    if len(user_characteristics) == 1:
        print("Only one characteristic selected, no need to define weights")
        characteristics_weights = [{user_characteristics[0]: 100}]
        return user_characteristics, characteristics_weights

    characteristics_weights = []

    while True:
        for x in user_characteristics:
            characteristics_weights.append(define_weight(x, characteristics[x]["name"]))

        if validate_weight_sum(characteristics_weights):
            break
        else:
            print(INVALID_WEIGHT_SUM_ERROR)
            characteristics_weights = []

    return user_characteristics, characteristics_weights


def define_measures(user_sub_characteristics, available_pre_config):
    measures = available_pre_config["measures"]

    if len(measures) == 1:
        user_measures = list(measures.keys())[0]
        measures_weights = [{user_measures[0]: 100}]
        return user_measures, measures_weights

    reversed_measures = {v["name"]: k for k, v in measures.items()}

    selected_measures = []
    measures_weights = []

    for x in user_sub_characteristics:
        while True:
            local_selected_measures = sublevel_cli(
                available_pre_config["subcharacteristics"][x]["name"],
                "measures",
                available_pre_config["subcharacteristics"][x]["measures"],
                available_pre_config["measures"],
            )

            if len(local_selected_measures) > 0:
                break
            else:
                print("No measures selected")

        local_measures_weights = []

        while True:
            for y in local_selected_measures:
                local_measures_weights.append(
                    define_weight(y, available_pre_config["measures"][y]["name"])
                )

            if validate_weight_sum(local_measures_weights):
                break
            else:
                print(INVALID_WEIGHT_SUM_ERROR)
                local_measures_weights = []

        selected_measures.extend(local_selected_measures)
        measures_weights.extend(local_measures_weights)

    return selected_measures, measures_weights


def define_subcharacteristics(user_characteristics, available_pre_config):
    sub_characteristic = available_pre_config["subcharacteristics"]

    if len(sub_characteristic) == 1:
        user_sub_characteristics = list(sub_characteristic.keys())[0]
        subcharacteristics_weights = [{user_sub_characteristics[0]: 100}]
        return user_sub_characteristics, subcharacteristics_weights

    reversed_sub_characteristic = {v["name"]: k for k, v in sub_characteristic.items()}

    selected_sub_characteristics = []
    sub_characteristic_weights = []
    for x in user_characteristics:
        # TODO Apply this to measures
        if len(available_pre_config["characteristics"][x]["subcharacteristics"]) == 1:
            local_selected_sub_characteristics = available_pre_config[
                "characteristics"
            ][x]["subcharacteristics"]
            local_sub_characteristics_weights = [
                {local_selected_sub_characteristics[0]: 100}
            ]
            print(
                f"Only one subcharacteristic (%s) available, no need to select or define weights"
                % (
                    available_pre_config["subcharacteristics"][
                        local_selected_sub_characteristics[0]
                    ]["name"]
                )
            )
        else:
            local_selected_sub_characteristics = sublevel_cli(
                available_pre_config["characteristics"][x]["name"],
                "subcharacteristics",
                available_pre_config["characteristics"][x]["subcharacteristics"],
                available_pre_config["subcharacteristics"],
            )

            local_sub_characteristics_weights = []

            while True:
                for y in local_selected_sub_characteristics:
                    local_sub_characteristics_weights.append(
                        define_weight(
                            y, available_pre_config["subcharacteristics"][y]["name"]
                        )
                    )

                if validate_weight_sum(local_sub_characteristics_weights):
                    break
                else:
                    print(INVALID_WEIGHT_SUM_ERROR)
                    local_sub_characteristics_weights = []

        selected_sub_characteristics.extend(local_selected_sub_characteristics)
        sub_characteristic_weights.extend(local_sub_characteristics_weights)

    return selected_sub_characteristics, sub_characteristic_weights


def parse_import():
    print("Importing metrics")
    user_path = input("Please provide sonar json absolute file path: ")
    file_reader(r"{}".format(user_path))


BASE_URL = "http://localhost:5000/"


def parse_create():
    headers = {"Content-type": "application/json"}
    print("Creating a new pre conf")

    available_pre_config = requests.get(
        BASE_URL + "available-pre-configs", headers={"Accept": "application/json"}
    ).json()

    [user_characteristics, caracteristics_weights] = define_characteristic(
        available_pre_config
    )

    [user_sub_characteristic, sub_characteristic_weights] = define_subcharacteristics(
        user_characteristics, available_pre_config
    )

    [user_measures, measures_weights] = define_measures(
        user_sub_characteristic, available_pre_config
    )

    pass


def setup():
    parser = argparse.ArgumentParser(
        description="Command line interface for measuresoftgram"
    )
    subparsers = parser.add_subparsers(help="sub-command help")
    parser_import = subparsers.add_parser("import", help="Import a metrics file")
    parser_create = subparsers.add_parser(
        "create", help="Create a new model pre configuration"
    )

    parser_import.set_defaults(func=parse_import)
    parser_create.set_defaults(func=parse_create)

    args = parser.parse_args()
    # if args is empty show help
    if not sys.argv[1:]:
        parser.print_help()
        return
    args.func()


def main():
    """Entry point for the application script"""

    setup()


if __name__ == "__main__":
    main()
