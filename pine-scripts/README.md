# TradingView Pine Script - Trading Signals

This Pine Script exactly replicates the signal logic implemented in the Python chart analysis application.

## 📋 Features

- **Exact signal logic** matching Python `indicators/signals.py`
- **Same indicator calculations** as Python `indicators/calculator.py`
- **Custom Gann HiLo implementation** matching Python `indicators/gann_hilo.py`
- **Position tracking** to ensure balanced OPEN/CLOSE signals
- **Visual markers** with same colors as the Python charts
- **Automated alerts** for all signal types

## 🔧 Indicator Settings

All settings match `config/settings.py`:

| Indicator | Settings |
|-----------|----------|
| **MACD** | Fast: 12, Slow: 26, Signal: 9 |
| **RSI** | Period: 14, MA: 14 |
| **Supertrend** | Period: 10, Multiplier: 3.0 |
| **Ichimoku** | Conversion: 9, Base: 26, Span B: 52, Displacement: 26 |
| **Gann HiLo** | Fast (High): 13, Slow (Low): 21 |
| **EMAs** | 8, 21, 50 |

## 🎯 Signal Logic

### 🟢 Long OPEN (All 5 conditions must be TRUE)
1. MACD > MACD Signal
2. Close > Gann HiLo
3. RSI > RSI MA
4. Close > Supertrend
5. Close > Previous High

### 🔴 Long CLOSE (Any 1 of 3 triggers exit)
1. Close < Gann HiLo
2. MACD < MACD Signal
3. Price in Ichimoku Cloud

### 🟠 Short OPEN (All 6 conditions must be TRUE)
1. MACD < MACD Signal
2. MACD < Previous MACD
3. Close < Gann HiLo
4. RSI < RSI MA
5. Close < Supertrend
6. Close < Previous Low

### 🔵 Short CLOSE (Any 1 of 3 triggers exit)
1. Close > Gann HiLo
2. MACD > MACD Signal
3. Price in Ichimoku Cloud

## 📊 Position Tracking

The script implements state-based position tracking (matching Python `_apply_position_tracking`):

- Can only CLOSE a position that was OPENED
- Can't open LONG while LONG is already open
- Can't open SHORT while SHORT is already open
- Opening LONG automatically closes SHORT (if open)
- Opening SHORT automatically closes LONG (if open)

## 🎨 Visual Elements

### Chart Indicators
- **Gann HiLo** - Green (uptrend) / Red (downtrend)
- **Supertrend** - Green (bullish) / Red (bearish)
- **EMAs** - 8 (yellow), 21 (orange), 50 (blue)
- **Ichimoku Cloud** - Green/Red cloud

### Signal Markers
- 🟢 **Long OPEN** - Bright lime triangle up below bar (#00FF00)
- 🔴 **Long CLOSE** - Bright magenta triangle down above bar (#FF00FF)
- 🟠 **Short OPEN** - Bright orange triangle down above bar (#FFA500)
- 🔵 **Short CLOSE** - Bright cyan triangle up below bar (#00FFFF)

Colors exactly match `charts/plotly_renderer.py`

## 🔔 Setting Up Alerts

1. Open TradingView and add the script to your chart
2. Click "Create Alert" button
3. Select condition from dropdown:
   - `Long OPEN` - For long entry alerts
   - `Long CLOSE` - For long exit alerts
   - `Short OPEN` - For short entry alerts
   - `Short CLOSE` - For short exit alerts
4. Configure alert delivery (email, SMS, webhook, etc.)

## 📥 Installation

### Method 1: TradingView Web
1. Open [TradingView](https://www.tradingview.com/)
2. Open Pine Editor (bottom panel)
3. Click "New" and select "Blank indicator script"
4. Delete all default code
5. Copy entire contents of `trading-signals.pine`
6. Paste into Pine Editor
7. Click "Save" and give it a name
8. Click "Add to Chart"

### Method 2: Direct Import
1. Copy the script code
2. In TradingView, go to Chart → Pine Editor
3. Paste the code
4. Click "Add to Chart"

## ✅ Verification

To verify the signals match your Python app:

1. Open the same ticker in both apps
2. Set the same date range
3. Compare signal markers on specific dates
4. Signals should match exactly (same dates, same types)

## 🎯 Strategy vs Indicator

The script is set as a **strategy** which:
- Shows backtest results
- Displays position changes
- Calculates profit/loss
- Shows performance metrics

To use as an **indicator only** (no backtest):
- Change line 2 from `strategy(...)` to `indicator(...)`
- Remove or comment out the `strategy.entry()` and `strategy.close()` lines

## 📝 Notes

- The script replicates the **exact** logic from your Python implementation
- All indicator calculations use TradingView's built-in functions with matching parameters
- Gann HiLo uses custom logic to match Python implementation
- Position tracking ensures signals are balanced (no orphaned closes)
- Alert conditions are built-in and ready to use

## 🐛 Troubleshooting

**Signals don't match Python app?**
- Verify you're looking at the same date range
- Check that data providers match (some differences in historical data)
- Ensure indicator settings haven't been modified

**No signals appearing?**
- Check that all required indicators have enough data (need at least 52 bars for Ichimoku)
- Verify the ticker has sufficient trading history
- Conditions are strict - signals are rare by design

**Want to see more signals?**
- This is a conservative strategy by design
- Modify the conditions in the script to be less strict
- Consider testing on multiple timeframes

## 📚 Related Files

- Python implementation: `indicators/signals.py`
- Indicator calculations: `indicators/calculator.py`
- Gann HiLo logic: `indicators/gann_hilo.py`
- Chart rendering: `charts/plotly_renderer.py`
- Configuration: `config/settings.py`
