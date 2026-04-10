<div align="center">

# ⚖️ Esquerda ou Direita — Analisador de Orientação Política

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/otavioaugust1/esquerda_ou_direita/blob/main/LICENSE)
![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1+-green.svg)
![Status](https://img.shields.io/badge/status-Active-brightgreen.svg)

**Projeto de estudo acadêmico** que analisa a orientação política de perfis públicos em redes sociais com base em palavras-chave, figuras políticas seguidas e publicações públicas.

[🚀 Como Executar](#-como-executar) • [📊 Como Funciona](#-como-funciona-a-análise) • [🔌 API](#-endpoints) • [🏗️ Arquitetura](#-arquitetura) • [📚 Documentação](#-documentação)

</div>

---

## 📋 Sobre o Projeto

Este aplicativo web coleta **dados exclusivamente públicos** de redes sociais (Twitter/X, Instagram e Facebook) e aplica um modelo de classificação baseado em **palavras-chave** e **banco de figuras políticas conhecidas** para estimar se determinado perfil tende à **esquerda**, ao **centro** ou à **direita** do espectro político brasileiro.

**Importante:** Este é um exercício de análise textual, não uma classificação definitiva. O modelo possui limitações inerentes e deve ser interpretado com senso crítico.

---

## 🏗️ Arquitetura

```
esquerda_ou_direita/
│
├── app.py                  # Servidor Flask (rotas web e API JSON)
├── render.yaml             # Configuração de deploy no Render
├── requirements.txt        # Dependências Python
│
├── analisador/             # Pacote de análise (módulos independentes)
│   ├── __init__.py         # executar_analise — orquestra coleta PARALELA
│   ├── dados.py            # Constantes: FIGURAS_POLITICAS, PALAVRAS_*, NOMES_*
│   ├── utils.py            # Normalização, filtros, buscar_web/noticias/wikipedia
│   ├── analise.py          # Pontuação e classificação política
│   ├── twitter.py          # Coleta Twitter/X (API v2, Nitter, busca web)
│   ├── instagram.py        # Coleta Instagram (scraping + busca web)
│   ├── facebook.py         # Coleta Facebook (scraping + busca web)
│   └── geral.py            # Coleta Web/Notícias (Google News, Wikipédia)
│
├── templates/
│   ├── base.html           # Layout base (header, footer)
│   ├── index.html          # Página inicial (formulário de busca)
│   └── resultado.html      # Página de resultado (abas por plataforma)
│
├── static/
│   └── style.css           # Estilos (tema escuro, responsivo)
│
├── DOC/
│   └── informacoes.md      # Documentação detalhada do projeto
│
├── BKP/                    # Versões anteriores do script
│   └── ...
│
└── venv/                   # Ambiente virtual Python
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10+
- pip

### Instalação local

```bash
# 1. Clonar o repositório
git clone https://github.com/otavioaugust1/esquerda_ou_direita.git
cd esquerda_ou_direita

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. (Opcional) Configurar API do Twitter para melhores resultados
export TWITTER_BEARER_TOKEN="seu_bearer_token_aqui"

# 5. Iniciar o servidor
python app.py
```

O servidor estará disponível em **http://127.0.0.1:5000**.

### Deploy no Render (produção)

O projeto inclui `render.yaml` pronto para deploy:

1. Acesse [render.com](https://render.com) e conecte o repositório
2. O Render detecta automaticamente o `render.yaml` e configura o serviço
3. Defina a variável de ambiente `TWITTER_BEARER_TOKEN` (opcional) no painel
4. O deploy usa `gunicorn` como servidor WSGI de produção

---

## 📊 Como Funciona a Análise

### Coleta por Plataforma

Cada rede social é analisada **separadamente**, permitindo identificar que uma pessoa pode ter posições diferentes em cada plataforma:

| Plataforma | Fonte de Dados | Tipo de Coleta |
|---|---|---|
| **🐦 X / Twitter** | API v2 + Nitter + busca web | Tweets, bios, perfis seguidos |
| **📸 Instagram** | Scraping público + busca web | Bio, perfil público, menções |
| **👤 Facebook** | Scraping público + busca web | Bio, página pública, menções |
| **🌐 Web / Notícias** | DuckDuckGo, Google News, Wikipédia | Notícias, artigos, menções |

> **⚡ Execução paralela:** as quatro fontes são coletadas **simultaneamente** via `ThreadPoolExecutor`, reduzindo o tempo total para ≈ o tempo da coleta mais lenta.

### Modelo de Classificação

O modelo utiliza **três estratégias combinadas**:

1. **Palavras-chave** — 50 termos/frases de esquerda e 50 de direita (peso 1 por palavra simples, 2 por frase composta)
2. **Nomes conhecidos** — ~56 nomes de esquerda e ~48 de direita para detecção textual (peso 2 por menção)
3. **Figuras seguidas** — ~430 perfis políticos catalogados com score de -2 a +2 (peso **5× o score** por figura)

### Escala de Classificação

| Score | Classificação | Exemplo |
|---|---|---|
| **-2** | Esquerda forte | PT, PSOL, PCdoB, Lula, Boulos, Janones, Gleisi |
| **-1** | Centro-esquerda | Ciro Gomes, Marina Silva, Tabata Amaral, Carta Capital |
| **0** | Centro | Folha, Estadão, G1, BBC Brasil, CNN Brasil |
| **1** | Centro-direita | Sérgio Moro, Tarcísio, Gazeta do Povo, Jovem Pan |
| **2** | Direita forte | Bolsonaro, PL, Nikolas, Zambelli, Brasil Paralelo, Revista Oeste |

#### Por que a imprensa recebe score 0 (centro)?

Veículos como Folha de S.Paulo, Estadão, G1, O Globo, BBC Brasil, CNN Brasil, SBT e Record foram classificados com **score 0 (centro)** pois:

- São veículos de **grande circulação** que publicam conteúdo de autores de diferentes posições
- Seguir esses veículos **não indica orientação política** — milhões de pessoas de todos os espectros os acompanham
- Atribuir peso político a eles **distorceria a análise** de pessoas comuns que simplesmente se informam
- Jornais de referência buscam (ao menos formalmente) **equilíbrio editorial**, mesmo que tenham linha editorial própria

### Níveis de Confiança

| Total de Pontos | Confiança |
|---|---|
| < 3 | INCONCLUSIVO |
| 3–4 | MUITO BAIXA |
| 5–14 | BAIXA |
| 15–29 | MÉDIA |
| ≥ 30 | ALTA |

---

## 🔑 API do Twitter (Opcional)

Para melhores resultados, configure a API do Twitter v2:

1. Acesse [developer.twitter.com](https://developer.twitter.com/)
2. Crie um projeto (plano **Free** — sem cartão de crédito)
3. Copie o **Bearer Token**
4. Configure antes de executar:

```bash
export TWITTER_BEARER_TOKEN="seu_token"
```

Sem a API, o sistema funciona com busca web e Nitter como fallback, mas não consegue analisar **quem o perfil segue** (a fonte mais confiável para pessoas comuns).

---

## 🔒 Privacidade e Aspectos Legais

- **Dados públicos**: O sistema coleta APENAS informações que já são públicas nas redes sociais
- **LGPD**: Não há armazenamento de dados pessoais — tudo é processado em memória e descartado
- **Marco Civil da Internet (Lei 12.965/2014)**: O acesso a dados públicos para fins de pesquisa acadêmica é amparado por lei
- **Sem cadastro**: Nenhum dado do operador é coletado ou armazenado

Para mais detalhes, consulte [DOC/informacoes.md](DOC/informacoes.md).

---

## 📡 Endpoints

### Interface Web

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Página inicial com formulário |
| `/analisar` | POST | Executa análise e exibe resultado |

### API JSON

```bash
curl -X POST http://127.0.0.1:5000/api/analisar \
  -H "Content-Type: application/json" \
  -d '{"handle": "bolsonaro", "nome": "Jair Bolsonaro"}'
```

**Resposta:** JSON com classificação geral + `plataformas` contendo resultado individual de cada rede social.

---

## ⚠️ Limitações

- A análise é baseada em **palavras-chave**, não em compreensão semântica (NLP/IA)
- Instagram e Facebook **não oferecem API pública** para leitura de posts de terceiros — a coleta depende de busca web
- Perfis **privados** não podem ser analisados
- O banco de figuras políticas é focado no **cenário brasileiro**
- Pessoas sem presença pública significativa podem gerar resultados **inconclusivos**
- O modelo não detecta **ironia, sarcasmo ou citações contrárias**

---

## 🧪 Resultados de Validação

Testes realizados com perfis conhecidos:

| Perfil | Resultado Geral | Twitter/X | Instagram | Facebook |
|---|---|---|---|---|
| **Lula** | ESQUERDA 87% | 100% ESQ | 90.9% ESQ | 82.8% ESQ |
| **Bolsonaro** | DIREITA 78.2% | 93.5% DIR | 82.2% DIR | 78.4% DIR |

---

## 📚 Documentação

Consulte a documentação completa em [DOC/informacoes.md](DOC/informacoes.md), que inclui:

- Conceitos de esquerda e direita no espectro político
- Metodologia de calibração do modelo
- Lista completa de palavras-chave
- Aspectos legais (LGPD, Marco Civil da Internet)
- Reflexões sobre polarização política

---

## � Licença

**MIT License** — Use livremente, comercial ou pessoal. Veja [LICENSE](LICENSE).

---

## 👤 Autor

**Otávio August**
- 🌐 GitHub: [@otavioaugust1](https://github.com/otavioaugust1)
- 🇧🇷 Brasil

---

<div align="center">
<sub>Feito com ☕ e Python — Projeto de estudo acadêmico</sub>
</div>