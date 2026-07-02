from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm


def get_current_time() -> str:
    """Get the current time in the format HH:MM:SS.

    Returns:
        str: HH:MM:SS
    """
    from datetime import datetime

    return datetime.now().strftime("%H:%M:%S")


root_agent = LlmAgent(
    model=LiteLlm(model="openai/deepseek-ai/deepseek-v4-flash"),
    name="root_agent",
    instruction="You are a colock. The user will ask you to tell the time. You should respond with the current time in the format HH:MM:SS.",
    tools=[get_current_time],
)

if __name__ == "__main__":
    pass
