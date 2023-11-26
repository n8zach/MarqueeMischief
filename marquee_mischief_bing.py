from marquee_helper import message_to_letters, remove_punctuation, extra_letters, parse_return
import bing_helper
from image_to_text2 import image_to_text

def main():

    # original_message = 'Do unto others as you would have them do unto you'
    # original_message = 'feed your faith and your fears will starve to death'
    # original_message = 'If you are in deep water turn to the one who walked on it'
    # original_message = "Have a great summer School starts September 5th"
    # original_message = "Faith is an investment that never looses interest"
    # original_message = "God made you on purpose for a purpose"
    # original_message = "Come in and see our pretty armchairs"
    # original_message = "Please wear your socks on the gym floor"
    # original_message = "See our big football game today"
    # original_message = "new tasty cheese and lentil pot pies"

    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\GiantPlantSale.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\message.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\salon.jpg")
    # original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\starve.jpg")
    original_message = image_to_text(r"C:\Users\Gersh\Git\MarqueeMischief\TestImages\Contrary.jpg")

    print("[" + original_message + "]")

    bad, good = bing_helper.message_to_messages(original_message)

    if len(good) == 0:
        print("no valid messages found. Here is what we got...")
        print(bad)

    else:
        print('\n'.join(good))


if __name__ == "__main__":
    main()