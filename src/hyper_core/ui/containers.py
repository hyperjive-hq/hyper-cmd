"""
Container components for the UI framework.

This module provides container components that handle layout, borders,
and space allocation. These components separate the concerns of:
- Visual decoration (borders, titles)
- Space allocation and layout
- Content rendering

Key classes:
- BorderedContainer: Draws borders/titles and provides content area
- FlexContainer: Manages flexible space allocation for children
"""

from typing import Any, Optional

from .engine import RenderContext, RenderState, UIComponent
from .renderer import BoxChars, TextStyle


class BorderedContainer(UIComponent):
    """
    A container that draws a border and provides content area for children.

    This separates the concern of border drawing from content rendering.
    Children only get to render within the content area.
    """

    def __init__(self, title: Optional[str] = None, show_border: bool = True):
        super().__init__()
        self._title = title
        self._show_border = show_border
        self._padding = (1, 1, 1, 1) if show_border else (0, 0, 0, 0)  # top, right, bottom, left
        self._content: Optional[UIComponent] = None

    def set_content(self, component: UIComponent) -> None:
        """Set the content component."""
        if self._content:
            self._children.remove(self._content)
        self._content = component
        if component:
            self._children.append(component)
        self.mark_dirty()

    def get_content(self) -> Optional[UIComponent]:
        """Get the content component."""
        return self._content

    def get_size_hint(self) -> tuple[int, int]:
        """Calculate size including border and padding."""
        # Start with content size
        if self._content:
            content_width, content_height = self._content.get_size_hint()
        else:
            content_width, content_height = (0, 0)

        # Add padding/border space
        top, right, bottom, left = self._padding
        total_width = content_width + left + right
        total_height = content_height + top + bottom

        # Ensure minimum width for title
        if self._title and self._show_border:
            title_width = len(self._title) + 4  # " Title " format
            total_width = max(total_width, title_width + 2)  # +2 for borders

        return (total_width, total_height)

    def _render_children(self, ctx: RenderContext) -> None:
        """Override to prevent double rendering.

        BorderedContainer handles child rendering in render_content.
        """
        pass

    def render_content(self, ctx: RenderContext) -> None:
        """Render border and title, then render content in the inner area."""
        # Draw border if enabled
        if self._show_border:
            self._draw_border(ctx)
            if self._title:
                self._draw_title(ctx)

        # Calculate content area
        top, right, bottom, left = self._padding
        content_x = ctx.x + left
        content_y = ctx.y + top
        content_width = max(0, ctx.width - left - right)
        content_height = max(0, ctx.height - top - bottom)

        # Render content within the content area only
        if self._content and content_width > 0 and content_height > 0:
            content_ctx = RenderContext(
                window=ctx.window,
                x=content_x,
                y=content_y,
                width=content_width,
                height=content_height,
                theme=ctx.theme,
                frame_time=ctx.frame_time,
            )
            self._content.render(content_ctx)

    def _draw_border(self, ctx: RenderContext) -> None:
        """Draw border within our allocated space."""
        if ctx.width < 2 or ctx.height < 2:
            return  # Not enough space for border

        # Draw corners
        ctx.window.add_ch(ctx.y, ctx.x, BoxChars.ACS_ULCORNER or BoxChars.ULCORNER)
        ctx.window.add_ch(ctx.y, ctx.x + ctx.width - 1, BoxChars.ACS_URCORNER or BoxChars.URCORNER)
        ctx.window.add_ch(ctx.y + ctx.height - 1, ctx.x, BoxChars.ACS_LLCORNER or BoxChars.LLCORNER)
        ctx.window.add_ch(
            ctx.y + ctx.height - 1,
            ctx.x + ctx.width - 1,
            BoxChars.ACS_LRCORNER or BoxChars.LRCORNER,
        )

        # Draw horizontal lines
        hline = BoxChars.ACS_HLINE or BoxChars.HLINE
        for x in range(1, ctx.width - 1):
            ctx.window.add_ch(ctx.y, ctx.x + x, hline)
            ctx.window.add_ch(ctx.y + ctx.height - 1, ctx.x + x, hline)

        # Draw vertical lines
        vline = BoxChars.ACS_VLINE or BoxChars.VLINE
        for y in range(1, ctx.height - 1):
            ctx.window.add_ch(ctx.y + y, ctx.x, vline)
            ctx.window.add_ch(ctx.y + y, ctx.x + ctx.width - 1, vline)

    def _draw_title(self, ctx: RenderContext) -> None:
        """Draw title in the top border."""
        if not self._title or ctx.width < 6:  # Need space for " Title "
            return

        # Format title with spaces
        title_text = f" {self._title} "
        max_title_width = ctx.width - 4  # Leave space for corners and padding
        if len(title_text) > max_title_width:
            title_text = title_text[: max_title_width - 3] + "..."

        # Center the title
        title_x = ctx.x + (ctx.width - len(title_text)) // 2

        # Draw title over the top border
        ctx.window.add_str(ctx.y, title_x, title_text, TextStyle.BOLD)


