import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Dime algo (tienes 5 segundos)...")
    audio = r.listen(source, timeout=5)

try:
    print("Analizando...")
    text = r.recognize_google(audio, language='es-ES')
    print(f"He entendido: {text}")
except Exception as e:
    print("No te he entendido o el micro no va bien.")

