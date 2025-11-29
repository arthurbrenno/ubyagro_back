from agentle.agents.agent import Agent
from agentle.agents.conversations.local_conversation_store import LocalConversationStore
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.openrouter.openrouter_generation_provider import (
    OpenRouterGenerationProvider,
)
from agentle.web.extraction_preferences import ExtractionPreferences
from agentle.web.extractor import Extractor
from dotenv import load_dotenv
from playwright import async_api
from pydantic import BaseModel, Field

load_dotenv()


# Example how to use an Agent:


async def example_tool() -> None: ...


class InnerResponse(BaseModel):
    ok: int


class ExampleStructuredOutput(BaseModel):
    answer: str | None = Field(default=None)
    detail: InnerResponse | None = Field(default=None)


class DesiredWebsiteExtractedContent(BaseModel):
    most_relevant_information: str
    course_urls: list[str]


provider = OpenRouterGenerationProvider.with_fallback_models(["openai/gpt-5-nano"])
MODEL = "openai/gpt-oss-120b"


async def example_agent_usage() -> None:
    agent = Agent(
        instructions="you are ......",
        generation_provider=provider,
        model=MODEL,
        tools=[example_tool],
        response_schema=ExampleStructuredOutput,
        conversation_store=LocalConversationStore(),
    )

    message_history = [
        UserMessage(parts=[TextPart(text="Hi")]),
        AssistantMessage(parts=[TextPart(text="Hello!!! How can I help you.")]),
    ]

    output = await agent.run_async(message_history)

    example_structured_output = output.parsed
    print(example_structured_output.answer)


async def example_extractor_usage() -> None:
    extractor = Extractor(llm=provider, model=MODEL)

    async with async_api.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        urls = ["https://uniube.br"]

        preferences = ExtractionPreferences(
            only_main_content=True,
            wait_for_ms=2000,
            block_ads=True,
            remove_base_64_images=True,
            timeout_ms=15000,
        )

        result = await extractor.extract_async(
            browser=browser,
            urls=urls,
            extraction_preferences=preferences,
            prompt="extract the ...",
            output=DesiredWebsiteExtractedContent
        )

        output_parsed = result.output_parsed

        print(output_parsed.most_relevant_information)
