from asyncio.windows_events import NULL
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import pyodbc
from sqlalchemy.orm import aliased
from functools import wraps
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyodbc
import time
from datetime import datetime
import re
from selenium.webdriver.chrome.options import Options
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'Ccgls1021#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://sa:VisaHouse012345@LAPTOP-8VC0L6D2/VISTOAMERICANO?driver=ODBC+Driver+17+for+SQL+Server'
db = SQLAlchemy(app)

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'tcc-exemplo-ufsc@outlook.com'
app.config['MAIL_PASSWORD'] = 'VH012345'
app.config['MAIL_DEFAULT_SENDER'] = 'tcc-exemplo-ufsc@outlook.comm'

mail = Mail(app)


# Pasta para salvar os arquivos enviados
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuração da conexão com o banco de dados
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-8VC0L6D2;'
    'DATABASE=VISTOAMERICANO;'
    'UID=sa;'
    'PWD=VisaHouse012345'
)

class Assessor(db.Model):
    __tablename__ = 'TB_ASSESSORES'
    ID_ASSESSOR = db.Column(db.Integer, primary_key=True)
    NOME = db.Column(db.String(40), nullable=False)
    LOGIN = db.Column(db.String(20), nullable=False)
    SENHA = db.Column(db.String(10), nullable=False)
    EMAIL = db.Column(db.String(40))
    ADMINISTRADOR = db.Column(db.Boolean, nullable=False)

class Cliente(db.Model):
    __tablename__ = 'TB_CLIENTES'
    ID_CLIENTE = db.Column(db.Integer, primary_key=True)
    NOME = db.Column(db.String(40), nullable=False)
    ID_ASSESSOR = db.Column(db.Integer, db.ForeignKey('TB_ASSESSORES.ID_ASSESSOR'), nullable=False)
    ID_CONTATO = db.Column(db.Integer, nullable=True)
    EMAIL = db.Column(db.String(40), nullable=True)
    SENHA = db.Column(db.String(10), nullable=False)
    DS160 = db.Column(db.String(10), nullable=True)
    ID_AISVISA = db.Column(db.String(50), nullable=True)
    AGENDAMENTO_CASV = db.Column(db.DateTime, nullable=True)
    CIDADE_CASV = db.Column(db.Integer, nullable=True)
    AGENDAMENTO_CONSULAR = db.Column(db.DateTime, nullable=True)
    CIDADE_CONSULAR = db.Column(db.Integer, nullable=True)

class Contato(db.Model):
    __tablename__ = 'TB_CONTATO'
    ID_CONTATO = db.Column(db.Integer, primary_key=True)
    NOME_CONTATO = db.Column(db.String(20), nullable=True)
    TEL_CONTATO = db.Column(db.Integer, nullable=True)

@app.route('/')
def index():
    return render_template('login.html')

