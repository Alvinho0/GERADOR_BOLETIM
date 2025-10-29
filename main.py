from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, make_response
from database import Database
from pdf_generator import gerar_boletim_pdf
import io
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Configurar o Flask para encontrar os templates
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

db = Database()

print("=" * 50)
print("🚀 SISTEMA DE BOLETIM ESCOLAR COM LOGIN")
print("=" * 50)
print(f"📁 Diretório atual: {os.getcwd()}")
print(f"📁 Pasta templates existe: {os.path.exists('templates')}")

if os.path.exists('templates'):
    print(f"📄 Arquivos nos templates: {os.listdir('templates')}")
else:
    print("❌ ERRO: Pasta templates não encontrada!")

# ==================== CONFIGURAÇÃO DE USUÁRIOS ====================
users_db = {
    'professor@escola.com': {
        'password_hash': generate_password_hash('123456'),
        'user_type': 'professor',
        'name': 'Professor João Silva',
        'active': True
    },
    'secretaria@escola.com': {
        'password_hash': generate_password_hash('123456'),
        'user_type': 'secretaria', 
        'name': 'Secretária Maria Santos',
        'active': True
    }
}

# ==================== DECORATORS DE AUTENTICAÇÃO ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token')
        
        if not token:
            return redirect('/login')
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return redirect('/login?error=Token expirado')
        except jwt.InvalidTokenError:
            return redirect('/login?error=Token inválido')
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROTAS DE AUTENTICAÇÃO ====================
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def login_page():
    error = request.args.get('error', '')
    return render_template('login.html', error=error)

