from pymongo import MongoClient
import hashlib
import tkinter as tk
import tkinter.messagebox
import customtkinter
from PIL import Image, ImageTk
from cryptography.fernet import Fernet
import pyotp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Configurações do email
EMAIL_REMETENTE = "lucas12akinori@gmail.com"
SENHA_REMETENTE = "gpgy wgzm cidy kwcb"

def enviar_email_2fa(email_destino, codigo):
    # Cria o conteúdo do email
    mensagem = MIMEMultipart()
    mensagem["From"] = EMAIL_REMETENTE
    mensagem["To"] = email_destino
    mensagem["Subject"] = "Seu código de verificação 2FA"

    corpo = f"Seu código de verificação é: {codigo}"
    mensagem.attach(MIMEText(corpo, "plain"))

    # Envia o email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()  # Criptografa a conexão
            servidor.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            servidor.sendmail(EMAIL_REMETENTE, email_destino, mensagem.as_string())
        print("Email enviado com sucesso!")
    except Exception as e:
        print("Erro ao enviar email:", e)

def gerar_codigo_2fa(email):
    # Gera o código de verificação para 2FA
    chave_secreta = pyotp.random_base32()
    totp = pyotp.TOTP(chave_secreta)
    codigo = totp.now()
    enviar_email_2fa(email, codigo)
    return chave_secreta

# Exemplo de uso
gerar_codigo_2fa("g.luiz.6128@gmail.com")
