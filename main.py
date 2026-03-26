#Este repo es un proyecto personal para aprender a crear un bot de Telegram que reporte el clima de Matamoros, Tamaulipas.
#A mi se me ocurrio la idea de crear un bot para mi familia, porque a veces me preguntan "¿Cómo va a estar hoy el dia?" 
#y pensé que sería divertido hacer un bot que les pueda responder eso automáticamente. 
#Además, es una buena oportunidad para aprender a usar APIs y a programar bots de Telegram.
#Al igual que se puede escalar y agregar más funcionalidades gracias al bot de Telegram.

import os
import requests
import telebot
import schedule
import time
import threading
from dotenv import load_dotenv
from datetime import datetime

# 1. Cargar las llaves secretas
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Aquí pondremos tu ID y los de tus papás cuando te los pasen
USUARIOS_AUTORIZADOS = ['5207047409'] # Tu ID ya está aquí configurado

# --- FUNCIONES DEL CLIMA ---
def obtener_clima():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Matamoros,MX&appid={WEATHER_API_KEY}&units=metric&lang=es"
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        
        # Extraemos los datos del "paquete"
        info = {
            "temp": datos['main']['temp'],
            "feels_like": datos['main']['feels_like'], 
            "humedad": datos['main']['humidity'],      
            "desc": datos['weather'][0]['description'].capitalize(),
            "temp_max": datos['main']['temp_max'],
            "temp_min": datos['main']['temp_min']
        }
        return info
    return None

def mandar_clima_automatico():
    print("⏳ Ejecutando envío automático...")
    clima = obtener_clima()
    
    if clima:
        mensaje = (
            f"🌡️ *REPORTE CLIMA MATAMOROS* 🌡️\n\n"
            f"🌤️ *Estado:* {clima['desc']}\n"
            f"🌡️ *Temperatura:* {clima['temp']}°C\n"
            f"🥵 *Sensación:* {clima['feels_like']}°C\n"
            f"💧 *Humedad:* {clima['humedad']}%\n"
            f"📈 *Hoy estará entre:* {clima['temp_min']}° y {clima['temp_max']}°\n\n"
            f"¡Tomen mucha agua y tengan un gran día! 🥤"
        )
        
        for chat_id in USUARIOS_AUTORIZADOS:
            try:
                # parse_mode='Markdown' permite que las negritas y emojis se vean bien
                bot.send_message(chat_id, mensaje, parse_mode='Markdown')
                print(f"✅ Enviado a {chat_id}")
            except Exception as e:
                print(f"❌ Error: {e}")

def reloj_interno():
    # Programamos que el intento sea cada hora en punto (ej: 1:00, 2:00, 3:00...)
    # Para la prueba podrías dejarlo cada minuto si quieres ver que funcione
    #schedule.every().hour.at(":00").do(validar_y_enviar)
    schedule.every(10).seconds.do(validar_y_enviar)

    while True:
        schedule.run_pending()
        time.sleep(1)

def validar_y_enviar():
    hora_actual = datetime.now().hour # Saca la hora en formato 24h (0 a 23)
    
    # Rango permitido: De las 7 AM hasta las 11 PM (23:00)
    # Esto bloquea el envío de 12:00 AM a 6:59 AM
    if 7 <= hora_actual <= 23:
        print(f"⏰ Son las {hora_actual}:00. Enviando reporte horario...")
        mandar_clima_automatico()
    else:
        print(f"😴 Son las {hora_actual}:00. Horario de descanso, no se envía nada.")
        

# --- EL CEREBRO DEL CHAT (HILO PRINCIPAL) ---
@bot.message_handler(commands=['start'])
def bienvenida(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"¡Hola! Tu ID secreto es: {chat_id}\n\nPásale este número a Felix para que te agregue a la lista del clima.")

@bot.message_handler(commands=['clima'])
def mandar_clima_manual(message):
    temp, desc = obtener_clima()
    if temp:
        bot.reply_to(message, f"🌡️ *Reporte a petición* 🌡️\nMatamoros: {temp}°C, {desc.capitalize()}")

# --- ARRANQUE DEL SISTEMA ---
if __name__ == "__main__":
    print("🤖 Iniciando Family Weather...")
    
    # 1. Prendemos el reloj en el "fondo"
    hilo_reloj = threading.Thread(target=reloj_interno, daemon=True)
    hilo_reloj.start()
    print("⏰ Reloj interno activado.")
    
    # 2. Prendemos al bot para que escuche mensajes
    print("👂 Bot escuchando mensajes...")
    bot.infinity_polling()