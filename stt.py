import speech_recognition as sr

def speech_to_text(filename):
    r = sr.Recognizer()

    # open the file
    try:
        with sr.AudioFile(filename) as source:
            # listen for the data (load audio to memory)
            audio_data = r.record(source)
            # recognize (convert from speech to text)
            text = r.recognize_google(audio_data, language="hu")
            print(text)
            f = open("stt.txt", "w")
            f.write(text)
            f.close()
    except IOError:
        print("Error: File does not appear to exist.")