# Verifica se é o administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        senha = request.form['senha']

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM TB_ASSESSORES WHERE LOGIN = ? AND SENHA = ?", (login, senha))
        assessor = cursor.fetchone()

        if assessor:
            session['logged_in'] = True
            session['user_id'] = assessor.ID_ASSESSOR
            session['user_name'] = assessor.NOME
            session['is_admin'] = assessor.ADMINISTRADOR
            return redirect(url_for('dashboard'))
        else:
            flash('Login ou senha incorretos')
            return redirect(url_for('index'))


    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor()
    query = """
        SELECT 
            C.ID_CLIENTE, C.NOME, A.NOME AS NOME_ASSESSOR, CO.NOME_CONTATO, CO.TEL_CONTATO, C.EMAIL,
            C.SENHA, C.DS160, C.ID_AISVISA, C.AGENDAMENTO_CASV, CIDADE_CASV.CIDADE AS CIDADE_CASV,
            C.AGENDAMENTO_CONSULAR, CIDADE_CONSULAR.CIDADE AS CIDADE_CONSULAR
        FROM 
            TB_CLIENTES C
            JOIN TB_ASSESSORES A ON C.ID_ASSESSOR = A.ID_ASSESSOR
            LEFT JOIN TB_CONTATO CO ON C.ID_CONTATO = CO.ID_CONTATO
            LEFT JOIN TB_CIDADE CIDADE_CASV ON C.CIDADE_CASV = CIDADE_CASV.ID_CIDADE
            LEFT JOIN TB_CIDADE CIDADE_CONSULAR ON C.CIDADE_CONSULAR = CIDADE_CONSULAR.ID_CIDADE
    """
    cursor.execute(query)
    clientes = cursor.fetchall()

    return render_template('dashboard.html', clientes=clientes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/refresh')
def refresh():
    return redirect(url_for('dashboard'))

@app.route('/sort/<criteria>')
def sort(criteria):
    # Ordena por nome
    if criteria == 'nome':
        cursor = conn.cursor()
        query = """
            SELECT 
                C.ID_CLIENTE, C.NOME, A.NOME AS NOME_ASSESSOR, CO.NOME_CONTATO, CO.TEL_CONTATO, C.EMAIL,
                C.SENHA, C.DS160, C.ID_AISVISA, C.AGENDAMENTO_CASV, CIDADE_CASV.CIDADE AS CIDADE_CASV,
                C.AGENDAMENTO_CONSULAR, CIDADE_CONSULAR.CIDADE AS CIDADE_CONSULAR
            FROM 
                TB_CLIENTES C
                JOIN TB_ASSESSORES A ON C.ID_ASSESSOR = A.ID_ASSESSOR
                LEFT JOIN TB_CONTATO CO ON C.ID_CONTATO = CO.ID_CONTATO
                LEFT JOIN TB_CIDADE CIDADE_CASV ON C.CIDADE_CASV = CIDADE_CASV.ID_CIDADE
                LEFT JOIN TB_CIDADE CIDADE_CONSULAR ON C.CIDADE_CONSULAR = CIDADE_CONSULAR.ID_CIDADE ORDER BY C.NOME

        """
        cursor.execute(query)
        clientes = cursor.fetchall()
    elif criteria == 'casv':
        # Ordena por agendamento na CASV
        cursor = conn.cursor()
        query = """
            SELECT 
                C.ID_CLIENTE, C.NOME, A.NOME AS NOME_ASSESSOR, CO.NOME_CONTATO, CO.TEL_CONTATO, C.EMAIL,
                C.SENHA, C.DS160, C.ID_AISVISA, C.AGENDAMENTO_CASV, CIDADE_CASV.CIDADE AS CIDADE_CASV,
                C.AGENDAMENTO_CONSULAR, CIDADE_CONSULAR.CIDADE AS CIDADE_CONSULAR
            FROM 
                TB_CLIENTES C
                JOIN TB_ASSESSORES A ON C.ID_ASSESSOR = A.ID_ASSESSOR
                LEFT JOIN TB_CONTATO CO ON C.ID_CONTATO = CO.ID_CONTATO
                LEFT JOIN TB_CIDADE CIDADE_CASV ON C.CIDADE_CASV = CIDADE_CASV.ID_CIDADE
                LEFT JOIN TB_CIDADE CIDADE_CONSULAR ON C.CIDADE_CONSULAR = CIDADE_CONSULAR.ID_CIDADE ORDER BY C.AGENDAMENTO_CASV

        """
        cursor.execute(query)
        clientes = cursor.fetchall()
    else:
        cursor = conn.cursor()
        # Ordena por agendamento no consulado
        query = """
            SELECT 
                C.ID_CLIENTE, C.NOME, A.NOME AS NOME_ASSESSOR, CO.NOME_CONTATO, CO.TEL_CONTATO, C.EMAIL,
                C.SENHA, C.DS160, C.ID_AISVISA, C.AGENDAMENTO_CASV, CIDADE_CASV.CIDADE AS CIDADE_CASV,
                C.AGENDAMENTO_CONSULAR, CIDADE_CONSULAR.CIDADE AS CIDADE_CONSULAR
            FROM 
                TB_CLIENTES C
                JOIN TB_ASSESSORES A ON C.ID_ASSESSOR = A.ID_ASSESSOR
                LEFT JOIN TB_CONTATO CO ON C.ID_CONTATO = CO.ID_CONTATO
                LEFT JOIN TB_CIDADE CIDADE_CASV ON C.CIDADE_CASV = CIDADE_CASV.ID_CIDADE
                LEFT JOIN TB_CIDADE CIDADE_CONSULAR ON C.CIDADE_CONSULAR = CIDADE_CONSULAR.ID_CIDADE ORDER BY C.AGENDAMENTO_CONSULAR

        """
        cursor.execute(query)
        clientes = cursor.fetchall()
    return render_template('dashboard.html', clientes=clientes)

# Recuperação de Senha
@app.route('/recover_password', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        email = request.form['email']
        assessor = conn.execute('SELECT * FROM TB_ASSESSORES WHERE EMAIL = ?', (email,)).fetchone()
        if assessor:
            return render_template('assessor_details.html', assessor=assessor)
        else:
            flash('Email não encontrado.')
    return render_template('recover_password.html')

# Atualização de Cliente
@app.route('/update-client', methods=['GET', 'POST'])
def update_client():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    if request.method == 'POST':
        selected_name = request.form.get('selected_name')
        cursor.execute("SELECT * FROM TB_CLIENTES WHERE NOME = ?", selected_name)
        cliente = cursor.fetchone()
        
        cursor.execute("SELECT * FROM TB_CONTATO WHERE ID_CONTATO = ?", cliente.ID_CONTATO)
        contato = cursor.fetchone()

        return render_template('update_client.html', cliente=cliente, contato=contato)

    cursor.execute("SELECT NOME FROM TB_CLIENTES ORDER BY NOME")
    clientes = cursor.fetchall()
    return render_template('select_client.html', clientes=clientes)

# Salva a atualização do cliente
@app.route('/save-client', methods=['POST'])
def save_client():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    cliente_id = request.form.get('ID_CLIENTE')
    nome = request.form.get('NOME')
    email = request.form.get('EMAIL')
    senha = request.form.get('SENHA')
    nome_contato = request.form.get('NOME_CONTATO')
    tel_contato = request.form.get('TEL_CONTATO')
    ds160 = request.form['DS160'] if request.form['DS160'] else None

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE TB_CLIENTES
        SET NOME = ?, EMAIL = ?, SENHA = ?, DS160 = ?
        WHERE ID_CLIENTE = ?
    """, (nome, email, senha, ds160, cliente_id))
    
    cursor.execute("""
        UPDATE TB_CONTATO
        SET NOME_CONTATO = ?, TEL_CONTATO = ?
        WHERE ID_CONTATO = (SELECT ID_CONTATO FROM TB_CLIENTES WHERE ID_CLIENTE = ?)
    """, (nome_contato, tel_contato, cliente_id))
    
    conn.commit()

    return redirect(url_for('dashboard'))

# Criação de um novo cliente
@app.route('/add-client', methods=['GET', 'POST'])
def add_client():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['NOME']
        email = request.form['EMAIL']
        senha = request.form['SENHA']
        nome_contato = request.form['NOME_CONTATO']
        tel_contato = request.form['TEL_CONTATO']
        ds160 = request.form['DS160'] if request.form['DS160'] else NULL

        # Obtém o ID do assessor logado
        id_assessor = session['user_id']

        cursor = conn.cursor()

        # Verifica se o contato já existe
        cursor.execute("SELECT ID_CONTATO FROM TB_CONTATO WHERE TEL_CONTATO = ?", tel_contato)
        row = cursor.fetchone()

        if row:
            id_contato = row[0]
        else:
            # Insere um novo contato se não existir
            cursor.execute("INSERT INTO TB_CONTATO (NOME_CONTATO, TEL_CONTATO) OUTPUT INSERTED.ID_CONTATO VALUES (?, ?)", (nome_contato, tel_contato))
            id_contato = cursor.fetchone()[0]
            conn.commit()

        # Insere um novo cliente
        cursor.execute("INSERT INTO TB_CLIENTES (NOME, EMAIL, SENHA, ID_ASSESSOR, ID_CONTATO, DS160) VALUES (?, ?, ?, ?, ?, ?)",
                       (nome, email, senha, id_assessor, id_contato, ds160))
        conn.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_client.html')

# Deleta um cliente
@app.route('/delete_client', methods=['POST'])
def delete_client():   
    if 'user_name' not in session:
        return redirect(url_for('login'))
    client_id = request.form.get('selected_name')
    client = Cliente.query.get(client_id)
    
    cursor = conn.cursor()
    
    if client:
        # Excluir o pagamento do cliente na TB_PAGAMENTOS
        cursor.execute("DELETE FROM TB_PAGAMENTOS WHERE ID_CLIENTE = ?", (client_id))
        
        # Excluir o cliente na TB_CLIENTES
        cursor.execute("DELETE FROM TB_CLIENTES WHERE ID_CLIENTE = ?", (client_id))
        db.session.commit()
        conn.commit()
    else:
        flash('Cliente não encontrado')
    
    return redirect(url_for('dashboard'))

# Atualizações da informação de um Assessor
@app.route('/update_assessor')
def update_assessor():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    assessor = Assessor.query.get(session['user_id'])
    return render_template('update_assessor.html', assessor=assessor)

# Salva atualizações do assessor
@app.route('/save_assessor', methods=['POST'])
def save_assessor():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    assessor = Assessor.query.get(session['user_id'])
    assessor.NOME = request.form['NOME']
    assessor.LOGIN = request.form['LOGIN']
    assessor.EMAIL = request.form['EMAIL']
    assessor.SENHA = request.form['SENHA']
    
    db.session.commit()
    flash('Informações atualizadas com sucesso')
    return redirect(url_for('dashboard'))

# Cria um novo assessor (Apenas o administrador pode realizar)
@app.route('/add-assessor', methods=['GET', 'POST'])
@admin_required
def add_assessor():
    if request.method == 'POST':
        nome = request.form['NOME']
        login = request.form['LOGIN']
        senha = request.form['SENHA']
        email = request.form['EMAIL']
        administrador = request.form.get('ADMINISTRADOR') == 'on'

        cursor = conn.cursor()

        # Insere novo assessor
        cursor.execute("INSERT INTO TB_ASSESSORES (NOME, LOGIN, SENHA, EMAIL, ADMINISTRADOR) VALUES (?, ?, ?, ?, ?)",
                       (nome, login, senha, email, administrador))
        conn.commit()

        return redirect(url_for('dashboard'))

    return render_template('add_assessor.html')

# Deleta um assessor (Apenas o administrador pode realizar)
@app.route('/delete-assessor', methods=['GET', 'POST'])
@admin_required
def delete_assessor():
    if 'user_name' not in session:
        return redirect(url_for('login'))
    
    cursor = conn.cursor()

    if request.method == 'POST':
        assessor_id_now = session['user_id']
        
        assessor_id = request.form['assessor_id']
        
        cursor.execute("UPDATE TB_PAGAMENTOS SET ID_ASSESSOR = ? WHERE ID_ASSESSOR = ?", (assessor_id_now, assessor_id))

        cursor.execute("DELETE FROM TB_ASSESSORES WHERE ID_ASSESSOR = ?", (assessor_id))
        conn.commit()

        return redirect(url_for('dashboard'))

    cursor.execute("SELECT ID_ASSESSOR, NOME FROM TB_ASSESSORES WHERE LOGIN != ? AND ADMINISTRADOR = 0", (session['user_name'],))
    assessores = cursor.fetchall()

    return render_template('delete_assessor.html', assessores=assessores)

# Gerenciamento de Pagamentos
@app.route('/manage-payments', methods=['GET', 'POST'])
def manage_payments():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form['action']
        client_id = request.form['client_id']

        # Get assessor ID from session login
        assessor_id = session['user_id']
        
        valor_pago = float(request.form['valor_pago'])
        valor_cobrado = float(request.form['valor_cobrado'])

        if valor_pago > valor_cobrado:
                flash('Valor pago não pode ser maior que o valor cobrado.', 'danger')
        else:
            if action == 'create':
                valor_pago = request.form['valor_pago']
                valor_cobrado = request.form['valor_cobrado']

                # Check if payment already exists for this client
                cursor.execute("SELECT COUNT(*) FROM TB_PAGAMENTOS WHERE ID_CLIENTE = ?", (client_id,))
                if cursor.fetchone()[0] > 0:
                    flash('Já existe um pagamento para este cliente.', 'danger')
                else:
                    # Insert new payment
                    cursor.execute("""
                        INSERT INTO TB_PAGAMENTOS (ID_CLIENTE, ID_ASSESSOR, VALOR_PAGO, VALOR_COBRADO)
                        VALUES (?, ?, ?, ?)
                    """, (client_id, assessor_id, valor_pago, valor_cobrado))
                    conn.commit()
                    flash('Pagamento criado com sucesso.', 'success')
            elif action == 'update':
                cursor.execute("SELECT * FROM TB_PAGAMENTOS WHERE ID_CLIENTE = ?", (client_id))
                payment = cursor.fetchone()

                if not payment:
                    flash('Não existe pagamento para este cliente.', 'danger')
                else:
                    valor_pago = request.form['valor_pago']
                    valor_cobrado = request.form['valor_cobrado']
                    
                    # Update payment
                    cursor.execute("""
                        UPDATE TB_PAGAMENTOS
                        SET VALOR_PAGO = ?, VALOR_COBRADO = ?, ID_ASSESSOR = ?
                        WHERE ID_CLIENTE = ?
                    """, (valor_pago, valor_cobrado, assessor_id, client_id))
                    conn.commit()
                    flash('Pagamento atualizado com sucesso.', 'success')

    cursor.execute("SELECT ID_CLIENTE, NOME FROM TB_CLIENTES")
    clients = cursor.fetchall()

    return render_template('manage_payments.html', clients=clients)

# Obtem pagamentos existentes
@app.route('/get-payment-info/<int:client_id>', methods=['GET'])
def get_payment_info(client_id):
    if 'user_name' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    cursor.execute("SELECT VALOR_PAGO, VALOR_COBRADO, ID_ASSESSOR FROM TB_PAGAMENTOS WHERE ID_CLIENTE = ?", (client_id,))
    payment = cursor.fetchone()

    if payment:
        assessor_saved = payment.ID_ASSESSOR
        cursor.execute("SELECT NOME FROM TB_ASSESSORES WHERE ID_ASSESSOR = ?", (assessor_saved,))
        assessor_details = cursor.fetchone()
        return {
            'exists': True,
            'valor_pago': payment.VALOR_PAGO,
            'valor_cobrado': payment.VALOR_COBRADO,
            'nome_assessor': assessor_details.NOME
        }
    else:
        return {'exists': False}
 
 # Atualiza os agendamentos   
def login_and_capture_info():
    cursor = conn.cursor()

    # Recupera todos os clientes e suas credenciais de login
    cursor.execute("SELECT EMAIL, SENHA FROM TB_CLIENTES")
    clientes = cursor.fetchall()

    # Configura o navegador (nesse exemplo, usando Chrome)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    
    # código para capturar as informações
    for cliente in clientes:
        email = cliente.EMAIL.strip()
        senha = cliente.SENHA.strip()

        # Abre o site
        driver.get("https://ais.usvisa-info.com/en-br/niv/users/sign_in")

        # Aguarda até que os campos de login estejam presentes
        time.sleep(5)

        # Preenche o campo de email
        email_field = driver.find_element(By.ID, "user_email")
        email_field.clear()
        email_field.send_keys(email)

        # Preenche o campo de senha
        password_field = driver.find_element(By.ID, "user_password")
        password_field.clear()
        password_field.send_keys(senha)
        
        # Clicking the checkbox
        driver.find_element(By.XPATH, '//*[@id="sign_in_form"]/div[3]/label/div').click()
        
        # Aguarda processamento
        time.sleep(2)

        # Submete o formulário
        login_button = driver.find_element(By.NAME, "commit")
        login_button.click()

        # Aguarda até que a página de login seja processada
        time.sleep(5)

        # Captura as informações de agendamento
        try:
            consular_appt = driver.find_element(By.CSS_SELECTOR, ".card .consular-appt").text
            casv_appt = driver.find_element(By.CSS_SELECTOR, ".card .asc-appt").text
            
            print(f"{consular_appt}")
            print(f"{casv_appt}")

            # Expressão regular para extrair data, hora e cidade do agendamento consular
            consular_pattern = re.compile(r"(\d{2} \w+, \d{4}), (\d{2}:\d{2}) (.+?) -")
            consular_match = consular_pattern.search(consular_appt)
            if consular_match:
                consular_date = consular_match.group(1)
                consular_time = consular_match.group(2)
                consular_city = consular_match.group(3)

                # Converte a data e hora para datetime SQL
                consular_datetime = datetime.strptime(f"{consular_date} {consular_time}", "%d %B, %Y %H:%M")
                
                consular_city_id = get_city_id(cursor, consular_city)
                
                print(consular_datetime)

                print(f"Agendamento Consular: Data - {consular_date}, Hora - {consular_time}, Cidade - {consular_city}")


            # Expressão regular para extrair data, hora e cidade do agendamento CASV
            casv_pattern = re.compile(r"(\d{2} \w+, \d{4}), (\d{2}:\d{2}) (.+?) local time")
            casv_match = casv_pattern.search(casv_appt)
            if casv_match:
                casv_date = casv_match.group(1)
                casv_time = casv_match.group(2)
                casv_city = casv_match.group(3)

                # Converte a data e hora para datetime SQL
                casv_datetime = datetime.strptime(f"{casv_date} {casv_time}", "%d %B, %Y %H:%M")
                
                if casv_city == "Sao Paulo" :
                    casv_city = "São Paulo"
                
                casv_city_id = get_city_id(cursor, casv_city)
                
                print(casv_datetime)

                print(f"Agendamento CASV: Data - {casv_date}, Hora - {casv_time}, Cidade - {casv_city}")

            # Atualiza a tabela no banco de dados com as informações capturadas
            cursor.execute("""
                UPDATE TB_CLIENTES
                SET AGENDAMENTO_CONSULAR = ?, CIDADE_CONSULAR = ?, AGENDAMENTO_CASV = ?, CIDADE_CASV = ?
                WHERE EMAIL = ?
            """, (consular_datetime, consular_city_id, casv_datetime, casv_city_id, email))
            conn.commit()

        except Exception as e:
            print(f"Erro ao capturar informações: {e}")

        # Volta para a página de login para o próximo cliente
        driver.get("https://ais.usvisa-info.com/en-br/niv/users/sign_in")
        time.sleep(5)

    # Fecha o navegador
    driver.quit()

# Função Flask para o botão atualizar
@app.route('/update', methods=['GET'])
def update():
    success = login_and_capture_info()
    if success:
        flash('Informações atualizadas com sucesso.', 'success')
    else:
        flash('Erro ao atualizar informações.', 'danger')
    return redirect(url_for('dashboard'))


# Função para obter o ID da cidade
def get_city_id(cursor, city_name):
    cursor.execute("SELECT ID_CIDADE FROM TB_CIDADE WHERE CIDADE = ?", (city_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

# Funcao para enviar um email
@app.route('/send_email', methods=['GET', 'POST'])
def send_email():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor()

    # Recupera todos os clientes
    cursor.execute("SELECT ID_CLIENTE, NOME, EMAIL FROM TB_CLIENTES")
    clients = cursor.fetchall()

    # Converte objetos Row para dicionários
    clients_list = []
    for client in clients:
        clients_list.append({
            'ID_CLIENTE': client.ID_CLIENTE,
            'NOME': client.NOME,
            'EMAIL': client.EMAIL
        })

    if request.method == 'POST':
        client_id = request.form['client_id']
        client_email = request.form['client_email']
        assessor_email = request.form['assessor_email']
        email_subject = request.form['email_subject']
        email_body = request.form['email_body']

        # Processa os arquivos enviados
        files = request.files.getlist('files')
        file_paths = []
        for file in files[:2]:  # Limite de 2 arquivos
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)

        # Envia o e-mail
        try:
            msg = Message(subject=email_subject, recipients=[client_email])
            msg.body = email_body
            msg.sender = assessor_email

            # Adiciona os anexos
            for file_path in file_paths:
                with app.open_resource(file_path) as fp:
                    msg.attach(filename=file_path.split('/')[-1], content_type='application/octet-stream', data=fp.read())

            mail.send(msg)
            flash('E-mail enviado com sucesso.', 'success')
        except Exception as e:
            flash(f'Erro ao enviar o e-mail: {e}', 'danger')

        return redirect(url_for('send_email'))

    return render_template('send_email.html', clients=clients_list)

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(debug=True, host='0.0.0.0')