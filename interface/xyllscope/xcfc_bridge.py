# xyllscope/xcfc_bridge.py
import numpy as np, math
import xcfc  # Rust module built with maturin

class XCFCField:
    def __init__(self, size=8):
        self.size = size
        self.t = 0
        # initialize with harmonic center pattern
        x, y, z = np.indices((size, size, size))
        c = (size - 1) / 2
        r = np.sqrt((x - c) ** 2 + (y - c) ** 2 + (z - c) ** 2)
        self.energies = np.exp(-r ** 2 / (2 * (size / 4) ** 2))
        self.alpha = 0.1

    def step_dynamic(self):
        """Use Rust coherence_step to evolve the field."""
        flat = self.energies.flatten().tolist()
        new_flat = xcfc.coherence_step(flat, self.alpha)
        self.energies = np.array(new_flat).reshape(self.size, self.size, self.size)
        self.t += 1

    def entropy(self):
        flat = self.energies.flatten().tolist()
        return float(xcfc.compute_entropy(flat))

    def coherence(self):
        # Compute coherence index from Rust as well if available
        if hasattr(xcfc, "coherence_index"):
            flat = self.energies.flatten().tolist()
            return float(xcfc.coherence_index(flat))
        # fallback
        return 1 - np.var(self.energies)

    def apply_intent(self, intent):
        e_delta = float(intent.get("energy", 0.0))
        awareness = float(intent.get("awareness", 1.0))
        target = str(intent.get("target", "global"))
        factor = e_delta * awareness * 0.1
        if target == "core":
            c = self.size // 2
            self.energies[c-1:c+2, c-1:c+2, c-1:c+2] += factor
        else:
            self.energies += factor
        self.energies = np.clip(self.energies, 0, 1)
