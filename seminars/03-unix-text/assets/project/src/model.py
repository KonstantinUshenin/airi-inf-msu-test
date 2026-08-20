"""Заглушка модели."""


class Model:
    def __init__(self, hidden_size=128):
        self.hidden_size = hidden_size

    def forward(self, batch):
        # TODO: заменить заглушку настоящим слоем
        return batch
