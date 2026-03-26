import argparse
import json
import os
from os import environ as env

from book_maker.loader import BOOK_LOADER_DICT
from book_maker.translator import MODEL_DICT
from book_maker.utils import LANGUAGES, TO_LANGUAGE_CODE


def parse_prompt_arg(prompt_arg):
    prompt = None
    if prompt_arg is None:
        return prompt

    # Check if it's a path to a markdown file (PromptDown format)
    if prompt_arg.endswith(".md") and os.path.exists(prompt_arg):
        try:
            from promptdown import StructuredPrompt

            structured_prompt = StructuredPrompt.from_promptdown_file(prompt_arg)

            # Initialize our prompt structure
            prompt = {}

            # Handle developer_message or system_message
            # Developer message takes precedence if both are present
            if (
                hasattr(structured_prompt, "developer_message")
                and structured_prompt.developer_message
            ):
                prompt["system"] = structured_prompt.developer_message
            elif (
                hasattr(structured_prompt, "system_message")
                and structured_prompt.system_message
            ):
                prompt["system"] = structured_prompt.system_message

            # Extract user message from conversation
            if (
                hasattr(structured_prompt, "conversation")
                and structured_prompt.conversation
            ):
                for message in structured_prompt.conversation:
                    if message.role.lower() == "user":
                        prompt["user"] = message.content
                        break

            # Ensure we found a user message
            if "user" not in prompt or not prompt["user"]:
                raise ValueError(
                    "PromptDown file must contain at least one user message"
                )

            print(f"Successfully loaded PromptDown file: {prompt_arg}")

            # Validate required placeholders
            if any(c not in prompt["user"] for c in ["{text}"]):
                raise ValueError(
                    "User message in PromptDown must contain `{text}` placeholder"
                )

            return prompt
        except Exception as e:
            print(f"Error parsing PromptDown file: {e}")
            # Fall through to other parsing methods

    # Existing parsing logic for JSON strings and other formats
    if not any(prompt_arg.endswith(ext) for ext in [".json", ".txt", ".md"]):
        try:
            # user can define prompt by passing a json string
            # eg: --prompt '{"system": "You are a professional translator who translates computer technology books", "user": "Translate \`{text}\` to {language}"}'
            prompt = json.loads(prompt_arg)
        except json.JSONDecodeError:
            # if not a json string, treat it as a template string
            prompt = {"user": prompt_arg}

    elif os.path.exists(prompt_arg):
        if prompt_arg.endswith(".txt"):
            # if it's a txt file, treat it as a template string
            with open(prompt_arg, encoding="utf-8") as f:
                prompt = {"user": f.read()}
        elif prompt_arg.endswith(".json"):
            # if it's a json file, treat it as a json object
            # eg: --prompt prompt_template_sample.json
            with open(prompt_arg, encoding="utf-8") as f:
                prompt = json.load(f)
    else:
        raise FileNotFoundError(f"{prompt_arg} not found")

    # if prompt is None or any(c not in prompt["user"] for c in ["{text}", "{language}"]):
    if prompt is None or any(c not in prompt["user"] for c in ["{text}"]):
        raise ValueError("prompt must contain `{text}`")

    if "user" not in prompt:
        raise ValueError("prompt must contain the key of `user`")

    if (prompt.keys() - {"user", "system"}) != set():
        raise ValueError("prompt can only contain the keys of `user` and `system`")

    print("prompt config:", prompt)
    return prompt


