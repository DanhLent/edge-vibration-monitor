"""Compile the Wokwi sketch with Arduino CLI without renaming source files."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default=str(ROOT / ".tools" / "arduino-cli"))
    parser.add_argument("--config", default=str(ROOT / ".tools" / "arduino-cli.yaml"))
    args = parser.parse_args()
    if not Path(args.cli).is_file() and shutil.which(args.cli) is None:
        raise SystemExit("Arduino CLI is required; install the esp32 board core, PubSubClient, and ArduinoJson.")
    with tempfile.TemporaryDirectory(prefix="ce339-build-") as directory:
        sketch = Path(directory) / "sketch"
        shutil.copytree(ROOT / "firmware", sketch)
        command = [args.cli]
        if Path(args.config).is_file():
            command += ["--config-file", args.config]
        command += ["compile", "--fqbn", "esp32:esp32:esp32", "--warnings", "all",
                    "--build-path", str(ROOT / ".tools" / "arduino-build"),
                    "--output-dir", str(ROOT / "artifacts" / "firmware"), str(sketch)]
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
