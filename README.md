# Segway Ninebot BMS Serial Tool

A simple terminal-based monitor for Segway Ninebot BMS data over a serial connection. The tool periodically requests information from the BMS and prints a human‑readable dashboard including battery info, status, and individual cell voltages.

> **Disclaimer**  
> This is an **unofficial community tool**.  
> It is not affiliated with Segway or Ninebot in any way.  
> Use at your own risk!

## Features

- Realtime BMS monitoring via serial
- Cell voltages with min/max/diff summary
- Cross‑platform (macOS, Linux, Windows)

## Requirements

- Python
- A USB‑to‑serial adapter/cable connected to the BMS
- OS serial permissions to access the device port

## Installation

```bash
git clone https://github.com/HwangJungeon/segway-ninebot-bms-serial-tool.git
cd segway-ninebot-bms-serial-tool

# (Optional) Create and activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Then select the serial port from the interactive list (e.g., `/dev/tty.usbserial-*` on macOS, `/dev/ttyUSB*` or `/dev/ttyACM*` on Linux, `COM*` on Windows). Press Ctrl+C to stop.

### Example Output

```
============================================================
Segway-Ninebot BMS Monitor (Press Ctrl+C to exit)
============================================================
  [BATTERY INFORMATION]
   Serial Number: XXXXXXXXXXXXXX
   Firmware Version: 1.2.3.4
   Capacity: 5100 mAh
   Total Capacity: 5200 mAh
   Design Voltage: 36.00 V
   Cycle Count: 120
   Charge Count: 80

  [BATTERY STATUS]
   Remaining Capacity: 3000 mAh
   Remaining: 58%
   Current: 1.25 A
   Voltage: 40.12 V
   Temperature: 25°C / 26°C
   Health: 96%

  [CELL VOLTAGES]
   Cell 1: 4.012 V
   ...
   Min: 4.000V, Max: 4.015V, Diff: 0.015V

============================================================
Last updated: 2025-01-23 12:34:56
```

## Safety

Proceed carefully and at your own risk. The authors and contributors are not responsible for any damage, injury, or legal issues arising from the use of this tool.

## License

MIT
