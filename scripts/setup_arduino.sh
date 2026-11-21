#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
task_cli="${1:-arduino-cli}"
mkdir -p .tools
"$task_cli" config init --dest-dir .tools --overwrite
arduino_config="$project_root/.tools/arduino-cli.yaml"
"$task_cli" --config-file "$arduino_config" config set directories.data "$project_root/.tools/arduino-data"
"$task_cli" --config-file "$arduino_config" config set directories.downloads "$project_root/.tools/arduino-downloads"
"$task_cli" --config-file "$arduino_config" config set directories.user "$project_root/.tools/arduino-user"
board_index="https://espressif.github.io/arduino-esp32/package_esp32_index.json"
"$task_cli" --config-file "$arduino_config" core update-index --additional-urls "$board_index"
"$task_cli" --config-file "$arduino_config" core install esp32:esp32@4.0.0 --additional-urls "$board_index"
"$task_cli" --config-file "$arduino_config" lib install PubSubClient@2.8.0 ArduinoJson@7.4.3
