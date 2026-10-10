import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "@CurrencyPricee")
INTERVAL_SECONDS = 15 * 60

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_market_prices() -> dict | None:
    url = "https://raw.githubusercontent.com/iran-market/iran-market.github.io/main/data/latest-toman.json"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        items = {}
        for cat in data.get("data", {}).get("categories", {}).values():
            for item in cat:
                if item.get("symbol"):
                    items[item["symbol"]] = item

        result = {}
        if "USD_IRR_FREE" in items:
            result["usd"] = int(items["USD_IRR_FREE"]["price"])
        if "USDT_IRR" in items:
            result["usdt"] = int(items["USDT_IRR"]["price"])
        if "GOLD_18K_IRR" in items:
            result["gold18"] = int(items["GOLD_18K_IRR"]["price"])
        if "COIN_BAHAR_IRR" in items:
            result["bahar"] = int(items["COIN_BAHAR_IRR"]["price"])
        if "TRX_USD" in items:
            result["trx_usd"] = float(items["TRX_USD"]["price"])

        return result if "usd" in result else None
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت: {e}")
        return None



def format_price_board(prices: dict) -> str:
    def fmt(n):
        if isinstance(n, float):
            return f"{n:.4f}"
        return f"{n:,}"

    # ساعت و تاریخ لحظه‌ای به وقت تهران
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%Y/%m/%d")

    return (
        "📊 <b>تابلو قیمت لحظه‌ای</b>\n"
        f"🕒زمان: {time_str} - {date_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"💵 <b>دلار آمریکا</b>\n"
        f"   {fmt(prices.get('usd', 0))} تومان\n\n"
        
        f"🪙 <b>تتر (USDT)</b>\n"
        f"   {fmt(prices.get('usdt', 0))} تومان\n\n"
        
        f"🟡 <b>طلای ۱۸ عیار</b>\n"
        f"   {fmt(prices.get('gold18', 0))} تومان <i>(هر گرم)</i>\n\n"
        
        f"🏅 <b>سکه بهار آزادی</b>\n"
        f"   {fmt(prices.get('bahar', 0))} تومان\n\n"
        
        f"⚡ <b>ترون (TRX)</b>\n"
        f"   {fmt(prices.get('trx_usd', 0))} دلار\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏰ به‌روزرسانی هر ۱۵ دقیقه\n"
        f"📢 {CHAT_ID}"
    )



async def send_price(context: ContextTypes.DEFAULT_TYPE):
    prices = get_market_prices()
    if not prices:
        await context.bot.send_message(chat_id=CHAT_ID, text="⚠️ خطا در دریافت قیمت‌ها")
        return
    await context.bot.send_message(chat_id=CHAT_ID, text=format_price_board(prices), parse_mode="HTML")
    logger.info(f"قیمت ارسال شد | دلار: {prices.get('usd')}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات فعال است.\n/price برای دریافت قیمت فوری")


async def price_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = get_market_prices()
    if prices:
        await update.message.reply_text(format_price_board(prices), parse_mode="HTML")
    else:
        await update.message.reply_text("⚠️ خطا در دریافت قیمت")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_now))

    job_queue = app.job_queue
    job_queue.run_repeating(send_price, interval=INTERVAL_SECONDS, first=15)

    logger.info("ربات شروع به کار کرد...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