@app.route('/api/auth/login', methods=['POST'])
def login_api():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user_type = data.get('user_type', 'professor')

        # Validações básicas
        if not email or not password:
            return jsonify({'success': False, 'message': 'E-mail e senha são obrigatórios'}), 400

        # Verificar usuário
        user = users_db.get(email)
        if not user or not user['active']:
            return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

        # Verificar senha
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

        # Verificar tipo de usuário
        if user['user_type'] != user_type:
            return jsonify({'success': False, 'message': 'Tipo de acesso incorreto'}), 403

        # Gerar token JWT
        token = jwt.encode({
            'email': email,
            'user_type': user['user_type'],
            'name': user['name'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        response = jsonify({
            'success': True,
            'user': {
                'email': email,
                'name': user['name'],
                'user_type': user['user_type']
            }
        })

        # Configurar cookie HTTP-only
        response.set_cookie(
            'token', 
            token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=24*60*60
        )

        return response

    except Exception as e:
        print(f'Erro no login: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@app.route('/logout')
def logout():
    response = redirect('/login')
    response.set_cookie('token', '', expires=0)
    return response

# ==================== ROTAS DO SISTEMA (PROTEGIDAS) ====================
@app.route('/sistema')
@login_required
def sistema_index():
    try:
        termo_busca = request.args.get('busca', '')
        alunos = db.buscar_alunos(termo_busca)
        print(f"✅ Dashboard carregado - {len(alunos)} alunos")
        return render_template('index.html', alunos=alunos, termo_busca=termo_busca)
    except Exception as e:
        error_msg = f"❌ ERRO: {str(e)}"
        print(error_msg)
        return f"""
        <html>
            <body>
                <h1>Erro ao carregar a página</h1>
                <p><strong>Erro:</strong> {e}</p>
                <a href="/sistema">Tentar novamente</a>
            </body>
        </html>
        """

@app.route('/sistema/aluno/<matricula>')
@login_required
def detalhes_aluno(matricula):
    try:
        aluno, notas = db.buscar_aluno_por_matricula(matricula)
        if not aluno:
            return "Aluno não encontrado", 404
        print(f"✅ Página do aluno carregada - {aluno[1]}")
        return render_template('aluno.html', aluno=aluno, notas=notas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/sistema/gerar_boletim/<matricula>')
@login_required
def gerar_boletim(matricula):
    try:
        print(f"🔍 Buscando aluno com matrícula: {matricula}")
        aluno, notas = db.buscar_aluno_por_matricula(matricula)
        
        if not aluno:
            print("❌ Aluno não encontrado")
            return "Aluno não encontrado", 404
        
        print(f"📊 Gerando PDF para: {aluno[1]} - {len(notas)} disciplinas")
        
        # Gerar PDF
        pdf = gerar_boletim_pdf(aluno, notas)
        
        # Criar arquivo em memória
        pdf_output = pdf.output(dest='S')
        
        # Nome do arquivo
        nome_aluno = aluno[1].replace(' ', '_')
        nome_arquivo = f"BOLETIM_{nome_aluno}.pdf"
        
        print(f"📥 Enviando arquivo: {nome_arquivo}")
        
        return send_file(
            io.BytesIO(pdf_output),
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ ERRO na geração do PDF: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <html>
            <body>
                <h1>Erro ao gerar PDF</h1>
                <p><strong>Erro:</strong> {e}</p>
                <a href="/sistema/aluno/{matricula}">Voltar</a>
            </body>
        </html>
        """, 500

@app.route('/sistema/adicionar_aluno')
@login_required
def adicionar_aluno_form():
    """Exibe o formulário para adicionar novo aluno"""
    try:
        disciplinas = db.get_disciplinas_padrao()
        return render_template('adicionar_aluno.html', disciplinas=disciplinas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/sistema/adicionar_aluno', methods=['POST'])
@login_required
def adicionar_aluno():
    """Processa o formulário de adicionar aluno"""
    try:
        # Dados pessoais
        nome_completo = request.form['nome_completo']
        matricula = request.form['matricula']
        data_nascimento = request.form['data_nascimento']
        serie = request.form['serie']
        nome_responsavel = request.form['nome_responsavel']

        # Verificar se matrícula já existe
        if db.verificar_matricula_existe(matricula):
            return f"""
            <html>
                <body>
                    <h1>Erro no Cadastro</h1>
                    <p>A matrícula <strong>{matricula}</strong> já está em uso!</p>
                    <a href="/sistema/adicionar_aluno">Voltar e corrigir</a>
                </body>
            </html>
            """, 400

        # Inserir aluno
        aluno_id = db.inserir_aluno(
            nome_completo, data_nascimento, serie, nome_responsavel, matricula
        )

        # Inserir notas para cada disciplina
        disciplinas = db.get_disciplinas_padrao()
        for i, disciplina in enumerate(disciplinas):
            nota1 = float(request.form.get(f'nota1_{i}', 0))
            nota2 = float(request.form.get(f'nota2_{i}', 0))
            frequencia = float(request.form.get(f'frequencia_{i}', 0))
            
            db.inserir_nota(aluno_id, disciplina, nota1, nota2, frequencia)

        print(f"✅ Novo aluno cadastrado: {nome_completo} (ID: {aluno_id})")
        
        return redirect(f'/sistema/aluno/{matricula}')

    except Exception as e:
        print(f"❌ Erro ao cadastrar aluno: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <html>
            <body>
                <h1>Erro no Cadastro</h1>
                <p><strong>Erro:</strong> {e}</p>
                <a href="/sistema/adicionar_aluno">Voltar e Tentar Novamente</a>
            </body>
        </html>
        """, 500

@app.route('/sistema/confirmar_remocao/<matricula>')
@login_required
def confirmar_remocao(matricula):
    """Página de confirmação para remover aluno"""
    try:
        aluno, notas = db.buscar_aluno_por_matricula(matricula)
        if not aluno:
            return "Aluno não encontrado", 404
        
        return render_template('confirmar_remocao.html', aluno=aluno, notas=notas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/sistema/remover_aluno/<matricula>', methods=['POST'])
@login_required
def remover_aluno(matricula):
    """Remove um aluno do sistema"""
    try:
        sucesso, mensagem = db.remover_aluno(matricula)
        
        if sucesso:
            print(f"✅ Aluno removido: {matricula}")
            return redirect('/sistema')
        else:
            return f"""
            <html>
                <body>
                    <h1>Erro ao Remover Aluno</h1>
                    <p><strong>Erro:</strong> {mensagem}</p>
                    <a href="/sistema">Voltar à Lista</a>
                </body>
            </html>
            """, 500
            
    except Exception as e:
        print(f"❌ Erro ao remover aluno: {e}")
        return f"Erro ao remover aluno: {e}", 500

# ==================== APIs DO SISTEMA (PROTEGIDAS) ====================
@app.route('/sistema/api/buscar_alunos')
@login_required
def api_buscar_alunos():
    termo_busca = request.args.get('busca', '')
    alunos = db.buscar_alunos(termo_busca)
    return jsonify({'alunos': alunos})

@app.route('/sistema/api/verificar_matricula/<matricula>')
@login_required
def api_verificar_matricula(matricula):
    existe = db.verificar_matricula_existe(matricula)
    return jsonify({'existe': existe})

# ==================== ROTA DE SAÚDE ====================
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Sistema de Boletim Escolar'})

if __name__ == '__main__':
    print("🌐 Servidor iniciado!")
    print("🔐 Página de login: http://localhost:5000/login")
    print("📊 Sistema principal: http://localhost:5000/sistema")
    print("=" * 50)
    
    # Configurações para produção
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)