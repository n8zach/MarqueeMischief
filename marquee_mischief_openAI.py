# This code is for v1 of the openai package: pypi.org/project/openai
import openai
from marquee_helper import validate_messages, message_to_letters

def message_to_messages(message, use_proxy = False):

    letters = message_to_letters(message)
    count = min(max(4, int((len(letters)+2)/3/8)),5)
    client = openai.OpenAI(api_key = "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")

    prompt = f"Create 15 funny, complete sentences using only the letters in this multiset: {letters}. "
    prompt = prompt + "If possible, use words that a 10 year old would find funny like fart, farts, gross, toilet, boogers, stupid, dumb, poopy, smelly, pee, poop, etc.  "
    prompt = prompt + "Keep each sentence to {count} words or less. "
    #prompt = prompt + "Keep each sentence to 7 words or less. "
    prompt = prompt + "Put all the sentences on one line separated by $"

    response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
        "role": "user",
        "content": prompt
        },
    ],
    temperature=0.1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )

    messages_raw = response.choices[0].message.content.split('$')

    bad, good = validate_messages(messages_raw, letters)
    if len(good) == 0:
        print("no valid messages found. Here is what we got...")
        print(bad)
        return("Sorry...  I got nothin. :( ")
    else:
        return('\n'.join(good))

