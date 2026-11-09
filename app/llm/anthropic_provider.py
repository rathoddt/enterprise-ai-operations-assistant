from anthropic import AsyncAnthropicFoundry
from app.llm.schemas import LLMResult


class AnthropicProvider:

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
    ):
        self.deployment = deployment

        self.client = AsyncAnthropicFoundry(
            api_key=api_key,
            base_url=endpoint,
        )

    async def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            max_output_tokens: int,
        ) -> LLMResult:
        response = await self.client.messages.create(
            model=self.deployment,
            system=system_prompt,
            max_tokens=max_output_tokens,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

        usage = response.usage

        answer = "\n".join(
            block.text
            for block in response.content
            if block.type == "text"
        )
        finish_reason = response.stop_reason
        is_truncated = finish_reason == "max_tokens"
        incomplete_reason = (
            "max_tokens"
            if response.stop_reason == "max_tokens"
            else None
        )

        return LLMResult(
            answer=answer,
            provider="anthropic",
            model=self.deployment,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            # request_id=(
            #     getattr(response, "_request_id", None)
            #     or response.id
            # ),
            request_id=getattr(response, "_request_id", None),
            response_id=response.id,
            status="success",
            finish_reason=finish_reason,
            is_truncated=is_truncated,
            incomplete_reason=incomplete_reason,
        )

# --------------------- v1 -------------------
# from anthropic import AsyncAnthropicFoundry

# class AnthropicProvider:
#     def __init__(
#         self,
#         endpoint: str,
#         api_key: str,
#         deployment: str,
#     ):
#         self.deployment = deployment

#         self.client = AsyncAnthropicFoundry(
#             api_key=api_key,
#             base_url=endpoint,
#         )

#     async def generate(self, prompt: str) -> str:
#         response = await self.client.messages.create(
#             model=self.deployment,
#             max_tokens=1000,
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#         )

#         return "\n".join(
#             block.text
#             for block in response.content
#             if block.type == "text"
#         )
#  --------------------- v0 -------------------
# from anthropic import AsyncAnthropic, APIError
# from app.core.exceptions import LLMProviderError


# class AnthropicProvider:

#     def __init__(self, api_key: str, model: str):
#         self.client = AsyncAnthropic(api_key=api_key)
#         self.model = model

#     async def generate(self, prompt: str) -> str:
#         try:
#             response = await self.client.messages.create(
#                 model=self.model,
#                 max_tokens=2048,
#                 system=(
#                     "You are an Enterprise AI Operations Assistant. "
#                     "Provide accurate, concise and professional answers."
#                 ),
#                 messages=[
#                     {"role": "user", "content": prompt}
#                 ],
#             )

#             return "".join(
#                 block.text
#                 for block in response.content
#                 if block.type == "text"
#             )

#         except APIError as exc:
#             raise LLMProviderError(
#                 message="Anthropic request failed.",
#                 code="ANTHROPIC_ERROR",
#             ) from exc