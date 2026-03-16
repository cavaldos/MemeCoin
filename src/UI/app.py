from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Footer, Header, Static

from .components import APP_CSS
from .navigate import HELP_TAB_ID, NAV_ITEMS, TAB_TITLES
from .pages import (
    mount_analyze,
    mount_dashboard,
    mount_help,
    mount_portfolio,
    mount_settings,
    mount_signals,
    mount_trade,
)


class MemeCoinTUI(App):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "next_tab", "Next Tab", show=True),
        Binding("ctrl+shift+n", "prev_tab", "Prev Tab", show=True),
        Binding("f1", "show_help", "Help", show=True),
    ]

    CSS = APP_CSS

    def __init__(self) -> None:
        super().__init__()
        self.current_tab = "dashboard"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="app-container"):
            with Horizontal(id="main-area"):
                with Vertical(id="navbar"):
                    yield Static("\u25c8 MEMECOIN\n  Trading Terminal", id="nav-brand")
                    yield Static("NAVIGATION", classes="nav-section-label")

                    for item in NAV_ITEMS:
                        btn = Button(
                            f" {item.icon}  {item.label}",
                            id=f"nav_{item.id}",
                            classes="nav-item",
                        )
                        if item.id == self.current_tab:
                            btn.add_class("active")
                        yield btn

                with Container(id="content-area"):
                    yield Container(id="content-header")
                    yield ScrollableContainer(id="content-body")

        yield Footer()

    def on_mount(self) -> None:
        self.call_later(self.async_update_content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("nav_"):
            return

        tab_id = button_id.replace("nav_", "")
        if tab_id == self.current_tab:
            return

        self.current_tab = tab_id
        self.update_nav_active()
        self.call_later(self.async_update_content)

    def update_nav_active(self) -> None:
        for button in self.query("Button.nav-item"):
            button_id = (button.id or "").replace("nav_", "")
            if button_id == self.current_tab:
                button.add_class("active")
            else:
                button.remove_class("active")

    async def async_update_content(self) -> None:
        content_body = self.query_one("#content-body", ScrollableContainer)
        content_header = self.query_one("#content-header", Container)

        if self.current_tab == HELP_TAB_ID:
            await mount_help(content_header, content_body)
            return

        async with content_header.batch():
            await content_header.remove_children()
            title, breadcrumb = TAB_TITLES.get(self.current_tab, ("", ""))
            await content_header.mount(Static(title, classes="title"))
            await content_header.mount(Static(breadcrumb, classes="breadcrumb"))

        async with content_body.batch():
            await content_body.remove_children()

            if self.current_tab == "dashboard":
                await mount_dashboard(content_body)
            elif self.current_tab == "analyze":
                await mount_analyze(content_body)
            elif self.current_tab == "trade":
                await mount_trade(content_body)
            elif self.current_tab == "signals":
                await mount_signals(content_body)
            elif self.current_tab == "portfolio":
                await mount_portfolio(content_body)
            elif self.current_tab == "settings":
                await mount_settings(content_body)

    def action_next_tab(self) -> None:
        idx = next((i for i, item in enumerate(NAV_ITEMS) if item.id == self.current_tab), 0)
        self.current_tab = NAV_ITEMS[(idx + 1) % len(NAV_ITEMS)].id
        self.update_nav_active()
        self.call_later(self.async_update_content)

    def action_prev_tab(self) -> None:
        idx = next((i for i, item in enumerate(NAV_ITEMS) if item.id == self.current_tab), 0)
        self.current_tab = NAV_ITEMS[(idx - 1) % len(NAV_ITEMS)].id
        self.update_nav_active()
        self.call_later(self.async_update_content)

    def action_show_help(self) -> None:
        self.current_tab = HELP_TAB_ID
        self.update_nav_active()
        self.call_later(self.async_update_content)

    async def action_quit(self) -> None:
        self.exit()
