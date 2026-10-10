from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from marquee_helper import message_to_letters, validate_messages

client = OpenAI()    

class GeneratedSentence(BaseModel):
    text: str = Field(description="The generated sentence using only letters from the multiset.")

class MarqueeGameResponse(BaseModel):
    sentences: List[GeneratedSentence] = Field(description="A list of 15 generated sentences.")

def message_to_messages(message: str, use_proxy: bool = False):
    letters = message_to_letters(message)
    str_letters = ', '.join(letters)
    
    prompt = (
        f"Create 15 complete, funny or ironic sentences using ONLY the letters in the provided multiset. "
        f"Rules:\n"
        f"1. You must not use any letter more times than it appears in the multiset.\n"
        #f"2. Keep each sentence length to 4 or 5 words.\n"
        f"3. Favor short and funny words.\n"
        f"4. Do not use any punctuation or special characters. Not even a period at the end.\n"
        f"5. Aim for lots of variety in the sentences. Avoid repeating the same words.\n"
        f"The letter multiset is: [{str_letters}]"
    )

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": "You are a precise word game engine. Strictly adhere to character multiset constraints."
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