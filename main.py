#Este repo es un proyecto personal para aprender a crear un bot de Telegram que reporte el clima de Matamoros, Tamaulipas.
#A mi se me ocurrio la idea de crear un bot para mi familia, porque a veces me preguntan "¿Cómo va a estar hoy el dia?" 
#y pensé que sería divertido hacer un bot que les pueda responder eso automáticamente. 
#Además, es una buena oportunidad para aprender a usar APIs y a programar bots de Telegram.
#Al igual que se puede escalar y agregar más funcionalidades gracias al bot de Telegram.

import os
import requests
import telebot
from telebot import apihelper
apihelper.RETRY_ON_ERROR = True
import schedule
import time
import threading
from dotenv import load_dotenv
from datetime import datetime
import pytz

apihelper.proxy = {'https': 'http://proxy.server:3128'}
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
# 1. Cargar las llaves secretas
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

ID_FELIX = '5207047409'  # Mi ID
ID_MAMA = '8641690719'   # ID de mi mamá
ID_PAPA = '0000000000'   # ID de mi papá 

USUARIOS_AUTORIZADOS = [ID_FELIX, ID_MAMA, ID_PAPA]


# --- FUNCIONES DEL CLIMA ---
def obtener_clima():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Matamoros,Tamaulipas,MX&appid={WEATHER_API_KEY}&units=metric&lang=es"
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            
            info = {
                "temp": datos['main']['temp'],
                "feels_like": datos['main']['feels_like'], 
                "humedad": datos['main']['humidity'],      
                "desc": datos['weather'][0]['description'].capitalize(),
                "temp_max": datos['main']['temp_max'],
                "temp_min": datos['main']['temp_min']
            }
            return info
    except Exception as e:
        print(f"❌ Error al obtener clima: {e}") 
    return None

def mandar_clima_automatico():
    clima = obtener_clima()
    if not clima:
        return

    for chat_id in USUARIOS_AUTORIZADOS:
        # --- MENSAJE PARA MAMÁ ---
        if chat_id == ID_MAMA:
            saludo = "🌸 *¡Buenos días, maaa!* 🌸\nEspero que tengas un día hermoso."
            consejo = "No olvides llevar un suéter si refresca o tomar mucha agua. ✨"
        
        # --- MENSAJE PARA PAPÁ ---
        elif chat_id == ID_PAPA:
            saludo = "🕶️ *¡Qué onda, pá!* 🕶️\nAquí te paso el dato del tiempo."
            consejo = "¡Éxito en la chamba hoy! 🚀"
            
        # --- MENSAJE DEFAULT) ---
        else:
            saludo = "⚡ *¡Hey, Espero tengas buen dia!* ⚡\nAquí te dejo el reporte del clima."
            consejo = "¡A darle con todo hoy! 💪"

        # Se arma el cuerpo del mensaje (igual para todos)
        cuerpo_reporte = (
            f"\n\n🌤️ *Estado:* {clima['desc']}\n"
            f"🌡️ *Temp:* {clima['temp']}°C\n"
            f"🥵 *Sensación:* {clima['feels_like']}°C\n"
            f"💧 *Humedad:* {clima['humedad']}%\n\n"
            f"{consejo}"
        )

        mensaje_final = saludo + cuerpo_reporte

        try:
            # Si el ID es '0000000000', el bot no intentará mandar nada
            if chat_id != '0000000000':
                bot.send_message(chat_id, mensaje_final, parse_mode='Markdown')
        except Exception as e:
            print(f"No se pudo enviar a {chat_id}: {e}")


def reloj_interno():
    schedule.every().hour.at(":00").do(validar_y_enviar)
    #schedule.every(10).seconds.do(validar_y_enviar) Esto fue para testear si funcionaba, manda el mensaje cada 10 segundos

    while True:
        schedule.run_pending()
        time.sleep(1)

def validar_y_enviar():
    # Esto bloquea el envío de 12:00 AM a 6:59 AM (Esto es personal puedes modificarlos a las horas que quieras que funcione)
    zona_horaria = pytz.timezone('America/Matamoros')
    hora_actual = datetime.datetime.now(zona_horaria).hour
    
    if 7 <= hora_actual <= 23:
        mandar_clima_automatico()
    else:
        print(f"😴 Son las {hora_actual}:00. Horario de descanso, no se envía nada.")
        

# --- EL CEREBRO DEL CHAT  ---
@bot.message_handler(commands=['start'])
def bienvenida(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"¡Hola! Tu ID secreto es: {chat_id}")

@bot.message_handler(commands=['clima'])
def mandar_clima_manual(message):
    clima = obtener_clima() # Ahora recibimos TODO el diccionario
    
    if clima:
        # Aqui psss pasamos los datos al mensaje manual
        reporte = (
            f"🌡️ *REPORTE SOLICITADO* 🌡️\n\n"
            f"🌤️ *Estado:* {clima['desc']}\n"
            f"🌡️ *Temperatura:* {clima['temp']}°C\n"
            f"🥵 *Sensación:* {clima['feels_like']}°C\n"
            f"💧 *Humedad:* {clima['humedad']}%\n\n"
            f"📍 Matamoros, Tamaulipas"
        )
        bot.reply_to(message, reporte, parse_mode='Markdown')
    else:
        bot.reply_to(message, "Error al obtener el clima. Revisa la consola.")

# --- ARRANQUE DEL SISTEMA ---
if __name__ == "__main__":
    print("🤖 Iniciando Family Weather...")
    
    # 1. Prendemos el reloj en el "fondo" para las personas de la lista que se les mandara el clima cada hora
    hilo_reloj = threading.Thread(target=reloj_interno, daemon=True)
    hilo_reloj.start()
    print("⏰ Reloj interno activado.")
    
    while True:
        try:
            print("👂 Bot escuchando mensajes...")
            # Bajamos el tiempo de espera a 10s para que el servidor no se harte y nos corte
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ El servidor cortó la conexión. Reconectando en 3 segundos... Error: {e}")
            time.sleep(3)
