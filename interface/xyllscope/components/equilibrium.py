import numpy as np

class EquilibriumEngine:
    """Self-balancing engine controlling field parameters."""

    def __init__(self):
        self.target = 0.75
        self.adapt_rate = 0.02
        self.diffusion_strength = 0.4
        self.pulse_strength = 0.5

    def regulate(self, coherence):
        delta = coherence - self.target
        self.diffusion_strength = np.clip(self.diffusion_strength - delta*self.adapt_rate, 0.2, 0.8)
        self.pulse_strength = np.clip(self.pulse_strength + delta*self.adapt_rate, 0.2, 1.0)
        return self.diffusion_strength, self.pulse_strength
