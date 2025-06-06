"""
UI Rendering Engine for Hyper Framework

Provides a consistent, optimized rendering system for all UI components.
This engine handles:
- Render state management and dirty checking
- Optimized screen updates with double buffering
- Component lifecycle and drawing coordination
- Event-driven rendering with minimal redraws
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Protocol

from .renderer import RenderingBackend, Window, WindowSpec, TextStyle, BoxChars


class RenderState(Enum):
    """States that components can be in regarding rendering."""
    CLEAN = "clean"           # No redraw needed
    DIRTY = "dirty"           # Needs redraw
    INVALIDATED = "invalidated"  # Needs full rebuild
    HIDDEN = "hidden"         # Not visible, skip rendering


@dataclass
class RenderContext:
    """Context information passed to components during rendering."""
    window: Window  # Window object from renderer
    x: int
    y: int
    width: int
    height: int
    theme: Optional[Any] = None
    frame_time: float = field(default_factory=time.time)


class Renderable(Protocol):
    """Protocol for objects that can be rendered by the engine."""
    
    def get_render_state(self) -> RenderState:
        """Get current render state of this component."""
        ...
    
    def mark_dirty(self) -> None:
        """Mark this component as needing a redraw."""
        ...
    
    def render(self, ctx: RenderContext) -> None:
        """Render this component in the given context."""
        ...
    
    def get_size_hint(self) -> Tuple[int, int]:
        """Get preferred (width, height) for this component."""
        ...


class UIComponent(ABC):
    """Base class for UI components with built-in render state management."""
    
    def __init__(self):
        self._render_state = RenderState.DIRTY
        self._last_size = (0, 0)
        self._last_position = (0, 0)
        self._visible = True
        self._children: List[UIComponent] = []
        self._parent: Optional[UIComponent] = None
    
    @property
    def render_state(self) -> RenderState:
        """Get current render state."""
        if not self._visible:
            return RenderState.HIDDEN
        return self._render_state
    
    def mark_dirty(self) -> None:
        """Mark this component as needing a redraw."""
        if self._render_state != RenderState.INVALIDATED:
            self._render_state = RenderState.DIRTY
        
        # Propagate to parent
        if self._parent:
            self._parent.mark_dirty()
    
    def mark_clean(self) -> None:
        """Mark this component as clean (no redraw needed)."""
        self._render_state = RenderState.CLEAN
    
    def invalidate(self) -> None:
        """Mark this component as needing full rebuild."""
        self._render_state = RenderState.INVALIDATED
        
        # Invalidate all children
        for child in self._children:
            child.invalidate()
    
    def set_visible(self, visible: bool) -> None:
        """Set visibility of this component."""
        if self._visible != visible:
            self._visible = visible
            if self._parent:
                self._parent.mark_dirty()
    
    def add_child(self, child: 'UIComponent') -> None:
        """Add a child component."""
        child._parent = self
        self._children.append(child)
        self.mark_dirty()
    
    def remove_child(self, child: 'UIComponent') -> None:
        """Remove a child component."""
        if child in self._children:
            child._parent = None
            self._children.remove(child)
            self.mark_dirty()
    
    def get_render_state(self) -> RenderState:
        """Get current render state."""
        return self.render_state
    
    @abstractmethod
    def get_size_hint(self) -> Tuple[int, int]:
        """Get preferred (width, height) for this component."""
        pass
    
    @abstractmethod
    def render_content(self, ctx: RenderContext) -> None:
        """Render the content of this component."""
        pass
    
    def render(self, ctx: RenderContext) -> None:
        """Render this component and its children."""
        if self.render_state == RenderState.HIDDEN:
            return
        
        # Check if size or position changed
        current_size = (ctx.width, ctx.height)
        current_pos = (ctx.x, ctx.y)
        
        if (current_size != self._last_size or 
            current_pos != self._last_position):
            self.invalidate()
            self._last_size = current_size
            self._last_position = current_pos
        
        # Render if needed
        if self.render_state in (RenderState.DIRTY, RenderState.INVALIDATED):
            try:
                self.render_content(ctx)
                self.mark_clean()
            except Exception:
                # Handle rendering errors gracefully
                pass
        
        # Render children
        self._render_children(ctx)
    
    def _render_children(self, ctx: RenderContext) -> None:
        """Render all child components."""
        for child in self._children:
            if child.get_render_state() != RenderState.HIDDEN:
                child.render(ctx)


class RenderEngine:
    """
    Main rendering engine that coordinates all UI rendering.
    
    Provides optimized rendering with:
    - Dirty checking to minimize redraws
    - Double buffering for smooth updates
    - Component lifecycle management
    - Event-driven rendering
    """
    
    def __init__(self, backend: RenderingBackend):
        self.backend = backend
        self.root_window: Optional[Window] = None
        self.root_component: Optional[UIComponent] = None
        self.theme = None
        
        # Rendering state
        self._last_screen_size = (0, 0)
        self._force_redraw = True
        self._frame_count = 0
        
        # Performance tracking
        self._render_times: List[float] = []
        self._max_render_history = 100
        
        # Setup rendering
        self._setup_rendering()
    
    def _setup_rendering(self) -> None:
        """Setup optimal rendering settings."""
        # Initialize backend
        self.backend.init()
        
        # Initialize colors if supported
        if self.backend.has_colors():
            self.backend.init_colors()
        
        # Hide cursor
        self.backend.set_cursor_visible(False)
        
        # Create main window
        height, width = self.backend.get_screen_size()
        self.root_window = self.backend.create_window(
            WindowSpec(width=width, height=height, x=0, y=0)
        )
    
    def set_root_component(self, component: UIComponent) -> None:
        """Set the root component to render."""
        self.root_component = component
        self._force_redraw = True
    
    def set_theme(self, theme: Any) -> None:
        """Set the current theme."""
        self.theme = theme
        if self.root_component:
            self.root_component.invalidate()
    
    def needs_redraw(self) -> bool:
        """Check if anything needs to be redrawn."""
        # Check for screen size changes
        current_size = self.backend.get_screen_size()
        if current_size != self._last_screen_size:
            self._last_screen_size = current_size
            if self.root_component:
                self.root_component.invalidate()
            return True
        
        # Check if force redraw is needed
        if self._force_redraw:
            return True
        
        # Check if root component needs redraw
        if (self.root_component and 
            self.root_component.get_render_state() in 
            (RenderState.DIRTY, RenderState.INVALIDATED)):
            return True
        
        return False
    
    def render_frame(self) -> None:
        """Render a complete frame if needed."""
        if not self.needs_redraw():
            return
        
        start_time = time.time()
        
        try:
            # Clear the screen efficiently
            if self._force_redraw and self.root_window:
                self.root_window.clear()
            
            # Render root component if available
            if self.root_component:
                height, width = self.backend.get_screen_size()
                ctx = RenderContext(
                    window=self.root_window,
                    x=0, y=0,
                    width=width, height=height,
                    theme=self.theme,
                    frame_time=start_time
                )
                
                self.root_component.render(ctx)
            
            # Refresh display
            self.backend.refresh()
            
        except Exception:
            # Handle terminal resize or other rendering errors
            pass
        
        # Reset flags
        self._force_redraw = False
        self._frame_count += 1
        
        # Track performance
        render_time = time.time() - start_time
        self._render_times.append(render_time)
        if len(self._render_times) > self._max_render_history:
            self._render_times.pop(0)
    
    def force_redraw(self) -> None:
        """Force a complete redraw on next render."""
        self._force_redraw = True
        if self.root_component:
            self.root_component.invalidate()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics."""
        if not self._render_times:
            return {}
        
        avg_time = sum(self._render_times) / len(self._render_times)
        max_time = max(self._render_times)
        min_time = min(self._render_times)
        
        return {
            'frame_count': self._frame_count,
            'avg_render_time_ms': avg_time * 1000,
            'max_render_time_ms': max_time * 1000,
            'min_render_time_ms': min_time * 1000,
            'fps_estimate': 1.0 / avg_time if avg_time > 0 else 0,
            'render_samples': len(self._render_times)
        }


