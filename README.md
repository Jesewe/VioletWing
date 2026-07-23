<div align="center">
   <img src="/assets/assets/icon.png" alt="VioletWing" width="200" height="200">
   <h1>VioletWing</h1>
   <p>TriggerBot · ESP · Bunnyhop · NoFlash - all in one for Counter-Strike 2</p>

[![Downloads](https://img.shields.io/github/downloads/jesewe/VioletWing/total?style=for-the-badge&logo=github&color=8E44AD)](https://github.com/Jesewe/VioletWing/releases)
[![Latest Release](https://img.shields.io/github/v/release/jesewe/VioletWing?style=for-the-badge&logo=github&color=8E44AD)](https://github.com/Jesewe/VioletWing/releases/latest/)
[![License](https://img.shields.io/github/license/jesewe/VioletWing?style=for-the-badge&color=8E44AD)](LICENSE)

</div>

---

External tool for CS2. Reads game memory, draws an overlay, fires on your behalf - configurable per weapon, per key, per taste. On startup it runs [cs2-dumper](https://github.com/a2x/cs2-dumper) directly against the live CS2 process to generate fresh offsets, so you stay functional after patches without touching a config file.

> [!WARNING]
> Using this in online matchmaking violates CS2's Terms of Service and will get your account VAC banned. Run it offline or in private servers - that's on you.

> [!IMPORTANT]
> Antivirus software will flag this. It reads another process's memory, which looks identical to malware from AV's perspective. Read the source, build it yourself, and add an exception if you trust what you see.

---

## Quick Start

1. Download `VioletWing.exe` from the [**Releases**](https://github.com/Jesewe/VioletWing/releases) page
2. Launch CS2, then run VioletWing **as Administrator**
3. VioletWing downloads `cs2-dumper.exe` on first launch and generates offsets automatically
4. Enable features from the GUI

> [!NOTE]
> Run CS2 in **windowed** or **borderless windowed** mode. Exclusive fullscreen breaks the overlay.

---

## Features

### TriggerBot

Fires when your crosshair lands on an enemy. Weapon-specific delays keep the timing pattern from looking mechanical - Snipers wait longer than Pistols.

- Keys: `x`, `c`, `mouse4`, `mouse5` (or toggle mode)
- Per-class delays: Pistols, Rifles, Snipers, SMGs, Heavy
- Tunable `ShotDelayMin`, `ShotDelayMax`, `PostShotDelay`

### ESP Overlay

Draws over the game window. Only renders while you are in an active match - no spam in the lobby.

- Bounding boxes, skeletons, snaplines
- Health bars, player names, and weapon names
- Spectator list showing who watches you or your target
- Bomb timer with defuse countdown
- Watermark showing FPS, ping, and current map name
- Fully customizable colors and line thickness
- Selectable overlay typography (all fonts are sourced from [Google Fonts](https://fonts.google.com/))

### Bunnyhop

Synchronizes player jumps by writing to CS2's jump state (`+jump`) gated by the player's `m_fFlags` ground state. Checks `ON_GROUND` state each tick while the jump key is held to ensure 1-tick jump timing and preserve full momentum.

- Custom jump key binding
- Precise ground-state (`m_fFlags`) synchronization

### NoFlash

Clamps flash duration. Flashbangs still go off - you just stop going blind.

### GUI

Full desktop interface. No command line required.

- Dashboard: live status, cs2-dumper version, app version
- Tabs for General, Trigger, Overlay, and Additional settings
- Integrated log viewer and FAQ
- Auto-update checking with stable/pre-release toggle

---

## Build from Source

```bash
git clone https://github.com/Jesewe/VioletWing.git
cd VioletWing
pip install -r requirements.txt

# PyMeow is required for the overlay - download from:
# https://github.com/qb-0/pyMeow/releases
pip install pyMeow*.zip

python main.py
```

To build a standalone `.exe`:

```bash
compile.bat
```

**Python requirement:** `>= 3.8` and `< 3.12.10`

---

## Configuration

All settings save to `config.json`. The GUI writes it for you, but you can edit it by hand - VioletWing picks up changes live without a restart.

Log files: `%LOCALAPPDATA%\VioletWing\logs\`

Full config reference in the [wiki](https://github.com/Jesewe/VioletWing/wiki/Settings).

---

## Troubleshooting

| Issue                              | Fix                                                                                                                                                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cs2-dumper download fails          | Check internet connection; allow HTTPS to `github.com`                                                                                                                              |
| "CS2 is not running" on startup    | Launch CS2 before starting VioletWing                                                                                                                                               |
| Features break after a game update | Restart VioletWing - it reruns cs2-dumper automatically. If cs2-dumper hasn't updated yet, [wait for a new release](https://github.com/a2x/cs2-dumper/releases)                     |
| Can't open `cs2.exe`               | Run VioletWing as Administrator                                                                                                                                                     |
| Overlay not visible                | Switch CS2 to windowed or borderless mode                                                                                                                                           |
| ESP overlay is a black rectangle   | NVIDIA driver bug - NVIDIA Control Panel → Manage 3D Settings → **OpenGL GDI compatibility** → **Prefer compatible** ([raylib#2932](https://github.com/raysan5/raylib/issues/2932)) |
| Bunnyhop feels inconsistent        | CS2 window must have focus; verify your jump key binding                                                                                                                            |
| NoFlash does nothing               | Confirm offsets loaded and the feature is enabled in General settings                                                                                                               |

More detail in the [wiki](https://github.com/Jesewe/VioletWing/wiki/Troubleshooting).

---

## Credits

- [**a2x**](https://github.com/a2x) for [cs2-dumper](https://github.com/a2x/cs2-dumper)
- All fonts are sourced from [Google Fonts](https://fonts.google.com/)
- All [contributors](https://github.com/Jesewe/VioletWing/graphs/contributors) who filed issues, submitted PRs, and tested builds

---

## License

VioletWing is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for the full text.
