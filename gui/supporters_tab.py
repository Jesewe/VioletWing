import customtkinter as ctk
import orjson
import threading
import requests
from classes.logger import Logger
from classes.utility import Utility
from gui.theme import (FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION,
                         COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND, COLOR_BORDER,
                         COLOR_WIDGET_BACKGROUND, SECTION_STYLE)

# Cache the logger instance
logger = Logger.get_logger(__name__)

def populate_supporters(main_window, frame):
    """Populate the Supporters tab with data from a JSON file."""
    # Main container
    main_container = ctk.CTkFrame(frame, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=24, pady=24)

    # Scrollable container
    supporters_container = ctk.CTkScrollableFrame(
        main_container, fg_color="transparent"
    )
    supporters_container.pack(fill="both", expand=True)
    
    # Configure faster scroll speed by modifying canvas
    supporters_container._parent_canvas.configure(yscrollincrement=5)

    # Hero section
    hero_frame = ctk.CTkFrame(
        supporters_container,
        **SECTION_STYLE
    )
    hero_frame.pack(fill="x", pady=(0, 48), padx=24)

    # Hero content
    hero_content = ctk.CTkFrame(hero_frame, fg_color="transparent")
    hero_content.pack(fill="x", padx=48, pady=48)

    # Title and subtitle
    ctk.CTkLabel(
        hero_content, text="🤝 Project Supporters", font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(anchor="w")
    ctk.CTkLabel(
        hero_content, text="Celebrating our incredible community members who fuel this project's growth",
        font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY, wraplength=800
    ).pack(anchor="w", pady=(20, 0))

    # Stats frame
    stats_frame = ctk.CTkFrame(hero_content, fg_color="transparent")
    stats_frame.pack(fill="x", pady=(40, 0))

    # Content frame
    content_frame = ctk.CTkFrame(supporters_container, fg_color="transparent")
    content_frame.pack(fill="x", padx=24)

    # Loading container
    loading_container = ctk.CTkFrame(
        content_frame,
        **SECTION_STYLE
    )
    loading_container.pack(pady=24)

    # Loading content
    loading_content = ctk.CTkFrame(loading_container, fg_color="transparent")
    loading_content.pack(padx=48, pady=36)

    # Loading indicator and message
    ctk.CTkFrame(
        loading_content, width=48, height=48, corner_radius=24,
        fg_color=("#3B82F6", "#60A5FA")
    ).pack()
    ctk.CTkLabel(
        loading_content, text="Loading supporters data...", font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(20, 0))
    
    # Fetch supporter data in a background thread
    def fetch_supporters():
        try:
            # Fetch JSON data from GitHub with a timeout
            response = requests.get('https://raw.githubusercontent.com/Jesewe/VioletWing/refs/heads/main/src/supporters.json', timeout=10)
            response.raise_for_status()
            data = orjson.loads(response.content)
            main_window.root.after(0, lambda: update_supporters_ui(data, loading_container, stats_frame))
        except requests.exceptions.RequestException as e:
            main_window.root.after(0, lambda: show_error(loading_container, f"Failed to fetch supporters data: {e}"))
            logger.error(f"Failed to fetch supporters data: {e}")
        except orjson.JSONDecodeError as e:
            main_window.root.after(0, lambda: show_error(loading_container, "Invalid JSON data received"))
            logger.error(f"Invalid JSON data: {e}")
        except Exception as e:
            main_window.root.after(0, lambda: show_error(loading_container, str(e)))
            logger.error(f"Unexpected error: {e}")
    
    def update_supporters_ui(data, loading_container, stats_frame):
        """Update the UI with fetched supporter data."""
        # Remove loading container
        loading_container.destroy()
        
        # Get data from new structure
        general_data = data.get('general', {})
        developers = general_data.get('developers', [])
        supporters = general_data.get('supporter', [])
        total_count = len(developers) + len(supporters)
        
        # Update stats display
        create_stats_display(stats_frame, total_count, len(developers), len(supporters))
        
        # Create sections
        if developers:
            create_developers_section(content_frame, developers)
        
        if supporters:
            create_supporters_section(content_frame, supporters)
        
        if not developers and not supporters:
            show_no_supporters(content_frame)
    
    def create_stats_display(stats_frame, total_count, developers_count, supporters_count):
        """Create statistics display in hero section."""
        # Clear existing stats widgets
        for widget in stats_frame.winfo_children():
            widget.destroy()

        # Stats container
        container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        container.pack(fill="x", pady=8)

        # Card configuration
        card_config = {'corner_radius': 16, 'width': 200, 'height': 120, 'border_width': 2}
        
        # Theme configurations
        themes = [
            {
                'fg_color': ("#E0F2FE", "#0F172A"),
                'border_color': ("#0EA5E9", "#0284C7"),
                'number_color': ("#0C4A6E", "#38BDF8"),
                'label_color': ("#0369A1", "#0EA5E9"),
                'value': total_count,
                'label': "Total Contributors"
            },
            {
                'fg_color': ("#F0FDF4", "#0F172A"),
                'border_color': ("#22C55E", "#16A34A"),
                'number_color': ("#15803D", "#4ADE80"),
                'label_color': ("#16A34A", "#22C55E"),
                'value': developers_count,
                'label': "Developers"
            },
            {
                'fg_color': ("#FEF3C7", "#0F172A"),
                'border_color': ("#F59E0B", "#D97706"),
                'number_color': ("#92400E", "#FCD34D"),
                'label_color': ("#D97706", "#F59E0B"),
                'value': supporters_count,
                'label': "Supporters"
            }
        ]

        # Create stat cards
        for i, theme in enumerate(themes):
            # Card frame
            card = ctk.CTkFrame(container, fg_color=theme['fg_color'], border_color=theme['border_color'], **card_config)
            card.pack(side="left", padx=(0, 32 if i < len(themes) - 1 else 0))
            card.pack_propagate(False)

            # Content frame
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(expand=True, fill="both", padx=16, pady=16)

            # Value label
            ctk.CTkLabel(content, text=f"{theme['value']:,}", font=FONT_TITLE,
                        text_color=theme['number_color']).pack(expand=True, pady=(8, 0))

            # Description label
            ctk.CTkLabel(content, text=theme['label'], font=FONT_ITEM_DESCRIPTION,
                        text_color=theme['label_color']).pack(pady=(0, 8))
    
    def create_developers_section(container, developers):
        """Create the developers section with a grid of developer cards."""
        # Section wrapper
        section = ctk.CTkFrame(container, fg_color="transparent")
        section.pack(fill="x", pady=(0, 48))

        # Header frame
        header = ctk.CTkFrame(
            section,
            **SECTION_STYLE
        )
        header.pack(fill="x", pady=(0, 32))

        # Header content
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="x", padx=40, pady=32)

        # Title accent bar
        ctk.CTkFrame(
            content, height=4, width=100, corner_radius=2, 
            fg_color=("#22C55E", "#16A34A")
        ).pack(anchor="w", pady=(0, 16))
        
        # Title
        ctk.CTkLabel(
            content, text="Developers", font=FONT_SECTION_TITLE, 
            text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w")
        
        # Description
        ctk.CTkLabel(
            content, text="🚀 Core developers building and maintaining this project", 
            font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY
        ).pack(anchor="w", pady=(12, 0))

        # Member count badge
        badge = ctk.CTkFrame(
            content, corner_radius=24, fg_color=COLOR_WIDGET_BACKGROUND, 
            height=40, border_width=1, border_color=("#22C55E", "#16A34A")
        )
        badge.pack(anchor="w", pady=(20, 0))
        ctk.CTkLabel(
            badge, text=f"{len(developers)} {'developer' if len(developers) == 1 else 'developers'}", 
            font=FONT_ITEM_LABEL, text_color=("#15803D", "#22C55E")
        ).pack(padx=20, pady=8)

        # Developers grid
        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        
        # Calculate optimal columns (2-4 columns based on number of developers)
        columns = min(4, max(2, len(developers)))

        for i, username in enumerate(developers):
            # Developer card
            card = ctk.CTkFrame(
                grid, corner_radius=12, fg_color=COLOR_WIDGET_BACKGROUND, 
                border_width=1, border_color=COLOR_BORDER, height=70
            )
            card.grid(
                row=i // columns, column=i % columns, 
                padx=(0 if i % columns == 0 else 12, 0 if i % columns == columns - 1 else 12), 
                pady=(0, 16), sticky="ew"
            )
            card.grid_propagate(False)
            
            # Configure grid columns to expand equally
            for c in range(columns):
                grid.grid_columnconfigure(c, weight=1)

            # Card content
            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(fill="both", expand=True, padx=24, pady=20)
            
            # Developer indicator dot
            ctk.CTkFrame(
                card_content, width=12, height=12, corner_radius=6, 
                fg_color=("#22C55E", "#16A34A")
            ).pack(side="left")
            
            # Username label
            ctk.CTkLabel(
                card_content, text=username, font=FONT_ITEM_LABEL, 
                text_color=COLOR_TEXT_PRIMARY
            ).pack(side="left", padx=(16, 0))
    
    def create_supporters_section(container, supporters):
        """Create the supporters section with a grid of supporter cards."""
        # Section wrapper
        section = ctk.CTkFrame(container, fg_color="transparent")
        section.pack(fill="x", pady=(0, 48))

        # Header frame
        header = ctk.CTkFrame(
            section,
            **SECTION_STYLE
        )
        header.pack(fill="x", pady=(0, 32))

        # Header content
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="x", padx=40, pady=32)

        # Title accent bar
        ctk.CTkFrame(
            content, height=4, width=100, corner_radius=2, 
            fg_color=("#F59E0B", "#D97706")
        ).pack(anchor="w", pady=(0, 16))
        
        # Title
        ctk.CTkLabel(
            content, text="Community Supporters", font=FONT_SECTION_TITLE, 
            text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w")
        
        # Description
        ctk.CTkLabel(
            content, text="💙 Amazing community members supporting this project", 
            font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY
        ).pack(anchor="w", pady=(12, 0))

        # Member count badge
        badge = ctk.CTkFrame(
            content, corner_radius=24, fg_color=COLOR_WIDGET_BACKGROUND, 
            height=40, border_width=1, border_color=("#F59E0B", "#D97706")
        )
        badge.pack(anchor="w", pady=(20, 0))
        ctk.CTkLabel(
            badge, text=f"{len(supporters)} {'member' if len(supporters) == 1 else 'members'}", 
            font=FONT_ITEM_LABEL, text_color=("#92400E", "#F59E0B")
        ).pack(padx=20, pady=8)

        # Supporters grid
        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")
        
        # Calculate optimal columns (2-4 columns based on number of supporters)
        columns = min(4, max(2, len(supporters)))

        for i, username in enumerate(supporters):
            # Supporter card
            card = ctk.CTkFrame(
                grid, corner_radius=12, fg_color=COLOR_WIDGET_BACKGROUND, 
                border_width=1, border_color=COLOR_BORDER, height=70
            )
            card.grid(
                row=i // columns, column=i % columns, 
                padx=(0 if i % columns == 0 else 12, 0 if i % columns == columns - 1 else 12), 
                pady=(0, 16), sticky="ew"
            )
            card.grid_propagate(False)
            
            # Configure grid columns to expand equally
            for c in range(columns):
                grid.grid_columnconfigure(c, weight=1)

            # Card content
            card_content = ctk.CTkFrame(card, fg_color="transparent")
            card_content.pack(fill="both", expand=True, padx=24, pady=20)
            
            # Supporter indicator dot
            ctk.CTkFrame(
                card_content, width=12, height=12, corner_radius=6, 
                fg_color=("#F59E0B", "#D97706")
            ).pack(side="left")
            
            # Username label
            ctk.CTkLabel(
                card_content, text=username, font=FONT_ITEM_LABEL, 
                text_color=COLOR_TEXT_PRIMARY
            ).pack(side="left", padx=(16, 0))
    
    def show_no_supporters(container):
        """Display a message when no supporters are found."""
        # No supporters message frame
        message_frame = ctk.CTkFrame(
            container,
            **SECTION_STYLE
        )
        message_frame.pack(pady=24)

        # Message content
        content = ctk.CTkFrame(message_frame, fg_color="transparent")
        content.pack(padx=48, pady=36)

        # Icon
        icon = ctk.CTkFrame(
            content, width=56, height=56, corner_radius=28, 
            fg_color=("#64748B", "#94A3B8")
        )
        icon.pack()
        ctk.CTkLabel(
            icon, text="👥", font=("Chivo", 24), text_color=("#FFFFFF", "#FFFFFF")
        ).pack(expand=True)

        # Message
        ctk.CTkLabel(
            content, text="No Supporters Yet", font=FONT_SECTION_TITLE, 
            text_color=COLOR_TEXT_SECONDARY
        ).pack(pady=(20, 8))
        ctk.CTkLabel(
            content, text="Be the first to support this amazing project!", 
            font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY
        ).pack()
    
    def show_error(loading_container, error_msg):
        """Display an error message if data fetch fails."""
        loading_container.destroy()

        # Error frame
        error_frame = ctk.CTkFrame(
            content_frame, corner_radius=16, fg_color=("#FEF2F2", "#1F1715"), 
            border_width=2, border_color=("#FCA5A5", "#7F1D1D")
        )
        error_frame.pack(pady=24)

        # Error content
        content = ctk.CTkFrame(error_frame, fg_color="transparent")
        content.pack(padx=48, pady=36)

        # Error icon
        icon = ctk.CTkFrame(
            content, width=56, height=56, corner_radius=28, 
            fg_color=("#DC2626", "#7F1D1D")
        )
        icon.pack()
        ctk.CTkLabel(
            icon, text="✕", font=("Chivo", 24, "bold"), 
            text_color=("#FFFFFF", "#FFFFFF")
        ).pack(expand=True)

        # Error message
        ctk.CTkLabel(
            content, text="Failed to Load Data", font=("Chivo", 22, "bold"), 
            text_color=("#DC2626", "#F87171")
        ).pack(pady=(20, 8))
        ctk.CTkLabel(
            content, text=error_msg, font=("Gambetta", 16), 
            text_color=("#991B1B", "#EF4444"), wraplength=500
        ).pack()
        ctk.CTkLabel(
            content, text="Please check your internet connection and try again", 
            font=("Gambetta", 14), text_color=("#B91C1C", "#FCA5A5")
        ).pack(pady=(12, 0))
    
    # Start fetching supporters data
    threading.Thread(target=fetch_supporters, daemon=True).start()