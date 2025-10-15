from database import Database
from pdf_generator import gerar_boletim_pdf

def testar_geracao_pdf():
    db = Database()
    
    # Buscar um aluno para testar
    aluno, notas = db.buscar_aluno_por_matricula('2024001')
    
    if aluno and notas:
        print(f"📊 Testando PDF para: {aluno[1]}")
        print(f"📚 {len(notas)} disciplinas encontradas")
        
        try:
            pdf = gerar_boletim_pdf(aluno, notas)
            pdf.output("teste_boletim.pdf")
            print("✅ PDF gerado com sucesso: teste_boletim.pdf")
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
    else:
        print("❌ Aluno não encontrado para teste")

if __name__ == '__main__':
    testar_geracao_pdf()