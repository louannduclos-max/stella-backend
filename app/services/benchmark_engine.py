"""
BenchmarkEngine — enrichit les métriques avec les benchmarks nationaux.
100% déterministe, pas de réseau. Opère sur les métriques après collecte.
"""
from app.core.national_benchmarks import get_national_benchmark


def _interpret(value: float, benchmark: float, unit: str | None) -> str:
    """Génère une phrase d'interprétation relative au benchmark national."""
    if benchmark == 0:
        return ""
    ratio = value / benchmark
    u = f" {unit}" if unit else ""
    bk = f"{benchmark:g}{u}"
    if ratio >= 1.8:
        return f"Près du double de la moyenne nationale ({bk})"
    if ratio >= 1.25:
        return f"{ratio:.1f}× la moyenne nationale ({bk})"
    if ratio >= 1.05:
        return f"Au-dessus de la moyenne nationale ({bk})"
    if ratio >= 0.95:
        return f"Proche de la moyenne nationale ({bk})"
    if ratio >= 0.75:
        return f"En dessous de la moyenne nationale ({bk})"
    return f"Nettement sous la moyenne nationale ({bk})"


class BenchmarkEngine:

    def enrich_metrics(self, metrics: list, country: str = "FR") -> list:
        """
        Ajoute national_benchmark, benchmark_source_id, benchmark_year et
        benchmark_interpretation à chaque métrique qui a un benchmark.
        Les métriques sans benchmark sont retournées inchangées.
        """
        for m in metrics:
            bench = get_national_benchmark(m.metric_id, country)
            if not bench:
                continue
            try:
                v = float(m.value)
                b = float(bench["value"])
            except (TypeError, ValueError):
                continue
            m.national_benchmark = bench["value"]
            m.benchmark_source_id = bench["source"]
            m.benchmark_year = bench["year"]
            m.benchmark_interpretation = _interpret(v, b, bench.get("unit"))
        return metrics


benchmark_engine = BenchmarkEngine()
