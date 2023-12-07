#https://www.buzzfeed.com/andrewpena/delightfully-innocent-jokes-from-captain-underpants

from random import shuffle, choice
from collections import Counter
import http.client
import openai

SENTENCE_COUNT = "20"

def main():
    openai.api_key = "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"

    # get starting message
    # original_message = 'Do unto others as you would have them do unto you'
    # original_message = 'feed your faith and your fears will starve to death'
    # original_message = 'If you are in deep water turn to the one who walked on it'
    original_message = "Have a great summer School starts September 5th"
    # original_message = "Faith is an investment that never looses interest"
    # original_message = "God made you on purpose for a purpose"
    # original_message = "Come in and see our pretty armchairs"
    # original_message = "Please wear your socks on the gym floor"
    # original_message = "See our big football game today"
    # original_message = "new tasty cheese and lentil pot pies"



    print("[" + original_message + "]")
    # scramble the letters
    letters = scramble(original_message)

    print("Thinking...")
    messages = gpt_messages(letters)

    for message in messages:
        m = remove_punctuation(message).replace(' ','')
        extra = extra_letters(m, letters)
        if(len(extra) > 0):
            print("[fail: " + message.replace('\\', '') + " " + ','.join(extra) + "]")
            continue
        print(remove_punctuation(message).strip())

def scramble(message):
    letters = list(message.strip().replace(' ','').lower())
    shuffle(letters)
    return ''.join(letters)

def remove_punctuation(input):
    punc = '''!1234567890()-[]{};:'"\,<>./?@#$%^&*_~'''
    for letter in input:
        if letter in punc:
            input = input.replace(letter, "")
    return input.replace('\\\"','\"')

def gpt_messages(letters):
    system1 = "You are a creative puzzle solver.\nYou will create 20 short complete sentences using letters from a provided multiset.\nDo not use a letter more times than it appears in the multiset.\nDo not use any letters that are not in the multiset of letters provided. \nYou do not need to use all the letters in the multiset."
    system2 = "" #"The sentence should be 5 words or less"
    user = "Here is the multiset of letters you are allowed to use: '" + '\', \''.join(sorted(letters)) \
           # + "'. Don't use these letters: '" + '\', \''.join(dont_letters(letters)) + "'." 
    
    print(system1)
    print(system2)
    print(user)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": system1
            },
            {
                "role": "system",
                "content": system2
            },
            {
                "role": "user",
                "content": user
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        
    print("total_tokens: " + str(response["usage"]["total_tokens"]))
    return parse_return(response["choices"][0]["message"]["content"])
    

def dont_letters(letters):
    all = "abcdefghijklmnopqrstuvwxyz"
    return set(all).difference(letters)

def parse_return(data):
    split = data.split("\n")
    messages = []
    for message in split:
        messages.append(message)

    return messages

def extra_letters(a, b):
    la = list(a.lower())
    lb = list(b)
    extra = []  
    for letter in la:
        if letter in lb:
            lb.remove(letter)
        else:
            extra.append(letter)

    return extra
    

if __name__ == "__main__":
    main()