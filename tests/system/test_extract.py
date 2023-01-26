import subprocess
import tempfile
import shutil


def capture(command):
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    return out, err, proc.returncode


# def command_extract_should_succeed():
#     config_dirpath = tempfile.mkdtemp()
#     breakpoint()
#     _, err, returncode = capture(
#         ["msgram", "extract", "-o", "sonarqube", "-cp", config_dirpath, "-dp", "sonar-output-fake"]
#     )


def test_extract_metrics_folder_not_found_exception_handling():
    config_dirpath = tempfile.mkdtemp()
    _, err, returncode = capture(
        ["msgram", "extract", "-o", "sonarqube", "-cp", config_dirpath, "-dp", "sonar-output-fake"]
    )

    assert returncode == 1
    message = "src.cli.exceptions.exceptions.MeasureSoftGramCLIException: No files .json found inside folder."
    assert message in err.decode("utf-8")
    shutil.rmtree(config_dirpath)


def test_extract_metrics_config_folder_not_found_exception_handling():
    msg, _, returncode = capture(
        ["msgram", "extract", "-o", "sonarqube", "-cp", "config-fake", "-dp", "sonar-output-fake"]
    )

    assert returncode == 1
    assert "FileNotFoundError: config directory" in msg.decode("utf-8")
