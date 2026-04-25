from __future__ import annotations

import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TELEMETRY_PATH = BASE_DIR / "telemetry.js"
TEMP_PATTERN = re.compile(r"temp=([0-9]+(?:\.[0-9]+)?)")
UPDATE_INTERVAL_SECONDS = 10 * 60
HEARTBEAT_INTERVAL_SECONDS = 15


def measure_cpu_temp() -> str:
    result = subprocess.run(
        ["vcgencmd", "measure_temp"],
        check=True,
        capture_output=True,
        text=True,
    )
    match = TEMP_PATTERN.search(result.stdout)
    if not match:
        raise ValueError(f"Unexpected vcgencmd output: {result.stdout!r}")
    return f"{match.group(1)}°C"


def read_existing_telemetry() -> dict[str, str]:
    content = TELEMETRY_PATH.read_text()
    fields = {
        key: value
        for key, value in re.findall(r'(\w+):\s*"([^"]*)"', content)
    }
    return fields


def read_telemetry() -> dict[str, str]:
    telemetry = read_existing_telemetry()
    telemetry["cpuTemp"] = measure_cpu_temp()
    telemetry["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return telemetry


def render_telemetry_js(telemetry: dict[str, str]) -> str:
    ordered_keys = ["deviceUptime", "humidity", "cpuTemp", "temperature", "updatedAt"]
    lines = ["window.HOME_TELEMETRY = {"]

    used = set()
    for key in ordered_keys:
        if key in telemetry:
            lines.append(f'  {key}: "{telemetry[key]}",')
            used.add(key)

    for key in telemetry:
        if key not in used:
            lines.append(f'  {key}: "{telemetry[key]}",')

    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(',')

    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def update_telemetry_js() -> dict[str, str]:
    telemetry = read_telemetry()
    TELEMETRY_PATH.write_text(render_telemetry_js(telemetry))
    return telemetry


def main() -> None:
    print(
        "Telemetry loop started. "
        f"Updating telemetry.js every {UPDATE_INTERVAL_SECONDS // 60} minutes. "
        f"Heartbeat every {HEARTBEAT_INTERVAL_SECONDS} seconds."
    )
    next_update_at = time.monotonic()
    while True:
        try:
            cpu_temp = measure_cpu_temp()
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Program running. CPU temp {cpu_temp}"
            )

            if time.monotonic() >= next_update_at:
                telemetry = read_existing_telemetry()
                telemetry["cpuTemp"] = cpu_temp
                telemetry["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                TELEMETRY_PATH.write_text(render_telemetry_js(telemetry))
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Updated telemetry.js with CPU temp {cpu_temp}"
                )
                next_update_at = time.monotonic() + UPDATE_INTERVAL_SECONDS
        except Exception as error:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Update failed: {error}")

        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
