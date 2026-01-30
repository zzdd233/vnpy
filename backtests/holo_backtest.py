from datetime import datetime, timedelta
from math import sin

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database
from vnpy.trader.utility import ZoneInfo
from vnpy.trader.setting import SETTINGS
from vnpy_ctastrategy.backtesting import BacktestingEngine

from strategies.holo_reversal_strategy import HoloReversalStrategy


def main() -> None:
    symbol = "TEST"
    exchange = Exchange.LOCAL
    interval = Interval.MINUTE
    vt_symbol = f"{symbol}.{exchange.value}"

    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 3)

    price = 100.0
    bars: list[BarData] = []

    step = timedelta(minutes=1)
    current = start

    while current < end:
        base = price + sin((current - start).total_seconds() / 3600) * 0.8
        open_price = base
        high_price = base + 0.4
        low_price = base - 0.4
        close_price = base + sin((current - start).total_seconds() / 1800) * 0.2
        bar = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=current,
            interval=interval,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=100,
            gateway_name="BACKTESTING",
        )
        bars.append(bar)
        current += step
        price = close_price

    if bars:
        tz = ZoneInfo(SETTINGS["database.timezone"])
        for bar in bars:
            if bar.datetime.tzinfo is None:
                bar.datetime = bar.datetime.replace(tzinfo=tz)

        db = get_database()
        db.delete_bar_data(symbol, exchange, interval)
        db.save_bar_data(bars)

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=0.0,
        slippage=0.0,
        size=1,
        pricetick=0.01,
        capital=1_000_000,
    )

    setting = {
        "fixed_size": 1,
        "signal_window": 1,
        "day_start_hour": 0,
        "price_tick": 0.01,
        "be1_points": 5,
        "be5_points": 10,
        "enable_trailing": True,
        "trailing_step": 5,
    }

    engine.add_strategy(HoloReversalStrategy, setting)
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    stats = engine.calculate_statistics(output=False)

    print("回测统计：")
    for k, v in stats.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
