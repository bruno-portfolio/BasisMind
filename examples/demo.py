#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "data"))

from mock_generator import (
    generate_scenario_normal,
    generate_scenario_crisis,
    generate_scenario_opportunity,
    MockMarketData,
)
from engine import DecisionEngine, MarketInputs, DecisionReport
from book import BookState
from premium import get_regime


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_report_summary(report: DecisionReport) -> None:
    print(f"\n  Data: {report.data_referencia}")
    print(f"  Score Fisico: {report.score_fisico:.1f} ({report.classificacao})")
    print(f"\n  Componentes:")
    for name, comp in report.componentes.items():
        print(f"    {name:15} score={comp['score']:5.1f}")
    print(f"\n  Recomendacao Fisica: {report.recomendacao_fisica['acao']}")
    print(f"    Intensidade: {report.recomendacao_fisica['intensidade']}")
    print(f"    Sizing: {report.recomendacao_fisica['sizing_pct']:+.1f}%")
    print(f"\n  Recomendacao Hedge: {report.recomendacao_hedge['acao']}")
    print(f"    Delta: {report.recomendacao_hedge['delta_pp']:+.1f}pp")
    if report.overrides_ativos:
        print(f"\n  OVERRIDES ATIVOS: {', '.join(report.overrides_ativos)}")
        print(f"    Dominante: {report.override_dominante}")
    if report.modulacao_aplicada:
        print(f"\n  MODULACAO: {report.modulacao_razao}")
    print(f"\n  Justificativa: {report.justificativa[:100]}...")


def calculate_metrics_from_mock(
    data: list[MockMarketData],
    index: int,
) -> dict:
    current = data[index]

    if index >= 5:
        prev_lineup = data[index - 5].lineup_liquido
        var_semanal = ((current.lineup_liquido - prev_lineup) / prev_lineup) * 100
    else:
        var_semanal = 0.0

    premium_min, premium_max = 40, 160
    percentil = ((current.premium_paranagua - premium_min) / (premium_max - premium_min)) * 100
    percentil = max(0, min(100, percentil))

    spread = current.fob_paranagua - current.fob_us_gulf

    z_pace = (current.exports_weekly_tons - 2_500_000) / 500_000

    if index >= 5:
        prev_usd = data[index - 5].usd_brl
        var_cambio = ((current.usd_brl - prev_usd) / prev_usd) * 100
    else:
        var_cambio = 0.0

    chicago_min, chicago_max = 950, 1450
    chicago_pct = ((current.chicago_front - chicago_min) / (chicago_max - chicago_min)) * 100
    chicago_pct = max(0, min(100, chicago_pct))

    if index >= 5:
        prev_chicago = data[index - 5].chicago_front
        var_chicago = ((current.chicago_front - prev_chicago) / prev_chicago) * 100
        chicago_spike = var_chicago > 5
    else:
        chicago_spike = False

    return {
        "var_semanal_lineup": var_semanal,
        "percentil_premium": percentil,
        "spread_adjusted": spread,
        "z_pace": z_pace,
        "var_cambio_5d": var_cambio,
        "chicago_percentile": chicago_pct,
        "chicago_is_spike": chicago_spike,
    }


def demo_cenario_normal() -> None:
    print_header("CENARIO 1: Mercado Normal")
    print("\n  Condicoes: Safra em andamento, lineup estavel, premio moderado")

    data = generate_scenario_normal(days=30)
    current = data[-1]
    metrics = calculate_metrics_from_mock(data, len(data) - 1)

    inputs = MarketInputs(
        dt=current.date,
        var_semanal_lineup=metrics["var_semanal_lineup"],
        percentil_premium=metrics["percentil_premium"],
        spread_adjusted=metrics["spread_adjusted"],
        z_pace=metrics["z_pace"],
        var_cambio_5d=metrics["var_cambio_5d"],
        chicago_percentile=metrics["chicago_percentile"],
        chicago_is_spike=metrics["chicago_is_spike"],
        logistics_flag_active=False,
        logistics_reason=None,
    )

    engine = DecisionEngine()
    report = engine.run(inputs)
    print_report_summary(report)


def demo_override_queda_conjunta() -> None:
    print_header("CENARIO 2: Override - Queda Conjunta")
    print("\n  Condicoes: Lineup despencando E premio caindo")
    print("  Esperado: Override QUEDA_CONJUNTA -> Reduzir exposicao")

    inputs = MarketInputs(
        dt=date(2024, 4, 20),
        var_semanal_lineup=-15.0,
        percentil_premium=25.0,
        spread_adjusted=5.0,
        z_pace=-0.5,
        var_cambio_5d=1.0,
        chicago_percentile=45.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )

    engine = DecisionEngine()
    report = engine.run(inputs)
    print_report_summary(report)


