from marquee_helper import message_to_letters, remove_punctuation, extra_letters, parse_return
import bing_helper

def main():

    # get starting message
    # original_message = 'Do unto others as you would have them do unto you'
    original_message = 'feed your faith and your fears will starve to death'
    # original_message = 'If you are in deep water turn to the one who walked on it'
    # original_message = "Have a great summer School starts September 5th"
    # original_message = "Faith is an investment that never looses interest"
    # original_message = "God made you on purpose for a purpose"
    # original_message = "Come in and see our pretty armchairs"
    # original_message = "Please wear your socks on the gym floor"
    # original_message = "See our big football game today"
    # original_message = "new tasty cheese and lentil pot pies"


    print("[" + original_message + "]")

    bad, good = bing_helper.message_to_messages(original_message)

    if len(good) == 0:
        print(bad)

    else:
        print('\n'.join(good))


if __name__ == "__main__":
    main()