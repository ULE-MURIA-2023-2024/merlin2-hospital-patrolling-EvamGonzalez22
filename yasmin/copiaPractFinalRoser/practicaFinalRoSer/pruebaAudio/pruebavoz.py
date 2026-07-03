from gtts import gTTS
import os

text = "Hola Eva, estoy probando mis altavoces. ¿Me escuchas bien?"
tts = gTTS(text=text, lang='es')
tts.save("hola.mp3")
print("Reproduciendo audio...")
os.system("mpg123 hola.mp3")