def demo_override_armadilha() -> None:
    print_header("CENARIO 3: Override - Armadilha de Premio")
    print("\n  Condicoes: Premio alto MAS lineup caindo")
    print("  Esperado: Override ARMADILHA_PREMIO -> Vender antes da correcao")

    inputs = MarketInputs(
        dt=date(2024, 5, 10),
        var_semanal_lineup=-12.0,
        percentil_premium=85.0,
        spread_adjusted=-5.0,
        z_pace=0.3,
        var_cambio_5d=-0.5,
        chicago_percentile=60.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )

    engine = DecisionEngine()
    report = engine.run(inputs)
    print_report_summary(report)


def demo_override_logistica() -> None:
    print_header("CENARIO 4: Override - Crise Logistica")
    print("\n  Condicoes: Greve de caminhoneiros, portos congestionados")
    print("  Esperado: Override LOGISTICA -> Maior prioridade, vender urgente")

    inputs = MarketInputs(
        dt=date(2024, 3, 25),
        var_semanal_lineup=5.0,
        percentil_premium=70.0,
        spread_adjusted=-8.0,
        z_pace=0.8,
        var_cambio_5d=0.2,
        chicago_percentile=55.0,
        chicago_is_spike=False,
        logistics_flag_active=True,
        logistics_reason="Greve de caminhoneiros - portos com fila > 20 dias",
    )

    engine = DecisionEngine()
    report = engine.run(inputs)
    print_report_summary(report)


def demo_limite_book() -> None:
    print_header("CENARIO 5: Modulacao por Limite de Book")
    print("\n  Condicoes: Mercado forte, mas ja estamos no limite comprado")
    print("  Esperado: Recomendacao AUMENTAR -> modulada para MANTER")

    inputs = MarketInputs(
        dt=date(2024, 6, 5),
        var_semanal_lineup=12.0,
        percentil_premium=78.0,
        spread_adjusted=-15.0,
        z_pace=1.2,
        var_cambio_5d=-1.5,
        chicago_percentile=70.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )

    book = BookState(
        exposicao_fisica_pct=80.0,
        limite_long_pct=80.0,
        limite_short_pct=-50.0,
        hedge_atual_pct=60.0,
        hedge_meta_pct=60.0,
    )

    engine = DecisionEngine(book)
    report = engine.run(inputs)
    print_report_summary(report)


def demo_chicago_spike() -> None:
    print_header("CENARIO 6: Override - Chicago Especulativo")
    print("\n  Condicoes: Chicago subiu 8% em 5 dias sem fundamento")
    print("  Esperado: Override CHICAGO_ESPECULATIVO -> Hedge, nao comprar")

    inputs = MarketInputs(
        dt=date(2024, 7, 15),
        var_semanal_lineup=3.0,
        percentil_premium=55.0,
        spread_adjusted=2.0,
        z_pace=0.1,
        var_cambio_5d=0.3,
        chicago_percentile=75.0,
        chicago_is_spike=True,
        logistics_flag_active=False,
        logistics_reason=None,
        narrativa_confirmada=False,
    )

    engine = DecisionEngine()
    report = engine.run(inputs)
    print_report_summary(report)


def demo_json_output() -> None:
    print_header("CENARIO 7: Output JSON Completo")

    inputs = MarketInputs(
        dt=date(2024, 5, 20),
        var_semanal_lineup=8.0,
        percentil_premium=72.0,
        spread_adjusted=5.0,
        z_pace=0.5,
        var_cambio_5d=-0.8,
        chicago_percentile=65.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )

    engine = DecisionEngine()
    report = engine.run(inputs)

    print("\n  JSON Output:")
    print("-" * 60)
    print(report.to_json(indent=2))


def main() -> None:
    print("\n" + "=" * 70)
    print("       MOTOR DE DECISAO - MERCADO FISICO DE GRAOS")
    print("                  Demonstracao de Cenarios")
    print("=" * 70)

    demo_cenario_normal()
    demo_override_queda_conjunta()
    demo_override_armadilha()
    demo_override_logistica()
    demo_limite_book()
    demo_chicago_spike()
    demo_json_output()

    print("\n" + "=" * 70)
    print("  Demonstracao concluida!")
    print("  Todos os cenarios executados com sucesso.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
