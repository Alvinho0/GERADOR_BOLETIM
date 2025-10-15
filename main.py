# SISTEMA DE BOLETIM ESCOLAR - VERSÃO ONLINE
from flask import Flask, render_template, request, send_file
from database import Database
from pdf_generator import gerar_boletim_pdf
import io
import os
from datetime import datetime

# Configurar o Flask para encontrar os templates
app = Flask(__name__, template_folder='templates')
db = Database()

print("=" * 50)
print("🚀 INICIANDO SISTEMA DE BOLETIM ESCOLAR")
print("=" * 50)
print(f"📁 Diretório atual: {os.getcwd()}")
print(f"📁 Pasta templates existe: {os.path.exists('templates')}")

if os.path.exists('templates'):
    print(f"📄 Arquivos nos templates: {os.listdir('templates')}")
else:
    print("❌ ERRO: Pasta templates não encontrada!")

@app.route('/')
def index():
    try:
        termo_busca = request.args.get('busca', '')
        alunos = db.buscar_alunos(termo_busca)
        print(f"✅ Página inicial carregada - {len(alunos)} alunos")
        return render_template('index.html', alunos=alunos, termo_busca=termo_busca)
    except Exception as e:
        error_msg = f"❌ ERRO: {str(e)}"
        print(error_msg)
        return f"""
        <html>
            <body>
                <h1>Erro ao carregar a página</h1>
                <p><strong>Erro:</strong> {e}</p>
                <p>Verifique se o arquivo templates/index.html existe</p>
                <a href="/">Tentar novamente</a>
            </body>
        </html>
        """

