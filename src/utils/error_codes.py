from dataclasses import dataclass


@dataclass(frozen=True)
class _Entry:
    id: str
    label: str
    solution: str


# E0xxx - Startup / Init
E0001 = _Entry(
    id="E0001",
    label="Resource path resolution failed",
    solution="A bundled asset could not be located. Reinstall VioletWing or run from the correct working directory.",
)

# E1xxx - Config / File I/O
E1001 = _Entry(
    id="E1001",
    label="Config directory creation failed",
    solution="VioletWing could not create its config folder. Check that you have write permissions to %APPDATA%\\Local\\VioletWing.",
)

E1002 = _Entry(
    id="E1002",
    label="Config load failed",
    solution="config.json could not be read or is malformed. The default configuration will be used. Delete config.json to regenerate it, or check for syntax errors.",
)

E1003 = _Entry(
    id="E1003",
    label="Config save failed",
    solution="VioletWing could not write config.json. Check that the file is not open in another program and that you have write access to the config directory.",
)

E1004 = _Entry(
    id="E1004",
    label="ghosts.json parse error",
    solution="ghosts.json is not valid JSON. Open it in a text editor, fix the syntax error, and restart VioletWing. Disguise mode is disabled until resolved.",
)

E1005 = _Entry(
    id="E1005",
    label="ghosts.json schema error",
    solution="ghosts.json must contain a JSON array (e.g. [{...}, {...}]). Check the file structure and restart VioletWing.",
)

E1006 = _Entry(
    id="E1006",
    label="Profile save failed",
    solution="VioletWing could not write the profile file. Check that you have write permissions to the profiles directory inside the config folder.",
)

E1007 = _Entry(
    id="E1007",
    label="Profile load failed",
    solution="The selected profile file could not be read or is malformed. Delete the profile and save it again, or check for JSON syntax errors in the profiles directory.",
)

# E2xxx - Memory / Offsets
E2001 = _Entry(
    id="E2001",
    label="CS2 process not found",
    solution="cs2.exe is not running. Launch CS2 before starting VioletWing.",
)

E2002 = _Entry(
    id="E2002",
    label="CS2 process attach failed",
    solution="VioletWing could not attach to cs2.exe. Try running VioletWing as Administrator.",
)

E2003 = _Entry(
    id="E2003",
    label="client.dll not found",
    solution="client.dll is not loaded. Make sure CS2 has fully loaded into the main menu before starting VioletWing.",
)

E2004 = _Entry(
    id="E2004",
    label="client.dll retrieval failed",
    solution="VioletWing could not read the client.dll module. Try running as Administrator. If the problem persists, restart CS2 and VioletWing.",
)

E2005 = _Entry(
    id="E2005",
    label="Offset extraction failed",
    solution="The downloaded offset data is missing required fields. Wait for updated offsets to be published after a CS2 update, then restart VioletWing.",
)

E2006 = _Entry(
    id="E2006",
    label="Stale offsets - game updated",
    solution="CS2 was updated and the current offsets are no longer valid. Wait for cs2-dumper to publish new offsets (usually within a few hours), then restart VioletWing.",
)

E2007 = _Entry(
    id="E2007",
    label="Offset init error - missing keys",
    solution="The offset data is incomplete. Restart VioletWing to re-fetch offsets. If the error persists, CS2 may have just updated - wait and try again.",
)

# E3xxx - Features (Bunnyhop, ESP, TriggerBot, NoFlash)
E3001 = _Entry(
    id="E3001",
    label="Bunnyhop address init failed",
    solution="The jump offset is not available. Ensure offsets loaded successfully (check for E2xxx errors above). Bunnyhop is disabled until resolved.",
)

E3002 = _Entry(
    id="E3002",
    label="Bunnyhop unexpected crash",
    solution="An unhandled exception occurred in the Bunnyhop loop. Check the detailed log for the full traceback. If it happens repeatedly, report it via GitHub Issues.",
)

E3003 = _Entry(
    id="E3003",
    label="NoFlash address init failed",
    solution="The player or flash offset is not available. Ensure offsets loaded successfully (check for E2xxx errors). NoFlash is disabled until resolved.",
)

E3004 = _Entry(
    id="E3004",
    label="NoFlash unexpected crash",
    solution="An unhandled exception occurred in the NoFlash loop. Check the detailed log for the full traceback. If it happens repeatedly, report it via GitHub Issues.",
)

E3005 = _Entry(
    id="E3005",
    label="ESP overlay init failed",
    solution="The ESP overlay window could not be created. Check that your graphics drivers are up to date. If using multiple monitors, try moving the game to your primary display.",
)

E3006 = _Entry(
    id="E3006",
    label="ESP overlay unexpected crash",
    solution="An unhandled exception occurred in the ESP loop. Check the detailed log for the full traceback. If it happens repeatedly, report it via GitHub Issues.",
)

E3007 = _Entry(
    id="E3007",
    label="TriggerBot unexpected crash",
    solution="An unhandled exception occurred in the TriggerBot loop. Check the detailed log for the full traceback. If it happens repeatedly, report it via GitHub Issues.",
)

E3008 = _Entry(
    id="E3008",
    label="TriggerBot mouse listener error",
    solution="VioletWing could not stop the mouse listener cleanly. This is usually harmless. Restart VioletWing if mouse input behaves unexpectedly afterward.",
)

# E4xxx - Network / Updates / Offsets fetch
E4010 = _Entry(
    id="E4010",
    label="Update check failed",
    solution="VioletWing could not reach the update server. This is non-critical - all features still work. Check your internet connection if you want to verify your version.",
)

E4011 = _Entry(
    id="E4011",
    label="Update download failed",
    solution="VioletWing downloaded an update but could not apply it. Check that the update directory is writable and that no antivirus is blocking the installer. You can update manually from the GitHub releases page.",
)

E4012 = _Entry(
    id="E4012",
    label="cs2-dumper cannot run - CS2 is not running",
    solution="Launch CS2 and wait for it to reach the main menu before starting VioletWing. cs2-dumper reads live process memory and requires an active CS2 process.",
)
 
E4013 = _Entry(
    id="E4013",
    label="cs2-dumper subprocess failed",
    solution="cs2-dumper exited with an error. Run VioletWing as Administrator and ensure CS2 is fully loaded into the main menu. Check the detailed log for cs2-dumper's stderr output. If cs2-dumper is outdated after a CS2 update, it will be re-downloaded automatically on the next attempt.",
)
 
E4014 = _Entry(
    id="E4014",
    label="cs2-dumper binary missing or could not be downloaded",
    solution="VioletWing failed to download cs2-dumper.exe from GitHub Releases. Check your internet connection and firewall. If the problem persists, manually place cs2-dumper.exe in the VioletWing config directory.",
)
 
E4015 = _Entry(
    id="E4015",
    label="cs2-dumper output files missing or invalid",
    solution="cs2-dumper ran but did not produce valid output. Ensure CS2 is fully loaded into the main menu (not mid-loading) before retrying. Check the detailed log for cs2-dumper's own error output.",
)

# Lookup helpers
CATALOG: dict[str, _Entry] = {
    v.id: v
    for k, v in globals().items()
    if isinstance(v, _Entry)
}
