"""Pattern: Visitor.
separa operatiile de obiectele pe care le prelucreaza, permitand adaugarea de operatii noi fara modificarea claselor element.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class Shape(ABC):
    @abstractmethod
    def accept(self, visitor: "ShapeVisitor") -> float:
        raise NotImplementedError


@dataclass
class Circle(Shape):
    radius: float

    def accept(self, visitor: "ShapeVisitor") -> float:
        return visitor.visit_circle(self)


@dataclass
class Rectangle(Shape):
    width: float
    height: float

    def accept(self, visitor: "ShapeVisitor") -> float:
        return visitor.visit_rectangle(self)


class ShapeVisitor(ABC):
    @abstractmethod
    def visit_circle(self, circle: Circle) -> float:
        raise NotImplementedError

    @abstractmethod
    def visit_rectangle(self, rectangle: Rectangle) -> float:
        raise NotImplementedError


class AreaVisitor(ShapeVisitor):
    def visit_circle(self, circle: Circle) -> float:
        pi = 3.14159
        return pi * circle.radius * circle.radius

    def visit_rectangle(self, rectangle: Rectangle) -> float:
        return rectangle.width * rectangle.height


def demo() -> None:
    shapes: list[Shape] = [Circle(2), Rectangle(3, 4)]
    visitor = AreaVisitor()

    for shape in shapes:
        print(f"Arie: {shape.accept(visitor):.2f}")


if __name__ == "__main__":
    demo()
