import structlog
from openai import AsyncOpenAI


class OpenAIClient:
    """
    Async client for interacting with the OpenAI API.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        logger: structlog.stdlib.AsyncBoundLogger | None = None,
    ) -> None:
        """
        Initializes the OpenAI client.

        Args:
            api_key: The OpenAI API key.
            logger: A structlog logger for structured logging.
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.logger = logger or structlog.get_logger(__name__)

    async def get_completion(
        self, prompt: str, model: str = "gpt-3.5-turbo"
    ) -> str | None:
        """
        Generates a text completion using the specified model.

        Args:
            prompt: The text prompt to send to the model.
            model: The model to use for the completion.

        Returns:
            The completed text as a string, or None if an error occurs.
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            completion = response.choices[0].message.content
            await self.logger.info(
                "Successfully received completion from OpenAI",
                model=model,
                prompt_length=len(prompt),
                completion_length=len(completion) if completion else 0,
            )
            return completion
        except Exception as e:
            await self.logger.error(
                "Failed to get completion from OpenAI",
                error=e,
                model=model,
            )
            return None
