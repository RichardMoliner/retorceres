# Retorceres — Bots de Automação

Dois bots de automação para o jogo:

- **Runemaker (`bot.py`)** — cria runas monitorando a barra de mana e clica na comida periodicamente
- **Fisher (`fish.py`)** — pesca automaticamente em 10 SQMs em sequência

Funciona em **macOS** e **Windows**.

---

## Requisitos

- **Python 3.9 ou superior** instalado
- Jogo rodando em janela visível durante toda a execução

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/RichardMoliner/retorceres.git
cd retorceres
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

> No macOS/Linux pode ser necessário usar `pip3` em vez de `pip`.

### 3. Configure permissões do sistema

#### macOS

O macOS bloqueia controle de mouse/teclado e captura de tela por padrão.
Você precisa autorizar o **Terminal** (ou o app que roda o Python):

- **Ajustes do Sistema → Privacidade e Segurança → Acessibilidade**
  - Adicione e ative o Terminal
- **Ajustes do Sistema → Privacidade e Segurança → Gravação de Tela**
  - Adicione e ative o Terminal
- **Ajustes do Sistema → Privacidade e Segurança → Monitoramento de Entrada**
  - Adicione e ative o Terminal

Após autorizar, **feche e reabra o Terminal**.

#### Windows

Não precisa configurar permissões especiais, mas:

- Se o jogo estiver rodando como **Administrador**, o terminal/Python também precisa ser executado como Administrador (clique com botão direito em "Prompt de Comando" ou "PowerShell" → "Executar como administrador"). Caso contrário, o bot não consegue enviar cliques e teclas para a janela do jogo.
- O **Windows Defender** pode marcar o script como suspeito por causa da automação de mouse/teclado. Se isso acontecer, adicione a pasta do projeto como exceção.

---

## Bot de Runemaking (`bot.py`)

### Passo 1 — Configurar (só precisa fazer uma vez)

Com o jogo aberto e visível:

**macOS / Linux:**
```bash
python3 setup.py
```

**Windows:**
```cmd
python setup.py
```

O script vai te guiar para capturar cada posição e configurar:

1. Início da barra de mana (extremidade esquerda)
2. Fim da barra de mana (extremidade direita)
3. Sua mana máxima (ex: 1500)
4. Valor de gatilho — mana mínima para criar uma runa (ex: 120)
5. Posição da blank rune
6. Slot da mão
7. Slot da backpack
8. Posição da comida
9. Hotkey (ex: `shift+5`)
10. Tempo de espera após a hotkey (ex: `2`)
11. Intervalo da comida em segundos (ex: `180` = 3 minutos)
12. Quantas runas criar por execução (ex: `20`)

Isso gera um arquivo `config.json`.

### Passo 2 — Rodar o bot

**macOS / Linux:**
```bash
python3 bot.py
```

**Windows:**
```cmd
python bot.py
```

O bot vai:
- Monitorar a mana continuamente
- Criar uma runa sempre que a mana atingir o gatilho
- Clicar com botão direito na comida a cada X segundos
- Parar automaticamente após criar a quantidade configurada de runas
- Tocar um som ao concluir

**Controles durante a execução:**
- `F8` — pausar/despausar
- `ESC` — parar
- Mover o mouse para o canto superior esquerdo — parada de emergência

---

## Bot de Fishing (`fish.py`)

Pesca automaticamente clicando com o botão direito na fishing rod e depois com
o botão esquerdo em cada SQM configurado, em sequência e em loop.

### Como usar

Com o jogo aberto e visível:

**macOS / Linux:**
```bash
python3 fish.py
```

**Windows:**
```cmd
python fish.py
```

Na primeira execução, o script vai pedir para você configurar:

1. Posição da **fishing rod** (onde ela fica no inventário)
2. Posição dos **10 SQMs** onde quer pescar (um por um)

Depois de configurar, ele começa a pescar: clica com botão direito na fishing
rod, clica com botão esquerdo no SQM 1, repete para o SQM 2, e assim por diante
até o SQM 10. Quando terminar todos os 10, reinicia do SQM 1 automaticamente.

O loop continua até você apertar **ESC**.

### Reconfigurar

Se quiser capturar as posições novamente:

```bash
python3 fish.py --setup
```

Ou rode normalmente — quando já existe uma config salva, o script pergunta se
você quer iniciar ou reconfigurar antes de começar.

**Controles durante a execução:**
- `ESC` — parar
- Mover o mouse para o canto superior esquerdo — parada de emergência

---

## Ajustes finos

### A detecção de mana está errada?

Abra `bot.py` e ajuste a função `is_blue_pixel`:

```python
def is_blue_pixel(r, g, b):
    return b > 100 and b > r + 30 and b > g + 20
```

Os limiares `100`, `30` e `20` podem ser ajustados se a barra do seu jogo
tiver um tom de azul diferente.

### O arrasto é muito rápido/lento?

Em `bot.py`, na função `drag`, ajuste o parâmetro `duration`.

### Quer mudar alguma coordenada sem refazer tudo?

Abra o `config.json` direto e edite o valor.

---

## Solução de problemas

### macOS: "Python quit unexpectedly" ou crash

Se você está usando **Python 3.14 no macOS recente** e o `pynput` causa crash, instale uma versão anterior do Python (3.11 ou 3.12 funcionam bem).

### macOS: o bot não move o mouse nem clica

Verifique novamente as permissões em *Privacidade e Segurança* e feche/reabra o Terminal.

### Windows: o bot "clica" mas o jogo não recebe

Isso geralmente significa que o jogo está rodando como Administrador e o terminal não. Rode o terminal como Administrador.

### As coordenadas capturadas estão estranhas

No macOS com tela Retina pode haver diferença entre coordenadas lógicas e físicas. Se a detecção da barra de mana falhar, a solução é capturar a barra com o jogo na mesma posição em que vai ser usado depois.

---

## Aviso

Verifique as regras do jogo antes de usar. Muitos jogos proíbem
automação e podem banir contas que usem esse tipo de ferramenta.
Use por sua conta e risco.