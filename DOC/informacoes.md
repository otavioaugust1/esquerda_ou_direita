# 📚 Documentação Completa — Esquerda ou Direita?

> Tudo sobre o funcionamento do analisador, conceitos políticos, metodologia de calibração, aspectos legais e preocupações éticas.

---

## Sumário

1. [⚖️ O que é Esquerda e Direita?](#️-o-que-é-esquerda-e-direita)
2. [🔬 Sobre este Aplicativo](#-sobre-este-aplicativo)
3. [🎯 Calibração do Modelo](#-calibração-do-modelo)
4. [🔤 Palavras-chave Utilizadas](#-palavras-chave-utilizadas)
5. [👥 Banco de Figuras Políticas](#-banco-de-figuras-políticas)
6. [📺 Por que a Imprensa tem Score 0?](#-por-que-a-imprensa-tem-score-0)
7. [🔒 LGPD, Marco Civil e Dados Públicos](#-lgpd-marco-civil-e-dados-públicos)
8. [🌐 Polarização Política](#-polarização-política-importância-e-preocupações)
9. [🚧 Limitações Conhecidas](#-limitações-conhecidas)

---

## ⚖️ O que é Esquerda e Direita?

A divisão **esquerda–direita** tem origem na Revolução Francesa (1789), quando os deputados que apoiavam o rei se sentavam à *direita* do presidente da Assembleia, e os que defendiam reformas populares se sentavam à *esquerda*.

Ao longo dos séculos, essa divisão evoluiu e ganhou significados mais amplos:

### 🔴 Esquerda

- **Estado ativo** — defende maior participação do Estado na economia e políticas sociais
- **Igualdade social** — redistribuição de renda, cotas, políticas afirmativas
- **Direitos sociais** — SUS, educação pública, programas de transferência de renda
- **Progressismo** — defesa de direitos LGBT+, feminismo, laicidade do Estado
- **Meio ambiente** — preservação ambiental, demarcação de terras indígenas
- **Trabalhismo** — sindicatos, direitos trabalhistas, salário mínimo

**Partidos associados:** PT, PSOL, PCdoB, PDT, Rede

### 🟡 Centro

- **Pragmatismo** — posições moderadas, negociação entre lados
- **Equilíbrio** — Estado presente, mas com espaço para a iniciativa privada
- **Reformismo gradual** — mudanças incrementais, sem rupturas
- **Institucionalismo** — defesa das instituições democráticas

**Partidos associados:** MDB, PSD, PSDB

### 🔵 Direita

- **Livre mercado** — menos intervenção estatal, privatizações, empreendedorismo
- **Meritocracia** — igualdade de oportunidades, não de resultados
- **Conservadorismo** — valores tradicionais, família, religião
- **Segurança** — endurecimento penal, armamento, ordem pública
- **Patriotismo** — nacionalismo, soberania, fortalecimento militar
- **Redução de impostos** — estado mínimo, desburocratização

**Partidos associados:** PL, NOVO, PP, Republicanos

### ⚠️ Simplificação necessária

O espectro esquerda–direita é uma **simplificação**. Uma pessoa pode ser economicamente liberal (direita) e socialmente progressista (esquerda), ou vice-versa. Existem outros eixos como autoritarismo vs. libertarismo, globalismo vs. nacionalismo, etc. Este app utiliza o eixo unidimensional como ferramenta de estudo.

---

## 🔬 Sobre este Aplicativo

O **Esquerda ou Direita?** é um projeto de **estudo acadêmico** que analisa a tendência política de perfis públicos a partir de dados disponíveis publicamente na internet.

### Como funciona

1. **Coleta paralela** — o sistema busca dados públícos do perfil em 4 fontes **simultaneamente** via `ThreadPoolExecutor`: Twitter/X, Instagram, Facebook e Web/Notícias (Google News, Wikipédia, DuckDuckGo). O tempo total é equivalente à coleta mais lenta, não a soma de todas.
2. **Processamento** — o texto coletado é normalizado (sem acentos, minúsculas) e comparado com listas de palavras-chave e nomes de figuras políticas
3. **Pontuação** — cada ocorrência gera pontos: palavras-chave simples = 1pt, nomes = 2pt, frases compostas = 2pt, figuras políticas seguidas = **5× o score da figura** (cada figura contada uma vez)
4. **Classificação** — a proporção entre pontos de esquerda e direita determina a classificação final e o percentual de confiança

### Análise por plataforma

Uma pessoa pode ter **comportamento político diferente** em cada rede social. Por isso, cada plataforma é analisada separadamente. O resultado final combina todas as fontes.

---

## 🛠️ Arquitetura do Código

O motor de análise está organizado como um **pacote Python modular**:

| Módulo | Responsabilidade |
|---|---|
| `analisador/__init__.py` | Orquestra a execução paralela e consolida os resultados |
| `analisador/dados.py` | Banco de figuras políticas, palavras-chave e configurações |
| `analisador/utils.py` | Normalização de texto, filtros de username e busca na web |
| `analisador/analise.py` | Pontuação por palavras-chave, seguidores e classificação |
| `analisador/twitter.py` | Coleta Twitter/X: API v2, Nitter e busca web |
| `analisador/instagram.py` | Coleta Instagram: scraping público e busca web |
| `analisador/facebook.py` | Coleta Facebook: scraping público e busca web |
| `analisador/geral.py` | Coleta Web: Google News, Wikipédia, busca genérica |

---

## 🎯 Calibração do Modelo

O modelo foi calibrado manualmente, sem machine learning. A calibração segue estas etapas:

### 1. Seleção de figuras de referência

**~430 perfis** de políticos (governadores, senadores, deputados federais), partidos, jornalistas, influenciadores, ministérios do governo federal e veículos de mídia foram classificados manualmente em uma escala de -2 (esquerda forte) a +2 (direita forte).

### 2. Curadoria de palavras-chave

50 termos/frases de esquerda e 50 termos/frases de direita foram selecionados a partir de discursos, hashtags e publicações reais de figuras políticas brasileiras. Palavras ambíguas foram **removidas** para evitar falsos positivos. Os bancos estão **balanceados** (mesma quantidade) para não distorcer resultados.

### 3. Pesos diferenciados

Nem toda evidência tem o mesmo peso:

| Tipo de Evidência | Peso | Justificativa |
|---|---|---|
| Palavra-chave simples | 1pt | Pode aparecer em contextos variados |
| Nome de figura política | 2pt | Menção direta a uma pessoa conhecida |
| Frase composta detectada | 2pt | Termos específicos multi-palavra |
| Figura política seguida | 5× score | Seguir alguém é escolha deliberada |

**Seguir uma figura** é o indicador mais confiável — cada figura é contada apenas uma vez (sem duplicatas).

### 4. Validação empírica

O modelo foi testado com perfis públícos conhecidos (execução paralela):

| Perfil | Resultado Geral | Twitter/X | Instagram | Facebook |
|---|---|---|---|---|
| **Lula** | ESQUERDA 87% | 100% ESQ | 90.9% ESQ | 82.8% ESQ |
| **Bolsonaro** | DIREITA 78.2% | 93.5% DIR | 82.2% DIR | 78.4% DIR |

Esses resultados validam a coerência do modelo.

### Escala de classificação

| Score | Classificação |
|---|---|
| **-2** | Esquerda forte |
| **-1** | Centro-esquerda |
| **0** | Centro |
| **+1** | Centro-direita |
| **+2** | Direita forte |

### Níveis de confiança

| Total de Evidências | Confiança |
|---|---|
| < 3 | INCONCLUSIVO |
| 3–4 | MUITO BAIXA |
| 5–14 | BAIXA |
| 15–29 | MÉDIA |
| ≥ 30 | ALTA |

---

## 🔤 Palavras-chave Utilizadas

Cada ocorrência de uma palavra-chave vale **1 ponto**; frases compostas (com espaço) valem **2 pontos**. Palavras genéricas usadas por ambos os lados foram **removidas** para evitar falsos positivos.

### 🔴 Esquerda (50 termos e frases)

**Palavras simples — 32 termos (1pt):**  
`igualdade`, `feminismo`, `feminista`, `LGBTQIA`, `indígena`, `quilombola`, `socialismo`, `socialista`, `progressista`, `antifascismo`, `antifascista`, `redistribuição`, `minorias`, `oprimidos`, `esquerda`, `progressismo`, `inclusão`, `diversidade`, `PSOL`, `PCdoB`, `Lula`, `Dilma`, `Boulos`, `Haddad`, `Janones`, `Freixo`, `Sakamoto`, `vacinação`, `SUS`, `desigualdade`, `trabalhismo`, `trabalhista`

**Frases compostas — 18 termos (2pt):**  
`saúde pública`, `saúde coletiva`, `política pública`, `políticas públicas`, `assistência social`, `educação pública`, `Bolsa Família`, `saúde mental`, `combate à fome`, `Fome Zero`, `cotas raciais`, `ação afirmativa`, `movimento social`, `movimentos sociais`, `reforma agrária`, `direitos humanos`, `direitos trabalhistas`, `renda básica`

### 🔵 Direita (50 termos e frases)

**Palavras simples — 30 termos (1pt):**  
`meritocracia`, `bolsonaro`, `bolsonarismo`, `bolsonarista`, `petismo`, `petista`, `agronegócio`, `neoliberalismo`, `privatismo`, `anticomunismo`, `anticomunista`, `antiesquerda`, `doutrinação`, `globalismo`, `globalista`, `Nikolas`, `Zambelli`, `Marçal`, `Gayer`, `privatização`, `comunismo`, `marxismo`, `marxista`, `conservadorismo`, `olavismo`, `olavista`, `armamentismo`, `petralha`, `mortadela`, `patriotismo`

**Frases compostas — 20 termos (2pt):**  
`ideologia de gênero`, `kit gay`, `família tradicional`, `valores conservadores`, `escola sem partido`, `estado mínimo`, `livre mercado`, `voto impresso`, `fraude eleitoral`, `intervenção militar`, `Globo mentira`, `mamãe falei`, `Brasil acima de tudo`, `Deus acima de todos`, `porte de arma`, `imposto é roubo`, `contra o aborto`, `comunismo na educação`, `aparelhamento do estado`, `menos estado`

### 📝 Princípio de especificidade

Palavras como "patriota", "cristão", "empreendedor", "agro", "armado", "popular", "povo", "capitalismo", "conservador" foram **removidas** pois são usadas por ambos os lados e geravam falsos positivos.

---

## 👥 Banco de Figuras Políticas

O app contém **~430 perfis** classificados manualmente: partidos políticos, governadores, senadores, deputados federais (de diversos partidos: PT, PSOL, PCdoB, PSB, PDT, MDB, PSD, PP, PSDB, União Brasil, Republicanos, NOVO, Podemos e PL), lideranças nacionais, ministérios do governo federal e veículos de mídia. Quando o sistema identifica que o usuário seguia uma dessas figuras, o score é multiplicado por **5×** e adicionado à pontuação (cada figura contada uma única vez). Além disso, o sistema mantém **~56 nomes de esquerda** e **~48 nomes de direita** para detecção textual em notícias, bios e publicações (peso 2pt por menção).

| Score | Classificação | Exemplos |
|---|---|---|
| **-2** | Esquerda Forte | **Partidos:** PT, PCdoB, PSOL · **Governo Lula:** Min. Saúde, Fiocruz, Gov. Federal, Planalto, MEC, Min. Meio Ambiente, Min. Cidades · **Lideranças:** Lula, Dilma, Boulos, Janones, Gleisi, Freixo, Jean Wyllys, Gregório Duvivier, Jones Manoel, Sabrina Fernandes · **Governadores:** Elmano (CE/PT), Jerônimo (BA/PT), Fátima (RN/PT), Camilo Santana, Rafael Fonteles (PI/PT) · **Senadores:** Paulo Paim, Randolfe, Humberto Costa, Jaques Wagner, Fabiano Contarato, Rogério Carvalho · **Deputados:** Sâmia Bomfim, Glauber Braga, Taliria, Fernanda Melchionna, Jandira Feghali, Erika Kokay, Erika Hilton, Luíza Erundina, Benedita da Silva, Perpétua Almeida, Alice Portugal, Léo Péricles, Rui Falcão, Chico Alencar · **Mídia:** Brasil 247, Mídia NINJA, DCM Online, Opera Mundi, Revista Fórum |
| **-1** | Centro-Esquerda | **Partidos:** PDT, PSB, Rede Sustentabilidade · **Lideranças:** Ciro Gomes, Marina Silva, Flávio Dino, Tabata Amaral, Reinaldo Azevedo, Luís Nassif, Juca Kfouri · **Governadores:** Helder Barbalho (PA), Casagrande (ES), João Campos (Recife), Clécio Luís (AP) · **Senadores:** Renan Calheiros, Omar Aziz, Eliziane Gama, Weverton Rocha · **Mídia:** Carta Capital, The Intercept Brasil |
| **0** | Centro (Imprensa) | **Partidos:** MDB, PSD, Cidadania, Avante, Solidariedade · **Líderes:** Rodrigo Pacheco, Eduardo Leite (Gov. RS), Ibaneis (Gov. DF), Raquel Lyra (Gov. PE) · **Mídia:** Folha de S.Paulo, Estadão, O Globo, G1, UOL, BBC Brasil, CNN Brasil, BandNews, SBT, Record, Jornal Nacional, Correio Braziliense, Valor Econômico, Agência Senado, Agência Câmara |
| **+1** | Centro-Direita | **Partidos:** PSDB, União Brasil, Podemos, Republicanos, PP, NOVO · **Lideranças:** Tarcísio (Gov. SP), Sérgio Moro (Sen.), Romeu Zema (Gov. MG), Kim Kataguiri, Van Hattem, Hamilton Mourão · **Governadores:** Ratinho Jr (PR), Caiado (GO), Mauro Mendes (MT), Eduardo Riedel (MS), Wanderlei Barbosa (TO) · **Senadores:** Ciro Nogueira, Marcos Pontes, Efraim Filho · **Deputados:** Arthur Lira (PP/AL), Aécio Neves, Elmar Nascimento, Celso Russomanno, Tiago Mitraud · **Mídia:** Jovem Pan, Gazeta do Povo, O Antagonista, Alexandre Garcia, Leandro Narloch |
| **+2** | Direita Forte | **Partidos:** PL · **Lideranças:** Bolsonaro (família), Nikolas Ferreira, Carla Zambelli, Damares Alves, Pablo Marçal, Rodrigo Constantino, Allan dos Santos, Bernardo Küster · **Governadores:** Jorginho Mello (SC/PL), Cláudio Castro (RJ/PL) · **Senadores:** Flávio Bolsonaro, Damares, General Girão, Marcos Rogério · **Deputados:** Eduardo Bolsonaro, Bia Kicis, Marco Feliciano, Sóstenes Cavalcante, André Fernandes, Daniel Silveira, Filipe Barros, Gustavo Gayer, Delegado Bilynsky e dezenas de outros do PL · **Mídia:** Brasil Paralelo, Revista Oeste, Terça Livre, Senso Incomum, Conexão Política |

---

## 📺 Por que a Imprensa tem Score 0?

Veículos de imprensa tradicionais como Folha, Estadão, Globo, UOL, CNN Brasil e BBC Brasil recebem score **0 (neutro/centro)** no modelo. Esta é uma decisão deliberada de design:

### 1. Audiência transversal

Veículos de grande imprensa são seguidos por pessoas de **todos os espectros políticos**. Um apoiador de Lula e um de Bolsonaro podem ambos seguir a Folha. Portanto, seguir um veículo de mídia não indica posição política.

### 2. Evitar falsos positivos

Se a Folha tivesse score -1 (centro-esquerda), qualquer pessoa que a seguisse teria sua análise distorcida para a esquerda — mesmo que seja conservadora. O score 0 **não polui** a análise.

### 3. Neutralidade metodológica

Classificar veículos de imprensa como esquerda ou direita é um debate complexo e subjetivo. O modelo opta por **não se posicionar** sobre a orientação editorial da mídia tradicional, focando apenas em figuras e veículos **explicitamente engajados**.

### Veículos com score 0

Folha de S.Paulo, Estadão, O Globo, G1, UOL, BBC Brasil, CNN Brasil, BandNews, SBT, Record, Jornal Nacional

### Veículos com viés editorial explícito

Já veículos com viés editorial explícito recebem scores diferentes de zero:

| Veículo | Score | Lado |
|---|---|---|
| Brasil 247 | -2 | Esquerda Forte |
| Mídia NINJA | -2 | Esquerda Forte |
| DCM Online | -2 | Esquerda Forte |
| Opera Mundi | -2 | Esquerda Forte |
| Carta Capital | -1 | Centro-Esquerda |
| The Intercept Brasil | -1 | Centro-Esquerda |
| Gazeta do Povo | +1 | Centro-Direita |
| O Antagonista | +1 | Centro-Direita |
| Jovem Pan | +1 | Centro-Direita |
| Revista Oeste | +2 | Direita Forte |
| Brasil Paralelo | +2 | Direita Forte |
| Terça Livre | +2 | Direita Forte |

---

## 🔒 LGPD, Marco Civil e Dados Públicos

### Lei Geral de Proteção de Dados (LGPD — Lei 13.709/2018)

A LGPD regula o tratamento de dados pessoais no Brasil. Pontos relevantes para este projeto:

- **Art. 7º, §4º** — dados tornados **manifestamente públicos** pelo titular podem ser tratados sem consentimento, desde que respeitados os princípios da lei
- **Art. 7º, IV** — o tratamento é permitido para **estudos por órgão de pesquisa**, garantida a anonimização quando possível
- Publicações em redes sociais com perfil **público** são consideradas dados manifestamente públicos pelo titular

### Marco Civil da Internet (Lei 12.965/2014)

- **Art. 7º, I** — garante a **inviolabilidade e sigilo** das comunicações privadas. Este app não acessa mensagens privadas
- **Art. 7º, III** — garante a **inviolabilidade e sigilo** dos dados pessoais armazenados. Este app não armazena dados

### Como este app respeita a legislação

| Prática | Status |
|---|---|
| Apenas dados **públicos** são coletados | ✅ |
| **Nenhum dado é armazenado** — processamento em memória | ✅ |
| Não acessa mensagens privadas, DMs ou dados restritos | ✅ |
| Não cria perfil de comportamento persistente | ✅ |
| Finalidade de **estudo acadêmico** | ✅ |
| Não monetiza nem compartilha dados com terceiros | ✅ |

### ⚠️ Aviso legal

Este projeto é uma ferramenta de **estudo**. O uso da classificação gerada para fins de discriminação, perseguição, assédio ou qualquer ação que viole a dignidade de uma pessoa é **ilegal** — tanto pela LGPD quanto pelo Código Penal (Art. 140 — Injúria, Art. 147 — Ameaça). O autor não se responsabiliza pelo uso indevido da ferramenta.

---

## 🌐 Polarização Política: Importância e Preocupações

### O fenômeno das bolhas

As redes sociais criaram **câmaras de eco** (echo chambers) onde as pessoas são expostas predominantemente a opiniões que confirmam suas próprias crenças. Os algoritmos de recomendação amplificam esse efeito, criando **bolhas ideológicas** cada vez mais fechadas.

### Por que estudar polarização?

- **Consciência** — entender em que bolha você está é o primeiro passo para buscar informação diversificada
- **Diálogo** — reconhecer a existência de diferentes perspectivas políticas facilita o diálogo democrático
- **Pensamento crítico** — questionar mensagens políticas e verificar fontes combate a desinformação
- **Saúde democrática** — democracias saudáveis dependem de cidadãos informados de múltiplas perspectivas

### Preocupações éticas

#### 🏷️ Rotulação
Classificar pessoas como "esquerda" ou "direita" simplifica a complexidade do pensamento individual. Nenhuma pessoa é definida por um rótulo.

#### 🎯 Uso indevido
Ferramentas de classificação política podem ser usadas para perseguição, discriminação ou manipulação. Este não é o propósito deste app.

#### 🤖 Automação
Classificações automatizadas sempre terão erros. Ironia, sarcasmo, citações e mudanças de opinião não são detectados por palavra-chave.

#### 📊 Viés do modelo
A seleção de palavras-chave e figuras políticas reflete as escolhas do desenvolvedor. Outro pesquisador poderia escolher termos e pesos diferentes.

### 💡 Propósito deste projeto

Este app **não** foi criado para rotular ou atacar pessoas. Foi criado como um **exercício de análise de dados textuais** e como reflexão sobre como nossas escolhas online — quem seguimos, o que publicamos, o que curtimos — constroem uma **identidade digital** que pode ser interpretada politicamente.

O objetivo é **educacional**: provocar reflexão sobre bolhas informacionais e a importância de buscar **diversidade de fontes**.

---

## 🚧 Limitações Conhecidas

| Limitação | Descrição |
|---|---|
| 🎭 Sem detecção de ironia | Se alguém cita ironicamente "viva o capitalismo!", o modelo conta como ponto de direita |
| 📱 APIs limitadas | Instagram e Facebook não têm API pública. Os dados vêm de busca web, que é incompleta |
| 🔑 Twitter API opcional | Sem a chave TWITTER_BEARER_TOKEN, a análise do Twitter usa apenas busca web |
| 👤 Perfis privados | Perfis privados ou protegidos não são acessíveis. A análise ficará incompleta |
| 🌍 Contexto brasileiro | Palavras-chave e figuras são do cenário político brasileiro. Não funciona para outros países |
| ⏱️ Snapshot temporal | A análise reflete o momento da consulta. Pessoas mudam de opinião ao longo do tempo |

---

## 📄 Licença

**MIT License** — Veja [LICENSE](../LICENSE).

## 👤 Autor

**Otávio August**
- 🌐 GitHub: [@otavioaugust1](https://github.com/otavioaugust1)
- 🇧🇷 Brasil
