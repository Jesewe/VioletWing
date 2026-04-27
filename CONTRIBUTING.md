# Contributing to VioletWing

## Before you start

Search [open issues](https://github.com/Jesewe/VioletWing/issues) and [pull requests](https://github.com/Jesewe/VioletWing/pulls) before opening anything new. For significant changes, open an issue first to align on approach before writing code.

---

## Setup

**Requirements:** Python `>= 3.8` and `< 3.12.10`, Windows only.

```bash
git clone https://github.com/Jesewe/VioletWing.git
cd VioletWing
pip install -r requirements.txt

# PyMeow is required for the overlay
# Download the .zip from https://github.com/qb-0/pyMeow/releases
pip install pyMeow*.zip

python main.py
```

---

## Workflow

```bash
# Fork, then clone your fork
git clone https://github.com/YOUR_USERNAME/VioletWing.git

# Add upstream
git remote add upstream https://github.com/Jesewe/VioletWing.git

# Branch off main
git checkout -b fix/trigger-delay-smg

# Keep your branch current
git fetch upstream && git rebase upstream/main
```

One feature or fix per PR. Keep changes focused.

---

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add per-key delay override for TriggerBot
fix: incorrect shot delay for SMG weapon class
docs: update PyMeow install steps
chore: bump customtkinter to 5.2.3
refactor: extract overlay color parsing to utility
```

---

## Code standards

- PEP 8, max line length 120
- `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants
- Imports: standard library → third-party → local, separated by blank lines
- Comments explain _why_, not _what_
- All public functions and classes need docstrings

**Error handling:** catch specific exceptions first, log with `exc_info=True` on unexpected errors, always fail gracefully.

**GUI:** use `customtkinter` only. Match the existing purple accent (`#8E44AD`), Chivo/Gambetta fonts, card-based layout. Test at 1000×600 minimum.

**Overlay:** test at 1080p, 1440p, and 4K. Keep the render loop at 60+ FPS.

**Offsets:** all memory reads depend on [cs2-dumper](https://github.com/a2x/cs2-dumper). Don't hardcode offsets - fetch them at runtime.

---

## Testing

Run the app and test your change in CS2 offline or in a private server. There is no automated test suite - include a short description of what you tested in your PR.

| Feature    | Test focus                                      |
| ---------- | ----------------------------------------------- |
| TriggerBot | Key bindings, per-weapon delays, toggle mode    |
| Overlay    | Visual elements, FPS impact, resolution scaling |
| Bunnyhop   | Timing at different FPS, window focus behavior  |
| NoFlash    | Suppression strength range, no visual artifacts |
| GUI        | Config persistence, live reload, window resize  |

Logs write to `%LOCALAPPDATA%\VioletWing\logs\violetwing.log`. Check them before submitting.

---

## Pull request checklist

- [ ] Rebased on `main`
- [ ] Tested in CS2 offline or private server
- [ ] No new linting errors
- [ ] README updated if the change affects documented behavior
- [ ] PR description explains what changed and why

---

## Reporting bugs

Use the [Bug Report](https://github.com/Jesewe/VioletWing/issues/new?template=bug_report.yml) template. Attach logs - reports without them are difficult to act on.

---

## Questions

Check the [in-app FAQ](https://violetwing.featurebase.app/en/help) or open a [Discussion](https://github.com/Jesewe/VioletWing/discussions). Don't open issues for general questions.
