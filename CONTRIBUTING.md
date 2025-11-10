# 🤝 Contributing to VioletWing

First off, **thank you** for considering contributing to VioletWing! It's people like you who make this project better for the entire community. Whether you're fixing a bug, adding a feature, or improving documentation, every contribution matters.

## 📋 Table of Contents

- [🌟 Ways to Contribute](#-ways-to-contribute)
- [📜 Code of Conduct](#-code-of-conduct)
- [🚀 Quick Start for Contributors](#-quick-start-for-contributors)
- [💻 Development Setup](#-development-setup)
- [🐛 Reporting Issues](#-reporting-issues)
- [🔄 Pull Request Process](#-pull-request-process)
- [💡 Feature Requests](#-feature-requests)
- [❓ Questions?](#-questions)

---

## 🌟 Ways to Contribute

You don't have to be a coding expert to contribute! Here are various ways you can help:

### For Everyone

- 🐛 **Report Bugs**: Found something broken? Let us know!
- 💡 **Suggest Features**: Have an idea? We'd love to hear it!
- 📖 **Improve Documentation**: Help others understand the project better
- ⭐ **Star the Project**: Show your support on GitHub
- 💬 **Help Others**: Answer questions in issues and discussions

### For Developers

- 🔧 **Fix Bugs**: Tackle open issues
- ✨ **Add Features**: Implement new functionality
- 🎨 **Enhance UI/UX**: Improve the GUI experience
- ⚡ **Optimize Performance**: Make the code faster and more efficient
- 🧪 **Write Tests**: Help ensure code quality

### For Designers

- 🎨 **Create Assets**: Design icons, banners, or UI elements
- 📱 **Improve Layouts**: Enhance the visual appeal of the GUI
- 🌈 **Theme Development**: Create new color schemes

---

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive environment. By participating, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

**In short:**

- ✅ Be respectful and inclusive
- ✅ Welcome newcomers warmly
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community
- ❌ No harassment, trolling, or inappropriate behavior

---

## 🚀 Quick Start for Contributors

Ready to contribute? Here's how to get started in 5 minutes:

### 1️⃣ Fork & Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/Jesewe/VioletWing.git
cd VioletWing
```

### 2️⃣ Set Up Remote

```bash
# Add the original repository as upstream
git remote add upstream https://github.com/Jesewe/VioletWing.git
```

### 3️⃣ Create a Branch

```bash
# Create a new branch for your changes
git checkout -b feature/your-awesome-feature
```

### 4️⃣ Make Changes

- Write your code
- Test thoroughly
- Commit with clear messages

### 5️⃣ Submit Pull Request

- Push to your fork
- Open a PR to the main repository
- Respond to feedback

---

## 💻 Development Setup

### System Requirements

- **Python Version**: ≥ 3.8 and < 3.12.10
- **Operating System**: Windows (CS2 compatibility)

### Installation Steps

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install PyMeow (required for overlay rendering)
# Download from: https://github.com/qb-0/pyMeow/releases
pip install pyMeow*.zip

# 3. Run the application
python main.py
```

### Testing Your Changes

#### Basic Testing

```bash
# Run the application
python main.py

# Check for errors in logs
# Location: %LOCALAPPDATA%\VioletWing\logs\
```

#### Feature-Specific Testing

| Feature           | What to Test                                         |
| ----------------- | ---------------------------------------------------- |
| **TriggerBot**    | Key bindings, delays, weapon-specific timing         |
| **Overlay (ESP)** | Visual elements at different resolutions, FPS impact |
| **Bunnyhop**      | Movement smoothness, key response, timing            |
| **NoFlash**       | Flash suppression effectiveness, performance         |
| **GUI**           | Responsiveness, theme consistency, element alignment |

#### Testing Checklist

- [ ] Application launches without errors
- [ ] All GUI elements display correctly
- [ ] Configuration changes apply properly
- [ ] Logs show no unexpected errors
- [ ] Features work in CS2 (offline/casual mode)
- [ ] No performance degradation

---

## ✍️ Coding Standards

Consistent code is maintainable code! Follow these guidelines:

### General Python Guidelines

#### ✅ Do This

```python
# Clear, descriptive names
trigger_key = "x"
shot_delay_min = 0.1
is_trigger_enabled = True

# Proper docstrings
def calculate_delay(weapon_type: str) -> float:
    """
    Calculate shot delay based on weapon type.

    Args:
        weapon_type: Type of weapon (pistol, rifle, sniper, etc.)

    Returns:
        Calculated delay in seconds
    """
    pass
```

#### ❌ Avoid This

```python
# Unclear, abbreviated names
tk = "x"
sd_min = 0.1
te = True

# Missing documentation
def calc_del(wt):
    pass
```

### Code Style Rules

- **Follow PEP 8**: Use the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/)
- **Line Length**: Maximum 120 characters (not the strict 79)
- **Imports**: Group by standard library, third-party, local (with blank lines between)
- **Naming Conventions**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Error Handling

Always implement robust error handling:

```python
# Good error handling
try:
    result = risky_operation()
    logger.info(f"Operation successful: {result}")
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    # Handle gracefully
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # Fallback behavior
```

### Logging Best Practices

```python
# Use appropriate log levels
logger.info("Application started successfully")      # General info
logger.warning("Offset fetch took longer than expected")  # Potential issues
logger.error("Failed to connect to game process")    # Errors
logger.debug("Variable state: x=5, y=10")           # Debugging info
```

### GUI Development

When working with the GUI:

- **Framework**: Use `customtkinter` for all UI elements
- **Theme Consistency**:
  - Colors: Match existing palette (purple accents: `#8E44AD`)
  - Fonts: Use Chivo (regular), Gambetta (headings)
- **Layout**: Follow the card-based design pattern
- **Responsiveness**: Test at different window sizes (minimum 1000x600)

#### GUI Example

```python
# Good GUI code
button = ctk.CTkButton(
    master=parent_frame,
    text="Enable Feature",
    command=self.toggle_feature,
    fg_color="transparent",
    hover_color=COLOR_WIDGET_BACKGROUND,
    text_color=COLOR_TEXT_SECONDARY,
    font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4),
    corner_radius=8
)
button.pack(pady=10, padx=20, fill="x")
```

### Feature-Specific Guidelines

#### TriggerBot Development

- Ensure compatibility with offset updates from [cs2-dumper](https://github.com/a2x/cs2-dumper)
- Test weapon-specific timing across all categories
- Validate key binding edge cases

#### Overlay (ESP) Development

- Test visual elements at 1920x1080, 2560x1440, 3840x2160
- Optimize rendering for 60+ FPS
- Ensure proper cleanup of overlay resources

#### Bunnyhop Development

- Verify timing across different surfaces (concrete, metal, etc.)
- Test at various FPS rates
- Handle edge cases (stairs, ladders, water)

#### NoFlash Development

- Test with various flash suppression strengths
- Ensure no unintended visual artifacts
- Validate performance impact is minimal

### Documentation Standards

- **Docstrings**: Required for all public functions and classes
- **Comments**: Explain WHY, not WHAT (code should be self-explanatory)
- **README**: Update if you add/change features
- **Changelog**: Mention significant changes

---

## 🐛 Reporting Issues

Found a bug? Here's how to report it effectively:

### Before You Submit

1. **Search Existing Issues**: Your issue might already be reported
2. **Update to Latest**: Ensure you're using the latest version
3. **Reproduce**: Try to reproduce the bug consistently
4. **Gather Info**: Collect logs, screenshots, system details

### Creating a Great Bug Report

Use the [Issues tab](https://github.com/Jesewe/VioletWing/issues) and include:

#### Required Information

- **Clear Title**: e.g., "[Bug] TriggerBot not firing with Mouse5 key"
- **Description**: What happened
- **Environment**:
  - OS: Windows 11 Pro 25H2
  - Python: 3.12.10
  - VioletWing Version: 1.2.8.9
- **Logs**: Attach relevant excerpts from `violetwing.log` or `violetwing_detailed.log`

#### Optional But Helpful

- Screenshots or video recordings
- Configuration file (`config.json`)
- Console output
- Related issues or PRs

### Issue Templates

We provide templates for:

- 🐛 Bug Reports
- ✨ Feature Requests
- 📖 Documentation Improvements
- ❓ Questions

---

## 🔄 Pull Request Process

### Before You Start

- **Discuss First**: For major changes, open an issue to discuss your approach
- **Check Existing PRs**: Someone might already be working on it
- **One Feature Per PR**: Keep changes focused and reviewable

### Step-by-Step Guide

#### 1. Create Your Branch

```bash
# Use descriptive branch names
git checkout -b feature/add-weapon-switching
git checkout -b bugfix/trigger-delay-calculation
git checkout -b docs/update-installation-guide
```

#### 2. Make Your Changes

- Write clean, documented code
- Follow coding standards
- Test thoroughly
- Keep commits logical and atomic

#### 3. Commit with Clear Messages

```bash
# Good commit messages
git commit -m "feat: Weapon switching detection for TriggerBot"
git commit -m "fix: Incorrect delay calculation for SMG weapons"
git commit -m "docs: Update installation guide with PyMeow steps"

# Use conventional commits (optional but appreciated)
# feat: New feature
# fix: Bug fix
# docs: Documentation
# style: Formatting
# refactor: Code restructuring
# test: Adding tests
# chore: Maintenance
```

#### 4. Keep Your Branch Updated

```bash
# Sync with upstream regularly
git fetch upstream
git rebase upstream/main

# Or merge if you prefer
git merge upstream/main
```

#### 5. Push to Your Fork

```bash
git push origin feature/your-feature-name

# If you rebased, you'll need to force push
git push --force origin feature/your-feature-name
```

#### 6. Open a Pull Request

Navigate to the [Pull Requests tab](https://github.com/Jesewe/VioletWing/pulls) and click "New Pull Request".

### PR Description Template

```markdown
## Proposed Feature

_Describe the proposed solution. Describe what the new feature is intended to do._

## Checklist

- [ ] This feature is not already implemented or planned (please search existing issues).
- [ ] I have reviewed the [contributing guidelines](https://github.com/Jesewe/cs2-triggerbot/blob/main/CONTRIBUTING.md) for feature requests.
```

---

## 💡 Feature Requests

Have an idea to make VioletWing better? We'd love to hear it!

### Submitting Feature Requests

1. **Open an Issue**: Use the [Issues tab](https://github.com/Jesewe/VioletWing/issues)
2. **Select Template**: Choose "Feature Request"
3. **Provide Details**:
   - **Problem**: What problem does this solve?
   - **Solution**: Describe your proposed solution
   - **Alternatives**: Any alternative approaches?
   - **Use Case**: When would this be useful?
   - **Mockups**: Visual examples (optional)

### What Makes a Good Feature Request?

✅ **Good Features:**

- Solve a real problem
- Fit the project's scope
- Are technically feasible
- Benefit multiple users
- Don't compromise ethics/safety

❌ **Avoid:**

- Features that violate game ToS in online play
- Unrealistic or impossible implementations
- Duplicate existing functionality
- Overly complex single-use features

---

## ❓ Questions?

### Getting Help

- **Documentation**: Check the README and in-app FAQ
- **Issues**: Search existing issues for answers
- **Logs**: Check `%LOCALAPPDATA%\VioletWing\logs\` for error details

### Community Channels

- **GitHub Issues**: Technical questions and bug reports
- **Pull Requests**: Code-specific discussions

### Response Times

We're a community-driven project, so response times vary:

- **Issues**: Usually within 24-48 hours
- **PRs**: Initial review within 1-3 days
- **Discussions**: Community members may respond anytime

---

## 🙏 Thank You!

Every contribution, no matter how small, makes VioletWing better for everyone. Thank you for taking the time to contribute!

### Recognition

- Contributors are listed in the project's README
- Significant contributions are highlighted in release notes
- Your GitHub profile will show your contributions

### Next Steps

1. ⭐ **Star the Repository**: Show your support
2. 👀 **Watch the Repository**: Stay updated on changes
3. 🍴 **Fork and Experiment**: Try adding your own features
4. 🤝 **Submit Your First PR**: Even small fixes are valuable!

---
