# KarutaSniper (v2.4.0)

A modified version of KarutaSniper focused on fixing core bugs and improving overall throughput.

---

## Technical Improvements

### Vision & OCR
- 4x image scaling for better print detection.
- Adaptive Gaussian thresholding to handle varied card lighting and backgrounds.
- PSM 7 single-line detection for stats.

### Performance
- Multithreaded execution using a 16-worker thread pool.
- 10ms polling for button states.
- Parallel processing for all card segments.

### Logic
- Scoring-based priority for personal drops (Whitelist > Lowest Print).
- Emergency fallback grab for processing errors on own drops.
- Self-healing cooldown parser with reply verification.

### Stealth
- Activity command redirection to secondary channels.
- Micro-typing status before automated commands.
- Channel permission verification to prevent 403 errors.

---

## Autofarm Instructions

The autofarm module now requires a specific worker bot to handle command mirroring. 

1. Invite the worker bot to your farm server: [Worker Bot (Top.gg)](https://top.gg/bot/1271850048707231744)
2. Ensure the bot has permissions to view the channel and send messages.
3. Configure the `resourcechannel` in `config.json`.

---

## Android (Termux) Setup

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) (F-Droid version).
2. Run these commands:
   ```bash
   pkg update && pkg upgrade
   pkg install python tesseract opencv libjpeg-turbo
   pip install discord.py-self pytesseract opencv-python colorama aiohttp
   ```
3. Copy this project folder to your phone.
4. Run `python main.py`.

---

## Setup

1. Rename `config_example.json` to `config.json`.
2. Fill in your token and channel IDs.
3. Add targets to the `keywords/` text files.

---

## Disclaimer
Self-bots violate Discord TOS. This project is for research purposes only. Use at your own risk.
