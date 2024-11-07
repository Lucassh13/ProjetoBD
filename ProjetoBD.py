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
from datetime import datetime
import uuid


try:
    with open("chave.key", "rb") as chave_file:
        chave = chave_file.read()
    fernet = Fernet(chave)
except Exception as e:
    print("Erro ao carregar a chave:", e)
    exit(1)

uri = "mongodb+srv://Luquinhas:TropaDaMarketada@cluster0.miiol.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['meu_banco']
usuarios = db['usuarios']
cartao = db["cartao"]
customtkinter.set_appearance_mode("light")  
customtkinter.set_default_color_theme("green") 
EMAIL_REMETENTE = "lucas12akinori@gmail.com"
SENHA_REMETENTE = "gpgy wgzm cidy kwcb"

def gerar_hash(valor):
    hash_obj = hashlib.sha256(valor.encode())
    return hash_obj.hexdigest()

def enviar_email_2fa(email_destino, codigo):
    mensagem = MIMEMultipart()
    mensagem["From"] = EMAIL_REMETENTE
    mensagem["To"] = email_destino
    mensagem["Subject"] = "Seu código de verificação 2FA"

    corpo = f"Seu código de verificação é: {codigo}"
    mensagem.attach(MIMEText(corpo, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()  
            servidor.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            servidor.sendmail(EMAIL_REMETENTE, email_destino, mensagem.as_string())
        print("Email enviado com sucesso!")
    except Exception as e:
        print("Erro ao enviar email:", e)

def gerar_codigo_2fa(email):
    global codigo
    chave = pyotp.random_base32()
    totp = pyotp.TOTP(chave)
    codigo = totp.now()
    enviar_email_2fa(email, codigo)
    return chave

def armazenar_cartao(usuario, numero_cartao, cvv, vencimento, email):
    try:
        numero_criptografado = fernet.encrypt(numero_cartao.encode())
        cvv_criptografado = fernet.encrypt(cvv.encode())
        vencimento_criptografado = fernet.encrypt(vencimento.encode())
        print("Dados criptografados com sucesso.")
    except Exception as e:
        print("Erro ao criptografar os dados:", e)
        tkinter.messagebox.showerror("Erro", "Erro ao criptografar os dados.")
        return

    try:
        cartao.insert_one({
            'usuario': usuario, 
            "email": email,
            'numero': numero_criptografado, 
            'CVV': cvv_criptografado, 
            'vencimento': vencimento_criptografado
        })
        print("Dados armazenados no banco de dados.")
        tkinter.messagebox.showinfo("Sucesso", "Cartão armazenado com sucesso!")
    except Exception as e:
        print("Erro ao inserir dados no banco de dados:", e)
        tkinter.messagebox.showerror("Erro", "Erro ao salvar os dados no banco de dados.")

def salvarCompra(produto, valor):
    global loginAtual
    if not loginAtual:
        tkinter.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return
    
    compra = {
        "id_transacao": str(uuid.uuid4()), 
        "email": loginAtual,
        "produto": produto,
        "valor": valor,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    
    try:
      
        db['compras'].insert_one(compra)
        print("Compra salva com sucesso.")
    except Exception as e:
        print("Erro ao salvar a compra:", e)
        tkinter.messagebox.showerror("Erro", "Erro ao salvar a compra.")


def cartaoDados():
    for widget in app.winfo_children():
        widget.destroy()

    customtkinter.CTkLabel(app, text="NOME COMPLETO:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=5, sticky='e')
    global entry_nome
    entry_nome = customtkinter.CTkEntry(app, width=200, font=("Arial", 10))
    entry_nome.grid(row=0, column=1, padx=10, pady=5)

    customtkinter.CTkLabel(app, text="NUMERO DO CARTÃO:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky='e')
    global entry_cartao
    entry_cartao = customtkinter.CTkEntry(app, width=200, font=("Arial", 10))
    entry_cartao.grid(row=1, column=1, padx=10, pady=5)

    customtkinter.CTkLabel(app, text="CVV DO CARTÃO:", font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky='e')
    global cvv_var
    cvv_var = tk.StringVar()
    cvv_var.trace("w", limitar_cvv)
    global entry_cvv
    entry_cvv = customtkinter.CTkEntry(app, textvariable=cvv_var, show='*', width=200, font=("Arial", 10))
    entry_cvv.grid(row=2, column=1, padx=10, pady=5)

    customtkinter.CTkLabel(app, text="VENCIMENTO (MM/AA):", font=("Arial", 10)).grid(row=3, column=0, padx=10, pady=5, sticky='e')
    global expiry_var
    expiry_var = tk.StringVar()
    expiry_var.trace("w", formatar_vencimento) 
    global entry_expiry
    entry_expiry = customtkinter.CTkEntry(app, textvariable=expiry_var, width=200, font=("Arial", 10))
    entry_expiry.grid(row=3, column=1, padx=10, pady=5)

    def verificar_campos_vazios():
        if not entry_nome.get().strip() or not entry_cartao.get().strip() or not entry_cvv.get().strip() or not entry_expiry.get().strip():
            customtkinter.CTkMessageBox.show_error("Erro", "Todos os campos devem ser preenchidos.")
        else:
            cartaoSubmit()

    submit_button = customtkinter.CTkButton(app, text="Enviar", command=verificar_campos_vazios, fg_color="#4CAF50", font=('Arial', 10), width=150, height=40)
    submit_button.grid(row=4, column=0, columnspan=2, pady=10)

    voltar_button = customtkinter.CTkButton(app, text="Voltar", command=comprinhasTela, fg_color="#D32F2F", font=('Arial', 10), width=150, height=40)
    voltar_button.grid(row=5, column=0, columnspan=2, pady=10)



def cartaoSubmit():
    nomeCartao = entry_nome.get()
    numero_cartao = entry_cartao.get()
    cvv = entry_cvv.get()
    expiry = entry_expiry.get()

   
    armazenar_cartao(nomeCartao, numero_cartao, cvv, expiry, loginAtual)

    comprinhasTela()

def limitar_cvv(*args):
    valor = cvv_var.get()
    if len(valor) > 3:
        cvv_var.set(valor[:3])

def formatar_vencimento(*args):
    valor = expiry_var.get().replace("/", "")  
    if len(valor) > 4:
        valor = valor[:4]  
    if len(valor) > 2:
        valor = valor[:2] + '/' + valor[2:]  
    expiry_var.set(valor)

def comprinhasTela():
    for widget in app.winfo_children():
        widget.destroy()  

    
    imagem_coca = Image.open("images.jpg").resize((150, 150), Image.LANCZOS)
    img_coca = ImageTk.PhotoImage(imagem_coca)
    label_imagem = tk.Label(app, image=img_coca)
    label_imagem.image = img_coca
    label_imagem.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    label_descricao = customtkinter.CTkLabel(app, text=("Lamborghini"), font=("Arial", 16))
    label_explica = customtkinter.CTkLabel(app, text=("Somente um por usuário\nPreço: R$ 2.700.000,00"), font=("Arial", 12))
    label_descricao.grid(row=1, column=1, padx=15, pady=(0, 25), sticky="w")
    label_explica.grid(row=1, column=1, padx=15, pady=(25, 0), sticky="w")
    
    botao_comprar_carrão = customtkinter.CTkButton(app, text="Comprar", width=200, command=escolherCartao)
    botao_comprar_carrão.grid(row=2, column=1, padx=10, pady=(10, 0), sticky="w")
    
    sucesso = usuarios.find_one({"email": loginAtual}, {"produto1": 1, "_id": 0})
    sucesso = sucesso.get("produto1")
    
    if sucesso: 
        label_sucesso = customtkinter.CTkLabel(app, text="Compra efetuada com sucesso!", font=("Arial", 12), text_color="green")
        label_sucesso.grid(row=3, column=1, padx=10, pady=(20, 0), sticky="w")
    
    
    imagem_amg = Image.open("G63 AMG.jpg").resize((150, 150), Image.LANCZOS)
    img_amg1 = ImageTk.PhotoImage(imagem_amg)
    label_imagem1 = tk.Label(app, image=img_amg1)
    label_imagem1.image = img_amg1
    label_imagem1.grid(row=5, column=0, padx=10, pady=10, sticky="e")

    label_descricao1 = customtkinter.CTkLabel(app, text=("AMG G63"), font=("Arial", 16))
    label_explica1 = customtkinter.CTkLabel(app, text=("Somente um por usuário\nPreço: R$ 2.700.000,00"), font=("Arial", 12))
    label_descricao1.grid(row=5, column=1, padx=15, pady=(0, 25), sticky="w")
    label_explica1.grid(row=5, column=1, padx=15, pady=(25, 0), sticky="w")
    
    botao_comprar_amg = customtkinter.CTkButton(app, text="Comprar", width=200, command=escolherCartao)
    botao_comprar_amg.grid(row=6, column=1, padx=10, pady=(10, 0), sticky="w")
    
    
    botao_historico_amg = customtkinter.CTkButton(app, text="Histórico de Compras", command=historicoCompras)
    botao_historico_amg.grid(row=7, column=1, padx=10, pady=(10, 0), sticky="w")
    
    sucesso1 = usuarios.find_one({"email": loginAtual}, {"produto2": 2, "_id": 1})
    sucesso1 = sucesso1.get("produto2")
    
    if sucesso1:  
        label_sucesso1 = customtkinter.CTkLabel(app, text="Compra efetuada com sucesso!", font=("Arial", 12), text_color="green")
        label_sucesso1.grid(row=8, column=1, padx=10, pady=(20, 0), sticky="w")

    
    voltarLogin = customtkinter.CTkButton(app, text="VOLTAR", font=("Arial", 12), command=loginDados)
    voltarLogin.grid(row=0, column=0, padx=(0, 50), pady=(0, 10), sticky="e")



def cartoesSalvos():
    global loginAtual
    if not loginAtual:
        tkinter.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return
   
    cartoes = list(cartao.find({"email": loginAtual}))

    if not cartoes:
        tkinter.messagebox.showinfo("Informação", "Nenhum cartão salvo.")
        cartaoDados()
        return

    if cartoes:
        escolherCartao()
        return

def loginDados():
    for widget in app.winfo_children():
        widget.destroy()

    customtkinter.CTkLabel(app, text="E-MAIL DE LOGIN:", font=("Arial", 10)).grid(row=0, column=0, pady=(0, 0), sticky='e')
    
    global entry_login
    entry_login = customtkinter.CTkEntry(app, width=200, font=("Arial", 10))
    entry_login.grid(row=0, column=1, pady=(0, 0))
    
    customtkinter.CTkLabel(app, text="SENHA:", font=("Arial", 10)).grid(row=0, column=0, pady=(75, 0), sticky="e")
    
    global entry_senhaLogin
    entry_senhaLogin = customtkinter.CTkEntry(app, show="*", width=200, font=("Arial", 10))
    entry_senhaLogin.grid(row=0, column=1, pady=(75, 0))

    mostrar_senha_checkbox = customtkinter.CTkCheckBox(app, text='MOSTRAR', command=agreement_changed, variable=mostrarSenha, onvalue=1, offvalue=0)
    mostrar_senha_checkbox.grid(row=0, column=2, padx=10, pady=(75, 0))
    
    submit_button = customtkinter.CTkButton(app, text="Enviar", command=submitLogin, font=('Arial', 10), width=150, height=40)
    submit_button.grid(row=1, column=0, columnspan=4, pady=10, padx=(0, 30))

    registra_button = customtkinter.CTkButton(app, text="Registrar-se", command=registrarLogin, fg_color="#6600ff", font=('Arial', 12), width=75, height=40)
    registra_button.grid(row=1, column=2, columnspan=4, pady=10)

def agreement_changed():  
    if mostrarSenha.get() == 0:
        entry_senhaLogin.configure(show="*")
    else:
        entry_senhaLogin.configure(show="")

def submitLogin():
    global loginAtual
    usuario = usuarios.find_one({"email": entry_login.get(), "senha": gerar_hash(entry_senhaLogin.get()) })
    loginAtual = entry_login.get()
    if usuario:
        confirmar2FA()
        gerar_codigo_2fa(loginAtual)
    else:
        tkinter.messagebox.showinfo("ERRO", "EMAIL OU SENHA INCORRETOS")

def registrarLogin():
    for widget in app.winfo_children():
        widget.destroy()

    customtkinter.CTkLabel(app, text="E-MAIL:", font=("Arial", 10)).grid(row=0, column=0, pady=(0, 75), sticky='e')
    global entry_email
    entry_email = customtkinter.CTkEntry(app, width=200, font=("Arial", 10))
    entry_email.grid(row=0, column=1, pady=(0, 75))

    customtkinter.CTkLabel(app, text="SENHA:", font=("Arial", 10)).grid(row=0, column=0, pady=(0, 0), sticky='e')
    global entry_senha
    entry_senha = customtkinter.CTkEntry(app, show="*", width=200, font=("Arial", 10))
    entry_senha.grid(row=0, column=1, pady=(0, 0))

    customtkinter.CTkLabel(app, text="CONFIRME A SENHA:", font=("Arial", 10)).grid(row=0, column=0, pady=(75, 0), sticky='e')
    global entry_senha_confirma
    entry_senha_confirma = customtkinter.CTkEntry(app, show="*", width=200, font=("Arial", 10))
    entry_senha_confirma.grid(row=0, column=1, pady=(75, 0))

    register_button = customtkinter.CTkButton(app, text="Registrar", command=submitRegistro, fg_color="#4CAF50", font=('Arial', 10), width=150, height=40)
    register_button.grid(row=1, column=0, columnspan=2, pady=10)
    voltar_button = customtkinter.CTkButton(app, text="Voltar", command=loginDados, fg_color="#D32F2F", font=('Arial', 10), width=150, height=40)
    voltar_button.grid(row=5, column=0, columnspan=2, pady=10)



def submitRegistro():
    email = entry_email.get()
    senha = entry_senha.get()
    senha_confirma = entry_senha_confirma.get()
    if senha != senha_confirma:
        tkinter.messagebox.showinfo("ERRO", "AS SENHAS NÃO COINCIDEM")
        return
    if len(senha) <5:
        tkinter.messagebox.showinfo("ERRO", "A SENHA DEVE POSSUIR NO MINIMO 5 CARACTERES")
        return
    if not email or "@" not in email:
        tkinter.messagebox.showinfo("ERRO", "INSIRA UM E-MAIL VÁLIDO")
        return
    if usuarios.find_one({"email": email}):
        tkinter.messagebox.showinfo("ERRO", "E-MAIL JÁ REGISTRADO")
        return
    senha_hash = gerar_hash(senha)
    usuarios.insert_one({"email":email, "senha":senha_hash,"produto1":False})
    loginDados()
def confirmar2FA():
    global loginAtual
    global chave
    if not loginAtual:
        tkinter.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return
    app_x = app.winfo_x()
    app_y = app.winfo_y()
    app_width = app.winfo_width()
    global FA_janela
    FA_janela = customtkinter.CTkToplevel(app)
    FA_janela.title("Autenticação de 2 fatores:")
    FA_janela.geometry(f"300x200+{app_x + app_width + 20}+{app_y}")  
    customtkinter.CTkLabel(FA_janela,text="Código:",font=("Arial",12)).pack(pady=10)
    global entry_chave
    entry_chave = customtkinter.CTkEntry(FA_janela)
    entry_chave.pack(pady=20)
    customtkinter.CTkButton(FA_janela,text="CONFIRMAR",command=testarCod).pack(pady=30)
   
def testarCod():
     chaveuser = entry_chave.get().strip()  
     print(codigo)
     print(chaveuser)
   
     if codigo == chaveuser:
        FA_janela.destroy()
        comprinhasTela()
     else:
        tkinter.messagebox.showwarning("ERRO", "DIGITE O CÓDIGO CORRETO!")

def historicoCompras():
    global loginAtual
    if not loginAtual:
        tkinter.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return

    app_x = app.winfo_x()
    app_y = app.winfo_y()
    app_width = app.winfo_width()

    historico_janela = customtkinter.CTkToplevel(app)
    historico_janela.title("Histórico de Compras")
    historico_janela.geometry(f"400x400+{app_x + app_width + 20}+{app_y}")
    
    customtkinter.CTkLabel(historico_janela, text="Histórico de Compras", font=("Arial", 14)).pack(pady=10)


    compras = list(db['compras'].find({"email": loginAtual}))

    if not compras:
        customtkinter.CTkLabel(historico_janela, text="Nenhuma compra encontrada.", font=("Arial", 12)).pack(pady=20)
    else:
        for compra in compras:
            produto = compra.get("produto", "Produto não especificado")
            data = compra.get("data", "Data não especificada")
            valor = compra.get("valor", "Valor não especificado")
            id_transacao = compra.get("id_transacao", "ID não disponível")
            
       
            texto_compra = f"ID da Transação: {id_transacao}\nProduto: {produto}\nData: {data}\nValor: {valor}\n"
            customtkinter.CTkLabel(historico_janela, text=texto_compra, font=("Arial", 10), anchor="w", justify="left").pack(pady=5)


def escolherCartao():
    global loginAtual
    if not loginAtual:
        tkinter.messagebox.showinfo("Erro", "Usuário não autenticado.")
        return

    app_x = app.winfo_x()
    app_y = app.winfo_y()
    app_width = app.winfo_width()
    
    escolha_cartao_janela = customtkinter.CTkToplevel(app)
    escolha_cartao_janela.title("Escolha um Cartão")
    escolha_cartao_janela.geometry(f"400x400+{app_x + app_width + 20}+{app_y}")  

    try:

        cartoes = list(cartao.find({"email": loginAtual}))

        if not cartoes:
            tkinter.messagebox.showinfo("Informação", "Nenhum cartão salvo.")
            escolha_cartao_janela.destroy()
            cartaoDados()
            return

        customtkinter.CTkLabel(escolha_cartao_janela, text="Selecione um cartão:", font=("Arial", 12)).pack(pady=10)
        novoCartao = customtkinter.CTkButton(escolha_cartao_janela, text="Adicionar novo cartão", font=("Arial", 10), command=cartaoDados)
        novoCartao.pack(pady=0)
        
        for i, cartao_salvo in enumerate(cartoes):
            try:
             
                numero_cartao = fernet.decrypt(cartao_salvo["numero"]).decode()
                numero_final = numero_cartao[-4:]
                vencimento = fernet.decrypt(cartao_salvo["vencimento"]).decode()

                cartao_texto = f"Cartão **** **** **** {numero_final} - Vencimento: {vencimento}"

                frame_cartao = customtkinter.CTkFrame(escolha_cartao_janela)
                frame_cartao.pack(pady=5, fill="x", padx=10)

                botao_cartao = customtkinter.CTkButton(
                    frame_cartao, text=cartao_texto, font=("Arial", 10), width=250,
                    command=lambda: confirmarCompra(escolha_cartao_janela)
                )
                botao_cartao.pack(side="left", padx=5)

                botao_remover = customtkinter.CTkButton(
                    frame_cartao, text="X", fg_color="red", font=("Arial", 10), width=40,
                    command=lambda c=cartao_salvo["_id"]: removerCartao(c, frame_cartao)
                )
                botao_remover.pack(side="right", padx=5)

            except Exception as e:
                print(f"Erro ao descriptografar o cartão {i+1}:", e)

    except Exception as e:
        print("Erro ao recuperar os cartões:", e)
        tkinter.messagebox.showerror("Erro", "Erro ao recuperar os cartões.")

def removerCartao(cartao_id, frame_cartao):
    try:
        cartao.delete_one({"_id": cartao_id})
        frame_cartao.destroy()  
        tkinter.messagebox.showinfo("Cartão Removido", "O cartão foi removido com sucesso.")
    except Exception as e:
        print("Erro ao remover o cartão:", e)
        tkinter.messagebox.showerror("Erro", "Erro ao remover o cartão.")


def confirmarCompra(janela):
    salvarCompra("Lamborghini", "R$ 3.000.000,00")
    janela.destroy()
    usuarios.update_one({"email": loginAtual}, {"$set": {"produto1": True}})
    comprinhasTela()
    salvarCompra("AMG G63", "R$ 2.700.000,00")
    janela.destroy()
    usuarios.update_one({"email": loginAtual}, {"$set": {"produto2": True}})
    comprinhasTela()

def selecionarCartao(cartao_salvo):
    
    numero_cartao = fernet.decrypt(cartao_salvo["numero"]).decode()
    numero_final = numero_cartao[-4:]
    vencimento = fernet.decrypt(cartao_salvo["vencimento"]).decode()
    tkinter.messagebox.showinfo("Cartão Selecionado", f"Cartão **** **** **** {numero_final} - Vencimento: {vencimento}")
           
     

app = customtkinter.CTk()
app.title("PROJETO DE BANCO DE DADOS ❤")
app.geometry("400x400")

for i in range(5):
    app.grid_rowconfigure(i, weight=1)
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=3)

mostrarSenha = tk.IntVar(value=0)
qtd_doritos = 0
qtd_coca = 0
loginDados()
app.mainloop()
