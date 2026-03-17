from .webhook import send_message as webhook_send_message
from .webhook import send_filtered_alert as webhook_send_filtered_alert
from .bot import send_message as bot_send_message
from .bot import send_filtered_alert as bot_send_filtered_alert
from .bot import run_bot, run_bot_async

send_message = webhook_send_message
send_filtered_alert = webhook_send_filtered_alert

__all__ = [
    "send_message",
    "send_filtered_alert",
    "webhook_send_message",
    "webhook_send_filtered_alert",
    "bot_send_message",
    "bot_send_filtered_alert",
    "run_bot",
    "run_bot_async",
]
