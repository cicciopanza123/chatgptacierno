from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Per session e flash messages

# Simuliamo un unico conto utente con dati in memoria
account = {
    'pin': '1234',
    'saldo': 1000.0,
    'movimenti': [],
    'telefono_credito': 10.0
}

def registra_movimento(tipo, importo, descrizione=''):
    movimento = {
        'data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'tipo': tipo,
        'importo': importo,
        'descrizione': descrizione
    }
    account['movimenti'].insert(0, movimento)
    # Manteniamo max 10 movimenti recenti
    if len(account['movimenti']) > 10:
        account['movimenti'].pop()

def verifica_pin(pin):
    return pin == account['pin']

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')
        if verifica_pin(pin):
            session['logged_in'] = True
            flash('Accesso effettuato con successo!', 'success')
            return redirect(url_for('home'))
        else:
            flash('PIN errato, riprova.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sei stato disconnesso.', 'info')
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Devi effettuare il login.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/saldo')
@login_required
def saldo():
    return render_template('saldo.html', saldo=account['saldo'])

@app.route('/movimenti')
@login_required
def movimenti():
    return render_template('movimenti.html', movimenti=account['movimenti'])

@app.route('/prelievo', methods=['GET', 'POST'])
@login_required
def prelievo():
    if request.method == 'POST':
        try:
            importo = float(request.form.get('importo'))
            if importo <= 0:
                flash('Inserisci un importo positivo.', 'danger')
            elif importo > account['saldo']:
                flash('Saldo insufficiente.', 'danger')
            else:
                account['saldo'] -= importo
                registra_movimento('Prelievo', -importo, 'Prelievo contanti')
                flash(f'Prelievo di {importo:.2f}€ effettuato con successo.', 'success')
                return redirect(url_for('saldo'))
        except ValueError:
            flash('Inserisci un importo valido.', 'danger')
    return render_template('prelievo.html')

@app.route('/versamento', methods=['GET', 'POST'])
@login_required
def versamento():
    if request.method == 'POST':
        try:
            importo = float(request.form.get('importo'))
            if importo <= 0:
                flash('Inserisci un importo positivo.', 'danger')
            else:
                account['saldo'] += importo
                registra_movimento('Versamento', importo, 'Versamento contanti')
                flash(f'Versamento di {importo:.2f}€ effettuato con successo.', 'success')
                return redirect(url_for('saldo'))
        except ValueError:
            flash('Inserisci un importo valido.', 'danger')
    return render_template('versamento.html')

@app.route('/ricarica', methods=['GET', 'POST'])
@login_required
def ricarica():
    if request.method == 'POST':
        numero = request.form.get('numero')
        try:
            importo = float(request.form.get('importo'))
            if not numero.isdigit() or len(numero) < 8:
                flash('Numero di telefono non valido.', 'danger')
            elif importo <= 0:
                flash('Inserisci un importo positivo.', 'danger')
            elif importo > account['saldo']:
                flash('Saldo insufficiente per la ricarica.', 'danger')
            else:
                account['saldo'] -= importo
                account['telefono_credito'] += importo
                descrizione = f'Ricarica telefonica a {numero}'
                registra_movimento('Ricarica', -importo, descrizione)
                flash(f'Ricarica di {importo:.2f}€ al numero {numero} effettuata.', 'success')
                return redirect(url_for('saldo'))
        except ValueError:
            flash('Inserisci un importo valido.', 'danger')
    return render_template('ricarica.html')

@app.route('/pagamento', methods=['GET', 'POST'])
@login_required
def pagamento():
    if request.method == 'POST':
        bollettino = request.form.get('bollettino')
        try:
            importo = float(request.form.get('importo'))
            if not bollettino:
                flash('Inserisci il numero del bollettino.', 'danger')
            elif importo <= 0:
                flash('Inserisci un importo positivo.', 'danger')
            elif importo > account['saldo']:
                flash('Saldo insufficiente per il pagamento.', 'danger')
            else:
                account['saldo'] -= importo
                descrizione = f'Pagamento bollettino {bollettino}'
                registra_movimento('Pagamento', -importo, descrizione)
                flash(f'Pagamento bollettino {bollettino} di {importo:.2f}€ effettuato.', 'success')
                return redirect(url_for('saldo'))
        except ValueError:
            flash('Inserisci un importo valido.', 'danger')
    return render_template('pagamento.html')

@app.route('/cambio_pin', methods=['GET', 'POST'])
@login_required
def cambio_pin():
    if request.method == 'POST':
        pin_vecchio = request.form.get('pin_vecchio')
        pin_nuovo = request.form.get('pin_nuovo')
        pin_conferma = request.form.get('pin_conferma')
        if not verifica_pin(pin_vecchio):
            flash('PIN vecchio errato.', 'danger')
        elif len(pin_nuovo) != 4 or not pin_nuovo.isdigit():
            flash('Il nuovo PIN deve essere composto da 4 cifre.', 'danger')
        elif pin_nuovo != pin_conferma:
            flash('I PIN non coincidono.', 'danger')
        else:
            account['pin'] = pin_nuovo
            flash('PIN modificato con successo.', 'success')
            return redirect(url_for('home'))
    return render_template('cambio_pin.html')

if __name__ == '__main__':
    app.run(debug=True)
