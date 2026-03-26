from book_maker.translator.chatgptapi_translator import ChatGPTAPI
from book_maker.translator.claude_translator import Claude
from book_maker.translator.gemini_translator import Gemini

MODEL_DICT = {
    "openai": ChatGPTAPI,
    "chatgptapi": ChatGPTAPI,
    "gpt4": ChatGPTAPI,
    "gpt4omini": ChatGPTAPI,
    "gpt4o": ChatGPTAPI,
    "gpt5mini": ChatGPTAPI,
    "o1preview": ChatGPTAPI,
    "o1": ChatGPTAPI,
    "o1mini": ChatGPTAPI,
    "o3mini": ChatGPTAPI,
    "claude": Claude,
    "claude-sonnet-4-6": Claude,
    "claude-opus-4-6": Claude,
    "claude-opus-4-5-20251101": Claude,
    "claude-haiku-4-5-20251001": Claude,
    "claude-sonnet-4-5-20250929": Claude,
    "claude-opus-4-1-20250805": Claude,
    "claude-opus-4-20250514": Claude,
    "claude-sonnet-4-20250514": Claude,
    "gemini": Gemini,
    "geminipro": Gemini,
    # add more here
}
