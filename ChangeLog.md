### Summary

- The `SKELETON_BONES` structure has been completely revised and expanded. The new structure provides a more accurate and detailed representation of the human skeleton, including distinct chains for the trunk, arms, and legs. (by @jian2486)
- A centralized theme system has been implemented to manage UI styling. Hardcoded values for fonts, colors, and widget styles in the GUI tabs have been replaced with constants imported from a new `gui/theme.py` module.
- Updated the log directory and file names to be more consistent with the application name (e.g., `AppData\Local\VioletWing\logs\violetwing.log`).
- Simplified the implementation by removing the custom `DetailedFormatter` and the `_get_caller_info` method. Caller information (filename, line number) is now handled directly by the standard `logging.Formatter`.
- Added a `Logger.shutdown()` method, which is called when the main window closes, to ensure all log messages are properly flushed.

[![Downloads](https://img.shields.io/github/downloads/Jesewe/VioletWing/v1.2.8.8/total?style=for-the-badge&logo=github&color=8E44AD)](https://github.com/Jesewe/VioletWing/releases/tag/v1.2.8.8) [![Platforms](https://img.shields.io/badge/platform-Windows-blue?style=for-the-badge&color=8E44AD)](https://github.com/Jesewe/VioletWing/releases/download/v1.2.8.8/VioletWing.exe) [![License](https://img.shields.io/github/license/jesewe/cs2-triggerbot?style=for-the-badge&color=8E44AD)](https://github.com/Jesewe/VioletWing/blob/main/LICENSE)
