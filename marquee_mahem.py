import sys
from marquee_mischief_bing import message_to_messages
#from marquee_mischief_openAi import message_to_messages

def main():
    while(True):
        message = input("Original Message: ")
        print(message_to_messages(message))

if __name__ == "__main__":
    main()