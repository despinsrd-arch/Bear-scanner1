import csv
import yfinance as yf

# -----------------------------
# LOAD TICKERS
# -----------------------------
def load_tickers(path="tickers.csv"):
    tickers = []
    with open(path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                tickers.append(row[0].strip())
    return tickers

# -----------------------------
# FETCH DATA FOR ONE TICKER
# -----------------------------
def fetch_data(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="6mo")

        if hist is None or hist.empty:
            return None

        hist = hist.dropna()
        if hist.empty:
            return None

        last_close = hist["Close"].iloc[-1]
        if last_close is None or last_close <= 0:
            return None

        # Timeframe closes
        close_1w = hist["Close"].iloc[-5] if len(hist) >= 5 else None
        close_1m = hist["Close"].iloc[-22] if len(hist) >= 22 else None
        close_3m = hist["Close"].iloc[-66] if len(hist) >= 66 else None
        close_6m = hist["Close"].iloc[0]

        def pct(a, b):
            try:
                return ((a - b) / b * 100) if (a is not None and b is not None) else None
            except Exception:
                return None

        return {
            "ticker": ticker,
            "last_close": last_close,
            "change_1w": pct(last_close, close_1w),
            "change_1m": pct(last_close, close_1m),
            "change_3m": pct(last_close, close_3m),
            "change_6m": pct(last_close, close_6m),
        }

    except Exception:
        return None

# -----------------------------
# SAVE RESULTS TO CSV
# -----------------------------
def save_results(all_results, winners):
    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Ticker", "Last Close", "1W %", "1M %", "3M %", "6M %"])
        for r in all_results:
            writer.writerow([
                r["ticker"],
                r["last_close"],
                r["change_1w"],
                r["change_1m"],
                r["change_3m"],
                r["change_6m"]
            ])

    with open("winners.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Ticker", "3M %", "1M %", "1W %", "6M %"])
        for r in winners:
            writer.writerow([
                r["ticker"],
                r["change_3m"],
                r["change_1m"],
                r["change_1w"],
                r["change_6m"]
            ])

# -----------------------------
# MAIN SCAN FUNCTION (USED BY API)
# -----------------------------
def run_scan():
    tickers = load_tickers()
    results = []

    for t in tickers:
        info = fetch_data(t)
        if info is not None:
            if info["last_close"] < 1:
                continue
            results.append(info)

    winners = [
        r for r in results
        if r["change_3m"] is not None and r["change_3m"] > 20
    ]

    winners.sort(key=lambda x: x["change_3m"], reverse=True)

    save_results(results, winners)

    return winners

# -----------------------------
# FASTAPI WRAPPER (RENDER USES THIS)
# -----------------------------
from fastapi import FastAPI
from fastapi.responses import JSONResponse

api = FastAPI()

@api.get("/")
def home():
    return {"message": "Bear-Scanner is running"}

@api.get("/screen")
def screen():
    winners = run_scan()
    return JSONResponse(content=winners)