@app.route('/aluno/<matricula>')
def detalhes_aluno(matricula):
    try:
        aluno, notas = db.buscar_aluno_por_matricula(matricula)
        if not aluno:
            return "Aluno não encontrado", 404
        print(f"✅ Página do aluno carregada - {aluno[1]}")
        return render_template('aluno.html', aluno=aluno, notas=notas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/gerar_boletim/<matricula>')
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
                <a href="/aluno/{matricula}">Voltar</a>
            </body>
        </html>
        """, 500

@app.route('/adicionar_aluno')
def adicionar_aluno_form():
    """Exibe o formulário para adicionar novo aluno"""
    try:
        disciplinas = db.get_disciplinas_padrao()
        return render_template('adicionar_aluno.html', disciplinas=disciplinas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/verificar_matricula/<matricula>')
def verificar_matricula(matricula):
    """Verifica se uma matrícula já existe (para AJAX)"""
    try:
        existe = db.verificar_matricula_existe(matricula)
        return {'existe': existe}
    except Exception as e:
        return {'existe': False, 'erro': str(e)}

@app.route('/adicionar_aluno', methods=['POST'])
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
                    <a href="/adicionar_aluno">Voltar e corrigir</a>
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
        
        # Redirecionar para a página de sucesso com CSS
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aluno Cadastrado com Sucesso</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
            <style>
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .success-container {{
                    background: white;
                    border-radius: 20px;
                    padding: 50px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    width: 100%;
                }}
                .success-icon {{
                    font-size: 80px;
                    color: #28a745;
                    margin-bottom: 20px;
                    animation: bounce 1s infinite alternate;
                }}
                @keyframes bounce {{
                    from {{ transform: translateY(0px); }}
                    to {{ transform: translateY(-10px); }}
                }}
                .success-title {{
                    color: #28a745;
                    font-weight: bold;
                    margin-bottom: 20px;
                }}
                .student-name {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: bold;
                    font-size: 1.5em;
                }}
                .btn-success-custom {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    border: none;
                    border-radius: 10px;
                    padding: 12px 30px;
                    font-weight: 600;
                    margin: 5px;
                    transition: all 0.3s ease;
                }}
                .btn-success-custom:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 20px rgba(40, 167, 69, 0.3);
                }}
                .btn-primary-custom {{
                    background: linear-gradient(135deg, #007bff, #0056b3);
                    border: none;
                    border-radius: 10px;
                    padding: 12px 30px;
                    font-weight: 600;
                    margin: 5px;
                    transition: all 0.3s ease;
                }}
                .btn-primary-custom:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 20px rgba(0, 123, 255, 0.3);
                }}
                .btn-secondary-custom {{
                    background: linear-gradient(135deg, #6c757d, #495057);
                    border: none;
                    border-radius: 10px;
                    padding: 12px 30px;
                    font-weight: 600;
                    margin: 5px;
                    transition: all 0.3s ease;
                }}
                .btn-secondary-custom:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 10px 20px rgba(108, 117, 125, 0.3);
                }}
                .success-message {{
                    background: linear-gradient(135deg, #d4edda, #c3e6cb);
                    border: 1px solid #c3e6cb;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .student-info {{
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #28a745;
                }}
            </style>
        </head>
        <body>
            <div class="success-container">
                <div class="success-icon">
                    <i class="bi bi-check-circle-fill"></i>
                </div>
                
                <h1 class="success-title">Aluno Cadastrado com Sucesso! 🎉</h1>
                
                <div class="success-message">
                    <h4>✅ Cadastro realizado com sucesso!</h4>
                    <p class="mb-0">O aluno foi adicionado ao sistema e já pode ter seu boletim gerado.</p>
                </div>
                
                <div class="student-info">
                    <h5>📋 Dados do Aluno:</h5>
                    <p class="mb-1"><strong>Nome:</strong> <span class="student-name">{nome_completo}</span></p>
                    <p class="mb-1"><strong>Matrícula:</strong> {matricula}</p>
                    <p class="mb-1"><strong>Série:</strong> {serie}</p>
                    <p class="mb-0"><strong>Data de Cadastro:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="mt-4">
                    <p class="text-muted mb-3">O que você gostaria de fazer agora?</p>
                    
                    <div class="d-flex flex-column flex-md-row justify-content-center gap-2">
                        <a href="/aluno/{matricula}" class="btn btn-primary-custom">
                            <i class="bi bi-eye"></i> Ver Aluno
                        </a>
                        <a href="/adicionar_aluno" class="btn btn-success-custom">
                            <i class="bi bi-person-plus"></i> Adicionar Outro
                        </a>
                        <a href="/" class="btn btn-secondary-custom">
                            <i class="bi bi-list-ul"></i> Voltar à Lista
                        </a>
                    </div>
                </div>
                
                <div class="mt-4">
                    <small class="text-muted">
                        <i class="bi bi-info-circle"></i>
                        O boletim em PDF já pode ser gerado na página do aluno.
                    </small>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

    except Exception as e:
        print(f"❌ Erro ao cadastrar aluno: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Erro no Cadastro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
            <style>
                body {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                    min-height: 100vh;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .error-container {{
                    background: white;
                    border-radius: 20px;
                    padding: 50px;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    width: 100%;
                }}
                .error-icon {{
                    font-size: 80px;
                    color: #dc3545;
                    margin-bottom: 20px;
                }}
                .error-title {{
                    color: #dc3545;
                    font-weight: bold;
                    margin-bottom: 20px;
                }}
                .error-message {{
                    background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                    border: 1px solid #f5c6cb;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .btn-danger-custom {{
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    border: none;
                    border-radius: 10px;
                    padding: 12px 30px;
                    font-weight: 600;
                    margin: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                </div>
                
                <h1 class="error-title">Erro no Cadastro ❌</h1>
                
                <div class="error-message">
                    <h4>⚠️ Ocorreu um erro durante o cadastro</h4>
                    <p class="mb-2"><strong>Erro:</strong> {e}</p>
                    <p class="mb-0">Por favor, verifique os dados e tente novamente.</p>
                </div>
                
                <div class="mt-4">
                    <a href="/adicionar_aluno" class="btn btn-danger-custom">
                        <i class="bi bi-arrow-left"></i> Voltar e Tentar Novamente
                    </a>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """, 500

@app.route('/confirmar_remocao/<matricula>')
def confirmar_remocao(matricula):
    """Página de confirmação para remover aluno"""
    try:
        aluno, notas = db.buscar_aluno_por_matricula(matricula)
        if not aluno:
            return "Aluno não encontrado", 404
        
        return render_template('confirmar_remocao.html', aluno=aluno, notas=notas)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/remover_aluno/<matricula>', methods=['POST'])
def remover_aluno(matricula):
    """Remove um aluno do sistema"""
    try:
        sucesso, mensagem = db.remover_aluno(matricula)
        
        if sucesso:
            print(f"✅ Aluno removido: {matricula}")
            return f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Aluno Removido</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
                <style>
                    body {{
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                        min-height: 100vh;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .removal-container {{
                        background: white;
                        border-radius: 20px;
                        padding: 50px;
                        text-align: center;
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                        max-width: 600px;
                        width: 100%;
                    }}
                    .removal-icon {{
                        font-size: 80px;
                        color: #dc3545;
                        margin-bottom: 20px;
                    }}
                    .removal-title {{
                        color: #dc3545;
                        font-weight: bold;
                        margin-bottom: 20px;
                    }}
                    .removal-message {{
                        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
                        border: 1px solid #f5c6cb;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .btn-primary-custom {{
                        background: linear-gradient(135deg, #007bff, #0056b3);
                        border: none;
                        border-radius: 10px;
                        padding: 12px 30px;
                        font-weight: 600;
                        margin: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="removal-container">
                    <div class="removal-icon">
                        <i class="bi bi-trash-fill"></i>
                    </div>
                    
                    <h1 class="removal-title">Aluno Removido</h1>
                    
                    <div class="removal-message">
                        <h4>🗑️ Aluno removido do sistema</h4>
                        <p class="mb-0">Matrícula: <strong>{matricula}</strong></p>
                        <p class="mb-0">Todos os dados foram excluídos permanentemente.</p>
                    </div>
                    
                    <div class="mt-4">
                        <a href="/" class="btn btn-primary-custom">
                            <i class="bi bi-list-ul"></i> Voltar à Lista de Alunos
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
                <body>
                    <h1>Erro ao Remover Aluno</h1>
                    <p><strong>Erro:</strong> {mensagem}</p>
                    <a href="/">Voltar à Lista</a>
                </body>
            </html>
            """, 500
            
    except Exception as e:
        print(f"❌ Erro ao remover aluno: {e}")
        return f"Erro ao remover aluno: {e}", 500

if __name__ == '__main__':
    print("🌐 Servidor iniciado! Acesse: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)