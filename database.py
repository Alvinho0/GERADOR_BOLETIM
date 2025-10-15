import os
import sys

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️  psycopg2 não disponível, usando SQLite")

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

class Database:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if self.db_url and POSTGRES_AVAILABLE:
            print("🔗 Conectando ao PostgreSQL (Produção)")
        else:
            print("🔗 Conectando ao SQLite (Desenvolvimento)")
        
    def get_connection(self):
        if self.db_url and POSTGRES_AVAILABLE:
            # PostgreSQL em produção
            conn = psycopg2.connect(self.db_url)
            return conn
        else:
            # SQLite em desenvolvimento
            import sqlite3
            return sqlite3.connect('escola.db')
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Detecta se é PostgreSQL
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        # Tabela Alunos
        if is_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alunos (
                    id SERIAL PRIMARY KEY,
                    nome_completo TEXT NOT NULL,
                    data_nascimento TEXT NOT NULL,
                    serie TEXT NOT NULL,
                    nome_do_responsavel TEXT NOT NULL,
                    matricula TEXT UNIQUE NOT NULL
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Alunos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_completo TEXT NOT NULL,
                    data_nascimento TEXT NOT NULL,
                    serie TEXT NOT NULL,
                    nome_do_responsavel TEXT NOT NULL,
                    matricula TEXT UNIQUE NOT NULL
                )
            ''')
        
        # Tabela Notas
        if is_postgres:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notas (
                    id SERIAL PRIMARY KEY,
                    aluno_id INTEGER NOT NULL,
                    disciplina TEXT NOT NULL,
                    nota_1_bimestre REAL NOT NULL,
                    nota_2_bimestre REAL NOT NULL,
                    media_final REAL NOT NULL,
                    frequencia_percentual REAL NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (aluno_id) REFERENCES alunos (id) ON DELETE CASCADE
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aluno_id INTEGER NOT NULL,
                    disciplina TEXT NOT NULL,
                    nota_1_bimestre REAL NOT NULL,
                    nota_2_bimestre REAL NOT NULL,
                    media_final REAL NOT NULL,
                    frequencia_percentual REAL NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (aluno_id) REFERENCES Alunos (id)
                )
            ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    def inserir_aluno(self, nome_completo, data_nascimento, serie, nome_responsavel, matricula):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('''
                INSERT INTO alunos (nome_completo, data_nascimento, serie, nome_do_responsavel, matricula)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (nome_completo, data_nascimento, serie, nome_responsavel, matricula))
            aluno_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO Alunos (nome_completo, data_nascimento, serie, nome_do_responsavel, matricula)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome_completo, data_nascimento, serie, nome_responsavel, matricula))
            aluno_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return aluno_id
    
    def inserir_nota(self, aluno_id, disciplina, nota_1, nota_2, frequencia):
        # Calcular média final
        media_final = (nota_1 + nota_2) / 2
        
        # Determinar status
        if media_final >= 7.0 and frequencia >= 75:
            status = "Aprovado"
        elif media_final >= 5.0 and frequencia >= 75:
            status = "Recuperação"
        else:
            status = "Reprovado"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('''
                INSERT INTO notas (aluno_id, disciplina, nota_1_bimestre, nota_2_bimestre, 
                                 media_final, frequencia_percentual, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (aluno_id, disciplina, nota_1, nota_2, media_final, frequencia, status))
        else:
            cursor.execute('''
                INSERT INTO Notas (aluno_id, disciplina, nota_1_bimestre, nota_2_bimestre, 
                                 media_final, frequencia_percentual, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (aluno_id, disciplina, nota_1, nota_2, media_final, frequencia, status))
        
        conn.commit()
        conn.close()
    
    def buscar_alunos(self, termo=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            if termo:
                cursor.execute('''
                    SELECT * FROM alunos 
                    WHERE nome_completo ILIKE %s OR matricula ILIKE %s
                    ORDER BY nome_completo
                ''', (f'%{termo}%', f'%{termo}%'))
            else:
                cursor.execute('SELECT * FROM alunos ORDER BY nome_completo')
        else:
            if termo:
                cursor.execute('''
                    SELECT * FROM Alunos 
                    WHERE nome_completo LIKE ? OR matricula LIKE ?
                    ORDER BY nome_completo
                ''', (f'%{termo}%', f'%{termo}%'))
            else:
                cursor.execute('SELECT * FROM Alunos ORDER BY nome_completo')
        
        alunos = cursor.fetchall()
        conn.close()
        return alunos
    
    def buscar_aluno_por_matricula(self, matricula):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('SELECT * FROM alunos WHERE matricula = %s', (matricula,))
            aluno = cursor.fetchone()
            
            if aluno:
                cursor.execute('SELECT * FROM notas WHERE aluno_id = %s', (aluno[0],))
                notas = cursor.fetchall()
            else:
                notas = []
        else:
            cursor.execute('SELECT * FROM Alunos WHERE matricula = ?', (matricula,))
            aluno = cursor.fetchone()
            
            if aluno:
                cursor.execute('SELECT * FROM Notas WHERE aluno_id = ?', (aluno[0],))
                notas = cursor.fetchall()
            else:
                notas = []
        
        conn.close()
        return aluno, notas
    
    def calcular_estatisticas_gerais(self, aluno_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('''
                SELECT COUNT(*), AVG(media_final), AVG(frequencia_percentual)
                FROM notas WHERE aluno_id = %s
            ''', (aluno_id,))
        else:
            cursor.execute('''
                SELECT COUNT(*), AVG(media_final), AVG(frequencia_percentual)
                FROM Notas WHERE aluno_id = ?
            ''', (aluno_id,))
        
        stats = cursor.fetchone()
        conn.close()
        return stats

    def get_disciplinas_padrao(self):
        """Retorna a lista de disciplinas padrão do sistema"""
        return [
            'Matemática', 'Língua Portuguesa', 'Ciências', 'História', 
            'Geografia', 'Inglês', 'Artes', 'Educação Física'
        ]

    def verificar_matricula_existe(self, matricula):
        """Verifica se uma matrícula já existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('SELECT id FROM alunos WHERE matricula = %s', (matricula,))
        else:
            cursor.execute('SELECT id FROM Alunos WHERE matricula = ?', (matricula,))
            
        resultado = cursor.fetchone()
        conn.close()
        return resultado is not None

    def remover_aluno(self, matricula):
        """Remove um aluno e todas as suas notas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        try:
            # Primeiro buscar o ID do aluno
            if is_postgres:
                cursor.execute('SELECT id FROM alunos WHERE matricula = %s', (matricula,))
            else:
                cursor.execute('SELECT id FROM Alunos WHERE matricula = ?', (matricula,))
                
            aluno = cursor.fetchone()
            
            if not aluno:
                conn.close()
                return False, "Aluno não encontrado"
            
            aluno_id = aluno[0]
            
            # Remover notas do aluno
            if is_postgres:
                cursor.execute('DELETE FROM notas WHERE aluno_id = %s', (aluno_id,))
                # Remover aluno
                cursor.execute('DELETE FROM alunos WHERE id = %s', (aluno_id,))
            else:
                cursor.execute('DELETE FROM Notas WHERE aluno_id = ?', (aluno_id,))
                # Remover aluno
                cursor.execute('DELETE FROM Alunos WHERE id = ?', (aluno_id,))
            
            conn.commit()
            conn.close()
            return True, "Aluno removido com sucesso"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Erro ao remover aluno: {e}"

    def buscar_aluno_por_id(self, aluno_id):
        """Busca aluno por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        is_postgres = self.db_url and POSTGRES_AVAILABLE
        
        if is_postgres:
            cursor.execute('SELECT * FROM alunos WHERE id = %s', (aluno_id,))
        else:
            cursor.execute('SELECT * FROM Alunos WHERE id = ?', (aluno_id,))
            
        aluno = cursor.fetchone()
        conn.close()
        return aluno