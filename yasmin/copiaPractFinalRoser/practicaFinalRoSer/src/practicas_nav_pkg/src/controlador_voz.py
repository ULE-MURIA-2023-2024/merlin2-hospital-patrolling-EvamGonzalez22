#!/usr/bin/env python3

"""
Módulo de Control de Voz
Gestiona la interacción hombre-máquina mediante síntesis de voz (TTS)
y reconocimiento de voz (STT) utilizando Google Speech Recognition.
"""

import os
import time
import speech_recognition as sr  # Speech Recognition: Convierte audio a texto
from gtts import gTTS  # Google Text-to-Speech: Convierte texto a audio


class ControladorVoz:
    """
    Clase encargada de gestionar toda la interacción por voz del robot.
    Permite al robot hablar (síntesis de voz) y escuchar (reconocimiento).
    """

    def __init__(self):
        """
        Constructor: Inicializa el reconocedor de voz y define las palabras clave
        para confirmar acciones o cancelar operaciones.
        """
        # Inicializar el objeto reconocedor de voz
        self.recognizer = sr.Recognizer()

        # Definición de diccionarios de palabras clave para el control por voz
        # Palabras que el usuario puede decir para confirmar/continuar
        self.palabras_clave_si = ["sí", "si", "continúa", "adelante", "vale", "ok", "sigue", "procede"]
        
        # Palabras que el usuario puede decir para detener/cancelar
        self.palabras_clave_no = ["no", "para", "detén", "detente", "espera", "quédate", "stop"]

    def decir(self, texto):
        """
        Genera un archivo de audio a partir de texto y lo reproduce mediante síntesis de voz.
        El texto se convierte a habla en español y se reproduce automáticamente.
        
        Args:
            texto (str): La frase que el robot debe pronunciar.
        """
        print(f"[Robot dice]: {texto}")
        
        # Generación del audio en español mediante Google Text-to-Speech
        tts = gTTS(text=texto, lang='es')
        
        # Guardamos el archivo MP3 en una ubicación temporal
        tts.save("/tmp/mensaje.mp3")
        
        # Reproducción silenciosa (-q) usando mpg123
        # Este comando evita mensajes de diagnóstico y solo produce el audio
        os.system("mpg123 -q /tmp/mensaje.mp3")

    def escuchar(self):
        """
        Activa el micrófono, escucha al usuario y convierte el audio a texto.
        Implementa ajuste automático para el ruido ambiental y timeout de espera.
        
        Returns:
            str: El texto reconocido en minúsculas, o cadena vacía si hubo error
                 (micrófono no disponible, sin entrada, timeout, etc.).
        """
        with sr.Microphone() as source:
            # Pausa táctica para evitar que el robot se escuche a sí mismo (eco del TTS previo)
            # 2.5 segundos de buffer permiten que el audio anterior se disipe
            time.sleep(2.5)
            
            try:
                # Ajuste dinámico automático del reconocedor al ruido ambiental
                # Esto mejora la precisión en entornos con ruido variable
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Escuchar con un tiempo límite de espera
                # Si el usuario no habla en 7 segundos, se lanza excepción
                audio = self.recognizer.listen(source, timeout=7)
                
                # Enviar audio a Google para reconocimiento de voz
                # Requiere conexión a Internet para procesar el audio
                # El parámetro 'language' especifica español de España
                orden = self.recognizer.recognize_google(audio, language='es-ES').lower()
                
                print(f"[He escuchado]: {orden}")
                return orden
            
            except Exception as e:
                # Retorna cadena vacía si hay error durante el reconocimiento
                # Esto puede deberse a:
                # - Micrófono no disponible
                # - Sin entrada de audio (usuario no habló)
                # - Timeout (usuario tardó más de 7 segundos)
                # - Error de conexión a Google
                # - Sonido ininteligible
                print(f"[Error en escucha]: {e}")
                return ""

    def esperar_confirmacion(self, palabras_si=None, palabras_no=None):
        """
        Utilidad para esperar una confirmación simple del usuario (sí/no).
        Usa las palabras clave predefinidas o acepta listas personalizadas.
        
        Args:
            palabras_si (list, optional): Lista personalizada de palabras para "sí".
                Si es None, usa self.palabras_clave_si
            palabras_no (list, optional): Lista personalizada de palabras para "no".
                Si es None, usa self.palabras_clave_no
                
        Returns:
            str: "si", "no" o "desconocido" según lo que se haya reconocido.
        """
        if palabras_si is None:
            palabras_si = self.palabras_clave_si
        if palabras_no is None:
            palabras_no = self.palabras_clave_no

        orden = self.escuchar()

        if any(palabra in orden for palabra in palabras_si):
            return "si"
        elif any(palabra in orden for palabra in palabras_no):
            return "no"
        else:
            return "desconocido"

    def contiene_palabra_clave_si(self, texto):
        """
        Verifica si el texto contiene alguna palabra clave de confirmación (sí/ok/continúa/etc).
        
        Args:
            texto (str): Texto a verificar.
            
        Returns:
            bool: True si contiene palabra clave positiva, False en caso contrario.
        """
        return any(palabra in texto for palabra in self.palabras_clave_si)

    def contiene_palabra_clave_no(self, texto):
        """
        Verifica si el texto contiene alguna palabra clave de negación (no/para/detén/etc).
        
        Args:
            texto (str): Texto a verificar.
            
        Returns:
            bool: True si contiene palabra clave negativa, False en caso contrario.
        """
        return any(palabra in texto for palabra in self.palabras_clave_no)
