"""
Discord bot with commands to manage the coin trend database.

Commands:
    !list [trend]        - List coins in a trend (main/strong/fast or all)
    !info <symbol>       - Show detailed info for a coin across all trends
    !delete <symbol>     - Delete a coin from all trends (or specify trend)
    !clear <trend>       - Clear all coins from a trend database
    !stats               - Show statistics across all trend databases
    !help_trends         - Show available commands
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

async def get_prefix(bot: commands.Bot, message: discord.Message) -> list[str]:
    """Return command prefixes including bot mention."""
    prefixes = ["!"]
    if message.guild:
        prefixes.append(f"<@{bot.user.id}> ")
        prefixes.append(f"<@!{bot.user.id}> ")
    return prefixes

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# Maps user-friendly names to internal filter keys
TREND_ALIAS: dict[str, str] = {
    "main": "main_trading",
    "main_trading": "main_trading",
    "main_trend": "main_trading",
    "strong": "strong_trending",
    "strong_trending": "strong_trending",
    "strong_trend": "strong_trending",
    "fast": "fast_trend",
    "fast_trend": "fast_trend",
}

FILTER_LABELS: dict[str, str] = {
    "main_trading": "Main Trend",
    "strong_trending": "Strong Trend",
    "fast_trend": "Fast Trend",
}

ALL_FILTER_KEYS = ("main_trading", "strong_trending", "fast_trend")


def _coerce_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _format_amount(value: object) -> str:
    amount = _coerce_float(value)
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.2f}K"
    return f"${amount:,.2f}"


def _format_percent(value: object) -> str:
    amount = _coerce_float(value)
    return f"{amount:+.2f}%"


def _resolve_trend(name: str | None) -> str | None:
    """Resolve user-friendly trend name to internal filter key. None = all."""
    if name is None:
        return None
    return TREND_ALIAS.get(name.strip().lower())


def _disable_embed(text: str) -> str:
    """Wrap URLs in < > to disable Discord link previews."""
    url_pattern = re.compile(r'https?://[^\s<>\]]+')
    return url_pattern.sub(lambda m: f"<{m.group(0)}>", text)


# ---------------------------------------------------------------------------
# Bot events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    logger.info("Discord bot logged in as %s", bot.user)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@bot.command(name="list")
async def cmd_list(ctx: commands.Context, trend: str | None = None):
    """List coins in a trend database. Usage: !list [main|strong|fast]"""
    from core.database import load_coins

    if trend is not None:
        filter_key = _resolve_trend(trend)
        if filter_key is None:
            await ctx.send(f"Unknown trend `{trend}`. Use: `main`, `strong`, `fast`.")
            return
        filter_keys = [filter_key]
    else:
        filter_keys = list(ALL_FILTER_KEYS)

    total_sent = 0
    for fk in filter_keys:
        coins = load_coins(fk)
        label = FILTER_LABELS.get(fk, fk)

        if not coins:
            await ctx.send(f"**{label}** — No coins saved.")
            continue

        header = f"**{label}** — {len(coins)} coin(s):\n"
        lines: list[str] = []
        for i, coin in enumerate(coins, 1):
            symbol = str(coin.get("symbol") or "?").upper()
            chain = str(coin.get("chain") or "-").upper()
            mcap = _format_amount(coin.get("market_cap"))
            vol = _format_amount(coin.get("volume"))
            vol_chg = _format_percent(coin.get("volume_change_percent_24h"))
            age = coin.get("age_minutes")
            age_str = f"{age}m" if isinstance(age, int) else "-"
            lines.append(
                f"`{i}.` **{symbol}** | {chain} | MCap: {mcap} | Vol: {vol} ({vol_chg}) | Age: {age_str}"
            )

        # Discord has a 2000 char limit per message
        message = header
        for line in lines:
            if len(message) + len(line) + 1 > 1900:
                await ctx.send(message)
                message = ""
                total_sent += 1
            message += line + "\n"

        if message.strip():
            await ctx.send(message)
            total_sent += 1


@bot.command(name="info")
async def cmd_info(ctx: commands.Context, symbol: str | None = None):
    """Show detailed info for a coin. Usage: !info <symbol>"""
    if not symbol:
        await ctx.send("Usage: `!info <symbol>` (e.g. `!info SOL`)")
        return

    from core.database import find_coin

    matches = find_coin(symbol)
    if not matches:
        await ctx.send(f"No coin found with symbol `{symbol.upper()}`.")
        return

    for coin in matches:
        fk = str(coin.get("filter_key") or "?")
        label = FILTER_LABELS.get(fk, fk)
        sym = str(coin.get("symbol") or "?").upper()
        name = str(coin.get("name") or "-")
        chain = str(coin.get("chain") or "-").upper()
        address = str(coin.get("address") or "-")
        mcap = _format_amount(coin.get("market_cap"))
        vol = _format_amount(coin.get("volume"))
        vol_chg = _format_percent(coin.get("volume_change_percent_24h"))
        age = coin.get("age_minutes")
        age_str = f"{age}m" if isinstance(age, int) else "-"
        url = str(coin.get("url") or "-")
        added = str(coin.get("added_at") or "-")
        updated = str(coin.get("updated_at") or "-")

        source_sites = coin.get("source_sites", [])
        src_str = ", ".join(str(s).upper() for s in source_sites) if isinstance(source_sites, list) and source_sites else "-"

        msg = "\n".join([
            f"**{sym}** — {name}",
            f"Trend: `{label}`",
            f"Chain: `{chain}`",
            f"Address: `{address}`",
            f"Market Cap: `{mcap}`",
            f"Volume: `{vol}` ({vol_chg})",
            f"Age: `{age_str}`",
            f"Sources: `{src_str}`",
            f"Added: `{added}`",
            f"Updated: `{updated}`",
            f"URL: <{url}>",
            "─" * 30,
        ])
        await ctx.send(msg)


@bot.command(name="delete")
async def cmd_delete(ctx: commands.Context, symbol: str | None = None, trend: str | None = None):
    """Delete a coin. Usage: !delete <symbol> [trend]"""
    if not symbol:
        await ctx.send("Usage: `!delete <symbol> [main|strong|fast]`")
        return

    from core.database import delete_coin, delete_coin_all_trends

    if trend is not None:
        filter_key = _resolve_trend(trend)
        if filter_key is None:
            await ctx.send(f"Unknown trend `{trend}`. Use: `main`, `strong`, `fast`.")
            return
        deleted = delete_coin(filter_key, symbol)
        if deleted:
            label = FILTER_LABELS.get(filter_key, filter_key)
            await ctx.send(f"Deleted `{symbol.upper()}` from **{label}**.")
        else:
            await ctx.send(f"`{symbol.upper()}` not found in **{FILTER_LABELS.get(filter_key, filter_key)}**.")
    else:
        deleted_from = delete_coin_all_trends(symbol)
        if deleted_from:
            labels = [FILTER_LABELS.get(fk, fk) for fk in deleted_from]
            await ctx.send(f"Deleted `{symbol.upper()}` from: {', '.join(labels)}.")
        else:
            await ctx.send(f"`{symbol.upper()}` not found in any trend database.")


@bot.command(name="clear")
async def cmd_clear(ctx: commands.Context, trend: str | None = None):
    """Clear all coins from a trend. Usage: !clear <main|strong|fast>"""
    if not trend:
        await ctx.send("Usage: `!clear <main|strong|fast>` — specify which trend to clear.")
        return

    filter_key = _resolve_trend(trend)
    if filter_key is None:
        await ctx.send(f"Unknown trend `{trend}`. Use: `main`, `strong`, `fast`.")
        return

    from core.database import clear_coins

    count = clear_coins(filter_key)
    label = FILTER_LABELS.get(filter_key, filter_key)
    await ctx.send(f"Cleared **{count}** coin(s) from **{label}**.")


@bot.command(name="stats")
async def cmd_stats(ctx: commands.Context):
    """Show statistics across all trend databases."""
    from core.database import get_stats

    stats = get_stats()
    lines = ["**Trend Database Stats**", ""]
    for fk in ALL_FILTER_KEYS:
        label = FILTER_LABELS.get(fk, fk)
        count = stats.get(fk, 0)
        lines.append(f"  {label}: **{count}** coin(s)")

    lines.append(f"\n  Total: **{stats.get('total', 0)}** coin(s)")
    await ctx.send("\n".join(lines))


@bot.command(name="check")
async def cmd_check(ctx: commands.Context, trend: str | None = None):
    """Check volume change of coins in a trend. Usage: !check <main|strong|fast>"""
    if not trend:
        await ctx.send("Usage: `!check <main|strong|fast>`")
        return

    filter_key = _resolve_trend(trend)
    if filter_key is None:
        await ctx.send(f"Unknown trend `{trend}`. Use: `main`, `strong`, `fast`.")
        return

    from core.database import load_coins

    coins = load_coins(filter_key)
    label = FILTER_LABELS.get(filter_key, filter_key)

    if not coins:
        await ctx.send(f"**{label}** — No coins in database.")
        return

    lines: list[str] = []
    for coin in coins:
        symbol = str(coin.get("symbol") or "?").upper()
        vol_now = _coerce_float(coin.get("volume"))
        vol_added = _coerce_float(coin.get("volume_at_added"))
        address = str(coin.get("address") or "")
        chain = str(coin.get("chain") or "sol").lower()
        url = coin.get("url")

        if url:
            link = url
        elif address:
            link = f"https://dexscreener.com/{chain}/{address}"
        else:
            link = None

        if vol_added > 0:
            change_pct = ((vol_now - vol_added) / vol_added) * 100
        else:
            change_pct = 0.0

        if change_pct > 0:
            arrow = "+"
        elif change_pct < 0:
            arrow = ""
        else:
            arrow = ""

        if link:
            lines.append(
                f"**{symbol}** | {link} | Vol: {_format_amount(vol_now)} | "
                f"Added: {_format_amount(vol_added)} | "
                f"Change: `{arrow}{change_pct:.2f}%`"
            )
        else:
            lines.append(
                f"**{symbol}** | Vol: {_format_amount(vol_now)} | "
                f"Added: {_format_amount(vol_added)} | "
                f"Change: `{arrow}{change_pct:.2f}%`"
            )

    header = f"**{label}** — Volume Check ({len(coins)} coin(s)):\n"
    message = header
    for line in lines:
        if len(message) + len(line) + 1 > 1900:
            await ctx.send(_disable_embed(message))
            message = ""
        message += line + "\n"

    if message.strip():
        await ctx.send(_disable_embed(message))


@bot.command(name="delete-chat")
async def cmd_delete_chat(ctx: commands.Context, channel_id: str | None = None):
    """Delete all messages in a channel. Usage: @bot delete-chat <channel_id>"""
    if not channel_id:
        await ctx.send("Usage: `@bot delete-chat <channel_id>`")
        return

    try:
        target_channel_id = int(channel_id.strip())
    except ValueError:
        await ctx.send(f"Invalid channel ID: `{channel_id}`. Please provide a valid numeric channel ID.")
        return

    target_channel = bot.get_channel(target_channel_id)
    if not target_channel:
        await ctx.send(f"Channel with ID `{target_channel_id}` not found. Make sure the bot has access to this channel.")
        return

    if not isinstance(target_channel, discord.TextChannel):
        await ctx.send(f"Channel with ID `{target_channel_id}` is not a text channel.")
        return

    try:
        deleted_count = await target_channel.purge(limit=None, check=lambda m: True)
        await ctx.send(f"Deleted **{len(deleted_count)}** message(s) from <#{target_channel_id}>.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete messages in that channel.")
    except discord.HTTPException:
        await ctx.send("Failed to delete messages. Some messages may be older than 14 days.")


@bot.command(name="all")
async def cmd_all(ctx: commands.Context):
    """Show all coins in database across all trends."""
    from core.database import load_all_coins

    all_coins = load_all_coins()
    total = sum(len(coins) for coins in all_coins.values())

    if total == 0:
        await ctx.send("No coins in database.")
        return

    lines: list[str] = [f"**All Coins in Database** — {total} total\n"]

    for fk in ALL_FILTER_KEYS:
        coins = all_coins.get(fk, [])
        label = FILTER_LABELS.get(fk, fk)
        if coins:
            lines.append(f"**{label}** ({len(coins)} coins):")
            for coin in coins:
                symbol = str(coin.get("symbol") or "?").upper()
                chain = str(coin.get("chain") or "-").upper()
                mcap = _format_amount(coin.get("market_cap"))
                lines.append(f"  • **{symbol}** | {chain} | MCap: {mcap}")

    message = "\n".join(lines)
    if len(message) > 1900:
        await ctx.send(lines[0])
        await ctx.send("\n".join(lines[1:]))
    else:
        await ctx.send(message)


@bot.command(name="help_trends")
async def cmd_help_trends(ctx: commands.Context):
    """Show all available trend commands."""
    msg = "\n".join([
        "**Trend Bot Commands**",
        "",
        "`!all` — Show all coins in database",
        "`!list [main|strong|fast]` — List coins (all trends if no argument)",
        "`!info <symbol>` — Detailed info for a coin",
        "`!delete <symbol> [main|strong|fast]` — Delete a coin (all trends if no argument)",
        "`!clear <main|strong|fast>` — Clear all coins from a trend",
        "`!check <main|strong|fast>` — Check volume change since added",
        "`!stats` — Show statistics",
        "`!help_trends` — This help message",
    ])
    await ctx.send(msg)


# ---------------------------------------------------------------------------
# Send alert via bot channel (used by webhook fallback)
# ---------------------------------------------------------------------------

async def send_message(message: str) -> bool:
    """Send message to Discord channel via bot."""
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID:
        return False
    try:
        channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
        if channel:
            await channel.send(message)
            return True
    except Exception:
        pass
    return False


async def send_filtered_alert(filter_key: str, filter_label: str, row: dict[str, object], detected_at: str) -> bool:
    symbol = str(row.get("symbol") or "?")
    name = str(row.get("name") or "-")
    chain = str(row.get("chain") or "-").upper()
    source_sites = row.get("source_sites", [])
    if isinstance(source_sites, list) and source_sites:
        source_label = ", ".join(str(source).upper() for source in source_sites)
    else:
        sources = row.get("sources", [])
        if isinstance(sources, list) and sources:
            source_label = ", ".join(str(source).upper() for source in sources)
        else:
            source_label = str(row.get("source") or "-").upper()

    filter_tag_map = {
        "main_trading": "MAIN",
        "strong_trending": "STRONG",
        "fast_trend": "FAST",
    }
    filter_tag = filter_tag_map.get(filter_key, filter_key.upper())

    age_minutes = row.get("age_minutes")
    age_label = f"{age_minutes}m" if isinstance(age_minutes, int) else "-"
    url = str(row.get("url") or row.get("coin_url") or "-")

    message = "\n".join(
        [
            "**NEW FILTER HIT**",
            f"Filter: `{filter_tag}` ({filter_label})",
            f"Token: `{symbol}` - {name}",
            f"Chain: `{chain}`",
            f"Source: `{source_label}`",
            f"Volume: `{_format_amount(row.get('volume'))}`",
            f"Vol 24h Change: `{_format_percent(row.get('volume_change_percent_24h'))}`",
            f"Market Cap: `{_format_amount(row.get('market_cap'))}`",
            f"Age: `{age_label}`",
            f"Detected: `{detected_at}`",
            f"URL: <{url}>",
        ]
    )
    return await send_message(message)


# ---------------------------------------------------------------------------
# Bot runner
# ---------------------------------------------------------------------------

def run_bot():
    """Run the Discord bot (blocking)."""
    if not DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set, skipping bot startup")
        return
    bot.run(DISCORD_BOT_TOKEN)


def run_bot_async(loop: asyncio.AbstractEventLoop | None = None):
    """Start the Discord bot in a background thread."""
    if not DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set, skipping bot startup")
        return

    import threading

    def _start():
        try:
            bot.run(DISCORD_BOT_TOKEN)
        except Exception:
            logger.exception("Discord bot crashed")

    thread = threading.Thread(target=_start, name="discord-bot", daemon=True)
    thread.start()
    logger.info("Discord bot started in background thread")
    return thread
