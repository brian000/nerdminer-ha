# Nerdminer-HA Home Assistant integration

A custom Home Assistant integration that polls NerdMiner devices over the local network.

## Install with HACS

Until the repository is added to the HACS default store, add it as a custom repository:

1. Open **HACS** in Home Assistant.
2. Select **Integrations**.
3. Open the three-dot menu in the upper-right corner and choose **Custom repositories**.
4. Enter `https://github.com/brian000/nerdminer-ha` as the repository.
5. Select **Integration** as the category and click **Add**.
6. Search for **Nerdminer-HA**, open it, and select **Download**.
7. Restart Home Assistant.

After restarting, go to **Settings > Devices & services**, select **Add Integration**, and search for **Nerdminer-HA**.

Add one integration entry for each miner using its hostname or IP address.

## Manual installation

Copy `custom_components/nerdminer_ha` into the `custom_components` directory of your Home Assistant configuration and restart Home Assistant.

Then go to **Settings > Devices & services**, select **Add Integration**, and search for **Nerdminer-HA**. Add one integration entry for each miner using its hostname or IP address. The integration creates sensors for hashing, shares, difficulty, blocks, temperatures, uptime, CPU frequency, and MAC address. Controls are not currently exposed.

---

This is entirely vibecoded.  I have no idea what I'm doing.  