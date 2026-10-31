import json
import os
import random
import re
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from marquee_helper import message_to_letters, validate_messages

client = OpenAI()    

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "original_message_history.json")
HISTORY_SIZE = 30
MAX_ATTEMPTS = 5

def is_valid_sign_message(message: str) -> bool:
    """Only letters a-z and single spaces, non-empty, under 40 characters."""
    return bool(message) and len(message) < 40 and re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)*", message.strip()) is not None
MUNDANE_RATIO = 0.5  # share of generated messages that are plain, real-world style

def load_message_history() -> list:
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [str(m) for m in json.load(f)][-HISTORY_SIZE:]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def add_to_message_history(message: str) -> None:
    history = load_message_history()
    history.append(message)
    history = history[-HISTORY_SIZE:]  # rolling: drop the oldest
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    tmp = HISTORY_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    os.replace(tmp, HISTORY_FILE)

class GeneratedSentence(BaseModel):
    text: str = Field(description="The generated sentence using only letters from the multiset.")

class MarqueeGameResponse(BaseModel):
    sentences: List[GeneratedSentence] = Field(description="A list of generated sentences.")

class OriginalMessageResponse(BaseModel):
    sign_message: str = Field(description="The sign message under 40 characters, no punctuation.")
    caption: str = Field(description="A friendly, self-promotional caption.")

