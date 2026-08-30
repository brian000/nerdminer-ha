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

Then go to **Settings > Devices & services**, select **Add Integration**, and search for **Nerdminer-HA**. Add one integration entry for each miner using its hostname or IP address. The integration creates sensors for hashing, shares, difficulty, blocks, temperature, uptime, CPU frequency, Wi-Fi signal, free heap, and diagnostic sensors for firmware version, MAC address, hostname, board, and chip. A light entity controls the LCD backlight (on/off and brightness).

## Nerdminer dashboard card

The repository includes custom Lovelace cards with live metrics and history graphs. HACS installs and automatically loads the card JavaScript with the integration; no file copying or dashboard resource registration is required.

Add the card to a dashboard in YAML mode. Replace `nm01` with the entity prefix shown by your miner's entities:

```yaml
type: custom:nerdminer-card
title: Nerdminer-HA / nm01
entity_prefix: nm01
hours_to_show: 6
```

The card plots the 1-minute and 5-minute average hashrates together, shows hardware/software hashrate composition, and includes current hashrate, shares, board temperature, uptime, and refresh status. After a browser hard refresh, both cards appear in **Add card** under custom cards and provide GUI configuration fields with sensible defaults.

For a farm-wide view, add the second card. It automatically discovers all Nerdminer sensor entities:

```yaml
type: custom:nerdminer-farm-card
title: Nerdminer farm
hours_to_show: 6
```

Both cards use Home Assistant's native card and history-graph rendering. They do not include custom CSS, gradients, SVG, canvas, or other custom graphics.

---

This is entirely vibecoded.  I have no idea what I'm doing.  