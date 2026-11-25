---
name: "desktop-app-packager"
description: "Transforma um projeto (script Python, app web ou JavaScript) em um aplicativo de desktop para usuários leigos no Windows: gera um instalador com atalhos, empacota tudo em um .zip com instruções em português e adiciona aviso de nova versão. Use quando pedirem para \"transformar em app de desktop\", \"criar instalador\", \"empacotar para o usuário final\", \"gerar .exe\", \"distribuir como zip\" ou algo parecido."
---

# Desktop App Packager

Esta skill pega um projeto existente (ou uma ideia já implementada) e o transforma em um aplicativo de desktop para o Windows que uma pessoa leiga consegue instalar com dois cliques. A entrega final é um arquivo `.zip` contendo o instalador e um guia de uso em português simples.

## Premissas de público

O usuário final não sabe usar terminal, não sabe o que é Python e não deve precisar instalar nada além do próprio app. Por isso:

- Nada de linha de comando para usar o app. Erros aparecem em caixas de diálogo com texto claro, nunca como traceback.
- Os dados do usuário ficam em uma pasta de dados do próprio usuário (por exemplo `%APPDATA%\NomeDoApp`), nunca dentro da pasta de instalação.
- O app tem nome, ícone e textos em português.
- O instalador cria atalho na Área de Trabalho e no Menu Iniciar e registra o app para desinstalação no Painel de Controle.

## Passo 1: entender o projeto

Antes de qualquer coisa, leia a estrutura do projeto e identifique:

- Nome do app em português (pergunte ao usuário se não estiver claro).
- Stack: Python, JavaScript/Node, ou uma aplicação web que pode rodar dentro de uma janela própria.
- Ponto de entrada (arquivo principal que abre o app).
- Dependências (`requirements.txt`, `package.json`, etc.).
- Se já existe um ícone. Se não existir, peça um arquivo `.ico` ou use um ícone padrão e avise.
- Número da versão (use `1.0.0` se não houver).
- URL onde o arquivo de versão ficará publicado (ver Passo 4). Se o usuário ainda não tiver, deixe o placeholder e avise.

## Passo 2: escolher a tecnologia de empacotamento

Regra geral:

- Projeto Python (tkinter, PyQt, ou script): use **PyInstaller** para gerar o executável e **Inno Setup** para gerar o instalador. Não precisa de Node.
- Projeto web ou JavaScript: use **Electron** com **electron-builder** (alvo NSIS, que gera um instalador `.exe` com atalhos). Isso exige Node.js na máquina que gera o pacote, não na do usuário final.
- Se o projeto for uma página web sem backend, Electron é o caminho mais limpo. Se for um app Python com dados locais, PyInstaller é mais simples.

Explique a escolha em uma frase para o usuário.

## Passo 3: preparar o código para uso por leigos

Antes de empacotar, ajuste o código:

1. Caminho de dados: troque caminhos relativos (como `dados.json` na pasta atual) por uma pasta do usuário. Em Python use `os.environ["APPDATA"]`; em Electron use `app.getPath("userData")`.
2. Erros: envolva a inicialização principal em `try/except` (ou equivalente) e mostre a mensagem com `messagebox.showerror` (Python) ou `dialog.showErrorBox` (Electron).
3. Sem terminal: não use `input()` nem `print()` como interface.
4. Aviso de nova versão: adicione o código do Passo 4.

### Trecho Python para checar versão (tkinter)

```python
import json
import threading
import urllib.request
import webbrowser
from tkinter import messagebox

VERSAO_ATUAL = "1.0.0"
URL_VERSAO = "https://SEU-SITE.com/minhas-tarefas/version.json"  # placeholder


def _tupla(v):
    return tuple(int(p) for p in v.split("."))


def checar_atualizacao(root):
    def trabalhar():
        try:
            with urllib.request.urlopen(URL_VERSAO, timeout=5) as r:
                info = json.loads(r.read().decode("utf-8"))
            if _tupla(info["versao"]) > _tupla(VERSAO_ATUAL):
                root.after(0, lambda: avisar(info))
        except Exception:
            pass  # sem internet ou erro: o app segue normalmente

    def avisar(info):
        if messagebox.askyesno(
            "Nova versão disponível",
            f"Existe a versão {info['versao']}. Deseja abrir a página para baixar?",
        ):
            webbrowser.open(info["download"])

    threading.Thread(target=trabalhar, daemon=True).start()
```

Chame `checar_atualizacao(raiz)` logo antes de `raiz.mainloop()`. O app nunca instala a atualização sozinho; ele só avisa e leva o usuário ao download.

## Passo 4: arquivo de versão publicado

Crie um `version.json` e publique em um endereço fixo (site, GitHub Pages, pasta compartilhada, etc.):

```json
{
  "versao": "1.0.0",
  "download": "https://SEU-SITE.com/minhas-tarefas/MinhasTarefas-1.0.0.zip"
}
```

Ao lançar uma nova versão, atualize esse arquivo e o zip.

## Passo 5 (Python): build do executável e do instalador

### Script `build_windows.bat` (colocar na raiz do projeto)

