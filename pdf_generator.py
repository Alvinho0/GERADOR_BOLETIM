from fpdf import FPDF
from datetime import datetime

class BoletimPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ESCOLA MODELO DE TECNOLOGIA', 0, 1, 'C')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'BOLETIM ESCOLAR', 0, 1, 'C')
        self.ln(5)
    
    def create_boletim(self, aluno_data, notas_data):
        self.add_page()
        
        # Dados do Aluno
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'DADOS DO ALUNO', 0, 1)
        self.set_font('Arial', '', 10)
        
        info_aluno = f"""Nome: {aluno_data[1]}
Matrícula: {aluno_data[5]}
Série: {aluno_data[3]}
Data de Nascimento: {aluno_data[2]}
Responsável: {aluno_data[4]}"""
        
        self.multi_cell(0, 8, info_aluno)
        self.ln(10)
        
        # Tabela de Notas
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'DESEMPENHO ACADÊMICO', 0, 1)
        
        # Cabeçalho da tabela
        self.set_fill_color(200, 200, 200)
        self.set_font('Arial', 'B', 10)
        
        self.cell(60, 10, 'Disciplina', 1, 0, 'C', True)
        self.cell(25, 10, '1º Bim.', 1, 0, 'C', True)
        self.cell(25, 10, '2º Bim.', 1, 0, 'C', True)
        self.cell(25, 10, 'Média', 1, 0, 'C', True)
        self.cell(25, 10, 'Freq. %', 1, 0, 'C', True)
        self.cell(30, 10, 'Status', 1, 1, 'C', True)
        
        # Dados das notas
        self.set_font('Arial', '', 9)
        for nota in notas_data:
            disciplina = str(nota[2])[:25] if len(str(nota[2])) > 25 else str(nota[2])
            nota_1 = float(nota[3])
            nota_2 = float(nota[4])
            media = float(nota[5])
            frequencia = float(nota[6])
            status = str(nota[7])
            
            self.cell(60, 8, disciplina, 1)
            self.cell(25, 8, f"{nota_1:.1f}", 1, 0, 'C')
            self.cell(25, 8, f"{nota_2:.1f}", 1, 0, 'C')
            self.cell(25, 8, f"{media:.1f}", 1, 0, 'C')
            self.cell(25, 8, f"{frequencia:.1f}%", 1, 0, 'C')
            self.cell(30, 8, status, 1, 1, 'C')
        
        self.ln(10)
        
        # Rodapé
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Emitido em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_boletim_pdf(aluno_data, notas_data):
    """Gera um boletim em PDF para o aluno"""
    try:
        print(f"📄 Iniciando geração de PDF para: {aluno_data[1]}")
        pdf = BoletimPDF()
        pdf.create_boletim(aluno_data, notas_data)
        print("✅ PDF gerado com sucesso")
        return pdf
    except Exception as e:
        print(f"❌ Erro na geração do PDF: {e}")
        raise