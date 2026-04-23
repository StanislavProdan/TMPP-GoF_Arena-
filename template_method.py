"""Pattern: Template Method.
defineste scheletul unui algoritm in clasa de baza, iar pasii variabili sunt implementati in subclase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DataProcessor(ABC):
    def process(self) -> str:
        raw = self.load_data()
        parsed = self.parse_data(raw)
        result = self.analyze_data(parsed)
        return self.export_result(result)

    def load_data(self) -> str:
        return "10,20,30,40"

    @abstractmethod
    def parse_data(self, raw: str) -> list[int]:
        raise NotImplementedError

    def analyze_data(self, values: list[int]) -> int:
        return sum(values)

    def export_result(self, result: int) -> str:
        return f"Rezultat procesat: {result}"


class CsvDataProcessor(DataProcessor):
    def parse_data(self, raw: str) -> list[int]:
        return [int(x) for x in raw.split(",")]


def demo() -> None:
    processor = CsvDataProcessor()
    print(processor.process())


if __name__ == "__main__":
    demo()
