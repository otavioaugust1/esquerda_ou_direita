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

1. **Coleta** — o sistema busca dados públicos do perfil em 3 plataformas (Twitter/X, Instagram, Facebook) + fontes complementares (Google News, Wikipédia, DuckDuckGo)
2. **Processamento** — o texto coletado é normalizado (sem acentos, minúsculas) e comparado com listas de palavras-chave e nomes de figuras políticas
3. **Pontuação** — cada ocorrência gera pontos: palavras-chave = 1pt, nomes = 2pt, figuras políticas seguidas = 3× o score da figura
4. **Classificação** — a proporção entre pontos de esquerda e direita determina a classificação final e o percentual de confiança

### Análise por plataforma

Uma pessoa pode ter **comportamento político diferente** em cada rede social. Por isso, cada plataforma é analisada separadamente. O resultado final combina todas as fontes.

---

## 🎯 Calibração do Modelo

O modelo foi calibrado manualmente, sem machine learning. A calibração segue estas etapas:

### 1. Seleção de figuras de referência

~120 perfis de políticos, jornalistas, influenciadores e veículos de mídia foram classificados manualmente em uma escala de -2 (esquerda forte) a +2 (direita forte).

### 2. Curadoria de palavras-chave

~45 termos associados à esquerda e ~45 termos associados à direita foram selecionados a partir de discursos, hashtags e publicações reais de figuras políticas brasileiras.

### 3. Pesos diferenciados

Nem toda evidência tem o mesmo peso:

| Tipo de Evidência | Peso | Justificativa |
|---|---|---|
| Palavra-chave | 1pt | Pode aparecer em contextos variados |
| Nome de figura política | 2pt | Menção direta a uma pessoa conhecida |
| Figura política seguida | 3× score | Seguir alguém é escolha deliberada |

**Seguir uma figura** é mais revelador que uma menção textual — é o indicador mais confiável.

### 4. Validação empírica

O modelo foi testado com perfis públicos conhecidos:

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
| ≥ 15 | ALTA |
| 8–14 | MÉDIA |
| 3–7 | BAIXA |
| 0–2 | MUITO BAIXA |

---

## 🔤 Palavras-chave Utilizadas

Cada ocorrência de uma palavra-chave no texto coletado vale **1 ponto** para o lado correspondente. As palavras foram selecionadas por sua associação frequente com discursos de cada espectro político no Brasil.

### 🔴 Esquerda (~45 termos)

`democracia`, `democrático`, `direitos`, `humanos`, `justiça social`, `igualdade`, `trabalhador`, `trabalhadores`, `SUS`, `saúde pública`, `educação`, `feminismo`, `feminista`, `LGBT`, `LGBTQIA`, `diversidade`, `inclusão`, `amazônia`, `indígena`, `quilombola`, `reforma agrária`, `PT`, `PSOL`, `PCdoB`, `socialismo`, `socialista`, `progressista`, `coletivo`, `popular`, `povo`, `antifascismo`, `antifascista`, `resistência`, `redistribuição`, `minorias`, `oprimidos`, `regulação`, `soberania`, `intervenção`, `Lula`, `Dilma`, `Boulos`, `Haddad`, `Janones`, `Freixo`, `Duvivier`, `Sakamoto`

### 🔵 Direita (~45 termos)

`liberdade econômica`, `livre mercado`, `capitalismo`, `empreendedor`, `empreendedorismo`, `privatização`, `privatizar`, `meritocracia`, `imposto`, `impostos`, `redução`, `família tradicional`, `cristão`, `cristãos`, `conservador`, `conservadorismo`, `direita`, `petismo`, `corrupção`, `patriota`, `patriotismo`, `armamento`, `armas`, `segurança`, `ordem`, `militar`, `agronegócio`, `agro`, `liberal`, `liberalismo`, `propriedade privada`, `anticomunismo`, `anticomunista`, `comunismo`, `doutrinação`, `ideologia de gênero`, `valores`, `moral`, `nação`, `nacionalismo`, `Bolsonaro`, `Moro`, `Nikolas`, `Zambelli`, `Marçal`, `Gayer`

### 📝 Nota sobre palavras ambíguas

Algumas palavras como "democracia", "liberdade" e "soberania" são usadas por ambos os lados. Nesta versão, cada termo está associado a apenas um lado com base em sua **frequência de uso predominante** no discurso político brasileiro. Uma versão futura poderia usar pesos fracionários ou análise de contexto.

---

## 👥 Banco de Figuras Políticas

O app contém ~120 perfis classificados manualmente. Quando o sistema identifica que o usuário analisado **segue** uma dessas figuras, o score da figura é multiplicado por **3×** e adicionado à pontuação. Esta é a evidência de maior peso no modelo.

| Score | Classificação | Exemplos |
|---|---|---|
| **-2** | Esquerda Forte | Lula, Dilma, Boulos, Janones, Gleisi, Freixo, Jean Wyllys, Gregório Duvivier, Jones Manoel, Sabrina Fernandes, Brasil 247, Mídia NINJA, DCM, Opera Mundi |
| **-1** | Centro-Esquerda | Ciro Gomes, Marina Silva, Flávio Dino, Tabata Amaral, Reinaldo Azevedo, Carta Capital, The Intercept Brasil |
| **0** | Centro (Imprensa) | Folha de S.Paulo, Estadão, O Globo, G1, UOL, BBC Brasil, CNN Brasil, BandNews, SBT, Record, Jornal Nacional |
| **+1** | Centro-Direita | Tarcísio, Sérgio Moro, Romeu Zema, Kim Kataguiri, Van Hattem, Alexandre Garcia, Jovem Pan, Gazeta do Povo, O Antagonista |
| **+2** | Direita Forte | Bolsonaro (família), Nikolas Ferreira, Carla Zambelli, Damares, Pablo Marçal, Rodrigo Constantino, Brasil Paralelo, Revista Oeste, Terça Livre |

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
