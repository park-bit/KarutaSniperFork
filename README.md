# KarutaSniper (Optimized)

A refined, high-performance automation tool for Karuta and Tofu. Focuses on sub-millisecond reaction times, intelligent personal drop priority, and autonomous farming.

---

## What's New (v2.4.0)

### Improved Vision
- **4x Scaling**: Better accuracy on small print numbers.
- **Adaptive Filters**: Handles all card frames and lighting automatically.
- **Single-Line OCR**: Optimized for reading bottom-bar stats without noise.

### Sniping & Drops
- **10ms Polling**: Clicks buttons the moment they become active.
- **Priority Scoring**: On your own drops, the bot scans all cards and picks the best one (Whitelist > Lowest Print).
- **Parallel Processing**: Scans all cards simultaneously to win speed battles.

### Automation
- **Worker Bot Sync**: Compatible with `@1271850048707231744` for exact message mirroring.
- **Coordinated Cycles**: Automated `kn`, `kw`, and `kcd` loops.
- **Activity Redirection**: Offloads clutter commands to secondary channels.

### Stealth
- **Humanized Jitter**: Randomized reaction windows to avoid detection.
- **Micro-Typing**: Simulates typing status before commands.
- **Permission Guard**: Silently handles locked channels and 403 errors.

---

## Configuration

Standard setup in `config.json`. Key settings:

| Setting | Description |
| :--- | :--- |
| `grab_delay_min/max` | Reaction jitter for competitive drops. |
| `grab_delay_own` | Delay for your own drops (0.0 recommended). |
| `accuracy` | Fuzzy matching sensitivity (0.815 default). |
| `autodropchannel` | Where you want the bot to drop. |

---

## Disclaimer
Self-bots violate Discord TOS. This is for research purposes only. Use at your own risk.
