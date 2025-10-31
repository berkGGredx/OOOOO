import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from textblob import TextBlob
import io
import logging

# ---------------------- CONFIG ----------------------
TOKEN = "8404903661:AAFd17CEORekRNj3OHZgxJ63BWxL03va4JA"
ALPHA_API_KEY = "IJOV258ACD0G9QSP"
# ---------------------------------------------------

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# ---------------------- Fonksiyonlar ----------------------

def get_stock_data(symbol):
    """
    Alpha Vantage API ile günlük veri çeker
    """
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_API_KEY}&outputsize=compact"
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data['Time Series (Daily)']).T.astype(float)
        df = df.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. adjusted close': 'Adj Close',
            '6. volume': 'Volume'
        })
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    except Exception as e:
        logging.error(f"Data fetch error: {e}")
        return None

def simple_sentiment(symbol):
    """
    Basit TextBlob ile sentiment puanı
    """
    sample_texts = [
        f"{symbol} fiyatları yükseliyor, yatırımcılar umutlu",
        f"{symbol} düşüşte, bazı yatırımcılar endişeli",
        f"{symbol} stabil, piyasa sakin"
    ]
    score = 0
    for text in sample_texts:
        tb = TextBlob(text)
        score += tb.sentiment.polarity
    return round(score)

def analyze(symbol):
    df = get_stock_data(symbol)
    if df is None or df.empty:
        return f"{symbol} için veri alınamadı."
    
    # Teknik analiz
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    latest = df.iloc[-1]
    
    score = 0
    if latest['EMA20'] > latest['EMA50']: score += 1
    else: score -= 1
    if latest['RSI'] < 70: score += 1
    elif latest['RSI'] > 70: score -= 1
    
    sentiment_score = simple_sentiment(symbol)
    score += sentiment_score
    
    if score >= 2:
        signal = "LONG ✅"
    elif score <= -1:
        signal = "SHORT ❌"
    else:
        signal = "NÖTR ⚪"
    
    return f"{symbol} Analizi:\nFiyat: {latest['Close']:.2f}\nEMA20: {latest['EMA20']:.2f}\nEMA50: {latest['EMA50']:.2f}\nRSI: {latest['RSI']:.2f}\nSentiment Skoru: {sentiment_score}\nSinyal: {signal}"

def plot_symbol(symbol):
    df = get_stock_data(symbol)
    if df is None: return None
    plt.figure(figsize=(10,5))
    plt.plot(df['Close'], label='Close', color='blue')
    plt.plot(df['Close'].ewm(span=20, adjust=False).mean(), label='EMA20', color='orange')
    plt.plot(df['Close'].ewm(span=50, adjust=False).mean(), label='EMA50', color='green')
    plt.title(f"{symbol} Fiyat Grafiği")
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# ---------------------- Telegram Komutları ----------------------

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Lütfen bir sembol girin, örn: /signal AAPL")
        return
    symbol = context.args[0].upper()
    result = analyze(symbol)
    await update.message.reply_text(result)

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Lütfen bir sembol girin, örn: /chart AAPL")
        return
    symbol = context.args[0].upper()
    buf = plot_symbol(symbol)
    if buf:
        await update.message.reply_photo(buf)
    else:
        await update.message.reply_text(f"{symbol} için grafik alınamadı.")

# ---------------------- Bot Başlatma ----------------------

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("chart", chart))

print("Bot çalışıyor...")
app.run_polling()
