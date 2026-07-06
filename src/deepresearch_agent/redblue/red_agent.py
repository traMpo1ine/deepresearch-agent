from __future__ import annotations

from deepresearch_agent.agents.critic import CriticAgent


class RedAgent(CriticAgent):
    """Alias for the adversarial reviewer used in docs and experiments."""

    name = "red_agent"