class FlexContainer(UIComponent):
    """
    A container that manages space allocation for its children.

    Children can be configured with:
    - Fixed size (always gets exactly that space)
    - Flex size (shares remaining space proportionally)
    - Min/max constraints
    """

    def __init__(self, direction: str = "vertical"):
        super().__init__()
        if direction not in ("vertical", "horizontal"):
            raise ValueError(f"Invalid direction: {direction}. Must be 'vertical' or 'horizontal'.")
        self.direction = direction
        self._child_configs: dict[UIComponent, dict[str, Any]] = {}

    def add_child_with_config(
        self,
        child: UIComponent,
        fixed_size: Optional[int] = None,
        flex: float = 0.0,
        min_size: int = 0,
        max_size: Optional[int] = None,
    ) -> None:
        """Add a child with specific size configuration."""
        self.add_child(child)
        self._child_configs[child] = {
            "fixed_size": fixed_size,
            "flex": flex,
            "min_size": min_size,
            "max_size": max_size,
        }

    def get_size_hint(self) -> tuple[int, int]:
        """Calculate size based on children."""
        if not self._children:
            return (0, 0)

        if self.direction == "vertical":
            # Width is the maximum child width
            # Height is sum of all child heights
            max_width = 0
            total_height = 0

            for child in self._children:
                if child.get_render_state() != RenderState.HIDDEN:
                    w, h = child.get_size_hint()
                    max_width = max(max_width, w)

                    config = self._child_configs.get(child, {})
                    if config.get("fixed_size") is not None:
                        total_height += config["fixed_size"]
                    else:
                        total_height += h

            return (max_width, total_height)
        else:
            # Horizontal layout - opposite of vertical
            max_height = 0
            total_width = 0

            for child in self._children:
                if child.get_render_state() != RenderState.HIDDEN:
                    w, h = child.get_size_hint()
                    max_height = max(max_height, h)

                    config = self._child_configs.get(child, {})
                    if config.get("fixed_size") is not None:
                        total_width += config["fixed_size"]
                    else:
                        total_width += w

            return (total_width, max_height)

    def _render_children(self, ctx: RenderContext) -> None:
        """Override to prevent double rendering.

        FlexContainer handles child rendering in render_content,
        so we don't want the default behavior.
        """
        pass

    def render_content(self, ctx: RenderContext) -> None:
        """Render children with proper space allocation."""
        if not self._children:
            return

        # Calculate space allocation for each child
        allocations = self._calculate_allocations(ctx)

        # Render each child in its allocated space
        if self.direction == "vertical":
            current_y = ctx.y
            for child, allocation in allocations:
                if allocation["size"] > 0:
                    child_ctx = RenderContext(
                        window=ctx.window,
                        x=ctx.x,
                        y=current_y,
                        width=ctx.width,
                        height=allocation["size"],
                        theme=ctx.theme,
                        frame_time=ctx.frame_time,
                    )
                    child.render(child_ctx)
                    current_y += allocation["size"]
        else:
            # Horizontal layout
            current_x = ctx.x
            for child, allocation in allocations:
                if allocation["size"] > 0:
                    child_ctx = RenderContext(
                        window=ctx.window,
                        x=current_x,
                        y=ctx.y,
                        width=allocation["size"],
                        height=ctx.height,
                        theme=ctx.theme,
                        frame_time=ctx.frame_time,
                    )
                    child.render(child_ctx)
                    current_x += allocation["size"]

    def _calculate_allocations(self, ctx: RenderContext) -> list:
        """Calculate space allocation for each visible child."""
        allocations = []
        visible_children = [c for c in self._children if c.get_render_state() != RenderState.HIDDEN]

        if not visible_children:
            return allocations

        # Determine total available space
        if self.direction == "vertical":
            total_space = ctx.height
        else:
            total_space = ctx.width

        # First pass: allocate fixed sizes and calculate flex total
        remaining_space = total_space
        total_flex = 0.0

        for child in visible_children:
            config = self._child_configs.get(child, {})

            if config.get("fixed_size") is not None:
                # Fixed size child
                size = min(config["fixed_size"], remaining_space)
                allocations.append((child, {"size": size, "flex": 0}))
                remaining_space -= size
            else:
                # Flexible child
                flex = config.get("flex", 1.0)  # Default flex is 1.0
                total_flex += flex
                allocations.append((child, {"size": 0, "flex": flex}))

        # Second pass: distribute remaining space to flexible children
        if total_flex > 0 and remaining_space > 0:
            for i, (child, alloc) in enumerate(allocations):
                if alloc["flex"] > 0:
                    # Calculate proportional space
                    flex_space = int(remaining_space * (alloc["flex"] / total_flex))

                    # Apply min/max constraints
                    config = self._child_configs.get(child, {})
                    min_size = config.get("min_size", 0)
                    max_size = config.get("max_size")

                    flex_space = max(flex_space, min_size)
                    if max_size is not None:
                        flex_space = min(flex_space, max_size)

                    allocations[i] = (child, {"size": flex_space, "flex": alloc["flex"]})

        return allocations
