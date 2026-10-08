import logging
import httpx
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class TelegramAlertService:
    """
    Dispatches real-time paper trading telemetry and risk alerts to Telegram.
    Fails safely if credentials are not configured.
    """
    @classmethod
    def send_message(cls, text: str) -> bool:
        if not settings.enable_telegram_alerts or not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.debug(f"[Telegram Alert Disabled] {text}")
            return False

        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to dispatch Telegram alert: {e}")
            return False

    @classmethod
    def alert_paper_entry(
        cls,
        underlying: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        target: float,
        strategy: str,
        score: float,
        risk_amount: float
    ):
        msg = (
            f"🚀 *SHYAMEDGE PAPER TRADE ENTRY*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Underlying:* {underlying}\n"
            f"• *Contract:* `{symbol}` ({direction})\n"
            f"• *Strategy:* {strategy} (Score: {score}/100)\n"
            f"• *Entry Price:* ₹{entry_price:.2f}\n"
            f"• *Stop Loss:* ₹{stop_loss:.2f}\n"
            f"• *Target (1:2):* ₹{target:.2f}\n"
            f"• *Simulated Risk:* ₹{risk_amount:.2f}\n"
            f"• *Capital:* ₹15,000 Portfolio\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        cls.send_message(msg)

    @classmethod
    def alert_paper_exit(
        cls,
        symbol: str,
        entry_price: float,
        exit_price: float,
        gross_pnl: float,
        charges: float,
        slippage: float,
        net_pnl: float,
        exit_reason: str
    ):
        emoji = "🟢" if net_pnl > 0 else "🔴"
        msg = (
            f"{emoji} *SHYAMEDGE PAPER TRADE EXIT*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Contract:* `{symbol}`\n"
            f"• *Entry:* ₹{entry_price:.2f} | *Exit:* ₹{exit_price:.2f}\n"
            f"• *Gross P&L:* ₹{gross_pnl:+.2f}\n"
            f"• *Statutory Charges:* ₹{charges:.2f}\n"
            f"• *Slippage Drag:* ₹{slippage:.2f}\n"
            f"• *Net Realized P&L:* *₹{net_pnl:+.2f}*\n"
            f"• *Reason:* {exit_reason}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        cls.send_message(msg)

    @classmethod
    def alert_circuit_breaker(cls, reason: str, daily_loss: float):
        msg = (
            f"🚨 *CIRCUIT BREAKER TRIGGERED*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Status:* TRADING HALTED FOR THE DAY\n"
            f"• *Reason:* {reason}\n"
            f"• *Daily Net Loss:* ₹{daily_loss:.2f} (Limit: ₹450)\n"
            f"• *Safe Action:* All open positions liquidated\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        cls.send_message(msg)
