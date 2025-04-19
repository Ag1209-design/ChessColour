import pygame
import sys
import os
import random
import configuration

class SettingsScreen:
    """
    Graphical settings screen for Caesar's Chess game.
    Redesigned to match the provided UI design.
    """
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        self.start_game = False

        # Centralized configuration variables
        self.config = {
            # Screen dimensions
            'screen_width': 800,
            'screen_height': 600,
            
            # Padding
            'padding': {
                'top': 20,
                'bottom': 25,
                'left': 20,
                'right': 15
            },
            
            # Colors
            'colors': {
                'primary_text': (93, 29, 63),        # #5D1D3F
                'button_border': (232, 211, 190),    # #E8D3BE
                'button_bg': (232, 211, 190),   # #E8D3BE with alpha
                'button_selected': (223, 194, 158),  # Slightly darker for selected button
                'button_hover': (242, 231, 210),     # Slightly lighter for hover
                'background': (245, 235, 220)        # Light beige/parchment color
            },
            
            # Fonts
            'fonts': {
                'title': {
                    'name': "Cinzel-Bold.ttf", 
                    'size': 36
                },
                'subtitle': {
                    'name': "Cinzel-Regular.ttf", 
                    'size': 20
                },
                'section_title': {
                    'name': "Cinzel-Regular.ttf", 
                    'size': 24
                },
                'section_description': {
                    'name': "Cinzel-Regular.ttf", 
                    'size': 20
                },
                'button': {
                    'name': "Cormorant-Medium.ttf", 
                    'size': 20
                }
            },
            
            # Element dimensions
            'elements': {
                'section_container_width': 730,
                'button_gap': 12,
                'button_height': 34,
                'begin_button_width': 200,
                'begin_button_height': 50,
                'corner_size': 100,
                'separator_width': 166,
                'separator_height': 27
            },
            
            # Positioning
            'positions': {
                'title_y': 20,
                'subtitle_y': 55,
                'separator_y': 70,
                'section_start_y': 130,
                'section_gap': 100
            }
        }

        self.screen_width = self.config['screen_width']
        self.screen_height = self.config['screen_height']
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Caesar's Chess - Game Settings")


        # Use padding from config
        self.padding = self.config['padding']
        # Calculate content area dimensions
        self.content_width = self.screen_width - (self.padding['left'] + self.padding['right'])
        self.content_height = self.screen_height - (self.padding['top'] + self.padding['bottom'])

        # Use colors from config
        self.colors = self.config['colors']
        
        # Find and load assets
        self.assets_folder = self._find_assets_folder()
        
        # Load background
        self.background = self._load_background()

    
        # Load fonts using configuration
        self.cinzel_decorative_bold = self._load_font_from_config('title')
        self.cinzel_regular = self._load_font_from_config('subtitle')
        self.cinzel_regular_larger = self._load_font_from_config('section_title')
        self.cormorant_unicase = self._load_font_from_config('button')
        self.cormorant_unicase_medium = self._load_font_from_config('button')

        # Create font fallbacks if needed
        if not self.cinzel_decorative_bold:
            self.cinzel_decorative_bold = pygame.font.Font(None, self.config['fonts']['title']['size'])
        if not self.cinzel_regular:
            self.cinzel_regular = pygame.font.Font(None, self.config['fonts']['subtitle']['size'])
        if not self.cinzel_regular_larger:
            self.cinzel_regular_larger = pygame.font.Font(None, self.config['fonts']['section_title']['size'])
        if not self.cormorant_unicase:
            self.cormorant_unicase = pygame.font.Font(None, self.config['fonts']['button']['size'])
        if not self.cormorant_unicase_medium:
            self.cormorant_unicase_medium = pygame.font.Font(None, self.config['fonts']['button']['size'])
            
        # Settings and options
        self.settings = {
            'switch_trigger_mode': "move",
            'switch_mode': 2,
            'game_mode': "User vs AI",
            'use_tokens': True
        }
        
        try:
            # Options for each setting
            self.options = {
                'switch_trigger_mode': [
                    {'value': "move", 'label': "MOVE BASED", 'description': "Switch occurs every 5 moves"},
                    {'value': "timer", 'label': "TIME BASED", 'description': "Switch occurs every 15 seconds"},
                    {'value': "player", 'label': "PLAYER INITATED", 'description': "Player activates switch with button"},
                    {'value': "random_token", 'label': "RANDOM TOKEN", 'description': "Switch occurs at 3 random moves"}
                ],
                'switch_mode': [
                    {'value': 1, 'label': "SINGLE PIECE", 'description': "One piece changes color at a time"},
                    {'value': 2, 'label': "TWO PIECES", 'description': "One piece from each side changes color"}
                ],
                'game_mode': [
                    {'value': "User vs AI", 'label': "USER VS AI", 'description': "Play against the computer"},
                    {'value': "AI vs AI", 'label': "AI VS AI", 'description': "Watch computer players battle"},
                    {'value': "User vs User", 'label': "USER VS USER", 'description': "Play against another person"}
                ],
                'use_tokens': [
                    {'value': True, 'label': "ENABLED", 'description': "Use tokens to prevent piece switching"},
                    {'value': False, 'label': "DISABLED", 'description': "Play without tokens"}
                ]
            }
            print("Successfully initialized options")
        except Exception as e:
            print(f"Error initializing options: {e}")
            # Provide a basic fallback for options
            self.options = {
                'switch_trigger_mode': [{'value': "move", 'label': "MOVE BASED", 'description': "Default mode"}],
                'switch_mode': [{'value': 2, 'label': "TWO PIECES", 'description': "Default mode"}],
                'game_mode': [{'value': "User vs AI", 'label': "USER VS AI", 'description': "Default mode"}],
                'use_tokens': [{'value': True, 'label': "ENABLED", 'description': "Default mode"}]
}
        
        # Generate random token moves
        self.random_token_moves = [
            random.randint(5, 20),    # Early game
            random.randint(20, 45),   # Mid game
            random.randint(45, 70)    # Late game
        ]
        
        # Track button states
        self.buttons = {}
        self.active_button = None
        print("Button states initialized")
                    
        # Load separator image or create one
        try:
            self.separator = self._load_separator()
        except Exception as e:
            print(f"Error loading separator: {e}")
            # Fallback in case of error
            self.separator = None
        
        try:
            self.corner = self._load_corner()
        except:
            # Fallback in case of error
            self.corner = None

            # Make sure all required attributes exist
        self._ensure_attributes()
          
    
    def _load_font(self, font_name, font_size):
        """Load a font with the given name and size."""
        if not self.assets_folder:
            return None
            
        try:
            font_path = os.path.join(self.assets_folder, font_name)
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, font_size)
                
            # Try some alternative paths
            alt_paths = [
                os.path.join(self.assets_folder, "Cinzel", "static", font_name),
                os.path.join(self.assets_folder, "Cormorant", "static", font_name),
                r"C:\Users\avani\Documents\Work\Work_projects\Internships\Proxgy\Chess_game - V38 - UI\assets2\Cinzel\static",
                r"C:\Users\avani\Documents\Work\Work_projects\Internships\Proxgy\Chess_game - V38 - UI\assets2\Cormorant\static"
            ]
            
            for base_path in alt_paths:
                full_path = os.path.join(base_path, font_name) if not base_path.endswith(font_name) else base_path
                if os.path.exists(full_path):
                    return pygame.font.Font(full_path, font_size)
                    
            # If all else fails, use system font
            return pygame.font.Font(None, font_size)
        except Exception as e:
            print(f"Error loading font {font_name}: {e}")
            return None
        
    def _load_font_from_config(self, font_key):
        """Load a font using configuration settings"""
        font_config = self.config['fonts'][font_key]
        return self._load_font(font_config['name'], font_config['size'])

    def _find_assets_folder(self):
        """Find the assets folder."""
        possible_paths = [
            "assets",
            "assets2",
            os.path.join("Chess_game - V35 - Current", "assets"),
            os.path.join("Chess_game - V35 - Current", "assets2")
        ]
        
        # Check if the assets folder from configuration.py exists
        if hasattr(configuration, 'ASSETS_FOLDER'):
            possible_paths.insert(0, configuration.ASSETS_FOLDER)
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def _load_background(self):
        """Load the parchment background."""
        if not self.assets_folder:
            return None
            
        possible_textures = ["parchment.png", "parchment.jpeg", "texture.png", "background.png"]
        
        for texture_name in possible_textures:
            try:
                texture_path = os.path.join(self.assets_folder, texture_name)
                if os.path.exists(texture_path):
                    texture = pygame.image.load(texture_path).convert()
                    texture.set_alpha(255)  # Set 25% opacity
                    background = pygame.transform.scale(texture, (self.screen_width, self.screen_height))
                    # Overlay a semi-transparent white layer for extra softness
                    white_overlay = pygame.Surface((self.screen_width, self.screen_height))
                    white_overlay.set_alpha(75)  # 20% of 255 = 51
                    white_overlay.fill((255, 255, 255))
                    background.blit(white_overlay, (0, 0))

                    return background
            except Exception as e:
                print(f"Could not load background: {e}")
                
        # Create a fallback parchment-like surface if no image is found
        fallback = pygame.Surface((self.screen_width, self.screen_height))
        fallback.fill((245, 235, 220))  # Light beige/parchment color
        return fallback

    
    def _load_separator(self):
        """Load or create a separator element."""
        try:
            # Try to load a separator image from assets
            if self.assets_folder:
                separator_path = os.path.join(self.assets_folder, "separator.png")
                if os.path.exists(separator_path):
                    try:
                        separator = pygame.image.load(separator_path).convert_alpha()
                        # Resize the separator to 144x20 as specified
                        return pygame.transform.scale(separator, (172, 23))
                    except Exception as e:
                        print(f"Error loading separator image: {e}")
            
            # Create a simple separator (resized to 144x20)
            separator = pygame.Surface((172,23), pygame.SRCALPHA)
            separator_rect = pygame.Rect(0, 10, 172, 2)
            pygame.draw.rect(separator, self.colors['button_border'], separator_rect)
            
            # Add decorative elements to the separator
            circle_radius = 5
            pygame.draw.circle(separator, self.colors['button_border'], (72, 10), circle_radius)
            pygame.draw.circle(separator, self.colors['button_border'], (30, 10), circle_radius)
            pygame.draw.circle(separator, self.colors['button_border'], (114, 10), circle_radius)
            
            return separator
            
        except Exception as e:
            print(f"Error in _load_separator: {e}")
            # Return a minimal surface as fallback
            try:
                fallback = pygame.Surface((144, 20), pygame.SRCALPHA)
                return fallback
            except:
                return None
            
    def _load_corner(self):
        """Load or create corner decoration."""
        try:
            # Try to load a corner image from assets
            if self.assets_folder:
                corner_path = os.path.join(self.assets_folder, "corner.png")
                if os.path.exists(corner_path):
                    try:
                        corner_img = pygame.image.load(corner_path).convert_alpha()
                        return pygame.transform.scale(corner_img, (100, 100))
                    except Exception as e:
                        print(f"Error loading corner image: {e}")
            
            # Create a simple corner decoration if image not found
            corner = pygame.Surface((50, 50), pygame.SRCALPHA)
            # Draw L shape
            pygame.draw.rect(corner, self.colors['button_border'], (0, 0, 40, 5))
            pygame.draw.rect(corner, self.colors['button_border'], (0, 0, 5, 40))
            return corner
            
        except Exception as e:
            print(f"Error in _load_corner: {e}")
            # Return a minimal surface as fallback
            fallback = pygame.Surface((10, 10), pygame.SRCALPHA)
            return fallback
    
    def run(self):
        """Run the settings screen loop."""
        # Ensure critical attributes exist
        if not hasattr(self, 'buttons'):
            self.buttons = {}
        if not hasattr(self, 'active_button'):
            self.active_button = None
            
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle mouse clicks
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        self._handle_click(mouse_pos)
                        
                # Reset active button on mouse up
                if event.type == pygame.MOUSEBUTTONUP:
                    if hasattr(self, 'active_button'):
                        self.active_button = None
                    else:
                        self.active_button = None  # Create it if it doesn't exist
            
            # Draw the screen
            self._draw_screen()
            
            # Update display
            pygame.display.flip()
            
            # Check if user clicked start game
            if self._check_start_game():
                running = False
        
        # Clean up before returning settings
        pygame.quit()
        
        # Return the selected settings and random token moves if applicable
        return {
            'switch_trigger_mode': self.settings['switch_trigger_mode'],
            'switch_mode': self.settings['switch_mode'],
            'game_mode': self.settings['game_mode'],
            'use_tokens': self.settings['use_tokens'],
            'random_token_moves': self.random_token_moves if self.settings['switch_trigger_mode'] == "random_token" else None
        }
    
    def _draw_screen(self):
        """Draw the settings screen according to the design."""
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(self.colors['background'])  # Fallback color from config
        
        # Draw corner decorations
        self._draw_corners()
   
        # Draw title "CAESARS CHESS"
        title_text = self.cinzel_decorative_bold.render("CAESARS CHESS", True, self.colors['primary_text'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.padding['top'] + 20))
        self.screen.blit(title_text, title_rect)
                
        # Draw subtitle "GAME SETTINGS"
        subtitle_text = self.cinzel_regular.render("GAME SETTINGS", True, self.colors['primary_text'])
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, self.padding['top'] + 55))
        self.screen.blit(subtitle_text, subtitle_rect)
                
        # Draw separator
        if hasattr(self, 'separator') and self.separator is not None:
            try:
                separator_rect = self.separator.get_rect(center=(self.screen_width // 2, self.padding['top'] + 80))
                self.screen.blit(self.separator, separator_rect)
            except Exception as e:
                print(f"Error drawing separator: {e}")
       
        # Draw the four settings sections
        base_y = self.config['positions']['section_start_y']
        section_gap = self.config['positions']['section_gap']

        # Replace with more detailed diagnostics
        if hasattr(self, 'options'):
            try:
                self._draw_section("SWITCH TRIGGER MODE", "INSTRUCTION", 'switch_trigger_mode', self.padding['top'] + base_y)
                self._draw_section("SWITCH MODE", "INSTRUCTION", 'switch_mode', self.padding['top'] + base_y + section_gap)
                self._draw_section("GAME MODE", "INSTRUCTION", 'game_mode', self.padding['top'] + base_y + section_gap * 2)
                self._draw_section("TOKEN MECHANIC", "INSTRUCTION", 'use_tokens', self.padding['top'] + base_y + section_gap * 3)
            except Exception as e:
                print(f"Error drawing sections: {e}")
                # Draw error message with details
                error_font = pygame.font.Font(None, 30)
                error_text = error_font.render(f"Error: {str(e)[:50]}", True, (255, 0, 0))
                error_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(error_text, error_rect)
        else:
            print("Warning: Cannot draw settings sections, options not initialized")
            # Draw fallback message
            error_font = pygame.font.Font(None, 30)
            error_text = error_font.render("Settings could not be loaded properly", True, (255, 0, 0))
            error_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(error_text, error_rect)

        # Draw Begin button
        self._draw_begin_button()
    
    def _draw_corners(self):
        """Draw corner decorations at each corner of the screen."""
        # First check if self.corner exists and is not None
        if not hasattr(self, 'corner') or self.corner is None:
            return
            
        try:
            corner_size = self.corner.get_width()
            padding = 10  # Reduced padding from the edge of the screen
            
            # Top-left corner
            self.screen.blit(self.corner, (self.padding['left'], self.padding['top']))
                    
            # Top-right corner (flip horizontally)
            top_right = pygame.transform.flip(self.corner, True, False)
            self.screen.blit(top_right, (self.screen_width - corner_size - self.padding['right'], self.padding['top']))
                    
            # Bottom-left corner (flip vertically)
            bottom_left = pygame.transform.flip(self.corner, False, True)
            self.screen.blit(bottom_left, (self.padding['left'], self.screen_height - corner_size - self.padding['bottom']))
                    
            # Bottom-right corner (flip both horizontally and vertically)
            bottom_right = pygame.transform.flip(self.corner, True, True)
            self.screen.blit(bottom_right, (self.screen_width - corner_size - self.padding['right'], self.screen_height - corner_size - self.padding['bottom']))
        except Exception as e:
            print(f"Error drawing corners: {e}")

    # Add this check at the beginning of _draw_section()
    def _draw_section(self, title, instruction, setting_key, y_pos):
        """Draw a settings section with the design styling."""
        # Add defensive checks
        if not hasattr(self, 'options'):
            print(f"Warning: options attribute not found in _draw_section('{setting_key}')")
            return
            
        if setting_key not in self.options:
            print(f"Warning: setting key '{setting_key}' not found in options")
            return

        # Use the configured section title font
        section_title_font = self._load_font_from_config('section_title')
        
        title_text = section_title_font.render(title, True, self.colors['primary_text'])
        
        # Position the title at a fixed left margin to make room for description on the right
        container_width = self.config['elements']['section_container_width']
        title_width = title_text.get_width()
        
        # Calculate title x position to center the title+description container
        if hasattr(self, 'options') and setting_key in self.options:
            selected_option = next((opt for opt in self.options[setting_key] if opt['value'] == self.settings[setting_key]), None)
        else:
            print(f"Warning: options not available for {setting_key}")
            selected_option = None
        desc_width = 0
        if selected_option:
            desc_font = self._load_font_from_config('section_description')
            
            desc_width = desc_font.size(selected_option['description'])[0] + 20  # Add spacing
        
        # Calculate the combined width to center the entire section
        combined_width = min(title_width + desc_width, container_width)
        title_x = (self.screen_width - combined_width) // 2
        
        # Draw title at its calculated position
        self.screen.blit(title_text, (title_x, y_pos-20))
        
        # Draw options as buttons
        num_options = len(self.options[setting_key])
        total_width = self.config['elements']['section_container_width']
        button_gap = self.config['elements']['button_gap']
        
        # Dynamically calculate button widths based on text + padding
        cormorant_unicase_medium = self._load_font_from_config('button')
        button_heights = []
        button_rects = []

        for i, option in enumerate(self.options[setting_key]):
            label_text = option['label']
            label_surface = cormorant_unicase_medium.render(label_text, True, self.colors['primary_text'])
            text_width, text_height = label_surface.get_size()
            button_width = text_width + 2 * 20  # 5px horizontal padding on each side
            button_height = text_height + 2 * 7  # 10px vertical padding on top and bottom
            button_heights.append(button_height)
            button_rects.append((button_width, label_surface))  # Store width and surface for reuse

        
        # Position buttons
        total_buttons_width = sum(w for w, _ in button_rects) + button_gap * (num_options - 1)
        start_x = (self.screen_width - total_buttons_width) // 2
        buttons_y = y_pos + 12
        
        # Adjust container to accommodate title + description on top and buttons below
        section_top = y_pos - 30
        section_height = 100  # Maintain the same height
        
        # Create the container rect that spans the full width (respecting padding)
        container_x = self.padding['left']
        container_width = self.content_width
        container_rect = pygame.Rect(container_x, section_top, container_width, section_height)

        # Add padding to the container rect
        inner_rect = container_rect.inflate(-20, -20)  # 10px padding on each side
        
        # Draw the container border
        pygame.draw.rect(self.screen, self.colors['button_border'], container_rect, width=1)

        # Continue with the rest of the method using config values...

        if not hasattr(self, 'options') or setting_key not in self.options:
            print(f"Warning: cannot draw buttons for {setting_key} - options not available")
            return
            
        for i, option in enumerate(self.options[setting_key]):
                x = start_x + sum(button_rects[j][0] + button_gap for j in range(i))
                button_width, label_surface = button_rects[i]
                button_height = button_heights[i]
                button_rect = pygame.Rect(x, buttons_y, button_width, button_height)
                
                # Determine if this option is selected
                is_selected = self.settings[setting_key] == option['value']
                
                # Check for mouse hover
                mouse_pos = pygame.mouse.get_pos()
                is_hovered = button_rect.collidepoint(mouse_pos)
                
                # Check for active button (being clicked)
                button_id = f"{setting_key}_{i}"
                is_active = hasattr(self, 'active_button') and self.active_button == button_id
                
                # Choose button color based on state
                if is_active:
                    button_color = self.colors['button_selected']
                elif is_selected:
                    button_color = self.colors['button_selected']
                elif is_hovered:
                    button_color = self.colors['button_hover']
                else:
                    button_color = self.colors['button_bg']
                
                # Draw button with improved drop shadow
                shadow_rect = pygame.Rect(x, buttons_y + 1, button_width, button_height)
                shadow_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surface, (0, 0, 0, 64), pygame.Rect(0, 0, button_width, button_height), border_radius=12)
                # Apply blur effect for shadow (simple approximation)
                self.screen.blit(shadow_surface, (x, buttons_y + 1))
                # Draw the actual button with padding
                pygame.draw.rect(self.screen, button_color, button_rect, border_radius=12)
                pygame.draw.rect(self.screen, self.colors['button_border'], button_rect, 1, border_radius=12)
                
                # Draw button text with correct font and padding
                cormorant_unicase_medium = self._load_font_from_config('button')
                option_text = cormorant_unicase_medium.render(option['label'], True, self.colors['primary_text'])
                # Add padding between button edges and text (5px horizontal, 10px vertical)
                option_text_rect = option_text.get_rect(center=button_rect.center)
                self.screen.blit(option_text, option_text_rect)
                
                # Store button for click detection
                self.buttons[button_id] = {'rect': button_rect, 'value': option['value'], 'setting': setting_key}
            
                # Draw description for selected option to the right of the title
                if hasattr(self, 'options') and setting_key in self.options:
                    selected_option = next((opt for opt in self.options[setting_key] if opt['value'] == self.settings[setting_key]), None)
                else:
                    print(f"Warning: options not available for {setting_key}")
                    selected_option = None
                if selected_option:
                    # Create description text with new font size (20px)
                    desc_font = self._load_font_from_config('section_description')
                    
                    # Get the width of the title to position the description
                    title_width = title_text.get_width()
                    
                    # Implement text wrapping for description
                    max_desc_width = self.screen_width - title_width - 80  # Allow some margin
                    words = selected_option['description'].split()
                    lines = []
                    current_line = []
                    
                    # Simple text wrapping implementation
                    for word in words:
                        test_line = ' '.join(current_line + [word])
                        test_width = desc_font.size(test_line)[0]
                        
                        if test_width <= max_desc_width:
                            current_line.append(word)
                        else:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Position and render each line
                    if not lines:  # Fallback if wrapping failed
                        lines = [selected_option['description']]
                        
                    # Position the description to the right of the title
                    # Load description font
                    desc_font = self._load_font_from_config('section_description')
                    desc_surface = desc_font.render(selected_option['description'], True, self.colors['primary_text'])

                    # Measure total width of title + spacing + description
                    spacing = 20
                    combined_width = title_text.get_width() + spacing + desc_surface.get_width()

                    # Calculate centered x for the entire block
                    combined_x = (self.screen_width - combined_width) // 2
                    title_x = combined_x
                    desc_x = title_x + title_text.get_width() + spacing

                    
                    for i, line in enumerate(lines):
                        desc_text = desc_font.render(line, True, self.colors['primary_text'])
                        desc_y = y_pos - 20 + (i * 30)  # 25px line height
                        self.screen.blit(desc_text, (desc_x, desc_y))

    
    def _draw_begin_button(self):
        """Draw the Begin button at the bottom of the screen."""
        button_width = self.config['elements']['begin_button_width']
        button_height = self.config['elements']['begin_button_height']
        # Modified code
        button_rect = pygame.Rect((self.screen_width - button_width) // 2, self.screen_height - self.padding['bottom'] - button_height, button_width, button_height)
        
        # Check for mouse hover
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = button_rect.collidepoint(mouse_pos)
        is_active = hasattr(self, 'active_button') and self.active_button == 'begin'
        
        # Draw button with drop shadow
        shadow_rect = pygame.Rect(
            (self.screen_width - button_width) // 2,
            self.screen_height - self.padding['bottom'] - button_height + 1,
            button_width,
            button_height
        )

        pygame.draw.rect(self.screen, (0, 0, 0, 64), shadow_rect, border_radius=10)
        
        # Choose button color based on state
        if is_active:
            button_color = self.colors['button_selected']
        elif is_hovered:
            button_color = self.colors['button_hover']
        else:
            button_color = (252, 247, 243)  # #FCF7F3 for Begin button only

        
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.colors['button_border'], button_rect, 1, border_radius=5)
        
        # Draw button text
        begin_text = self.cinzel_decorative_bold.render("BEGIN", True, self.colors['primary_text'])
        begin_text_rect = begin_text.get_rect(center=button_rect.center)
        self.screen.blit(begin_text, begin_text_rect)
        
        # Store button for click detection
        self.buttons['begin'] = button_rect
    
    def _handle_click(self, mouse_pos):
        """Handle mouse clicks on buttons."""

        for button_id, button_data in self.buttons.items():
            if button_id == 'begin':
                if button_data.collidepoint(mouse_pos):
                    self.active_button = 'begin'
                    self.start_game = True
                    return
            else:
                if isinstance(button_data, dict) and 'rect' in button_data and button_data['rect'].collidepoint(mouse_pos):
                    self.active_button = button_id
                    if hasattr(self, 'settings') and 'setting' in button_data and 'value' in button_data:
                        self.settings[button_data['setting']] = button_data['value']
                    else:
                        print(f"Warning: Cannot update setting for {button_id}")
                    # If it's random token mode, generate new random moves
                    if button_data['setting'] == 'switch_trigger_mode' and button_data['value'] == 'random_token':
                        self.random_token_moves = [
                            random.randint(5, 20),    # Early game
                            random.randint(20, 45),   # Mid game
                            random.randint(45, 70)    # Late game
                        ]
                    return
    
    def _check_start_game(self):
        """Check if the start game button was clicked."""
        return hasattr(self, 'start_game') and self.start_game

    def _ensure_attributes(self):
        """Ensure all required attributes exist, creating them if missing."""
        critical_attributes = {
            'buttons': {},
            'active_button': None,
            'corner': None,
            'separator': None,
            'start_game': False,
            'options': self.options if hasattr(self, 'options') else {},
            'settings': self.settings if hasattr(self, 'settings') else {
                'switch_trigger_mode': "move",
                'switch_mode': 2,
                'game_mode': "User vs AI",
                'use_tokens': True
            },
            'random_token_moves': self.random_token_moves if hasattr(self, 'random_token_moves') else [
                random.randint(5, 20),
                random.randint(20, 45),
                random.randint(45, 70)
            ]
        }
        
        for attr, default_value in critical_attributes.items():
            if not hasattr(self, attr):
                print(f"Warning: Missing attribute '{attr}'. Initializing with default value.")
                setattr(self, attr, default_value)

# For testing the settings screen directly
if __name__ == "__main__":
    screen = SettingsScreen()
    settings = screen.run()
    print("Selected settings:", settings)