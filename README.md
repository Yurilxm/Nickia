# Nickia

Sistema local de síntese de voz com clonagem para narração de vídeos de lojá.
Roda 100% offline no Windows, sem APIs pagas, sem mensalidade, sem Docker, sem banco de dados.

Feito para uso direto, sem depender de terminal: a pessoa digita o texto,
gera o áudio com a própria voz, edita junto do vídeo e baixa o resultado.
Tudo pelo navegador.

---

## O que faz

1. **Gera narração** - texto em voz clonada, portugues brasileiro (WAV + MP3)
2. **Edita vídeo** - subir vídeo da lojá, escolher narração, cortar, ajustar modo de encaixe
3. **Voz de referencia** - cadastro por upload de qualquer formato (WhatsApp, gravador, MP4)
4. **Dicionario de pronúncia** - corrige palavras que o modelo fala errado (ex.: `leggings` -> `leguins`)
5. **Historico** - tudo que foi gerado fica disponivel para reuso, com nome, player e download

---

## Requisitos

- Windows 10/11
- Python 3.10 (instalado automaticamente pelo `install.ps1` se não existir)
- FFmpeg (instalado automaticamente)
- ~5 GB livres em disco (modelo + venv + áudios)
- 16 GB de RAM recomendado

Nao precisa de GPU. O sistema roda na CPU. Ryzen 5 8600G ou superior da conta.

---

## Instalacao

Em um PowerShell, na pasta onde voce quer o projeto:

    git clone <URL_DO_REPO> Nickia
    cd Nickia
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1

O instalador vai:

- Verificar/instalar Python 3.10
- Verificar/instalar FFmpeg
- Criar o venv e instalar as dependências
- Baixar o modelo de voz (~2 GB, uma vez so)
- Criar um atalho **Nickia** no Desktop

---

## Uso no dia a dia

Duplo clique no atalho **Nickia** do Desktop. O navegador abre sozinho em `http://localhost:8000`.

Para fechar, feche a jánela preta (o servidor).

### Fluxo recomendado

**1. Cadastrar a voz (uma vez so)**

- Aba **Gerar áudio** -> expandir **Cadastrar uma nova voz**
- Nome curto (`mae`) + arquivo de áudio limpo (10-20 s, sem musica, sem eco)
- Clica em **Enviar voz**

**2. Gerar uma narração**

- Aba **Gerar áudio** -> digitar o texto -> escolher a voz -> **Gerar narração**
- Ao terminar, o áudio aparece com player, download e opcao **Gerar outra versao**

**3. Editar o vídeo**

- Aba **Editar vídeo** -> escolher o vídeo da lojá -> escolher a narração
- Ajustar o **trecho do áudio** e o **trecho do vídeo** arrastando os handles nas trilhas
- Escolher **como encaixar** (áudio normal / repetir / ajustar vídeo ao áudio)
- Ajustar volume do som original do vídeo (0% = mudo)
- **Gerar vídeo** -> baixar

---

## Estrutura

    Nickia/
    |-- app/           Backend FastAPI (rotas, jobs em memória)
    |-- engine/        Interface TTSEngine + implementação Chatterbox
    |-- text/          Normalizacao, split de frases, pronúncia
    |-- áudio/         Concatenacao, conversão MP3, composição de vídeo
    |-- web/           Interface (HTML + CSS + JS puro)
    |-- data/
    |   |-- voices/    Audios de referencia (NAO versionado)
    |   |-- output/    Audios/vídeos gerados (NAO versionado)
    |   |-- texto.txt
    |   `-- pronúnciation.json
    |-- scripts/       Instalacao, teste manual, smoke tests
    |-- tests/         Suite pytest (44 testes)
    `-- config.py      Configuracoes centrais

---

## Testes

    python -m pytest tests/ -v

Cobrem: normalização de texto, pronúncia, split, concat, conversão MP3,
jobs, API FastAPI e composição de vídeo (5 modos + trims).

---

## Tecnologias

| Camada       | Stack                                       |
|--------------|---------------------------------------------|
| Motor de voz | Chatterbox Multilingual PT-BR (MIT)         |
| Backend      | FastAPI + Uvicorn                           |
| Inferencia   | PyTorch 2.6 (CPU)                           |
| Audio/Video  | FFmpeg                                      |
| Frontend     | HTML + CSS + JavaScript (ES modules, sem framework) |
| Testes       | pytest                                      |

---

## Privacidade

Os áudios de referencia e os arquivos gerados ficam apenas no computador local.
Nada e enviado para servidores externos após o download inicial do modelo.
O sistema não remove a marca d'água PerTh do Chatterbox.

---

## Licenca

Modelo Chatterbox: MIT (Resemble AI).
Codigo do Nickia: uso pessoal.
