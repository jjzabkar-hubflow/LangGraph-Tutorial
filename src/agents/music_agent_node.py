from langchain_openai import ChatOpenAI
import dotenv
import os
from src.agents import State
from src.agents.util import get_message_content_with_context

dotenv.load_dotenv()

print('Initializing OpenAI LLM...')
_openai_llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
print('Initialized OpenAI LLM')


def music_agent_node(state: State):
    messages = [
        {"role": "system",
         "content": """You are a music-obsessed assistant. 
            Provide any answer, as long as it rhymes. If possible, ensure the answer has a poetic rhythm.
            Keep it brief and do not ramble on.
            Do not worry about inaccuracies.
            If more context is required, assume the previous questions and answers are relevant."""
         },
        {
            "role": "user",
            "content": get_message_content_with_context(state)
        }
    ]

    reply = _openai_llm.invoke(messages)

    return {"messages": [{"role": "assistant", "content": reply.content}]}