```bat
@echo off
chcp 65001 >nul
setlocal

set NOME=Minhas Tarefas
set EXE=MinhasTarefas
set VERSAO=1.0.0

echo [1/4] Instalando dependencias de build...
python -m pip install --upgrade pyinstaller || goto erro

echo [2/4] Gerando executavel...
python -m PyInstaller --noconfirm --windowed --onedir --name %EXE% --icon icone.ico app_tarefas.py || goto erro

echo [3/4] Gerando instalador...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo Inno Setup 6 nao encontrado. Instale em https://jrsoftware.org/isinfo.php
    goto erro
)
%ISCC% /DVERSAO=%VERSAO% installer\setup.iss || goto erro

echo [4/4] Montando o zip para distribuicao...
powershell -NoProfile -Command "Compress-Archive -Force -Path 'dist\setup\MinhasTarefas-Setup-%VERSAO%.exe','installer\LEIA-ME.txt' -DestinationPath 'dist\MinhasTarefas-%VERSAO%.zip'" || goto erro

echo.
echo Pronto! Entregue o arquivo: dist\MinhasTarefas-%VERSAO%.zip
pause
exit /b 0

:erro
echo.
echo Ocorreu um erro. Veja as mensagens acima.
pause
exit /b 1
```

### Script `installer\setup.iss` (Inno Setup)

```iss
#ifndef VERSAO
  #define VERSAO "1.0.0"
#endif

[Setup]
AppName=Minhas Tarefas
AppVersion={#VERSAO}
AppPublisher=SEU NOME
DefaultDirName={autopf}\Minhas Tarefas
DefaultGroupName=Minhas Tarefas
OutputDir=..\dist\setup
OutputBaseFilename=MinhasTarefas-Setup-{#VERSAO}
SetupIconFile=..\icone.ico
UninstallDisplayIcon={app}\MinhasTarefas.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "atalhoarea"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist\MinhasTarefas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Minhas Tarefas"; Filename: "{app}\MinhasTarefas.exe"
Name: "{group}\Desinstalar Minhas Tarefas"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Minhas Tarefas"; Filename: "{app}\MinhasTarefas.exe"; Tasks: atalhoarea

[Run]
Filename: "{app}\MinhasTarefas.exe"; Description: "Abrir Minhas Tarefas"; Flags: nowait postinstall skipifsilent
```

Se o arquivo `BrazilianPortuguese.isl` não existir na instalação do Inno Setup, remova a seção `[Languages]` e use o inglês padrão.

## Passo 5 (Electron): build

No `package.json`, adicione:

```json
"build": {
  "appId": "com.seunome.minhastarefas",
  "productName": "Minhas Tarefas",
  "win": { "target": "nsis", "icon": "icone.ico" },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": false,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "shortcutName": "Minhas Tarefas",
    "language": "1046"
  },
  "directories": { "output": "dist" }
}
```

Depois rode `npm install` e `npx electron-builder --win`. Para o aviso de nova versão, use `dialog.showMessageBox` e `shell.openExternal` com a URL do `version.json`. Empacote o instalador gerado em `dist` junto com o `LEIA-ME.txt` (ver Passo 6).

## Passo 6: o zip para o usuário leigo

O conteúdo do zip deve ser exatamente:

- `MinhasTarefas-Setup-1.0.0.exe` (o instalador)
- `LEIA-ME.txt` (guia abaixo)

Modelo de `installer\LEIA-ME.txt`:

```
MINHAS TAREFAS - COMO INSTALAR

1. Extraia este arquivo ZIP (clique com o botão direito > Extrair Tudo).
2. Dê dois cliques em "MinhasTarefas-Setup-1.0.0.exe".
3. Se aparecer a tela "O Windows protegeu o seu PC", clique em
   "Mais informações" e depois em "Executar assim mesmo".
   Isso acontece porque o programa ainda não tem assinatura digital.
4. Siga os passos da instalação e clique em Concluir.
5. Use o atalho "Minhas Tarefas" na Área de Trabalho.

Para desinstalar: Configurações > Aplicativos > Minhas Tarefas > Desinstalar.
```

## Passo 7: verificação antes de entregar

Não entregue sem checar, na medida do possível:

1. Sintaxe: rode `python -m py_compile` no código principal (Python) ou `node --check` (JavaScript).
2. Build: confirme que `dist\MinhasTarefas\MinhasTarefas.exe` (ou o `.exe` do NSIS) foi criado.
3. Instalação limpa: instale em uma máquina ou VM Windows sem o projeto e sem Python. Abra pelo atalho, teste as funções principais e desinstale pelo Painel.
4. Pasta de dados: confirme que os dados são gravados em `%APPDATA%` e não na pasta de instalação.
5. Atualização: simule um `version.json` com versão maior e confirme que o aviso aparece.

Se algum passo não puder ser feito no ambiente atual (por exemplo, ambiente Linux que não gera `.exe`), diga isso claramente e entregue os scripts para o usuário rodar no Windows.

## Limitações a informar ao usuário

- O build precisa ser feito no Windows. Em Linux ou Mac não há como gerar o instalador `.exe`.
- Sem assinatura digital, o Windows mostra um aviso de "editor desconhecido" (SmartScreen) na primeira execução. A explicação já está no LEIA-ME. Um certificado de assinatura de código resolve isso, mas tem custo anual.
- O aviso de nova versão não instala atualizações automaticamente. Para atualização automática seria preciso um sistema de releases (como electron-updater ou Squirrel), o que aumenta a complexidade.
- Para Mac, o processo é diferente (`.app` e `.dmg`, com assinatura e notarização). Esta skill cobre apenas Windows por enquanto.

## Entrega

Ao final, apresente ao usuário apenas o `.zip` gerado (ou os arquivos de build, se o zip não pôde ser criado), com um resumo curto: o que foi empacotado, a tecnologia escolhida, o que falta preencher (URL do `version.json`, nome do editor, ícone) e as limitações acima.

