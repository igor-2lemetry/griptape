from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import Factory, define, field

from griptape.tokenizers import BaseTokenizer
from griptape.utils import import_optional_dependency

if TYPE_CHECKING:
    from anthropic import Anthropic
    from anthropic.types.beta import BetaMessageParam


@define()
class AnthropicTokenizer(BaseTokenizer):
    DEFAULT_MODEL = "claude-2.1"
    MODEL_PREFIXES_TO_MAX_TOKENS = {"claude-2.1": 200000, "claude": 100000}

    model: str = field(kw_only=True)
    max_tokens: int = field(kw_only=True, default=Factory(lambda self: self.default_max_tokens(), takes_self=True))
    client: Anthropic = field(
        default=Factory(lambda: import_optional_dependency("anthropic").Anthropic()),
        kw_only=True,
    )

    def default_max_tokens(self) -> int:
        tokens = next(v for k, v in self.MODEL_PREFIXES_TO_MAX_TOKENS.items() if self.model.startswith(k))

        return tokens

    def count_tokens(self, text: str | list[BetaMessageParam]) -> int:
        types = import_optional_dependency("anthropic.types.beta")

        # TODO: Refactor all Tokenizers to support Prompt Stack as an input.
        messages = [types.BetaMessageParam(role="user", content=text)] if isinstance(text, str) else text

        usage = self.client.beta.messages.count_tokens(
            model=self.model,
            messages=messages,
        )

        return usage.input_tokens
