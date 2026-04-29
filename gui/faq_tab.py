import customtkinter as ctk
from gui.icon_loader import icon_label, load_icon
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_ITEM_LABEL,
    FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER
)

def populate_faq(main_window, frame):
    """Populate the FAQ frame with questions and answers."""
    # Clear existing widgets to prevent duplication
    for widget in frame.winfo_children():
        widget.destroy()
    
    # Scrollable container for FAQ content
    faq_container = ctk.CTkScrollableFrame(
        frame,
        fg_color="transparent"
    )
    faq_container.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    faq_container._parent_canvas.configure(yscrollincrement=5)
    
    # Header section with fixed height
    header_frame = ctk.CTkFrame(
        faq_container,
        fg_color="transparent",
        height=100
    )
    header_frame.pack(fill="x", pady=(0, 35))
    header_frame.pack_propagate(False)
    
    # Container for title and subtitle
    title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_container.pack(side="left", fill="y")
    
    # FAQ title with icon
    _icon_row = ctk.CTkFrame(title_container, fg_color="transparent")
    _icon_row.pack(anchor="w", pady=(10, 0))
    icon_label(_icon_row, "circle_question_icon.png", size=(32, 32), padx=(0, 14))
    title_label = ctk.CTkLabel(
        _icon_row,
        text="Frequently Asked Questions",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    )
    title_label.pack(side="left")
    
    # Subtitle providing context
    subtitle_label = ctk.CTkLabel(
        title_container,
        text="Find answers to common questions about TriggerBot, Overlay, Bunnyhop, and NoFlash usage and configuration",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    )
    subtitle_label.pack(anchor="w", pady=(8, 0))
    
    # List of FAQ items
    faqs = [
        (
            "What is a TriggerBot?",
            "TriggerBot reads game memory to detect when your crosshair is over an enemy, then simulates a mouse click. Set your trigger key (e.g. 'x', 'mouse4'), enable toggle mode if you prefer, and tune per-weapon delays in the Trigger Settings tab or config.json."
        ),
        (
            "What does the Overlay (ESP) feature do?",
            "The Overlay draws on top of the game window and shows bounding boxes, skeletons, snaplines, health bars, names, and a minimap for enemies (and optionally teammates). Adjust colors, line thickness, and minimap size in the Overlay Settings tab. Changes to config.json apply instantly without a restart."
        ),
        (
            "What is the Bunnyhop feature?",
            "Bunnyhop monitors your jump key (default: Space) and re-triggers it automatically so you land and jump again at the right tick. The jump delay is configurable in the Additional Settings tab. CS2 must have window focus for it to work."
        ),
        (
            "What is the NoFlash feature?",
            "NoFlash modifies the flash duration value in memory so flashbangs have no effect. Set FlashSuppressionStrength to 0.0 for full removal or a higher value for partial suppression. Configure it in the Additional Settings tab or config.json."
        ),
        (
            "Is this tool safe to use?",
            "Not in online matchmaking. VAC, FACEIT, and ESEA all detect tools like this - a ban is the likely outcome. VioletWing is for offline modes and private servers only."
        ),
        (
            "How do I configure the trigger key?",
            "Open the Trigger Settings tab and pick or type your key (e.g. 'x', 'c', 'mouse4', 'mouse5'). You can also set 'TriggerKey' directly in config.json. For the full list of supported keys, see get_vk_code in utility.py."
        ),
        (
            "What are the delay settings for?",
            "ShotDelayMin and ShotDelayMax randomize how long TriggerBot waits before firing, making shots less mechanical. PostShotDelay adds a pause after each shot. Tune per weapon class - Rifles around 10–30 ms, Snipers around 50–100 ms - in the Trigger Settings tab or config.json."
        ),
        (
            "How do I customize the Overlay (ESP) settings?",
            "Use the Overlay Settings tab to toggle boxes, skeletons, snaplines, health, names, and the minimap. Set colors with hex codes (e.g. '#FFA500' for orange), adjust line thickness and minimap size, and cap the overlay FPS. Lower the FPS cap on weaker hardware to reduce CPU load."
        ),
        (
            "Can I use these features on FACEIT or ESEA?",
            "No. FACEIT and ESEA run kernel-level anti-cheat. Every feature in VioletWing is detectable there. You will get permanently banned. Use offline modes or private servers only."
        ),
        (
            "How do I update the offsets?",
            "VioletWing fetches offsets from github.com/a2x/cs2-dumper automatically on startup. After a CS2 update, wait for cs2-dumper to publish new offsets, then restart VioletWing. If auto-fetch fails, check your internet connection and firewall - the Dashboard tab shows the last successful update time."
        ),
        (
            "Why isn't the TriggerBot triggering?",
            "Work through this list: trigger key set correctly in Trigger Settings → CS2 window has focus → crosshair is on a live enemy (not a teammate) → offsets loaded successfully (check Dashboard) → toggle mode not stuck in off state. The Logs tab will show the exact failure if something is wrong."
        ),
        (
            "Why isn't the Overlay displaying?",
            "Check: Overlay enabled in General Settings → CS2 in windowed or borderless mode → boxes or snaplines enabled in Overlay Settings → PyMeow installed without errors → offsets current. If the overlay appears but shows a black rectangle instead of transparency, see the fullscreen/GPU question below."
        ),
        (
            "Why doesn't Bunnyhop work consistently?",
            "CS2 must have window focus - clicking away breaks it. Default jump delay is 0.01s; too low on high-tickrate servers can cause missed frames. Raise it slightly in Additional Settings and test in a private match."
        ),
        (
            "Why is NoFlash not working?",
            "Confirm it is enabled in General Settings and that offsets loaded on startup (check Dashboard). Set FlashSuppressionStrength to 0.0 for full removal. If it still fails, check the Logs tab for 'Error disabling flash' and restart VioletWing to force an offset refresh."
        ),
        (
            "What should I do if the app crashes?",
            r"Check %LOCALAPPDATA%\VioletWing\crashes\violetwing.log first - the error is almost always there. Common causes: wrong Python version (must be >=3.8 and <3.12.10), a missing dependency, or antivirus quarantining the binary. Disable AV temporarily and verify your Python version, then retry."
        ),
        (
            "Is there a hotkey to toggle features on/off?",
            "TriggerBot has a toggle key (set in Trigger Settings). It plays a tone when switching - 1000 Hz for on, 500 Hz for off. Overlay, Bunnyhop, and NoFlash toggle through the General Settings tab. Edits to config.json apply live without restarting."
        ),
        (
            "Why does the ESP overlay show a black background?",
            "This is an NVIDIA driver bug with transparent OpenGL windows. Open NVIDIA Control Panel → Manage 3D Settings → find 'OpenGL GDI compatibility' and set it to 'Prefer compatible'. The overlay will render correctly after restarting VioletWing. Intel and AMD GPUs are not affected."
        ),
        (
            "What should I do if I encounter an error?",
            r"Open the Logs tab or check %LOCALAPPDATA%\VioletWing\violetwing.log. Note the exact error message, then: verify offsets loaded (Dashboard) → confirm you're on the latest release → restart both CS2 and VioletWing → disable antivirus if it is blocking file access. If the issue persists, open a GitHub issue with the log attached."
        ),
    ]
    
    # Create FAQ cards
    for i, (question, answer) in enumerate(faqs):
        is_last = (i == len(faqs) - 1)
        create_faq_card(faq_container, i + 1, question, answer, is_last)
    
    # Footer with additional help information
    footer_frame = ctk.CTkFrame(
        faq_container,
        **SECTION_STYLE
    )
    footer_frame.pack(fill="x", pady=(40, 0))
    
    # Footer content
    footer_content = ctk.CTkFrame(footer_frame, fg_color="transparent")
    footer_content.pack(padx=50, pady=40)
    
    # Footer title
    _footer_title_row = ctk.CTkFrame(footer_content, fg_color="transparent")
    _footer_title_row.pack(pady=(0, 8))
    icon_label(_footer_title_row, "lightbulb_icon.png", size=(20, 20), padx=(0, 10))
    ctk.CTkLabel(
        _footer_title_row,
        text="Still have questions?",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(side="left")
    
    # Footer guidance text
    ctk.CTkLabel(
        footer_content,
        text="Explore these resources for more help or to contribute to VioletWing:",
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(0, 20))
    
    # Links container
    links_container = ctk.CTkFrame(footer_content, fg_color="transparent")
    links_container.pack()
    
    # GitHub Issues link
    def open_github_issues():
        import webbrowser
        webbrowser.open("https://github.com/Jesewe/VioletWing/issues")
    
    _bug_icon = load_icon("bug_icon.png", size=(16, 16))
    github_issues_btn = ctk.CTkButton(
        links_container,
        text="Report Issues",
        image=_bug_icon, compound="left",
        command=open_github_issues,
        width=160,
        **BUTTON_STYLE_DANGER
    )
    github_issues_btn.pack(side="left", padx=(0, 15))

    # GitHub Releases link
    def open_github_releases():
        import webbrowser
        webbrowser.open("https://github.com/Jesewe/VioletWing/releases/latest/")
    
    _archive_icon = load_icon("box_archive_icon.png", size=(16, 16))
    github_releases_btn = ctk.CTkButton(
        links_container,
        text="Check Updates",
        image=_archive_icon, compound="left",
        command=open_github_releases,
        width=160,
        **BUTTON_STYLE_PRIMARY
    )
    github_releases_btn.pack(side="left", padx=(0, 15))

    # Help Center link
    def open_help_center():
        import webbrowser
        webbrowser.open("https://violetwing.vercel.app/")
    
    _book_icon = load_icon("book_open_icon.png", size=(16, 16))
    help_center_btn = ctk.CTkButton(
        links_container,
        text="Help Center",
        image=_book_icon, compound="left",
        command=open_help_center,
        width=160,
        **BUTTON_STYLE_PRIMARY
    )
    help_center_btn.pack(side="left", padx=(0, 15))
    
    # Additional footer text
    ctk.CTkLabel(
        footer_content,
        text="Remember: This tool is for educational purposes only. Always respect game terms of service.",
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(20, 0))

def create_faq_card(container, number, question, answer, is_last=False):
    """Create a card for a single FAQ item."""
    # Card for each FAQ item
    faq_card = ctk.CTkFrame(
        container,
        **SECTION_STYLE
    )
    faq_card.pack(fill="x", pady=(0, 30 if not is_last else 0))
    
    # Frame for question header
    question_frame = ctk.CTkFrame(faq_card, fg_color="transparent")
    question_frame.pack(fill="x", padx=30, pady=(25, 15))
    
    # Number badge for question
    number_badge = ctk.CTkFrame(
        question_frame,
        width=50,
        height=50,
        corner_radius=25,
        fg_color=COLOR_ACCENT_FG
    )
    number_badge.pack(side="left", padx=(0, 18))
    number_badge.pack_propagate(False)
    
    # Number inside badge
    ctk.CTkLabel(
        number_badge,
        text=str(number),
        font=FONT_ITEM_LABEL,
        text_color="#ffffff"
    ).place(relx=0.5, rely=0.5, anchor="center")
    
    # Question text
    question_label = ctk.CTkLabel(
        question_frame,
        text=question,
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    )
    question_label.pack(side="left", fill="x", expand=True)
    
    # Frame for answer text
    answer_frame = ctk.CTkFrame(faq_card, fg_color="transparent")
    answer_frame.pack(fill="x", padx=78, pady=(0, 25))
    
    # Answer text with wrapping
    answer_label = ctk.CTkLabel(
        answer_frame,
        text=answer,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
        wraplength=800,
        justify="left"
    )
    answer_label.pack(fill="x")