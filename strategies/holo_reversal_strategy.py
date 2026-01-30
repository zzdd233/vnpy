from datetime import date, timedelta

from vnpy_ctastrategy import CtaTemplate, TickData, BarData


class HoloReversalStrategy(CtaTemplate):
    author = "VeighNa"

    parameters = [
        "fixed_size",
        "signal_window",
        "day_start_hour",
        "price_tick",
        "be1_points",
        "be5_points",
        "enable_trailing",
        "trailing_step",
    ]

    variables = [
        "pos",
        "ho",
        "lo",
        "daily_high",
        "daily_low",
        "prev_daily_high",
        "prev_daily_low",
        "entry_price",
        "sl_price",
        "short_ready",
        "long_ready",
        "last_signal_open",
        "last_day",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.fixed_size: int = 1
        self.signal_window: int = 15
        self.day_start_hour: int = 0
        self.price_tick: float = 0.01
        self.be1_points: int = 5
        self.be5_points: int = 10
        self.enable_trailing: bool = True
        self.trailing_step: int = 5

        self.ho: float | None = None
        self.lo: float | None = None
        self.daily_high: float | None = None
        self.daily_low: float | None = None
        self.prev_daily_high: float | None = None
        self.prev_daily_low: float | None = None
        self.entry_price: float | None = None
        self.sl_price: float | None = None
        self.short_ready: bool = False
        self.long_ready: bool = False
        self.last_signal_open: float | None = None
        self.last_day: date | None = None

        self._last_bid: float | None = None
        self._last_ask: float | None = None
        self._be_stage: int = 0

    def on_init(self):
        self.write_log("init")
        self.load_bar(10)

    def on_start(self):
        self.write_log("start")

    def on_stop(self):
        self.write_log("stop")

    def on_tick(self, tick: TickData):
        self._last_bid = tick.bid_price_1 or tick.last_price
        self._last_ask = tick.ask_price_1 or tick.last_price
        self._evaluate_entry_by_price()
        self._evaluate_exit_by_price()
        self.put_event()

    def on_bar(self, bar: BarData):
        self._update_session(bar)
        self._update_levels(bar)
        self._update_signal_open(bar)
        self._fallback_prices(bar)
        self._evaluate_entry_by_price()
        self._evaluate_exit_by_price()
        self.put_event()

    def on_order(self, order):
        pass

    def on_trade(self, trade):
        if self.pos != 0 and self.entry_price is None:
            self.entry_price = trade.price
            self._be_stage = 0
        self.put_event()

    def on_stop_order(self, stop_order):
        pass

    def _update_session(self, bar: BarData):
        d = self._get_trading_day(bar.datetime)
        if self.last_day != d:
            if self.daily_high is not None and self.daily_low is not None:
                self.prev_daily_high = self.daily_high
                self.prev_daily_low = self.daily_low
            self.last_day = d
            self.ho = None
            self.lo = None
            self.daily_high = bar.high_price
            self.daily_low = bar.low_price
            self.short_ready = False
            self.long_ready = False
            self.entry_price = None
            self.sl_price = None
            self._be_stage = 0

        if self.daily_high is None or bar.high_price > self.daily_high:
            self.daily_high = bar.high_price
        if self.daily_low is None or bar.low_price < self.daily_low:
            self.daily_low = bar.low_price

    def _update_levels(self, bar: BarData):
        if bar.datetime.minute == 0:
            if self.ho is None or bar.open_price > self.ho:
                self.ho = bar.open_price
            if self.lo is None or bar.open_price < self.lo:
                self.lo = bar.open_price

    def _get_trading_day(self, dt) -> date:
        d = dt.date()
        if self.day_start_hour <= 0:
            return d
        if dt.hour < self.day_start_hour:
            return d - timedelta(days=1)
        return d

    def _update_signal_open(self, bar: BarData):
        if self.signal_window <= 1:
            self.last_signal_open = bar.open_price
            return
        if bar.datetime.minute % self.signal_window == 0:
            self.last_signal_open = bar.open_price

    def _fallback_prices(self, bar: BarData):
        if self._last_bid is None:
            self._last_bid = bar.close_price
        if self._last_ask is None:
            self._last_ask = bar.close_price

    def _in_short_aoi(self, open_price: float) -> bool:
        if self.ho is None or self.daily_high is None:
            return False
        return self.ho <= open_price <= self.daily_high

    def _in_long_aoi(self, open_price: float) -> bool:
        if self.lo is None or self.daily_low is None:
            return False
        return self.daily_low <= open_price <= self.lo

    def _evaluate_entry_by_price(self):
        if self.pos != 0:
            return
        if (
            self.prev_daily_high is None
            or self.prev_daily_low is None
            or self._last_bid is None
            or self._last_ask is None
        ):
            return
        if not (self.prev_daily_low <= self._last_bid <= self.prev_daily_high):
            return
        if self.ho is not None and self._last_bid is not None:
            if self._last_bid > self.ho:
                self.short_ready = True
            if (
                self.short_ready
                and self._last_bid <= self.ho
                and self.last_signal_open is not None
                and self._in_short_aoi(self.last_signal_open)
            ):
                self._enter_short(self.ho)
                self.short_ready = False
        if self.lo is not None and self._last_ask is not None:
            if self._last_ask < self.lo:
                self.long_ready = True
            if (
                self.long_ready
                and self._last_ask >= self.lo
                and self.last_signal_open is not None
                and self._in_long_aoi(self.last_signal_open)
            ):
                self._enter_long(self.lo)
                self.long_ready = False

    def _enter_short(self, price: float):
        self.short(price, self.fixed_size)
        if self.daily_high is not None:
            self.sl_price = self.daily_high
        self.entry_price = price
        self._be_stage = 0
        self.write_log(f"short {price}")

    def _enter_long(self, price: float):
        self.buy(price, self.fixed_size)
        if self.daily_low is not None:
            self.sl_price = self.daily_low
        self.entry_price = price
        self._be_stage = 0
        self.write_log(f"buy {price}")

    def _evaluate_exit_by_price(self):
        if self.pos > 0:
            if self._last_bid is None or self.entry_price is None or self.sl_price is None:
                return
            profit_points = int(round((self._last_bid - self.entry_price) / self.price_tick))
            if profit_points >= self.be1_points and self._be_stage < 1:
                self.sl_price = self.entry_price + self.price_tick
                self._be_stage = 1
            if profit_points >= self.be5_points and self._be_stage < 2:
                self.sl_price = self.entry_price + self.price_tick * 5
                self._be_stage = 2
            if self.enable_trailing and profit_points >= self.be5_points:
                tp = self._last_bid - self.price_tick * self.trailing_step
                if tp > self.sl_price:
                    self.sl_price = tp
            if self._last_bid <= self.sl_price:
                self.sell(self.sl_price, abs(self.pos))
                self.write_log(f"sell {self.sl_price}")
                self.entry_price = None
                self._be_stage = 0
        elif self.pos < 0:
            if self._last_ask is None or self.entry_price is None or self.sl_price is None:
                return
            profit_points = int(round((self.entry_price - self._last_ask) / self.price_tick))
            if profit_points >= self.be1_points and self._be_stage < 1:
                self.sl_price = self.entry_price - self.price_tick
                self._be_stage = 1
            if profit_points >= self.be5_points and self._be_stage < 2:
                self.sl_price = self.entry_price - self.price_tick * 5
                self._be_stage = 2
            if self.enable_trailing and profit_points >= self.be5_points:
                tp = self._last_ask + self.price_tick * self.trailing_step
                if tp < self.sl_price:
                    self.sl_price = tp
            if self._last_ask >= self.sl_price:
                self.cover(self.sl_price, abs(self.pos))
                self.write_log(f"cover {self.sl_price}")
                self.entry_price = None
                self._be_stage = 0
