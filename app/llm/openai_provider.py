from openai import AsyncOpenAI
from app.llm.schemas import LLMResult

class OpenAIProvider:

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
    ):
        self.deployment = deployment

        self.client = AsyncOpenAI(
            base_url=endpoint,
            api_key=api_key,
        )

    async def generate(self, prompt: str) -> LLMResult:

        response = await self.client.responses.create(
            model=self.deployment,
            input=prompt,
        )

        usage = response.usage

        return LLMResult(
            answer=response.output_text,
            provider="openai",
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
        )

# ------------------------ v1 -------------------
# from openai import AsyncOpenAI
# class OpenAIProvider:

#     def __init__(
#         self,
#         endpoint: str,
#         api_key: str,
#         deployment: str,
#     ):
#         self.deployment = deployment

#         self.client = AsyncOpenAI(
#             base_url=endpoint,
#             api_key=api_key,
#         )

#     async def generate(self, prompt: str) -> str:
#         response = await self.client.responses.create(
#             model=self.deployment,
#             input=prompt,
#         )

#         return response.output_text
    
# ------------------------ v0 -------------------
# from openai import AsyncOpenAI, APIError
# from app.core.exceptions import LLMProviderError


# class OpenAIProvider:

#     def __init__(self, api_key: str, model: str):
#         self.client = AsyncOpenAI(api_key=api_key)
#         self.model = model

#     async def generate(self, prompt: str) -> str:
#         try:
#             response = await self.client.responses.create(
#                 model=self.model,
#                 instructions=(
#                     "You are an Enterprise AI Operations Assistant. "
#                     "Provide accurate, concise and professional answers."
#                 ),
#                 input=prompt,
#             )

#             return response.output_text

#         except APIError as exc:
#             raise LLMProviderError(
#                 message="OpenAI request failed.",
#                 code="OPENAI_ERROR",
#             ) from exc