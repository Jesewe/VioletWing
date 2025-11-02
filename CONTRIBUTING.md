# Contributing to VioletWing

Thank you for your interest in contributing to the VioletWing project. This guide outlines the process for setting up your development environment, contributing code, and submitting changes.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Submitting Issues](#submitting-issues)
- [Pull Request Process](#pull-request-process)
- [Feature Requests and Feedback](#feature-requests-and-feedback)

---

## Code of Conduct

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and open to constructive feedback.

## Getting Started

1. **Fork the Repository**: Create a personal fork on GitHub.
2. **Clone Your Fork**: Clone your fork locally:

   ```bash
   git clone https://github.com/Jesewe/VioletWing.git
   cd VioletWing
   ```

3. **Add Upstream Remote**: Sync with the original repository:

   ```bash
   git remote add upstream https://github.com/Jesewe/VioletWing.git
   ```

## Development Setup

1. **Install Python**: Use Python **≥ 3.8** and **< 3.12.5**.
2. **Install Dependencies**: Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**: Test the application:

   ```bash
   python main.py
   ```

### Testing Changes

- Run the application to validate changes.
- Check logs at `%LOCALAPPDATA%\VioletWing\logs\violetwing.log` or `violetwing_detailed.log` for debugging.
- Test in Counter-Strike 2 (casual or offline modes) to ensure TriggerBot, Overlay, Bunnyhop, and NoFlash features work as expected.

## Coding Standards

Follow these guidelines for consistent, high-quality code:

- **PEP 8**: Adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **Naming**: Use descriptive, meaningful names for variables, functions, and classes (e.g., `trigger_key` instead of `tk`).
- **Error Handling**: Implement robust exception handling and log errors using the `Logger` class.
- **Documentation**: Add docstrings for functions and comments for complex logic.
- **Modularity**: Break down large functions into smaller, reusable components.

### GUI Development

- **Customtkinter**: Use `customtkinter` for GUI enhancements.
- **Consistency**: Match the existing UI theme (colors, fonts: Chivo, Gambetta) and layout (e.g., scrollable frames, card designs).
- **Responsiveness**: Ensure GUI elements adapt to different window sizes.

### Feature-Specific Guidelines

- **TriggerBot**: Ensure compatibility with offset updates from [cs2-dumper](https://github.com/a2x/cs2-dumper).
- **Overlay (ESP)**: Test visual elements (bounding boxes, snaplines, minimap) in various game resolutions.
- **Bunnyhop**: Verify smooth movement automation across different surfaces.
- **NoFlash**: Confirm flashbang mitigation without affecting game performance.

### Logging

- **Format**: Follow the `Logger` class format for log entries.
- **Levels**: Use appropriate levels (`INFO`, `WARNING`, `ERROR`) based on context.
- **Location**: Logs are saved to `%LOCALAPPDATA%\VioletWing\logs\`.

## Submitting Issues

Before opening an issue:

1. Search existing issues to avoid duplicates.
2. Include:
   - A clear description of the problem or bug.
   - Steps to reproduce.
   - Expected vs. actual behavior.
   - Screenshots or log excerpts (from `violetwing.log` or `violetwing_detailed.log`).

Use the [Issues tab](https://github.com/Jesewe/VioletWing/issues) and select the appropriate template (e.g., Bug Report).

## Pull Request Process

1. **Create a Branch**: Use a descriptive name:

   ```bash
   git checkout -b feature/add-new-feature
   ```

2. **Commit Changes**: Write clear, concise commit messages:

   ```bash
   git commit -m "Add bunnyhop timing adjustment in settings"
   ```

3. **Push to Fork**:

   ```bash
   git push origin feature/add-new-feature
   ```

4. **Open a Pull Request**: Submit a PR to the main repository, including:

   - Purpose of the changes (e.g., “Adds NoFlash toggle to General Settings”).
   - Impact on existing features (e.g., “No changes to TriggerBot”).
   - Testing details (e.g., “Tested in CS2 casual mode, 1920x1080”).
   - Screenshots for GUI changes.

### Review Process

- PRs are reviewed for code quality, functionality, and adherence to standards.
- Respond to feedback promptly and make requested changes.
- PRs may require rebasing if the upstream repository updates:

  ```bash
  git fetch upstream
  git rebase upstream/main
  git push --force
  ```

## Feature Requests and Feedback

Submit new ideas or improvements via the [Issues tab](https://github.com/Jesewe/VioletWing/issues) with the **Feature Request** label. Include:

- Description of the feature (e.g., “Add customizable snapline colors for Overlay”).
- Use case or benefit.
- Any mockups or examples (optional).
