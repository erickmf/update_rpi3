# Update RPi3

Perform OTA update for Raspberry Pi 3.

Folders and files:
- *app*: app to be updated
- *new_fw*: where new FW will eb pulled from
- *ota*: main code
    - *manifest_handler*: receive and validate manifest
    - *pi3_device.py*: device operations
    - *run_update*: main program
    - *fw_info.json*: current FW metadata
    - *config.json*: platform credentials
- *manifest_server*: server for manifest and new FW
