# ☄️ KarutaSniper v2.4.0 (Enterprise Edition)

**KarutaSniper** is a high-performance, autonomous Discord self-bot designed for the ultimate Karuta and Tofu experience. Engineered for sub-millisecond reactions and 100% reliability on personal drops, it utilizes advanced in-memory OCR and human-simulated behaviors to dominate the sniping meta while maintaining account safety.

---

## 🚀 Core Features

### 🧠 Advanced OCR Engine (Vision System)
*   **Hyper-Scaling (4x)**: Small print numbers are upscaled 400% in memory before scanning, ensuring near-perfect accuracy on even the smallest fonts.
*   **Adaptive Gaussian Thresholding**: A self-adjusting light filter that handles every card edition, frame, and background lighting. It automatically cleans the image for the OCR engine.
*   **PSM 7 Optimized**: Specifically tuned for single-line numeric strings (Print Numbers) to prevent misreads.
*   **Multithreaded Processing**: Utilizes a 16-worker thread pool to process card segments (Top, Bottom, Print) in parallel.

### 🎯 Pro Sniping Engine
*   **10ms Button Hyper-Polling**: The bot checks Discord button states 100 times per second, executing clicks the absolute millisecond they become active.
*   **Scoring-Based Priority (Own Drops)**: On personal drops, the bot scans **all** cards and ranks them by value:
    1.  **Whitelist Characters** (Highest Priority)
    2.  **Whitelist Animes**
    3.  **Absolute Lowest Print**
*   **First-Hit-Wins (Foreign Drops)**: Optimized to click the first valid target it finds to win speed battles in high-traffic channels.
*   **Emergency Fallback**: If OCR fails or errors occur on your own drop, the bot triggers a fail-safe grab to ensure no personal card is ever lost.

### 🤖 Autonomous Autofarm
*   **Smart Worker Integration**: Fully compatible with the newest worker bot protocols (`@1271850048707231744`).
*   **Message Mirroring**: Automatically copies complex worker bot commands (like `k!jn abcde clay`) and replies with perfect accuracy.
*   **Coordinated Cycles**: Manages `kn`, `kw`, and `kcd` commands in a seamless, automated loop.
*   **Human-Simulated Typing**: Simulates "Typing..." status and variable delays to mimic a focused human player.

### 🛡️ Stealth & Account Safety
*   **Activity Redirection**: Send clutter commands like `kv`, `kt b`, and `kcd` to a designated "Activity Channel" to keep your main sniping rooms clean and avoid detection.
*   **Dynamic Jitter**: Uses randomized reaction windows (e.g., 200ms - 600ms) to ensure no two grabs ever have the same timing.
*   **Permission Guard**: Automatically detects channel permissions and silently skips actions in locked rooms, avoiding noisy `403 Forbidden` errors.
*   **Reply Verification**: Only syncs cooldowns from messages specifically addressed to your ID, preventing "timer hijacking" from other players.

---

## ⚙️ Configuration (`config.json`)

| Key | Description |
| :--- | :--- |
| `accuracy` | Float (0-1) for character matching sensitivity. |
| `grab_delay_min/max` | The "Human Jitter" range for foreign drops. |
| `grab_delay_own` | Delay for your own drops (Recommended: `0.0`). |
| `autodropchannel` | List of channel IDs where the bot is allowed to drop. |
| `resourcechannel` | The channel ID for your autofarm work. |
| `check_print` | Set to `true` to enable Low-Print sniping (Tier 3). |

---

## 📂 Project Structure
*   `main.py`: The heart of the bot. Manages events, timers, and decision-making.
*   `lib/ocr.py`: The vision processing pipeline (OpenCV + Tesseract).
*   `lib/api.py`: Utilities for fuzzy-matching and data handling.
*   `keywords/`: Folder containing your target `characters.txt` and `animes.txt`.

---

## 🛠 Installation & Usage
1.  **Prerequisites**: Python 3.10+, OpenCV, and Tesseract OCR.
2.  **Setup**: Fill in your token and channel IDs in `config.json`.
3.  **Run**:
    ```bash
    python main.py
    ```

---

## ⚠️ Disclaimer
*This project is for educational purposes only. Use of self-bots is a violation of Discord's Terms of Service and can result in account termination. Use at your own risk.*
