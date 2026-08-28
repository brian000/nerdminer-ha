# NerdMiner Home Assistant integration

A custom Home Assistant integration that polls NerdMiner devices over the local network.

## Installation

Copy `custom_components/nerdminer_ha` into the `custom_components` directory of your Home Assistant configuration, restart Home Assistant, and add **NerdMiner** from **Settings > Devices & services**.

Add one integration entry for each miner using its hostname or IP address. The integration creates sensors for hashing, shares, difficulty, blocks, temperatures, uptime, CPU frequency, and MAC address.
