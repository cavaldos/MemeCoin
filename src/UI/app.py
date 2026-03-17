import os
import platform
import shutil
import subprocess
from datetime import datetime
from math import ceil
from typing import TYPE_CHECKING, cast

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical, VerticalGroup
from textual.widgets import Button, Footer, Header, Input, Static

from core.trending_config import refresh_config_results, reset_config

from .components import APP_CSS
from .navigate import HELP_TAB_ID, NAV_ITEMS, TAB_TITLES
from .pages import (
    mount_all_symbols,
    mount_dexscreener,
    mount_gmgn,
    mount_help,
    mount_history,
    mount_settings,
    refresh_all_symbols_results,
    refresh_dexscreener_results,
    refresh_gmgn_results,
)

if TYPE_CHECKING:
    from core import MarketDataPoller


class MemeCoinTUI(App):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+n", "next_tab", "Next Tab", show=True),
        Binding("ctrl+shift+n", "prev_tab", "Prev Tab", show=True),
        Binding("f1", "show_help", "Help", show=True),
    ]

    CSS = APP_CSS

    def __init__(self, poller: "MarketDataPoller | None" = None) -> None:
        super().__init__()
        self.poller = poller
        self.current_tab = NAV_ITEMS[0].id
        self.search_queries = {
            "dexscreener": "",
            "gmgn": "",
            "all_symbols": "",
        }
        self._last_market_success: dict[str, datetime | None] = {
            "dexscreener": None,
            "gmgn": None,
        }
        self._uptime_started_at = datetime.now()

    @staticmethod
    def _display_url(url: str) -> str:
        if url.startswith("https://"):
            return url[8:]
        if url.startswith("http://"):
            return url[7:]
        return url

    def _format_uptime(self) -> str:
        elapsed = datetime.now() - self._uptime_started_at
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        return f"{elapsed.days}d {hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def _is_ssh_session() -> bool:
        return bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))

    @staticmethod
    def _copy_with_command(command: list[str], text: str) -> bool:
        try:
            subprocess.run(
                command,
                input=text,
                text=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return True

    def _copy_into_tmux_buffer(self, text: str) -> bool:
        if not os.environ.get("TMUX") or not shutil.which("tmux"):
            return False
        return self._copy_with_command(["tmux", "load-buffer", "-"], text)

    def _copy_url(self, url: str) -> bool:
        self._copy_into_tmux_buffer(url)

        if self._is_ssh_session():
            self.copy_to_clipboard(url)
            return True

        system_name = platform.system()
        if system_name == "Darwin" and shutil.which("pbcopy"):
            return self._copy_with_command(["pbcopy"], url)

        if system_name == "Windows" and shutil.which("clip"):
            return self._copy_with_command(["clip"], url)

        linux_commands = [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]
        for command in linux_commands:
            if shutil.which(command[0]) and self._copy_with_command(command, url):
                return True

        self.copy_to_clipboard(url)
        return True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="app-container"):
            with Horizontal(id="main-area"):
                with Vertical(id="navbar"):
                    yield Static("\u25c8 MEMECOIN\n  Trading Terminal", id="nav-brand")
                    yield Static("RUN TIME", classes="nav-section-label")
                    yield Static("00d 00:00:00", id="uptime-display")
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
        self.set_interval(1, self._tick_market_status)

    def _tick_market_status(self) -> None:
        self._update_uptime_display()
        self._update_market_poll_status()
        self._refresh_market_data_if_needed()

    def _update_uptime_display(self) -> None:
        try:
            uptime_widget = self.query_one("#uptime-display", Static)
            uptime_widget.update(self._format_uptime())
        except NoMatches:
            pass

    def _build_market_poll_status(self, source_name: str) -> Text:
        status_text = Text(style="#5c6370")

        if self.poller is None:
            status_text.append("Auto refresh: ")
            status_text.append("OFF", style="bold #e06c75")
            return status_text

        poller_status = self.poller.get_status()
        interval_seconds = cast(int, poller_status["interval_seconds"])
        cycle_in_progress = bool(poller_status["cycle_in_progress"])
        next_run_at = cast(datetime | None, poller_status["next_run_at"])
        last_success_map = cast(dict[str, datetime | None], poller_status["last_success_at"])
        last_error_map = cast(dict[str, str | None], poller_status["last_error"])
        last_success_at = last_success_map.get(source_name)
        last_error = last_error_map.get(source_name)

        status_text.append("Auto refresh every ")
        status_text.append(f"{interval_seconds}s", style="bold #abb2bf")

        if cycle_in_progress:
            status_text.append(" | Refreshing ")
            status_text.append("now", style="bold #e5c07b")
        elif next_run_at is not None:
            remaining_seconds = max(ceil((next_run_at - datetime.now()).total_seconds()), 0)
            status_text.append(" | Next API call in ")
            status_text.append(f"{remaining_seconds}s", style="bold #98c379")

        if last_success_at is not None:
            status_text.append(" | Last success ")
            status_text.append(last_success_at.strftime("%H:%M:%S"), style="bold #61afef")

        if last_error:
            status_text.append(" | Last error ")
            status_text.append(last_error[:60], style="bold #e06c75")

        return status_text

    def _update_market_poll_status(self) -> None:
        if self.current_tab not in {"dexscreener", "gmgn"}:
            return

        try:
            status_widget = self.query_one(f"#{self.current_tab}-poll-status", Static)
        except NoMatches:
            return

        status_widget.update(self._build_market_poll_status(self.current_tab))

    def _refresh_market_data_if_needed(self) -> None:
        if self.poller is None:
            return

        poller_status = self.poller.get_status()
        last_success_map = cast(dict[str, datetime | None], poller_status["last_success_at"])
        changed_sources: set[str] = set()

        for source_name in ("dexscreener", "gmgn"):
            last_success_at = last_success_map.get(source_name)
            if last_success_at is None or last_success_at == self._last_market_success[source_name]:
                continue
            self._last_market_success[source_name] = last_success_at
            changed_sources.add(source_name)

        if not changed_sources:
            return

        if self.current_tab in {"dexscreener", "gmgn"} and self.current_tab in changed_sources:
            self.call_later(self.async_refresh_search_results)
            return

        if self.current_tab in {"settings", "history"}:
            self.call_later(self.async_update_content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("copy_"):
            event.stop()
            url = (event.button.name or "").strip()
            if not url:
                self.notify("No URL available for this symbol.", title="Clipboard", severity="warning")
                return
            copied = self._copy_url(url)
            if not copied:
                self.notify(
                    f"Copy failed. Use this URL: {self._display_url(url)}",
                    title="Clipboard",
                    severity="warning",
                    markup=False,
                )
                return
            self.notify(
                f"Copied: {self._display_url(url)}",
                title="Clipboard",
                markup=False,
            )
            return

        if button_id == "settings-save":
            try:
                refresh_config_results(send_alerts=False)
                if self.poller is not None:
                    self.poller.reload_settings()
            except Exception as exc:
                self.notify(str(exc), title="Settings", severity="error")
                return

            self.notify("Saved trend presets to res/data/config.json", title="Settings")
            self.call_later(self.async_update_content)
            return

        if button_id == "settings-reset":
            try:
                config = reset_config()
                refresh_config_results(config=config, send_alerts=False)
                if self.poller is not None:
                    self.poller.reload_settings()
            except Exception as exc:
                self.notify(str(exc), title="Settings", severity="error")
                return

            self.notify("Reset trend presets in res/data/config.json", title="Settings")
            self.call_later(self.async_update_content)
            return

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

    def on_input_changed(self, event: Input.Changed) -> None:
        input_id = event.input.id or ""
        if input_id == "dexscreener-search":
            self.search_queries["dexscreener"] = event.value
        elif input_id == "gmgn-search":
            self.search_queries["gmgn"] = event.value
        elif input_id == "all_symbols-min-volume":
            self.search_queries["all_symbols"] = event.value
        else:
            return

        self.call_later(self.async_refresh_search_results)

    async def async_refresh_search_results(self) -> None:
        try:
            if self.current_tab == "dexscreener":
                results = self.query_one("#dexscreener-results", VerticalGroup)
                await refresh_dexscreener_results(results, self.search_queries["dexscreener"])
            elif self.current_tab == "gmgn":
                results = self.query_one("#gmgn-results", VerticalGroup)
                await refresh_gmgn_results(results, self.search_queries["gmgn"])
            elif self.current_tab == "all_symbols":
                results = self.query_one("#all_symbols-results", VerticalGroup)
                await refresh_all_symbols_results(results, self.search_queries["all_symbols"])
        except NoMatches:
            return
        finally:
            self._update_market_poll_status()

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

            if self.current_tab == "all_symbols":
                await mount_all_symbols(content_body, self.search_queries["all_symbols"])
            elif self.current_tab == "dexscreener":
                await mount_dexscreener(content_body, self.search_queries["dexscreener"])
            elif self.current_tab == "gmgn":
                await mount_gmgn(content_body, self.search_queries["gmgn"])
            elif self.current_tab == "history":
                await mount_history(content_body)
            elif self.current_tab == "settings":
                await mount_settings(content_body)

        self._update_market_poll_status()

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
