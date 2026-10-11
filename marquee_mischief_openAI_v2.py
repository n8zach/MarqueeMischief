from openai import OpenAI
from marquee_helper import message_to_letters, validate_messages

client = OpenAI()    

def message_to_messages(message: str, use_proxy: bool = False):
    letters = message_to_letters(message)
    str_letters = ', '.join(letters)
    
    prompt = (
        f"Create 15 complete, funny, ironic sentences using ONLY the letters in the provided multiset. "
        f"Rules:\n"
        f"1. You must write and run a Python script using the code interpreter tool to verify that every sentence strictly obeys the multiset character limits.\n"
        f"2. Do not include any sentence that fails the code check.\n"
        f"3. Keep each sentence length to 4 or 5 words.\n"
        f"4. Favor short and funny words.\n"
        f"The letter multiset is: [{str_letters}]"
    )

    response = client.responses.create(
        model="gpt-4o",
        tools=[
            {
                "type": "code_interpreter",
                "container": {"type": "auto"}  # Automatically manages the sandboxed execution container
            }
        ],
        instructions="You are a precise word game engine. Always write and execute Python code to verify character counts before outputting sentences.",
        input=prompt
    )

    output_text = response.output_text
    raw_sentences = [line.strip() for line in output_text.split('\n') if line.strip()]
    
    # Final local safety net validation
    validated = validate_messages(raw_sentences, letters)
    
    return validated