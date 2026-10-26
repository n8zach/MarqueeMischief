from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from marquee_helper import message_to_letters, validate_messages

client = OpenAI()    

class GeneratedSentence(BaseModel):
    text: str = Field(description="The generated sentence using only letters from the multiset.")

class MarqueeGameResponse(BaseModel):
    sentences: List[GeneratedSentence] = Field(description="A list of generated sentences.")

class OriginalMessageResponse(BaseModel):
    sign_message: str = Field(description="The sign message under 40 characters, no punctuation.")
    caption: str = Field(description="A friendly, self-promotional caption.")

def generate_new_original_message(use_proxy: bool = False):
    prompt = (
        "Create a single moveable letter sign message for public display outside a business or school. The sign message should be simple, generic, or commonplace—originality is fine but not required. Use standard sign messages suitable for either context (e.g., 'spring savings are here', 'parent teacher meeting this thursday', etc). The message should be a realistic, everyday starting point for a word game; high creativity is NOT needed.\n"
        "**Requirements:**\n"
        "- Do NOT use any punctuation anywhere in the sign message. This includes periods, commas, exclamation points, apostrophes, or any other symbols. The sign message must be entirely free of punctuation.\n"
        "- The sign message must be LESS THAN 40 characters in length, including spaces.\n"
        "- Do not reference any real business or school names, or use copyrighted/trademarked content.\n"
        "- The sign message must be suitable for general public or campus-wide audiences (family-friendly, non-political/non-controversial).\n\n"

        "**Caption requirements (self-promotional style):**\n"
        "- The caption must be friendly, personable, and sound like self-promotion of your creative abilities as an AI. It must clearly express that YOU (the AI) made this message for the user.\n"
        "- Use phrasings like: 'I made this just for you', 'Here you go, I hope you like it', 'I hope you like this one', or something similar. The caption should sound as if you are proud of your work and sharing it.\n"
        "- Do NOT simply introduce or explain the sign message, nor repeat/paraphrase the sign message in the caption.\n"
        "- The caption should change on every response.\n\n"

        "**Reasoning:**  \n"
        "Before producing your answer, reason step by step to ensure:\n"
        "- The sign message fits a plausible business or educational context.\n"
        "- The sign message is a realistic, standard, or generic phrase commonly used on such signs.\n"
        "- The sign message is under 40 characters, contains absolutely no punctuation, and is public-appropriate.\n"
        "- The caption is personable, unique, and *always* self-promotional (as described above), never a generic introductory line.\n"
        "- The caption does not repeat or paraphrase the sign message.\n\n"

        "After step-by-step reasoning, output ONLY a JSON object with two fields:\n"
        "- 'sign_message': the less-than-40-character sign message (no punctuation).\n"
        "- 'caption': the friendly, self-promotional caption (punctuation OK).\n\n"

        "Do not include any extra text, explanations, or code blocks—only the JSON object.\n\n"

        "# Steps\n\n"

        "1. Choose a type of business or educational venue (no real or trademarked names).\n"
        "2. Think of a simple, realistic, generic sign message appropriate for that context (examples: spring savings are here, parent teacher meeting this thursday).\n"
        "3. Confirm the sign message is under 40 characters, uses NO punctuation or special symbols, and is suitable for a public audience.\n"
        "4. Write a brief, self-promotional, friendly caption in which you (the AI) take credit and share the sign message enthusiastically, using the required style.\n"
        "5. Double-check both the sign and caption for compliance with all rules.\n"
        "6. Output only the specified JSON object.\n\n"

        "# Output Format\n\n"

        "Respond with a single JSON object, NOT wrapped in code blocks:\n"
        "{\n"
        '\"sign_message\": "[<sign message under 40 characters, no punctuation>]",\n'
        '\"caption\": "[<self-promotional, friendly introduction>]"\n'
        "}\n\n"

        "# Examples\n\n"

        "Example 1:\n"
        "Reasoning: For a bakery, a typical sign could promote fresh goods.\n"
        "{\n"
        "\"sign_message\": \"fresh bread baked daily\",\n"
        "\"caption\": \"I made this message just for you\"\n"
        "}\n\n"

        "Example 2:\n"
        "Reasoning: For a school, a common announcement sign.\n"
        "{\n"
        "\"sign_message\": \"first day of school august tenth\",\n"
        "\"caption\": \"I hope you enjoy this one I created\"\n"
        "}\n\n"

        "Example 3:\n"
        "Reasoning: For a hardware store, a simple seasonal promotion.\n"
        "{\n"
        "\"sign_message\": \"garden supplies now in stock\",\n"
        "\"caption\": \"I came up with this one for you\"\n"
        "}\n\n"

        "Example 4:\n"
        "Reasoning: For a coffee shop, a welcoming sign.\n"
        "{\n"
        "\"sign_message\": \"hot coffee always ready\",\n"
        "\"caption\": \"Here you go. I hope you like it\"\n"
        "}\n\n"

        "(In real responses, vary the caption wording, and make sure captions always adopt a self-promotional, friendly tone as shown above.)\n\n"

        "# Notes\n\n"

        "Never use punctuation or symbols in the sign_message.\n"
        "Captions MUST always sound like personable, self-promoting AI output (I made this for you, etc), not merely an introduction or explanation.\n"
        "Do not repeat or paraphrase the sign message in the caption.\n"
        "Output only the JSON object specified.\n\n"

        "# Reminder\n"
        "Always perform step-by-step reasoning before producing the final answer. Double-check the self-promotional style of the caption and that all requirements are followed. Output ONLY the required JSON object.\n"
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
        response_format=OriginalMessageResponse,
        temperature=0.7,
    )

    result = completion.choices[0].message.parsed

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