def generate_new_original_message(use_proxy: bool = False):
    history = load_message_history()
    history_text = ""
    if history:
        history_text = (
            "\n# History\n"
            "You will be provided with a history of the most recent sign messages you created. "
            "Create a sign message that is creatively different from ALL of them: a different "
            "type of business or school, a different topic, different key words, and a different "
            "joke or wordplay, and a different sentence structure and opening word. Do not copy the examples above either.\n"
            "Previous sign messages:\n" + "\n".join(f"- {m}" for m in history) + "\n"
        )

    # The model has no memory between calls, so the code picks the style to guarantee a mix.
    if random.random() < MUNDANE_RATIO:
        style_text = (
            "STYLE FOR THIS MESSAGE: mundane. Write an ordinary, realistic message of the kind people really see on "
            "roadside and storefront letter signs, such as a sale, store hours, a school event or date, or a seasonal "
            "reminder. No puns, no jokes, no wordplay."
        )
    else:
        style_text = (
            "STYLE FOR THIS MESSAGE: wordplay. Write ONE clever pun that anyone would get instantly. The best form takes a "
            "well-known phrase, idiom, or song/movie-style saying and swaps in a single real word that fits the business "
            "(examples: 'espresso yourself', 'better latte than never', 'fancy meeting you hair'). "
            "Rules for the pun: use only real dictionary words (never invent or misspell a word like 'bowlieve'), use only ONE pun per "
            "message (no stacking), and the message must read naturally and make sense. If the pun needs explaining, choose a simpler one."
        )

    # '<thing> at the <place>' is fine occasionally but the model overuses it, so mostly forbid it.
    if random.random() < 0.8:
        pattern_text = (
            "- Do NOT use the '<thing> at the <place>' template (for example 'sale at the mall'); avoid the phrase 'at the'. "
            "Vary sentence structure: statements, commands, questions, countdowns, dates, and short phrases are all fine."
        )
    else:
        pattern_text = "- Vary sentence structure: statements, commands, questions, countdowns, dates, and short phrases are all fine."

    prompt = (
        "Create a single moveable letter sign message for public display outside a business or school. "
        "The message is the starting point for a word game where players rearrange its letters. "
        f"{style_text}\n"
        "**Requirements:**\n"
        "- Do NOT use any punctuation anywhere in the sign message. This includes periods, commas, exclamation points, apostrophes, or any other symbols. The sign message must be entirely free of punctuation.\n"
        "- Do NOT use any digits or numerals (0-9) in the sign message. Spell out every number as words (for example 'august tenth', never 'august 10th'). Only the letters a to z and spaces are allowed.\n"
        "- The sign message must be LESS THAN 40 characters in length, including spaces.\n"
        "- Do not reference any real business or school names, or use copyrighted/trademarked content.\n"
        "- The sign message must be suitable for general public or campus-wide audiences (family-friendly, non-political/non-controversial).\n"
        f"{pattern_text}\n\n"

        "**Caption requirements (self-promotional style):**\n"
        "- The caption must be friendly, personable, and sound like self-promotion of your creative abilities as an AI. It must clearly express that YOU (the AI) made this message for the user.\n"
        "- Use phrasings like: 'I made this just for you', 'Here you go, I hope you like it', 'I hope you like this one', or something similar. The caption should sound as if you are proud of your work and sharing it.\n"
        "- Do NOT simply introduce or explain the sign message, nor repeat/paraphrase the sign message in the caption.\n"
        "- Vary the caption wording on every response.\n\n"

        "# Steps\n\n"

        "1. Choose a type of business or educational venue (no real or trademarked names). Pick an unusual one sometimes: a barber, a dentist, a library, a pet groomer, a bowling alley, a farm stand, a gym, a florist, and so on.\n"
        "2. Write the sign message in the style given at the top.\n"
        "3. Confirm it is under 40 characters, has NO digits, NO punctuation or symbols, and is suitable for a public audience.\n"
        "4. Write the caption.\n\n"

        "# Output\n\n"

        "Respond with only the structured result: 'sign_message' (under 40 characters, letters and spaces only, no digits, no punctuation) and 'caption' (punctuation OK).\n\n"

        "# Examples of sign messages\n\n"

        "Mundane: fresh bread baked daily | first day of school august tenth | garden supplies now in stock\n"
        "Wordplay: espresso yourself | better latte than never | fancy meeting you hair | donut worry be happy\n"
        "These only show the range of styles. Do NOT reuse or closely imitate them.\n\n"

        "Example captions: 'I made this message just for you' | 'I hope you enjoy this one I created' | 'I came up with this one for you' | 'Here you go. I hope you like it'\n"
        "Vary the caption wording rather than copying these.\n"
    ) + history_text

    result = None
    for _ in range(MAX_ATTEMPTS):
        completion = client.beta.chat.completions.parse(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a witty, creative sign writer for a word game. Follow the length and no-punctuation rules precisely."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format=OriginalMessageResponse,
            temperature=1.0,
        )
        result = completion.choices[0].message.parsed
        if result and is_valid_sign_message(result.sign_message):
            break
    else:
        raise ValueError(f"Could not generate a valid sign message after {MAX_ATTEMPTS} attempts (last: {result.sign_message if result else None!r}).")

    add_to_message_history(result.sign_message)

    return result

    
def message_to_messages(message: str, use_proxy: bool = False):
    letters = message_to_letters(message)
    str_letters = ', '.join(letters)
    
    prompt = (
        f"Create 15 complete, funny or ironic sentences using ONLY the letters in the provided multiset. "
        f"Rules:\n"
        f"1. You must not use any letter more times than it appears in the multiset.\n"
        #f"2. Keep each sentence length to 4 or 5 words.\n"
        f"2. Favor adolescent humor. Such as is employed by Dav Pilkey in the Captain Underpants series.\n"
        f"3. Favor short and funny words.\n"
        f"4. Do not use any punctuation or special characters. Not even a period at the end.\n"
        f"5. Aim for lots of variety in word choices across the sentences.\n"
        f"6. Do not include any acts of violence or harm to people or animals, even in jest.\n"
        f"The letter multiset is: [{str_letters}]"
    )   

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": "You are a creative and precise word game engine. Strictly adhere to character multiset constraints."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        response_format=MarqueeGameResponse,
        temperature=0.7,
    )

    result = completion.choices[0].message.parsed
    
    # Extract the raw sentence strings from the structured Pydantic response
    sentence_list = [item.text for item in result.sentences]
    
    # Pass them directly to your original, proven validator from marquee_helper
    validated = validate_messages(sentence_list, letters)
    
    return validated