def main():
    translate_model_list = list(MODEL_DICT.keys())
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--book_name",
        dest="book_name",
        type=str,
        help="path of the epub file to be translated",
    )
    ########## KEYS ##########
    parser.add_argument(
        "--openai_key",
        dest="openai_key",
        type=str,
        default="",
        help="OpenAI api key,if you have more than one key, please use comma"
        " to split them to go beyond the rate limits",
    )
    parser.add_argument(
        "--claude_key",
        dest="claude_key",
        type=str,
        help="you can find claude key from here (https://console.anthropic.com/account/keys)",
    )

    # for Google Gemini
    parser.add_argument(
        "--gemini_key",
        dest="gemini_key",
        type=str,
        help="You can get Gemini Key from  https://makersuite.google.com/app/apikey",
    )

    parser.add_argument(
        "--test",
        dest="test",
        action="store_true",
        help="only the first 10 paragraphs will be translated, for testing",
    )
    parser.add_argument(
        "--test_num",
        dest="test_num",
        type=int,
        default=10,
        help="how many paragraphs will be translated for testing",
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model",
        type=str,
        default="chatgptapi",
        choices=translate_model_list,
        metavar="MODEL",
        help="model to use, available: {%(choices)s}",
    )
    parser.add_argument(
        "--model_list",
        type=str,
        dest="model_list",
        help="specify the exact model name to use, e.g. claude-sonnet-4-6, gpt-4o, gemini-1.5-pro",
    )
    parser.add_argument(
        "--language",
        type=str,
        choices=sorted(LANGUAGES.keys())
        + sorted([k.title() for k in TO_LANGUAGE_CODE]),
        default="zh-hans",
        metavar="LANGUAGE",
        help="language to translate to, available: {%(choices)s}",
    )
    parser.add_argument(
        "--resume",
        dest="resume",
        action="store_true",
        help="if program stop unexpected you can use this to resume",
    )
    # args to change api_base
    parser.add_argument(
        "--api_base",
        metavar="API_BASE_URL",
        dest="api_base",
        type=str,
        help="specify base url other than the OpenAI's official API address",
    )
    parser.add_argument(
        "--exclude_filelist",
        dest="exclude_filelist",
        type=str,
        default="",
        help="if you have more than one file to exclude, please use comma to split them, example: --exclude_filelist 'nav.xhtml,cover.xhtml'",
    )
    parser.add_argument(
        "--translate-tags",
        dest="translate_tags",
        type=str,
        default="p",
        help="example --translate-tags p,blockquote",
    )
    parser.add_argument(
        "--exclude_translate-tags",
        dest="exclude_translate_tags",
        type=str,
        default="sup",
        help="example --exclude_translate-tags table,sup",
    )
    parser.add_argument(
        "--prompt",
        dest="prompt_arg",
        type=str,
        metavar="PROMPT_ARG",
        help="used for customizing the prompt. It can be the prompt template string, or a path to the template file. The valid placeholders are `{text}` and `{language}`.",
    )
    parser.add_argument(
        "--accumulated_num",
        dest="accumulated_num",
        type=int,
        default=1,
        help="""Wait for how many tokens have been accumulated before starting the translation.
gpt3.5 limits the total_token to 4090.
For example, if you use --accumulated_num 1600, maybe openai will output 2200 tokens
and maybe 200 tokens for other messages in the system messages user messages, 1600+2200+200=4000,
So you are close to reaching the limit. You have to choose your own value, there is no way to know if the limit is reached before sending
""",
    )
    parser.add_argument(
        "--translation_style",
        dest="translation_style",
        type=str,
        help="""ex: --translation_style "color: #808080; font-style: italic;" """,
    )
    parser.add_argument(
        "--batch_size",
        dest="batch_size",
        type=int,
        help="how many lines will be translated by aggregated translation(This options currently only applies to txt files)",
    )
    parser.add_argument(
        "--retranslate",
        dest="retranslate",
        nargs=4,
        type=str,
        help="""--retranslate "$translated_filepath" "file_name_in_epub" "start_str" "end_str"(optional)
        Retranslate from start_str to end_str's tag:
        python3 "make_book.py" --book_name "test_books/animal_farm.epub" --retranslate 'test_books/animal_farm_bilingual.epub' 'index_split_002.html' 'in spite of the present book shortage which' 'This kind of thing is not a good symptom. Obviously'
        Retranslate start_str's tag:
        python3 "make_book.py" --book_name "test_books/animal_farm.epub" --retranslate 'test_books/animal_farm_bilingual.epub' 'index_split_002.html' 'in spite of the present book shortage which'
""",
    )
    parser.add_argument(
        "--single_translate",
        action="store_true",
        help="output translated book, no bilingual",
    )
    parser.add_argument(
        "--use_context",
        dest="context_flag",
        action="store_true",
        help="adds an additional paragraph for global, updating historical context of the story to the model's input, improving the narrative consistency for the AI model (this uses ~200 more tokens each time)",
    )
    parser.add_argument(
        "--context_paragraph_limit",
        dest="context_paragraph_limit",
        type=int,
        default=0,
        help="if use --use_context, set context paragraph limit",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="temperature parameter for `chatgptapi`/`gpt4`/`gpt4omini`/`gpt4o`/`gpt5mini`/`claude`/`gemini`",
    )
    parser.add_argument(
        "--block_size",
        type=int,
        default=-1,
        help="merge multiple paragraphs into one block, may increase accuracy and speed up the process, but disturb the original format, must be used with `--single_translate`",
    )
    parser.add_argument(
        "--batch-use",
        dest="batch_use_flag",
        action="store_true",
        help="Use pre-generated batch translations to create files. Run with --batch first before using this option",
    )

    options = parser.parse_args()

    if not options.book_name:
        print("Error: please provide the path of your book using --book_name <path>")
        exit(1)
    if not os.path.isfile(options.book_name):
        print(f"Error: the book {options.book_name!r} does not exist.")
        exit(1)

    translate_model = MODEL_DICT.get(options.model)
    assert translate_model is not None, "unsupported model"
    API_KEY = ""
    if options.model in [
        "openai",
        "chatgptapi",
        "gpt4",
        "gpt4omini",
        "gpt4o",
        "gpt5mini",
        "o1preview",
        "o1",
        "o1mini",
        "o3mini",
    ]:
        if OPENAI_API_KEY := (
            options.openai_key
            or env.get(
                "OPENAI_API_KEY",
            )  # XXX: for backward compatibility, deprecate soon
            or env.get(
                "BBM_OPENAI_API_KEY",
            )  # suggest adding `BBM_` prefix for all the bilingual_book_maker ENVs.
        ):
            API_KEY = OPENAI_API_KEY
        else:
            raise Exception(
                "OpenAI API key not provided, please google how to obtain it",
            )
    elif options.model.startswith("claude"):
        API_KEY = options.claude_key or env.get("BBM_CLAUDE_API_KEY")
        if not API_KEY:
            raise Exception("Please provide claude key")
    elif options.model in ["gemini", "geminipro"]:
        API_KEY = options.gemini_key or env.get("BBM_GOOGLE_GEMINI_KEY")
    else:
        API_KEY = ""

    book_type = options.book_name.split(".")[-1]
    support_type_list = list(BOOK_LOADER_DICT.keys())
    if book_type not in support_type_list:
        raise Exception(
            f"now only support files of these formats: {','.join(support_type_list)}",
        )

    if options.block_size > 0 and not options.single_translate:
        raise Exception(
            "block_size must be used with `--single_translate` because it disturbs the original format",
        )

    book_loader = BOOK_LOADER_DICT.get(book_type)
    assert book_loader is not None, "unsupported loader"
    language = options.language
    if options.language in LANGUAGES:
        # use the value for prompt
        language = LANGUAGES.get(language, language)

    # change api_base for issue #42
    model_api_base = options.api_base

    e = book_loader(
        options.book_name,
        translate_model,
        API_KEY,
        options.resume,
        language=language,
        model_api_base=model_api_base,
        is_test=options.test,
        test_num=options.test_num,
        prompt_config=parse_prompt_arg(options.prompt_arg),
        single_translate=options.single_translate,
        context_flag=options.context_flag,
        context_paragraph_limit=options.context_paragraph_limit,
        temperature=options.temperature,
    )
    # other options
    if options.translate_tags:
        e.translate_tags = options.translate_tags
    if options.exclude_translate_tags:
        e.exclude_translate_tags = options.exclude_translate_tags
    if options.exclude_filelist:
        e.exclude_filelist = options.exclude_filelist
    if options.accumulated_num > 1:
        e.accumulated_num = options.accumulated_num
    if options.translation_style:
        e.translation_style = options.translation_style
    if options.batch_size:
        e.batch_size = options.batch_size
    if options.retranslate:
        e.retranslate = options.retranslate
    if options.block_size > 0:
        e.block_size = options.block_size
    if options.batch_use_flag:
        e.batch_use_flag = options.batch_use_flag

    # --model_list: override the specific model name for any provider
    if options.model_list:
        model_names = options.model_list.split(",")
        if options.model.startswith("claude"):
            # Claude: use the first model name from the list
            e.translate_model.set_claude_model(model_names[0])
        elif options.model in ("gemini", "geminipro"):
            e.translate_model.set_model_list(model_names)
        elif options.model in [
            "openai",
            "chatgptapi",
            "gpt4",
            "gpt4omini",
            "gpt4o",
            "gpt5mini",
            "o1preview",
            "o1",
            "o1mini",
            "o3mini",
        ]:
            e.translate_model.set_model_list(model_names)
    else:
        # No --model_list provided: use default model sets
        if options.model == "chatgptapi":
            e.translate_model.set_gpt35_models()
        elif options.model == "gpt4":
            e.translate_model.set_gpt4_models()
        elif options.model == "gpt4omini":
            e.translate_model.set_gpt4omini_models()
        elif options.model == "gpt4o":
            e.translate_model.set_gpt4o_models()
        elif options.model == "gpt5mini":
            e.translate_model.set_gpt5mini_models()
        elif options.model == "o1preview":
            e.translate_model.set_o1preview_models()
        elif options.model == "o1":
            e.translate_model.set_o1_models()
        elif options.model == "o1mini":
            e.translate_model.set_o1mini_models()
        elif options.model == "o3mini":
            e.translate_model.set_o3mini_models()
        elif options.model in ("gemini", "geminipro"):
            e.translate_model.set_interval(0.01)
            if options.model == "gemini":
                e.translate_model.set_geminiflash_models()
            else:
                e.translate_model.set_geminipro_models()

    e.make_bilingual_book()


if __name__ == "__main__":
    main()
