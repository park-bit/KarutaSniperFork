# KarutaSniper (Optimized v2.4.0)

A refined, high-performance automation tool for Karuta and Tofu. This fork focuses on fixing long-standing bugs in the original repository and maximizing speed and accuracy.

---

## ⚡ Improvements over Original

This version addresses several "Known Issues" and "TODOs" from the original repo:

### 🧠 Fixed OCR & Print Accuracy
- **Original Issue**: "print numbers and autofarm might be buggy" / "ocr can misread names."
- **Our Fix**: Implemented **4x Image Scaling**, **Gaussian Blurring**, and **Adaptive Gaussian Thresholding**. This eliminates background noise and textures, making print numbers and character names pinpoint accurate across all card editions.
- **PSM 7 Optimization**: Switched to single-line detection for stats, drastically reducing false hits.

### 🚀 Speed & Performance
- **Parallel Processing**: Unlike the original, this version uses a **16-worker Thread Pool**. It scans top, bottom, and print segments of all cards simultaneously.
- **10ms Hyper-Polling**: Buttons are checked 100x per second, ensuring the fastest possible click the moment they enable.
- **First-Hit Logic**: Optimized to click as soon as the first target is identified in competitive drops.

### 🤖 Reliable Automation
- **New Autofarm**: Completely overhauled the worker-bot logic. It now supports the latest worker bot (`@1271850048707231744`) with exact message mirroring.
- **Tofu Support**: Stable, unified success handling for both Karuta and Tofu drops.
- **Priority Scoring**: On your own drops, the bot intelligently compares all cards and picks the best one (Whitelist > Lowest Print) instead of just grabbing the first one.

### 🛡️ Stealth & Stability
- **Activity Redirection**: Offloads clutter commands (`kv`, `kcd`, `kt`) to secondary channels to stay under the radar.
- **Humanized Jitter**: Randomized delays and micro-typing simulation to look natural while staying fast.
- **Permission Guard**: Added checks for channel permissions to prevent `403 Forbidden` crashes.
- **Self-Healing Sync**: A robust cooldown parser that handles all time formats and verifies replies to prevent timer hijacking.

---

## Configuration

Settings are managed in `config.json`. Use `config_example.json` as a template.

| Setting | Description |
| :--- | :--- |
| `grab_delay_min/max` | Reaction jitter for foreign drops. |
| `grab_delay_own` | Delay for your own drops (0.0 recommended). |
| `accuracy` | Fuzzy matching sensitivity (0.815 default). |
| `autodropchannel` | Designated channels for scheduled drops. |

---

## Disclaimer
Self-bots violate Discord TOS. This fork is for research purposes only. Use at your own risk.
