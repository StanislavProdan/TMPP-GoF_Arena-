"""Pattern: Mediator.
centralizeaza comunicarea dintre obiecte, astfel incat ele nu se mai cunosc direct intre ele.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ChatMediator(ABC):
    @abstractmethod
    def send(self, message: str, sender: "User") -> None:
        raise NotImplementedError


class ChatRoom(ChatMediator):
    def __init__(self) -> None:
        self._users: list[User] = []

    def add_user(self, user: "User") -> None:
        self._users.append(user)

    def send(self, message: str, sender: "User") -> None:
        for user in self._users:
            if user is not sender:
                user.receive(f"{sender.name}: {message}")


@dataclass
class User:
    name: str
    mediator: ChatMediator

    def send(self, message: str) -> None:
        self.mediator.send(message, self)

    def receive(self, message: str) -> None:
        print(f"[{self.name} a primit] {message}")


def demo() -> None:
    room = ChatRoom()

    ana = User("Ana", room)
    bogdan = User("Bogdan", room)
    carmen = User("Carmen", room)

    room.add_user(ana)
    room.add_user(bogdan)
    room.add_user(carmen)

    ana.send("Salut tuturor!")
    bogdan.send("Salut, Ana!")


if __name__ == "__main__":
    demo()
