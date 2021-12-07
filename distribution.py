import abc
import random

class Distribution(abc.ABC):

    @abc.abstractmethod
    def sample(self):
        pass

class Uniform(Distribution):

    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def sample(self):
        return random.uniform(self.low, self.high)

class Gaussian(Distribution):

    def __init__(self, mean: float, std: float):
        self.mean = mean
        self.std = std

    def sample(self):
        return random.gauss(self.mean, self.std)

class TruncatedGaussian(Gaussian):

    def __init__(self, mean: float, std: float, low: float = None, high: float = None):
        super().__init__(mean, std)
        self.low = low
        self.high = high

    def accept(self, sample):
        if self.low is not None and sample < self.low:
            return False
        if self.high is not None and sample > self.high:
            return False
        return True

    def sample(self):
        r = super().sample()
        while not self.accept(r):
            r = super().sample()
        return r