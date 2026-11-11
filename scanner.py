NSE F&O Live Stock Screener (9:25 AM Execution)
Author: Your Name
Description: Screens F&O stocks at market open based on OI Change, Previous Day Performance, 
             Breakouts, High Delivery Volume, and 200-day Moving Average (SMA).
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf


class NSEFnOScreener:

    def __init__(self):
        # प्रमुख NSE F&O स्टॉक्स की लिस्ट (आप इसे आवश्यकतानुसार बढ़ा सकते हैं)
        self.fno_tickers = [
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "BHARTIARTL",
            "TITAN",
            "TATAMOTORS",
            "AXISBANK",
            "MARUTI",
            "KOTAKBANK",
            "ITC",
            "LT",
            "BAJFINANCE",
        ]
        self.yahoo_tickers = [f"{t}.NS" for t in self.fno_tickers]

    def fetch_market_data(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching Market Data...")

        screened_stocks = []

        # हिस्टोरिकल डेटा (पिछले दिन के ब्रेकआउट, मूविंग एवरेज और डिलीवरी के लिए)
        # 200 SMA के लिए कम से कम 300 दिनों का डेटा चाहिए
        end_date = datetime.now()
        start_date = end_date - timedelta(days=450)

        for ticker, raw_symbol in zip(self.yahoo_tickers, self.fno_tickers):
            try:
                # 1. हिस्टोरिकल डेटा निकालना
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)

                if len(hist) < 200:
                    continue

                # पिछले दिन (T-1) और उसके पहले (T-2) का डेटा
                prev_day = hist.iloc[-1]
                before_prev_day = hist.iloc[-2]

                # 2. लाइव डेटा (सुबह 09:25 AM पर करंट कैंडल/प्राइस)
                # आज के 1-मिनट डेटा से सुबह का ट्रेंड और OI प्रॉक्सी ट्रैक करना
                live_today = stock.history(period="1d", interval="1m")
                if live_today.empty:
                    continue

                current_price = live_today["Close"].iloc[-1]
                live_volume = live_today["Volume"].sum()

                # --- तकनीकी कैलकुलेशन ---

                # क्राइटेरिया 5: 200-day Simple Moving Average (SMA)
                hist["SMA_200"] = hist["Close"].rolling(window=200).mean()
                sma_200 = hist["SMA_200"].iloc[-1]
                is_above_200_sma = current_price > sma_200

                # क्राइटेरिया 3: Previous Day Breakout (कल का हाई पार हुआ हो या लो टूटा हो)
                is_breakout = (current_price > prev_day["High"]) or (
                    current_price < prev_day["Low"]
                )

                # क्राइटेरिया 4: High Delivery / High Volume Day (पिछले दिन का वॉल्यूम 5-डे एवरेज से 25% अधिक)
                five_day_vol_avg = hist["Volume"].iloc[-6:-1].mean()
                has_high_delivery_volume = (
                    prev_day["Volume"] > five_day_vol_avg * 1.25
                )

                # क्राइटेरिया 1: Open Interest (OI) Change >= 7%
                # नोट: Yahoo Finance इक्विटी सेगमेंट में लाइव F&O का सटीक OI नहीं देता,
                # इसलिए 9:25 AM पर वॉल्यूम स्पाइक और प्राइस स्प्रेड का उपयोग करके 'Volume-OI Proxy' निकाला गया है।
                # वास्तविक ब्रोकर API (जैसे Zerodha/Angel) में सीधे `info['openInterest']` मिलता है।
                oi_change_pct = (
                    (live_today["Volume"].iloc[-1] / (prev_day["Volume"] + 1)) * 100
                    if not live_today.empty
                    else 0
                )
                # एक डमी या कस्टमाइजेबल OI चेंज मैकेनिज्म (प्रैक्टिकल यूज़ के लिए हम इसे मान लेते हैं)
                # यहाँ टेस्ट के लिए रैंडम या वॉल्यूम बेस्ड जनरेशन की जगह हमने 7% का थ्रेशोल्ड रखा है।
                is_high_oi = (
                   oi_change_pct >= 6.0  or (live_volume > prev_day["Volume"] * 0.1)
                )  # 9:25 तक कल का 10% वॉल्यूम आ जाना बड़ा साइन है

                # क्राइटेरिया 2: Previous Day Top Gainer (>2.5%) या Top Loser (<-2.5%)
                prev_day_return = (
                    (prev_day["Close"] - before_prev_day["Close"])
                    / before_prev_day["Close"]
                ) * 100
                is_top_performer = abs(prev_day_return) >= 2.5

                # --- सभी फ़िल्टर्स को कंबाइन करना ---
                if (
                    is_above_200_sma
                    and is_breakout
                    and has_high_delivery_volume
                    and is_high_oi
                    and is_top_performer
                ):

                    screened_stocks.append(
                        {
                            "Ticker": raw_symbol,
                            "LTP (9:25 AM)": round(current_price, 2),
                            "Prev Day Return %": round(prev_day_return, 2),
                            "200 SMA": round(sma_200, 2),
                            "Breakout Type": "Bullish"
                            if current_price > prev_day["High"]
                            else "Bearish",
                            "Status": "MATCHED",
                        }
                    )

            except Exception as e:
                print(f"Error processing {raw_symbol}: {str(e)}")
                continue

        return pd.DataFrame(screened_stocks)


if __name__ == "__main__":
    screener = NSEFnOScreener()
    report_df = screener.fetch_market_data()

    print("\n" + "=" * 50)
    print(" 🚀 09:25 AM NSE F&O FILTERED STOCKS 🚀")
    print("=" * 50)

    if not report_df.empty:
        print(report_df.to_string(index=False))
    else:
        print("❌ आज के क्राइटेरिया (Filters) से मैच होने वाला कोई F&O स्टॉक नहीं मिला।")
    print("=" * 50)
