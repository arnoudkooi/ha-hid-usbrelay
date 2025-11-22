# HID USB Relay for Home Assistant

![USB Relay Board](usbrelay.jpg)

Control **HID USB Relay boards** (Commonly `16c0:05df`) directly from Home Assistant.

> **💡 Migrating from Raspberry Pi GPIO?**  
> This is an ideal replacement if you've been using GPIO pins on a Raspberry Pi and are switching to a Mini PC or other hardware without GPIO support. Simply connect a USB relay board to maintain your relay control functionality.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=arnoudkooi&repository=ha-hid-usbrelay&category=integration)

## Features
- **Full UI Configuration**: Auto-discovery and setup via the Integrations page.
- **Device Registry**: Relays are grouped under a single device.
- **Pulse Buttons**: Each relay gets a dedicated "Pulse" button entity (1s duration).
- **Native Integration**: No Node.js or external scripts required.
- **Automatic Discovery**: Detects 1, 2, 4, or 8 channel boards.

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant
2. Search for "HID USB Relay"
3. Click **Download**
4. **Restart Home Assistant**
5. **Full reboot required** (not just restart) after USB Relay is first connected

### Manual Installation

1. Download the latest release from [GitHub releases](https://github.com/arnoudkooi/ha-hid-usbrelay/releases)
2. Extract and copy the `custom_components/hid_usbrelay` folder to your Home Assistant's `custom_components` directory
3. **Restart Home Assistant**
4. **Full reboot required** (not just restart) after USB Relay is first connected

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration**.
3.  Search for **HID USB Relay**.
4.  If your device is plugged in and accessible, it will be discovered automatically.
5.  Click **Submit**.

### You will get:
*   **Switch Entities**: `switch.relay_1`, `switch.relay_2`... (On/Off)
*   **Pulse Buttons**: `button.pulse_relay_1`, `button.pulse_relay_2`... (Momentary 1s)

![USB Relay Board](ha-usbrelay.png)

---

## Troubleshooting

### "No HID USB Relay found"
If the setup fails saying it cannot find the device:

*   **HA OS on Bare Metal / Raspberry Pi**: You **MUST perform a FULL HOST REBOOT** (Shutdown -> Power On). A simple "Restart Home Assistant" is **NOT enough** to apply the USB permissions.
*   **Virtual Machines (Proxmox, ESXi, VirtualBox)**: You must **pass through** the specific USB device `16c0:05df` to the VM.
*   **Docker**: Map the USB bus:
    ```yaml
    volumes:
      - /dev/bus/usb:/dev/bus/usb
    privileged: true
    ```

### Linux Permissions (Manual Install)
If running manually on Core/Docker, you may need a udev rule:

`/etc/udev/rules.d/99-usbrelay.rules`:
```bash
SUBSYSTEM=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="05df", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="05df", MODE="0666"
```
Reload: `sudo udevadm control --reload-rules && sudo udevadm trigger`
