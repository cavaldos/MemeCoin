from textual.containers import Container, ScrollableContainer
from textual.widgets import Static


async def mount_help(content_header: Container, content_body: ScrollableContainer) -> None:
    async with content_header.batch():
        await content_header.remove_children()
        await content_header.mount(Static("?  Help", classes="title"))
        await content_header.mount(Static("Reference \u203a Keyboard Shortcuts", classes="breadcrumb"))

    async with content_body.batch():
        await content_body.remove_children()
        await content_body.mount(
            Static(
                "[bold #c678dd]KEYBOARD SHORTCUTS[/]\n\n"
                "[bold #61afef]Navigation[/]\n"
                "  [#e5c07b]Ctrl+N[/]           [#abb2bf]Next tab[/]\n"
                "  [#e5c07b]Ctrl+Shift+N[/]     [#abb2bf]Previous tab[/]\n"
                "  [#e5c07b]Up / Down[/]        [#abb2bf]Navigate items[/]\n"
                "  [#e5c07b]Tab / Shift+Tab[/]  [#abb2bf]Move focus[/]\n\n"
                "[bold #61afef]Actions[/]\n"
                "  [#e5c07b]Enter[/]            [#abb2bf]Select / Execute[/]\n"
                "  [#e5c07b]Escape[/]           [#abb2bf]Cancel / Clear[/]\n\n"
                "[bold #61afef]System[/]\n"
                "  [#e5c07b]F1[/]               [#abb2bf]Show this help[/]\n"
                "  [#e5c07b]Ctrl+Q[/]           [#abb2bf]Quit application[/]\n\n"
                "[#5c6370]Tip: Use arrow keys to navigate menu items, "
                "then press Enter to select.[/]",
                classes="panel",
            )
        )
