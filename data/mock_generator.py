from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator
import math


@dataclass
class MockMarketData:
    date: date
    premium_paranagua: float
    chicago_front: float
    usd_brl: float
    fob_paranagua: float
    fob_us_gulf: float
    lineup_bruto: int
    lineup_liquido: int
    cancelamentos_7d: int
    exports_weekly_tons: float


class MarketDataGenerator:

    BASE_PREMIUM = 80.0
    BASE_CHICAGO = 1200.0
    BASE_USD_BRL = 5.20
    BASE_FOB_PARANAGUA = 480.0
    BASE_FOB_US_GULF = 450.0
    BASE_LINEUP = 80
    BASE_EXPORTS = 2_500_000

    def __init__(self, seed: int | None = 42):
        self._rng = random.Random(seed)
        self._state: dict[str, float] = {}

    def _seasonal_factor(self, dt: date) -> float:
        month = dt.month
        if month in (3, 4, 5, 6, 7):
            return 1.0 + 0.15 * math.sin((month - 3) * math.pi / 4)
        else:
            return 0.85 + 0.1 * math.sin((month - 8) * math.pi / 6)

    def _trend_factor(self, day_index: int, total_days: int) -> float:
        cycle = 2 * math.pi * day_index / (365 * 2)
        return 1.0 + 0.1 * math.sin(cycle)

    def _random_walk(self, key: str, volatility: float = 0.02) -> float:
        current = self._state.get(key, 0.0)
        shock = self._rng.gauss(0, volatility)
        mean_reversion = -0.1 * current
        new_value = current + shock + mean_reversion
        self._state[key] = new_value
        return new_value

    def _generate_event(self, prob: float = 0.02) -> float:
        if self._rng.random() < prob:
            direction = self._rng.choice([-1, 1])
            magnitude = self._rng.uniform(0.1, 0.25)
            return direction * magnitude
        return 0.0

    def generate_day(self, dt: date, day_index: int, total_days: int) -> MockMarketData:
        seasonal = self._seasonal_factor(dt)
        trend = self._trend_factor(day_index, total_days)

        premium_walk = self._random_walk("premium", 0.03)
        premium_event = self._generate_event(0.03)
        premium = self.BASE_PREMIUM * seasonal * trend * (1 + premium_walk + premium_event)
        premium = max(20, min(200, premium))

        chicago_walk = self._random_walk("chicago", 0.015)
        chicago_correlation = premium_walk * 0.3
        chicago = self.BASE_CHICAGO * trend * (1 + chicago_walk + chicago_correlation)
        chicago = max(900, min(1600, chicago))

        usd_walk = self._random_walk("usd_brl", 0.008)
        usd_event = self._generate_event(0.02)
        usd_brl = self.BASE_USD_BRL * (1 + usd_walk + usd_event)
        usd_brl = max(4.5, min(6.5, usd_brl))

        fob_pnq = (chicago / 100 * 36.74 + premium / 100 * 36.74)
        fob_pnq = fob_pnq * (1 + self._random_walk("fob_pnq", 0.01))
        fob_pnq = max(350, min(650, fob_pnq))

        spread_base = -15 if dt.month in (3, 4, 5, 6, 7) else 10
        fob_gulf = fob_pnq + spread_base + self._rng.gauss(0, 5)
        fob_gulf = max(350, min(650, fob_gulf))

        lineup_walk = self._random_walk("lineup", 0.05)
        lineup_seasonal = seasonal * 1.2 if dt.month in (3, 4, 5, 6) else 0.7
        lineup_bruto = int(self.BASE_LINEUP * lineup_seasonal * (1 + lineup_walk))
        lineup_bruto = max(30, min(150, lineup_bruto))

        cancel_rate = 0.05 + self._rng.uniform(0, 0.1)
        cancelamentos = int(lineup_bruto * cancel_rate * self._rng.uniform(0.5, 1.5))
        cancelamentos = max(0, min(20, cancelamentos))
        lineup_liquido = max(20, lineup_bruto - cancelamentos - self._rng.randint(0, 5))

        exports_walk = self._random_walk("exports", 0.08)
        exports = self.BASE_EXPORTS * seasonal * (1 + exports_walk)
        exports = max(500_000, min(5_000_000, exports))

        return MockMarketData(
            date=dt,
            premium_paranagua=round(premium, 2),
            chicago_front=round(chicago, 2),
            usd_brl=round(usd_brl, 4),
            fob_paranagua=round(fob_pnq, 2),
            fob_us_gulf=round(fob_gulf, 2),
            lineup_bruto=lineup_bruto,
            lineup_liquido=lineup_liquido,
            cancelamentos_7d=cancelamentos,
            exports_weekly_tons=round(exports, 2),
        )

    def generate_series(
        self,
        start_date: date,
        end_date: date,
    ) -> list[MockMarketData]:
        self._state.clear()
        total_days = (end_date - start_date).days + 1
        series = []

        current = start_date
        day_index = 0
        while current <= end_date:
            if current.weekday() < 5:
                data = self.generate_day(current, day_index, total_days)
                series.append(data)
            current += timedelta(days=1)
            day_index += 1

        return series


def generate_scenario_normal(days: int = 30, seed: int = 42) -> list[MockMarketData]:
    gen = MarketDataGenerator(seed)
    end_date = date(2024, 6, 15)
    start_date = end_date - timedelta(days=days)
    return gen.generate_series(start_date, end_date)


def generate_scenario_crisis(days: int = 30, seed: int = 123) -> list[MockMarketData]:
    gen = MarketDataGenerator(seed)
    gen._state["lineup"] = -0.3
    gen._state["premium"] = -0.2
    end_date = date(2024, 4, 20)
    start_date = end_date - timedelta(days=days)
    return gen.generate_series(start_date, end_date)


def generate_scenario_opportunity(days: int = 30, seed: int = 456) -> list[MockMarketData]:
    gen = MarketDataGenerator(seed)
    gen._state["lineup"] = 0.25
    gen._state["premium"] = 0.3
    end_date = date(2024, 5, 10)
    start_date = end_date - timedelta(days=days)
    return gen.generate_series(start_date, end_date)


def generate_scenario_logistics_crisis(days: int = 30, seed: int = 789) -> list[MockMarketData]:
    gen = MarketDataGenerator(seed)
    gen._state["lineup"] = 0.4
    gen._state["exports"] = -0.4
    end_date = date(2024, 3, 25)
    start_date = end_date - timedelta(days=days)
    return gen.generate_series(start_date, end_date)


def generate_3y_history(seed: int = 42) -> list[MockMarketData]:
    gen = MarketDataGenerator(seed)
    end_date = date(2024, 12, 31)
    start_date = date(2022, 1, 1)
    return gen.generate_series(start_date, end_date)


if __name__ == "__main__":
    print("Gerando cenario normal (30 dias)...")
    normal = generate_scenario_normal()
    print(f"  {len(normal)} dias gerados")
    print(f"  Premium range: {min(d.premium_paranagua for d in normal):.0f} - {max(d.premium_paranagua for d in normal):.0f}")
    print(f"  Lineup range: {min(d.lineup_bruto for d in normal)} - {max(d.lineup_bruto for d in normal)}")

    print("\nGerando historico 3 anos...")
    history = generate_3y_history()
    print(f"  {len(history)} dias gerados")
    print(f"  Periodo: {history[0].date} a {history[-1].date}")
