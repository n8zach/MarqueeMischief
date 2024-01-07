import sys
#from marquee_mischief_bing import message_to_messages
from marquee_mischief_openAI import message_to_messages
import os
from dotenv import load_dotenv

load_dotenv('.env')

def main():
    while(True):
        message = input("Original Message: ")
        
        messages = message_to_messages(message, True)

        out = []
        out.append("\nGood Messages:")
        for g in messages["good"]:
            out.append(f"{g['text']} ({g['unused']})")
        out.append("\nClose Messages:")
        for b in messages["bad"]:
            if len(b["extra"]) == 1:
                out.append(f"{b['text']} [{b['extra']}] ({b['unused']})")

        print('\n'.join(out))

if __name__ == "__main__":
    main()