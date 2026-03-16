from textual.widgets import Input


class CopyField(Input):
    def __init__(self, value: str, *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(
            value,
            id=id,
            classes=classes,
            select_on_focus=True,
        )
        self.cursor_blink = False

    def insert_text_at_cursor(self, text: str) -> None:
        return None

    def action_delete_right(self) -> None:
        return None

    def action_delete_right_word(self) -> None:
        return None

    def action_delete_right_all(self) -> None:
        return None

    def action_delete_left(self) -> None:
        return None

    def action_delete_left_word(self) -> None:
        return None

    def action_delete_left_all(self) -> None:
        return None

    def action_paste(self) -> None:
        return None
