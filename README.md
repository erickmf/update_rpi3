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
- *create_update*: create a FW update at Konker platform
	- *connect_platform*: create authorization token por platform API
	- *create_update_platform*: uploads a FW and create update
- *manifest_server*: server for manifest and new FW
