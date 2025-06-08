"""
Standard UI Components for Hyper Framework

Provides common UI components built on the rendering engine:
- Text components
- Panels and containers  
- Headers and status bars
- Interactive elements
"""

import time
from enum import Enum
from typing import Optional, List, Tuple, Callable, Any

from .engine import UIComponent, RenderContext
from .renderer import TextStyle, BoxChars
from .containers import BorderedContainer, FlexContainer


class MenuAlignment(Enum):
    """Menu alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Text(UIComponent):
    """Simple text component with styling support."""
    
    def __init__(self, text: str = "", style: int = 0, align: str = "left"):
        super().__init__()
        self._text = text
        self._style = style
        self._align = align  # left, center, right
        self._wrap = True
        self._lines: List[str] = []
        self._update_lines()
    
    @property
    def text(self) -> str:
        return self._text
    
    @text.setter
    def text(self, value: str) -> None:
        if self._text != value:
            self._text = value
            self._update_lines()
            self.mark_dirty()
    
    @property 
    def style(self) -> int:
        return self._style
    
    @style.setter
    def style(self, value: int) -> None:
        if self._style != value:
            self._style = value
            self.mark_dirty()
    
    def _update_lines(self) -> None:
        """Update internal line representation."""
        if not self._text:
            self._lines = [""]
        else:
            self._lines = self._text.split('\n')
    
    def get_size_hint(self) -> Tuple[int, int]:
        """Get preferred size based on text content."""
        if not self._lines:
            return (0, 1)
        
        max_width = max(len(line) for line in self._lines)
        height = len(self._lines)
        return (max_width, height)
    
    def render_content(self, ctx: RenderContext) -> None:
        """Render the text content."""
        if not self._lines:
            return
        
        for i, line in enumerate(self._lines):
            if i >= ctx.height:
                break
            
            # Apply text alignment
            if self._align == "center":
                x_offset = max(0, (ctx.width - len(line)) // 2)
            elif self._align == "right":
                x_offset = max(0, ctx.width - len(line))
            else:  # left
                x_offset = 0
            
            # Truncate line if too long
            display_line = line[:ctx.width]
            
            ctx.window.add_str(
                ctx.y + i, 
                ctx.x + x_offset,
                display_line,
                self._style
            )



class Header(UIComponent):
    """Header component with title and subtitle."""
    
    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._title_style = TextStyle.BOLD
        self._subtitle_style = TextStyle.NORMAL
        self._show_separator = True
    
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        if self._title != value:
            self._title = value
            self.mark_dirty()
    
    @property
    def subtitle(self) -> str:
        return self._subtitle
    
    @subtitle.setter
    def subtitle(self, value: str) -> None:
        if self._subtitle != value:
            self._subtitle = value
            self.mark_dirty()
    
    def get_size_hint(self) -> Tuple[int, int]:
        """Calculate size hint for header."""
        height = 0
        width = 0
        
        if self._title:
            height += 1
            width = max(width, len(self._title))
        
        if self._subtitle:
            height += 1
            width = max(width, len(self._subtitle))
        
        if self._show_separator and (self._title or self._subtitle):
            height += 1
        
        return (width, height)
    
    def render_content(self, ctx: RenderContext) -> None:
        """Render header content."""
        current_y = ctx.y
        
        # Draw title
        if self._title and current_y < ctx.y + ctx.height:
            title_x = (ctx.width - len(self._title)) // 2
            ctx.window.add_str(
                current_y, ctx.x + max(0, title_x),
                self._title[:ctx.width], 
                self._title_style
            )
            current_y += 1
        
        # Draw subtitle
        if self._subtitle and current_y < ctx.y + ctx.height:
            subtitle_x = (ctx.width - len(self._subtitle)) // 2
            ctx.window.add_str(
                current_y, ctx.x + max(0, subtitle_x),
                self._subtitle[:ctx.width],
                self._subtitle_style
            )
            current_y += 1
        
        # Draw separator
        if self._show_separator and current_y < ctx.y + ctx.height:
            separator = (BoxChars.HLINE) * ctx.width
            ctx.window.add_str(current_y, ctx.x, separator)


class StatusBar(UIComponent):
    """Status bar component with message and help text."""
    
    def __init__(self):
        super().__init__()
        self._message = ""
        self._message_expiry = 0
        self._help_text = ""
        self._show_separator = True
    
    def set_message(self, message: str, duration: float = 3.0) -> None:
        """Set a temporary status message."""
        self._message = message
        self._message_expiry = time.time() + duration
        self.mark_dirty()
    
    def set_help_text(self, text: str) -> None:
        """Set persistent help text."""
        if self._help_text != text:
            self._help_text = text
            self.mark_dirty()
    
    def get_size_hint(self) -> Tuple[int, int]:
        """Status bar prefers full width and 2 lines (separator + content)."""
        height = 2 if self._show_separator else 1
        return (0, height)  # 0 width means "expand to fill"
    
    def render_content(self, ctx: RenderContext) -> None:
        """Render status bar content."""
        current_y = ctx.y
        
        # Draw separator
        if self._show_separator and current_y < ctx.y + ctx.height:
            separator = (BoxChars.HLINE) * ctx.width
            ctx.window.add_str(current_y, ctx.x, separator)
            current_y += 1
        
        # Determine what to show
        if current_y < ctx.y + ctx.height:
            # Check if temporary message is still valid
            if self._message and time.time() < self._message_expiry:
                display_text = self._message
            else:
                self._message = ""  # Clear expired message
                display_text = self._help_text
            
            if display_text:
                # Add padding and truncate to fit
                padded_text = f"  {display_text}"
                display_text = padded_text[:ctx.width]
                
                ctx.window.add_str(current_y, ctx.x, display_text)


class MenuBar(UIComponent):
    """Horizontal menu bar with clickable items and arrow key navigation."""
    
    def __init__(self, alignment: MenuAlignment = MenuAlignment.CENTER):
        super().__init__()
        self._items: List[Tuple[str, str, Optional[Callable]]] = []  # (key, label, action)
        self._alignment = alignment.value if isinstance(alignment, MenuAlignment) else alignment
        self._separator = "  "
        self._selected_index = 0  # Currently selected menu item
    
    def add_item(self, key: str, label: str, action: Optional[Callable] = None) -> None:
        """Add a menu item."""
        self._items.append((key, label, action))
        self.mark_dirty()
    
    def clear_items(self) -> None:
        """Clear all menu items."""
        self._items.clear()
        self.mark_dirty()
    
    def handle_key(self, key: str) -> Optional[Any]:
        """Handle key press and return action result if any."""
        for item_key, label, action in self._items:
            if item_key.lower() == key.lower() and action:
                return action()
        return None
    
    def handle_arrow_key(self, key_code: int) -> Optional[Any]:
        """Handle arrow key navigation and return action result if any."""
        import curses
        
        if not self._items:
            return None
        
        enabled_items = [(i, key, label, action) for i, (key, label, action) in enumerate(self._items) if action]
        if not enabled_items:
            return None
        
        if key_code == curses.KEY_LEFT:
            # Move to previous menu item and activate it immediately
            self._selected_index = (self._selected_index - 1) % len(enabled_items)
            self.mark_dirty()
            if enabled_items and 0 <= self._selected_index < len(enabled_items):
                _, _, _, action = enabled_items[self._selected_index]
                if action:
                    action()  # Call action immediately, don't return result
            return None
        elif key_code == curses.KEY_RIGHT:
            # Move to next menu item and activate it immediately
            self._selected_index = (self._selected_index + 1) % len(enabled_items)
            self.mark_dirty()
            if enabled_items and 0 <= self._selected_index < len(enabled_items):
                _, _, _, action = enabled_items[self._selected_index]
                if action:
                    action()  # Call action immediately, don't return result
            return None
        elif key_code == ord('\n') or key_code == ord('\r'):  # Enter key
            # Activate currently selected menu item (alternative to arrow keys)
            if enabled_items and 0 <= self._selected_index < len(enabled_items):
                _, _, _, action = enabled_items[self._selected_index]
                if action:
                    action()  # Call action but don't return result (consistent with arrow keys)
            return None
        return None
    
    def get_size_hint(self) -> Tuple[int, int]:
        """Calculate size hint for menu bar."""
        if not self._items:
            return (0, 1)
        
        # Calculate total width needed
        menu_parts = []
        for key, label, _ in self._items:
            menu_parts.append(f"[{key}] {label}")
        
        total_width = len(self._separator.join(menu_parts))
        return (total_width, 1)
    
    def render_content(self, ctx: RenderContext) -> None:
        """Render menu bar with selection highlighting."""
        if not self._items:
            return
        
        # Build menu string with selection highlighting
        menu_parts = []
        enabled_items = [(i, key, label, action) for i, (key, label, action) in enumerate(self._items) if action]
        
        if not enabled_items:
            return
        
        # Adjust selected index if necessary
        if self._selected_index >= len(enabled_items):
            self._selected_index = 0
        
        for j, (i, key, label, action) in enumerate(enabled_items):
            if j == self._selected_index:
                # Highlight selected item
                menu_parts.append(f">[{key}] {label}<")
            else:
                menu_parts.append(f"[{key}] {label}")
        
        menu_str = self._separator.join(menu_parts)
        
        # Calculate position based on alignment
        if self._alignment == "center":
            x_offset = max(0, (ctx.width - len(menu_str)) // 2)
        elif self._alignment == "right":
            x_offset = max(0, ctx.width - len(menu_str))
        else:  # left
            x_offset = 0
        
        # Render menu
        ctx.window.add_str(
            ctx.y, ctx.x + x_offset,
            menu_str[:ctx.width]
        )


class ApplicationFrame(FlexContainer):
    """Complete application frame with header, menu, content, and status."""
    
    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__(direction="vertical")
        
        # Create standard components
        self.header = Header(title, subtitle)
        self.menu_bar = MenuBar()
        self.content_container = BorderedContainer(show_border=True)
        self.status_bar = StatusBar()
        
        # Assemble layout with proper space allocation
        # Header gets its natural size
        header_height = self.header.get_size_hint()[1]
        self.add_child_with_config(self.header, fixed_size=header_height)
        
        # Menu bar gets its natural size (1 line)
        self.add_child_with_config(self.menu_bar, fixed_size=1)
        
        # Content gets remaining space (flex=1)
        self.add_child_with_config(self.content_container, flex=1.0, min_size=3)
        
        # Status bar gets its natural size (2 lines)
        self.add_child_with_config(self.status_bar, fixed_size=2)
        
        # Set default help text
        self.status_bar.set_help_text("Press 'q' to quit | Use arrow keys to navigate")
    
    def set_content(self, component: UIComponent) -> None:
        """Set the main content component."""
        self.content_container.set_content(component)
    
    def add_menu_item(self, key: str, label: str, action: Optional[Callable] = None) -> None:
        """Add a menu item."""
        self.menu_bar.add_item(key, label, action)
    
    def handle_key(self, key: str) -> Optional[Any]:
        """Handle key input and return action result."""
        # Try menu bar first
        result = self.menu_bar.handle_key(key)
        if result is not None:
            return result
        
        # Handle global keys
        if key.lower() == 'q':
            return 'quit'
        
        return None
    
    def handle_arrow_key(self, key_code: int) -> Optional[Any]:
        """Handle arrow key input and return action result."""
        # Pass arrow keys to menu bar for navigation
        result = self.menu_bar.handle_arrow_key(key_code)
        if result is not None:
            return result
        
        return None
    
    def set_status_message(self, message: str, duration: float = 3.0) -> None:
        """Set a temporary status message."""
        self.status_bar.set_message(message, duration)