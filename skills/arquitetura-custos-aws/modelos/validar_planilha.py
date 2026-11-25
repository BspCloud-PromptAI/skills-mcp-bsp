# Calcula a planilha com o avaliador "formulas" (sem LibreOffice) e confere que nenhuma célula tem erro.
# Uso: uv run --quiet --no-project --with formulas --with openpyxl python -I validar_planilha.py <arquivo.xlsx> \
#        "Resumo!B6=71.24" "Resumo!B7=193.55"      (opcional: confere valores com 2 casas)
import sys
import warnings

warnings.filterwarnings("ignore")

import formulas  # noqa: E402
from openpyxl import load_workbook  # noqa: E402


def chave(referencia):
    aba, celula = referencia.split("!")
    return f"{aba.strip(chr(39)).upper()}'!{celula.upper()}"


def main():
    caminho, esperados = sys.argv[1], sys.argv[2:]
    livro = load_workbook(caminho)
    total = sum(1 for aba in livro for linha in aba.iter_rows() for celula in linha
                if isinstance(celula.value, str) and celula.value.startswith("="))
    print(f"fórmulas: {total} | nomes definidos: {len(livro.defined_names)}")

    solucao = formulas.ExcelModel().loads(caminho).finish().calculate()
    valores, erros = {}, []
    for referencia, resultado in solucao.items():
        valor = getattr(resultado, "value", resultado)
        try:
            valor = valor[0][0]
        except (TypeError, IndexError, KeyError):
            pass
        if str(valor).startswith("#") or "Error" in type(valor).__name__:
            erros.append((referencia, str(valor)))
        valores[str(referencia).upper().split("]")[-1]] = valor
    print(f"células com erro: {len(erros)}")
    for referencia, texto in erros[:20]:
        print("  ", referencia, texto)

    falhas = 0
    for item in esperados:
        referencia, alvo = item.split("=")
        obtido = valores.get(chave(referencia))
        certo = obtido is not None and round(float(obtido), 2) == round(float(alvo), 2)
        falhas += not certo
        print(f"{referencia}: {obtido} (esperado {alvo}) {'ok' if certo else 'DIFERENTE'}")
    sys.exit(1 if erros or falhas else 0)


if __name__ == "__main__":
    main()
