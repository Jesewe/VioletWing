import customtkinter as ctk
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_ITEM_LABEL,
    FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER
)

def populate_faq(main_window, frame):
    """Populate the FAQ frame with questions and answers."""
    # Scrollable container for FAQ content
    faq_container = ctk.CTkScrollableFrame(
        frame,
        fg_color="transparent"
    )
    faq_container.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Frame for page title and subtitle
    title_frame = ctk.CTkFrame(faq_container, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 45))
    
    # FAQ title with icon
    ctk.CTkLabel(
        title_frame,
        text="❓ Frequently Asked Questions",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(anchor="w")
    
    # Subtitle providing context
    ctk.CTkLabel(
        title_frame,
        text="Find answers to common questions about TriggerBot, Overlay, Bunnyhop, and NoFlash usage and configuration",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(anchor="w", pady=(10, 0))
    
    # List of FAQ items
    faqs = [
        (
            "What is a TriggerBot?",
            "The TriggerBot automatically fires when your crosshair is over an enemy in Counter-Strike 2, enhancing reaction times in competitive play. It uses memory reads to detect enemies and simulates mouse clicks with configurable delays for a natural feel. You can set the trigger key (e.g., 'x', 'mouse4'), enable toggle mode, and adjust weapon-specific delays (Pistols, Rifles, etc.) in the Trigger Settings tab or config.json. For details, see the 'TriggerBot Overview' article in the Features collection."
        ),
        (
            "What does the Overlay (ESP) feature do?",
            "The Overlay (ESP) displays real-time visual aids on the game screen, including bounding boxes around enemies, skeletons, snaplines to targets, health numbers, nicknames, and a minimap. It helps track opponents and teammates (if enabled) effectively. Customize colors, line thickness, and minimap size in the Overlay Settings tab. For example, set 'snaplines_color_hex' to '#FFFFFF' in config.json for white lines. See the 'Overlay (ESP) Details' article for more."
        ),
        (
            "What is the Bunnyhop feature?",
            "The Bunnyhop feature automates continuous jumping in Counter-Strike 2 to maintain speed and improve movement control. It monitors the jump key (default: 'space') and writes to memory to force jumps with a configurable delay (e.g., 0.01 seconds). Adjust settings in the Additional Settings tab or config.json. Ensure the game window is focused for consistent performance. Check the 'Bunnyhop Automation' article for tips."
        ),
        (
            "What is the NoFlash feature?",
            "The NoFlash feature reduces or eliminates flashbang effects in Counter-Strike 2 by modifying the flash duration in memory. Set the suppression strength (0.0 for full removal, up to 1.0) in the Additional Settings tab or config.json. This ensures uninterrupted visibility during gameplay. For setup details, see the 'NoFlash Effect Reduction' article."
        ),
        (
            "Is this tool safe to use?",
            "VioletWing is for educational purposes only. Using automation tools in online games like Counter-Strike 2 violates terms of service and risks account bans, especially on VAC-secured servers, FACEIT, or ESEA. Use it in offline modes or private servers to avoid detection. Always review the 'Usage Disclaimer' in the Legal and Disclaimer collection before proceeding."
        ),
        (
            "How do I configure the trigger key?",
            "In the Trigger Settings tab, select or type a trigger key (e.g., 'x', 'c', 'mouse4', 'mouse5'). Alternatively, edit 'TriggerKey' in config.json (e.g., '\"TriggerKey\": \"x\"'). Supported keys include keyboard letters and mouse buttons (see 'get_vk_code' in utility.py for a full list). Test in a private match to ensure it triggers correctly. Refer to the 'TriggerBot Overview' article for advanced settings."
        ),
        (
            "What are the delay settings for?",
            "Delay settings in the Trigger Settings tab make TriggerBot shots feel human-like by randomizing timing. 'ShotDelayMin' and 'ShotDelayMax' set the range for initial shot delay (e.g., 0.01-0.03s for Rifles), while 'PostShotDelay' adds a pause after firing (e.g., 0.02s). Adjust per weapon type in the GUI or config.json (e.g., '\"Rifles\": {\"ShotDelayMin\": 0.01, \"ShotDelayMax\": 0.03, \"PostShotDelay\": 0.02}'). See 'Advanced Configuration' for examples."
        ),
        (
            "How do I customize the Overlay (ESP) settings?",
            "In the Overlay Settings tab, toggle features like bounding boxes, skeletons, snaplines, health numbers, nicknames, and the minimap. Adjust colors via hex codes (e.g., '#FFA500' for orange), line thickness, minimap size, and target FPS (default: 60). In config.json, modify the 'Overlay' section (e.g., '\"enable_box\": true, \"snaplines_color_hex\": \"#FFFFFF\"'). Lower FPS for better performance on low-end systems. See 'Overlay (ESP) Details' for a full guide."
        ),
        (
            "Can I use these features on FACEIT or ESEA?",
            "No, using VioletWing on anti-cheat platforms like FACEIT, ESEA, or VAC-secured servers is prohibited and will likely result in a permanent ban. Features like TriggerBot, Overlay, Bunnyhop, and NoFlash are detected by anti-cheat systems. Use only in offline modes, private servers, or casual matches. For safety, read the 'Usage Disclaimer' in the Legal and Disclaimer collection."
        ),
        (
            "How do I update the offsets?",
            "VioletWing automatically fetches offsets from https://github.com/a2x/cs2-dumper on startup, ensuring compatibility with Counter-Strike 2 updates. Check the last update time on the Dashboard tab. If fetching fails, manually download offsets.json, client_dll.json, and buttons.json from the cs2-dumper repository and update the URLs in utility.py. For troubleshooting, see 'Offset Fetching and Management' in the Features collection."
        ),
        (
            "Why isn't the TriggerBot triggering?",
            "If TriggerBot doesn't fire, check: 1) Trigger key is correctly set in Trigger Settings (e.g., 'x' or 'mouse4'). 2) Game window is focused. 3) Crosshair is on a valid enemy (health > 0, not teammate unless enabled). 4) Offsets are up-to-date (check Dashboard). 5) Toggle mode is active if set. Review logs in the Logs tab for errors like 'Failed to get fire logic data.' See 'Failed to Fetch Offsets' or 'Offset Errors After Game Update' in Troubleshooting."
        ),
        (
            "Why isn't the Overlay (ESP) displaying?",
            "If the Overlay isn't visible, ensure: 1) Overlay is enabled in General Settings. 2) Counter-Strike 2 is running in windowed or borderless mode (fullscreen may cause issues; see below). 3) Features like boxes or snaplines are enabled in Overlay Settings. 4) PyMeow is installed correctly (check Installation Guide). 5) Offsets are current. Check logs for errors like 'Overlay initialization error.' For details, see 'Overlay Not Displaying' in Troubleshooting."
        ),
        (
            "Why doesn't Bunnyhop work consistently?",
            "Inconsistent Bunnyhop may occur if: 1) Game window isn't focused (click the CS2 window). 2) Bunnyhop is disabled in General Settings. 3) Jump delay is too low/high (default: 0.01s; adjust in Additional Settings). 4) Server anti-cheat or tick rate limits jumping. Test in a private match and check logs for 'Error performing jump.' See 'Bunnyhop Inconsistencies' in Troubleshooting for solutions."
        ),
        (
            "Why is NoFlash not working?",
            "If NoFlash fails: 1) Ensure it's enabled in General Settings. 2) Verify offsets are updated (check Dashboard). 3) Adjust FlashSuppressionStrength (0.0 for full removal) in Additional Settings or config.json. 4) Check for anti-cheat interference. Look for 'Error disabling flash' in logs. Restart VioletWing to refresh offsets. See 'NoFlash Not Effective' in Troubleshooting."
        ),
        (
            "What should I do if the app crashes?",
            r"If VioletWing crashes: 1) Restart the app and ensure Counter-Strike 2 is running. 2) Check for updates (stable or pre-release) in the Notifications tab or https://github.com/Jesewe/VioletWing/releases. 3) Verify Python version (3.8 to <3.12.5) and dependencies (see Installation Guide). 4) Disable antivirus temporarily. 5) Review logs in %LOCALAPPDATA%\Requests\ItsJesewe\crashes\vw_logs.log for errors. See 'General Unexpected Errors' in Troubleshooting."
        ),
        (
            "Is there a hotkey to toggle features on/off?",
            "TriggerBot supports a toggle hotkey (set in Trigger Settings, e.g., 'x' or 'mouse4') with sound feedback (1000Hz for on, 500Hz for off). Other features (Overlay, Bunnyhop, NoFlash) are toggled via the General Settings tab in the GUI. To change configs quickly, edit config.json (dynamic updates apply instantly). See 'Dynamic Configuration Updates' and 'TriggerBot Overview' for more."
        ),
        (
            "Why doesn't VioletWing work properly in fullscreen mode?",
            r"Fullscreen mode may cause issues like a black background for the Overlay (ESP) due to rendering conflicts with PyMeow or graphics card settings. To fix: 1) Switch Counter-Strike 2 to windowed or borderless mode in game settings. 2) Ensure PyMeow is installed correctly (see Installation Guide). 3) Test with onboard graphics if using a dedicated GPU. 4) Check for client updates (stable or pre-release) at https://github.com/Jesewe/VioletWing/releases. For details, see 'Overlay Not Displaying' in Troubleshooting."
        ),
        (
            "What should I do if I encounter an error?",
            r"For any error: 1) Check the Logs tab or %LOCALAPPDATA%\Requests\ItsJesewe\crashes\vw_logs.log for details (e.g., 'Failed to read memory' or 'Offset error'). 2) Ensure you have the latest VioletWing client (check stable and pre-release versions at https://github.com/Jesewe/VioletWing/releases). 3) Verify offsets are updated (Dashboard). 4) Restart VioletWing and CS2. 5) Disable antivirus if blocking. See 'General Unexpected Errors' or specific Troubleshooting articles for your error."
        )
    ]
    
    # Create FAQ cards
    for i, (question, answer) in enumerate(faqs):
        # Card for each FAQ item
        faq_card = ctk.CTkFrame(
            faq_container,
            corner_radius=25,
            fg_color=SECTION_STYLE["fg_color"],
            border_width=3,
            border_color=SECTION_STYLE["border_color"]
        )
        faq_card.pack(fill="x", pady=(0, 25))
        
        # Frame for question header
        question_frame = ctk.CTkFrame(faq_card, fg_color="transparent")
        question_frame.pack(fill="x", padx=30, pady=(25, 15))
        
        # Number badge for question
        number_badge = ctk.CTkFrame(
            question_frame,
            width=45,
            height=45,
            corner_radius=22,
            fg_color=COLOR_ACCENT_FG
        )
        number_badge.pack(side="left", padx=(0, 18))
        number_badge.pack_propagate(False)
        
        # Number inside badge
        ctk.CTkLabel(
            number_badge,
            text=str(i+1),
            font=FONT_WIDGET,
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Question text
        question_label = ctk.CTkLabel(
            question_frame,
            text=question,
            font=FONT_ITEM_LABEL,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w"
        )
        question_label.pack(side="left", fill="x", expand=True)
        
        # Frame for answer text
        answer_frame = ctk.CTkFrame(faq_card, fg_color="transparent")
        answer_frame.pack(fill="x", padx=75, pady=(0, 25))
        
        # Answer text with wrapping
        ctk.CTkLabel(
            answer_frame,
            text=answer,
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
            wraplength=820,
            justify="left"
        ).pack(fill="x")
    
    # Footer with additional help information
    footer_frame = ctk.CTkFrame(
        faq_container,
        corner_radius=25,
        fg_color=SECTION_STYLE["fg_color"],
        border_width=3,
        border_color=SECTION_STYLE["border_color"]
    )
    footer_frame.pack(fill="x", pady=(40, 0))
    
    # Footer title
    ctk.CTkLabel(
        footer_frame,
        text="💡 Still have questions?",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(pady=(25, 8))
    
    # Footer guidance text
    ctk.CTkLabel(
        footer_frame,
        text="Explore these resources for more help or to contribute to VioletWing:",
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(0, 20))
    
    # Links container
    links_container = ctk.CTkFrame(footer_frame, fg_color="transparent")
    links_container.pack(pady=(0, 15))
    
    # GitHub Issues link
    def open_github_issues():
        import webbrowser
        webbrowser.open("https://github.com/Jesewe/VioletWing/issues")
    
    github_issues_btn = ctk.CTkButton(
        links_container,
        text="🐛 Report Issues",
        command=open_github_issues,
        width=160,
        **BUTTON_STYLE_DANGER
    )
    github_issues_btn.pack(side="left", padx=(0, 15))

    # GitHub Releases link
    def open_github_releases():
        import webbrowser
        webbrowser.open("https://github.com/Jesewe/VioletWing/releases")
    
    github_releases_btn = ctk.CTkButton(
        links_container,
        text="📦 Check Updates",
        command=open_github_releases,
        width=160,
        **BUTTON_STYLE_PRIMARY
    )
    github_releases_btn.pack(side="left", padx=(0, 15))

    # Help Center link
    def open_help_center():
        import webbrowser
        webbrowser.open("https://violetwing.featurebase.app/en/help")
    
    help_center_btn = ctk.CTkButton(
        links_container,
        text="📚 Help Center",
        command=open_help_center,
        width=160,
        **BUTTON_STYLE_PRIMARY
    )
    help_center_btn.pack(side="left", padx=(0, 15))
    
    # Additional footer text
    ctk.CTkLabel(
        footer_frame,
        text="Remember: This tool is for educational purposes only. Always respect game terms of service.",
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(20, 25))