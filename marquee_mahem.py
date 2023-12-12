import sys
#from marquee_mischief_bing import message_to_messages
from marquee_mischief_openAI import message_to_messages
import os
from dotenv import load_dotenv

load_dotenv('.env')

def main():
    while(True):
        message = input("Original Message: ")
        print(message_to_messages(message, True))

if __name__ == "__main__":
    main()