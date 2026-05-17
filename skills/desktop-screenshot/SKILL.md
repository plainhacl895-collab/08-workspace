---
name: desktop-screenshot
description: Capture the entire computer screen and save it as an image. Use when the user asks for a screenshot, verification, or visual proof of the current desktop state.
---

# Desktop Screenshot

Use this skill when the user asks to "take a screenshot", "show me what's on the screen", or "verify visually".

## Execution
1. Run the script:
   ```bash
   "C:\Users\Huawei\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\Huawei\.openclaw\workspace-tuantuan\tools\screenshot_desktop.py"
   ```
2. The script saves the image to `C:\Users\Huawei\Desktop\screenshot_TIMESTAMP.png`.
3. Read the output path.
4. If you have access to an image tool or can send the file to the user (e.g., via Telegram), do so using the path.
5. If you cannot send the image directly, report the path and describe what you see if you can read the screen via other means (though usually the user wants the image).

## Notes
- Requires Python 3.11 with `Pillow` installed.
- Works on multi-monitor setups (`all_screens=True`).
- Always save to the Desktop for easy access.
