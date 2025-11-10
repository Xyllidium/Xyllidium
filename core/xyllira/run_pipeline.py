"""
End-to-end demo:
Xyllira code -> Interpreter -> Translator -> JSON graph for Xyllencore
"""

import json
from interpreter import XylliraParser
from translator import Translator

XYLLIRA_CODE = """
intent transfer {
    from: wallet.me
    to: wallet.bob
    amount: 500 xyls
    condition: coherence(wallet.me) > 0.7
}

intent upgrade_protocol {
    when: coherence(governance.field) >= 0.85
    action: evolve(core.module)
}

intent ai_investment {
    delegate: xyllenai
    amount: 2000 xyls
    strategy: maximize(coherence(projects))
}

intent convert {
    from: xyls
    to: eth
    amount: 100
}
"""

if __name__ == "__main__":
    parser = XylliraParser()
    intents = parser.parse(XYLLIRA_CODE)

    graph = Translator().translate(intents)
    print("🧠 Intent Graph JSON:")
    print(graph.to_json())
