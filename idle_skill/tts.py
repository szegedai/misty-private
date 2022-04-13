import requests
from base64 import b64encode, b64decode
from mistyPy.Robot import Robot

def synthesize_text_to_robot(misty, text, file_name):

    result = requests.get("https://chatbot-rgai3.inf.u-szeged.hu/flask/tts", {"q": text})

    base64_str = str(b64encode(result.content), 'ascii', 'ignore')

    print(misty.SaveAudio(file_name, base64_str, True, True))

#def main():
#    misty = Robot("10.2.8.5")
#    synthesize_text_to_robot(misty, "Teszt teszt", "response.wav")

#if __name__ == '__main__':
#    main()
