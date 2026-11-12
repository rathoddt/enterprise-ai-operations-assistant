from anthropic import AsyncAnthropicFoundry
from app.llm.schemas import LLMResult
from app.core.config import settings

class AnthropicProvider:

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
    ):
        self.deployment = deployment

        # self.client = AsyncAnthropicFoundry(
        #     api_key=api_key,
        #     base_url=endpoint,
        # )
        self.client = AsyncAnthropicFoundry(
            api_key=api_key,
            base_url=endpoint,
            timeout=settings.llm_request_timeout_seconds,
            max_retries=0,
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

