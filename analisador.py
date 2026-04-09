"""
MÓDULO DE ANÁLISE POLÍTICA — POR PLATAFORMA
Coleta dados públicos de redes sociais e classifica orientação política.
Analisa cada plataforma (Twitter/X, Instagram, Facebook) separadamente.
Fontes: Twitter/X (API v2), Web Scraping, Google News, Wikipédia, DuckDuckGo
"""

import json
import os
import re
from collections import Counter
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv

load_dotenv()

try:
    from ddgs import DDGS

    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS

        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False

# =========================
# CONFIGURAÇÕES
# =========================

TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
TIMEOUT = 12

# =========================
# BANCO DE FIGURAS POLÍTICAS CONHECIDAS
# score: -2 = esquerda forte, -1 = centro-esquerda,
#         0 = centro, 1 = centro-direita, 2 = direita forte
# =========================

FIGURAS_POLITICAS = {
    # ════════════════════════════════════════
    # PARTIDOS POLÍTICOS
    # ════════════════════════════════════════

    # ── PARTIDOS ESQUERDA (-2) ──
    'pt_brasil': ('PT', -2),
    'ptbrasil': ('PT', -2),
    'pcdoboficial': ('PCdoB', -2),
    'psol50': ('PSOL', -2),
    'psoloficial': ('PSOL', -2),

    # ── PARTIDOS CENTRO-ESQUERDA (-1) ──
    'pdt_oficial': ('PDT', -1),
    'pdtoficial': ('PDT', -1),
    'psbnacional': ('PSB', -1),
    'psb_nacional': ('PSB', -1),
    'redesustentabilidade': ('Rede Sustentabilidade', -1),
    'rede_sustentabilidade': ('Rede Sustentabilidade', -1),

    # ── PARTIDOS CENTRO (0) ──
    'mdbnacional': ('MDB', 0),
    'mdb_oficial': ('MDB', 0),
    'psd_oficial': ('PSD', 0),
    'psdoficial': ('PSD', 0),
    'cidadaniaoficial': ('Cidadania', 0),
    'movimentoavante': ('Avante', 0),
    'solidariedade_br': ('Solidariedade', 0),

    # ── PARTIDOS CENTRO-DIREITA (1) ──
    'psdb': ('PSDB', 1),
    'psdb_oficial': ('PSDB', 1),
    'uniaobrasil': ('União Brasil', 1),
    'uniao_brasil': ('União Brasil', 1),
    'podemos_br': ('Podemos', 1),
    'podemosoficial': ('Podemos', 1),
    'republicanos10': ('Republicanos', 1),
    'republicanosbr': ('Republicanos', 1),
    'pp_progressistas': ('Progressistas', 1),
    'partidonovo30': ('Partido NOVO', 1),

    # ── PARTIDOS DIREITA (2) ──
    'pl_brasil': ('PL', 2),
    'ploficial': ('PL', 2),

    # ════════════════════════════════════════
    # GOVERNO FEDERAL LULA — MINISTÉRIOS E ÓRGÃOS (-2)
    # ════════════════════════════════════════
    'minsaude': ('Ministério da Saúde', -2),
    'ministeriodasaude': ('Ministério da Saúde', -2),
    'minsaude_': ('Ministério da Saúde', -2),
    'govbr': ('Governo Federal', -2),
    'secomgovbr': ('Secom Gov BR', -2),
    'planalto': ('Palácio do Planalto', -2),
    'mineducacao': ('MEC', -2),
    'mec_brasil': ('MEC', -2),
    'mds_brasil': ('Min. Desenvolvimento Social', -2),
    'mds_gov': ('Min. Desenvolvimento Social', -2),
    'agenciabrasil': ('Agência Brasil', -2),
    'portalsus': ('Portal SUS', -2),
    'sus_oficial': ('SUS Oficial', -2),
    'conass_br': ('CONASS', -2),
    'fiocruz': ('Fiocruz', -2),
    'fiocruzoficial': ('Fiocruz', -2),
    'nilsiatrindade': ('Nilsia Trindade', -2),
    'lulasaude': ('Lula Saúde', -2),
    'cremesp': ('CREMESP', -2),
    'cfm_oficial': ('CFM', -2),
    'alexandresilveira': ('Alexandre Silveira', -2),
    'jorgemeseias': ('Jorge Messias', -2),
    'analuisaaguimaraes': ('Ana Luísa Aguimarães', -2),
    'min_meio_ambiente': ('Min. Meio Ambiente', -2),
    'mcidades_oficial': ('Min. Cidades', -2),
    'mturismobrasil': ('Min. Turismo', -2),

    # ════════════════════════════════════════
    # GOVERNADORES
    # ════════════════════════════════════════

    # ── GOVERNADORES ESQUERDA (-2) ──
    'elmanofreitas': ('Elmano de Freitas (Gov. CE/PT)', -2),
    'jeronimobt': ('Jerônimo Rodrigues (Gov. BA/PT)', -2),
    'jeronimorodrigues': ('Jerônimo Rodrigues (Gov. BA/PT)', -2),
    'rafaelfonteles': ('Rafael Fonteles (Gov. PI/PT)', -2),
    'fatimabezerra': ('Fátima Bezerra (Gov. RN/PT)', -2),
    'camilosantana': ('Camilo Santana (Min. Educação/PT)', -2),

    # ── GOVERNADORES CENTRO-ESQUERDA (-1) ──
    'helderbarbalho': ('Helder Barbalho (Gov. PA/MDB)', -1),
    'helder_barbalho': ('Helder Barbalho (Gov. PA/MDB)', -1),
    'casagrande_es': ('Renato Casagrande (Gov. ES/PSB)', -1),
    'renatocasagrande': ('Renato Casagrande (Gov. ES/PSB)', -1),
    'joaocampos_': ('João Campos (Pref. Recife/PSB)', -1),
    'clecio_lm': ('Clécio Luís (Gov. AP/PDT)', -1),

    # ── GOVERNADORES CENTRO (0) ──
    'eduardoleite': ('Eduardo Leite (Gov. RS/PSDB)', 0),
    'ibaneisrocha': ('Ibaneis Rocha (Gov. DF/MDB)', 0),
    'raquellyra': ('Raquel Lyra (Gov. PE/PSDB)', 0),
    'paulodantas_al': ('Paulo Dantas (Gov. AL/MDB)', 0),

    # ── GOVERNADORES CENTRO-DIREITA (1) ──
    'tarcisiogdf': ('Tarcísio de Freitas (Gov. SP/Rep.)', 1),
    'romeuzema': ('Romeu Zema (Gov. MG/NOVO)', 1),
    'ronaldocaiado': ('Ronaldo Caiado (Gov. GO/União)', 1),
    'ratinhojunior': ('Ratinho Junior (Gov. PR/PSD)', 1),
    'mauro_mendes': ('Mauro Mendes (Gov. MT/União)', 1),
    'wanderlei_barbosa': ('Wanderlei Barbosa (Gov. TO/Rep.)', 1),
    'eduardoriedel': ('Eduardo Riedel (Gov. MS/PSDB)', 1),

    # ── GOVERNADORES DIREITA (2) ──
    'jorginhomello': ('Jorginho Mello (Gov. SC/PL)', 2),
    'claudiocastrorj': ('Cláudio Castro (Gov. RJ/PL)', 2),

    # ════════════════════════════════════════
    # SENADORES
    # ════════════════════════════════════════

    # ── SENADORES ESQUERDA (-2) ──
    'paulopaim': ('Paulo Paim (Sen. PT/RS)', -2),
    'fabiano_contarato': ('Fabiano Contarato (Sen. PT/ES)', -2),
    'humbertocosta': ('Humberto Costa (Sen. PT/PE)', -2),
    'jacqueswagner': ('Jaques Wagner (Sen. PT/BA)', -2),
    'rogeriocarvalhopt': ('Rogério Carvalho (Sen. PT/SE)', -2),
    'randolfe': ('Randolfe Rodrigues (Sen. PT/AP)', -2),
    'paulorocha_pt': ('Paulo Rocha (Sen. PT/PA)', -2),

    # ── SENADORES CENTRO-ESQUERDA (-1) ──
    'renancalheiros': ('Renan Calheiros (Sen. MDB/AL)', -1),
    'omaraziz': ('Omar Aziz (Sen. PSD/AM)', -1),
    'elizianegama': ('Eliziane Gama (Sen. PSD/MA)', -1),
    'weverton': ('Weverton Rocha (Sen. PDT/MA)', -1),

    # ── SENADORES CENTRO (0) ──
    'rodrigopacheco': ('Rodrigo Pacheco (Pres. Senado/PSD)', 0),

    # ── SENADORES CENTRO-DIREITA (1) ──
    'sergiomoro': ('Sérgio Moro (Sen. União/PR)', 1),
    'cironogueira': ('Ciro Nogueira (Sen. PP/PI)', 1),
    'efraim_filho': ('Efraim Filho (Sen. União/PB)', 1),
    'marcos_do_val': ('Marcos do Val (Sen. Podemos/ES)', 1),
    'marcopontes': ('Marcos Pontes (Sen. PL/SP)', 1),
    'astronautamarcos': ('Marcos Pontes (Sen. PL/SP)', 1),

    # ── SENADORES DIREITA (2) ──
    'flaviobolsonaro': ('Flávio Bolsonaro (Sen. PL/RJ)', 2),
    'damaresalves': ('Damares Alves (Sen. PL/DF)', 2),
    'general_girao': ('General Girão (Sen. PL/RN)', 2),
    'marcosrogerio': ('Marcos Rogério (Sen. PL/RO)', 2),

    # ════════════════════════════════════════
    # DEPUTADOS FEDERAIS
    # ════════════════════════════════════════

    # ── DEPUTADOS ESQUERDA (-2) ──
    'glauberbraga': ('Glauber Braga (Dep. PSOL/RJ)', -2),
    'taliria': ('Taliria Petrone (Dep. PSOL/RJ)', -2),
    'fmelchionna': ('Fernanda Melchionna (Dep. PSOL/RS)', -2),
    'fernandamelchionna': ('Fernanda Melchionna (Dep. PSOL/RS)', -2),
    'leopericles': ('Léo Péricles (Dep. PSOL/AM)', -2),
    'erikakokay': ('Erika Kokay (Dep. PT/DF)', -2),
    'pimenta13': ('Paulo Pimenta (Dep. PT/RS)', -2),
    'beneditapt': ('Benedita da Silva (Dep. PT/RJ)', -2),
    'reginaldolopes': ('Reginaldo Lopes (Dep. PT/MG)', -2),
    'aliceportugal': ('Alice Portugal (Dep. PCdoB/BA)', -2),
    'chicoalencar': ('Chico Alencar (Dep. PSOL/RJ)', -2),
    'ruifalcao': ('Rui Falcão (Dep. PT/SP)', -2),
    'zecadirceu': ('Zeca Dirceu (Dep. PT/PR)', -2),
    'samiabomfim': ('Sâmia Bomfim (Dep. PSOL/SP)', -2),
    'andrejanonesadv': ('André Janones (Dep. Avante/MG)', -2),
    'guilhermeboulos': ('Guilherme Boulos (Dep. PSOL/SP)', -2),
    'guilherme.boulos': ('Guilherme Boulos (Dep. PSOL/SP)', -2),
    'jandirafeghali': ('Jandira Feghali (Dep. PCdoB/RJ)', -2),
    'marcelofreixo': ('Marcelo Freixo (Dep./PT/RJ)', -2),

    # ── DEPUTADOS CENTRO-ESQUERDA (-1) ──
    'alessandromolon': ('Alessandro Molon (Dep. PSB/RJ)', -1),
    'tabataamaralsp': ('Tabata Amaral (Dep. PSB/SP)', -1),
    'marcelo_calero': ('Marcelo Calero (Dep. Cidadania/RJ)', -1),

    # ── DEPUTADOS CENTRO-DIREITA (1) ──
    'arthurlira': ('Arthur Lira (Dep. PP/AL)', 1),
    'kimkataguiri': ('Kim Kataguiri (Dep. MDB/SP)', 1),
    'marcelvanhattem': ('Marcel van Hattem (Dep. NOVO/RS)', 1),
    'osmarterra': ('Osmar Terra (Dep. MDB/RS)', 1),

    # ── DEPUTADOS DIREITA (2) ──
    'nikolasferreira': ('Nikolas Ferreira (Dep. PL/MG)', 2),
    'carlazambelli': ('Carla Zambelli (Dep. PL/SP)', 2),
    'eduardobolsonaro': ('Eduardo Bolsonaro (Dep. PL/SP)', 2),
    'edubolsonaro': ('Eduardo Bolsonaro (Dep. PL/SP)', 2),
    'carlosbolsonaro': ('Carlos Bolsonaro (Ver. PL/RJ)', 2),
    'biakicis': ('Bia Kicis (Dep. PL/DF)', 2),
    'marcofeliciano': ('Marco Feliciano (Dep. PL/SP)', 2),
    'sostenescavalcante': ('Sóstenes Cavalcante (Dep. PL/RJ)', 2),
    'coroneltadeu': ('Coronel Tadeu (Dep. PL/SP)', 2),
    'andrefernandes': ('André Fernandes (Dep. PL/CE)', 2),
    'christonietto': ('Chris Tonietto (Dep. PL/RJ)', 2),
    'danielsilveirarj': ('Daniel Silveira (Dep. PL/RJ)', 2),
    'jairrenan_': ('Jair Renan (Dep. PL/SC)', 2),

    # ════════════════════════════════════════
    # LIDERANÇAS NACIONAIS — ESQUERDA (-2)
    # ════════════════════════════════════════
    'lulaoficial': ('Lula', -2),
    'labordes': ('Lula', -2),
    'dilmabr': ('Dilma Rousseff', -2),
    'gleisihoffmannoficial': ('Gleisi Hoffmann', -2),
    'gleisihoffmann': ('Gleisi Hoffmann', -2),
    'fernandohaddad': ('Fernando Haddad', -2),
    'gduvivier': ('Gregório Duvivier', -2),
    'gregorioduvivier': ('Gregório Duvivier', -2),
    'jeanwyllys_real': ('Jean Wyllys', -2),
    'brenoaltman': ('Breno Altman', -2),
    'jonesmanoel': ('Jones Manoel', -2),
    'sabrinafernandes': ('Sabrina Fernandes', -2),
    'tempodecerejas': ('Sabrina Fernandes', -2),
    'brasil247': ('Brasil 247', -2),
    'dcm_online': ('DCM Online', -2),
    'midia_ninja': ('Mídia NINJA', -2),
    'midianinja': ('Mídia NINJA', -2),
    'tv247': ('TV 247', -2),
    'conversaafiada': ('Conversa Afiada', -2),
    'revistaforum': ('Revista Fórum', -2),
    'operamundi': ('Opera Mundi', -2),

    # ── LIDERANÇAS CENTRO-ESQUERDA (-1) ──
    'cirogomes': ('Ciro Gomes', -1),
    'marinasilvabr': ('Marina Silva', -1),
    'marinasilva': ('Marina Silva', -1),
    'flaviodino': ('Flávio Dino', -1),
    'reinaldoazevedo': ('Reinaldo Azevedo', -1),
    'luisnassif': ('Luís Nassif', -1),
    'leonardosakamoto': ('Leonardo Sakamoto', -1),
    'jucakfouri': ('Juca Kfouri', -1),
    'cartacapital': ('Carta Capital', -1),
    'theintercept_br': ('The Intercept Brasil', -1),
    'theinterceptbr': ('The Intercept Brasil', -1),

    # ════════════════════════════════════════
    # IMPRENSA E MÍDIA — CENTRO (0)
    # ════════════════════════════════════════
    'folha': ('Folha de S.Paulo', 0),
    'folhadespaulo': ('Folha de S.Paulo', 0),
    'estadao': ('Estadão', 0),
    'oglobo_rio': ('O Globo', 0),
    'oglobo': ('O Globo', 0),
    'g1': ('G1', 0),
    'portalg1': ('G1', 0),
    'uol': ('UOL', 0),
    'uolnoticias': ('UOL Notícias', 0),
    'bbcbrasil': ('BBC Brasil', 0),
    'cnn_brasil': ('CNN Brasil', 0),
    'cnnbrasil': ('CNN Brasil', 0),
    'bandnewsfm': ('BandNews', 0),
    'sbtonline': ('SBT', 0),
    'recordtv': ('Record', 0),
    'jornalnacional': ('Jornal Nacional', 0),
    'correio_braziliense': ('Correio Braziliense', 0),
    'valoreconomico': ('Valor Econômico', 0),
    'agenciasenadobr': ('Agência Senado', 0),
    'agenciacamara': ('Agência Câmara', 0),

    # ── IMPRENSA CENTRO-DIREITA (1) ──
    'oantagonista': ('O Antagonista', 1),
    'gazetadopovo': ('Gazeta do Povo', 1),
    'jovempannews': ('Jovem Pan News', 1),
    'jovempan': ('Jovem Pan', 1),
    'alexandregarcia': ('Alexandre Garcia', 1),
    'leandronarloch': ('Leandro Narloch', 1),

    # ── LIDERANÇAS / IMPRENSA DIREITA (2) ──
    'jairbolsonaro': ('Jair Bolsonaro', 2),
    'bolsonaro': ('Jair Bolsonaro', 2),
    'michellebolsonaro': ('Michelle Bolsonaro', 2),
    'rodrigoconstantino': ('Rodrigo Constantino', 2),
    'allandossantos': ('Allan dos Santos', 2),
    'bernardopkuster': ('Bernardo P. Küster', 2),
    'gustavogayer': ('Gustavo Gayer (Dep. PL/GO)', 2),
    'pablomarcal': ('Pablo Marçal', 2),
    'pablo_marcal': ('Pablo Marçal', 2),
    'revistaoeste': ('Revista Oeste', 2),
    'brasilparalelo': ('Brasil Paralelo', 2),
    'bparalelo': ('Brasil Paralelo', 2),
    'tercalivre': ('Terça Livre', 2),
    'sensoincomum': ('Senso Incomum', 2),
    'conexaopolitica': ('Conexão Política', 2),
}

# Nomes para busca textual em notícias/bio
# ATENÇÃO: usar apenas termos ESPECÍFICOS para evitar falsos positivos.
# Termos muito curtos ou comuns devem estar como FRASES (com espaço), não palavras soltas.
NOMES_ESQUERDA = {
    # lideranças
    'lula',
    'dilma',
    'haddad',
    'boulos',
    'gleisi',
    'janones',
    'jandira feghali',
    'marcelo freixo',
    'flavio dino',
    'marina silva',
    'ciro gomes',
    'samia bomfim',
    'jean wyllys',
    'jones manoel',
    'sabrina fernandes',
    'gregorio duvivier',
    'leonardo sakamoto',
    'luis nassif',
    'juca kfouri',
    # partidos
    'psol',
    'pcdob',
    'partido dos trabalhadores',
    # mídia
    'brasil 247',
    'dcm online',
    'carta capital',
    'the intercept',
    'midia ninja',
    'opera mundi',
    'revista forum',
    # governo federal lula
    'ministerio da saude',
    'ministerio da educacao',
    'ministerio do desenvolvimento',
    'governo federal',
    'governo lula',
    'palacio do planalto',
    'fiocruz',
    'agencia brasil',
    'nilsia trindade',
    # governadores/senadores esquerda
    'elmano de freitas',
    'jeronimo rodrigues',
    'fatima bezerra',
    'camilo santana',
    'helder barbalho',
    'randolfe rodrigues',
    'humberto costa',
    'paulo paim',
}

NOMES_DIREITA = {
    # lideranças
    'jair bolsonaro',
    'michelle bolsonaro',
    'flavio bolsonaro',
    'carlos bolsonaro',
    'eduardo bolsonaro',
    'sergio moro',
    'romeu zema',
    'tarcisio de freitas',
    'nikolas ferreira',
    'carla zambelli',
    'damares alves',
    'pablo marcal',
    'gustavo gayer',
    'bia kicis',
    'marco feliciano',
    'kim kataguiri',
    'marcel van hattem',
    'rodrigo constantino',
    'leandro narloch',
    'allan dos santos',
    'bernardo kuster',
    'olavo de carvalho',
    'daniel silveira',
    'marcos rogerio',
    'sostenes cavalcante',
    # mídia direita
    'revista oeste',
    'o antagonista',
    'gazeta do povo',
    'jovem pan',
    'brasil paralelo',
    'terca livre',
    'senso incomum',
    'conexao politica',
    # governadores/senadores direita
    'ronaldo caiado',
    'jorginho mello',
    'claudio castro',
    'wanderlei barbosa',
    # movimento
    'escola sem partido',
}

# Palavras-chave para análise de texto.
# REGRA: REMOVER palavras que qualquer pessoa (mesmo do lado oposto) usa.
# Manter apenas termos suficientemente específicos.
PALAVRAS_ESQUERDA = {
    # identidade / movimento
    'igualdade',
    'feminismo',
    'feminista',
    'lgbtqia',
    'indigena',
    'quilombola',
    'reforma agraria',
    'socialismo',
    'socialista',
    'progressista',
    'antifascismo',
    'antifascista',
    'redistribuicao',
    'minorias',
    'oprimidos',
    'esquerda',
    'progressismo',
    'inclusao',
    'diversidade',
    # nomes específicos (curtos o suficiente para serem palavras)
    'psol',
    'pcdob',
    'lula',
    'dilma',
    'boulos',
    'haddad',
    'janones',
    'freixo',
    'duvivier',
    'sakamoto',
    'fiocruz',
    # saúde pública / governo (como frases para evitar falsos positivos)
    'vacinacao',
    'vacina',
    'epidemiologia',
    'sus',
    'desigualdade',
    'trabalhismo',
    'trabalhista',
    # frases específicas (multi-token, matched por substring)
    'saude publica',
    'saude coletiva',
    'governo federal',
    'politica publica',
    'politicas publicas',
    'assistencia social',
    'educacao publica',
    'bolsa familia',
    'vigilancia sanitaria',
    'saude mental',
    'reducao de danos',
    'combate a fome',
    'fome zero',
    'cotas raciais',
    'acao afirmativa',
    'movimento social',
    'movimentos sociais',
    'reforma agraria',
    'direitos humanos',
    'direitos trabalhistas',
    'estado de bem estar',
    'renda basica',
}

PALAVRAS_DIREITA = {
    # termos específicos de direita
    'meritocracia',
    'bolsonaro',
    'bolsonarismo',
    'bolsonarista',
    'petismo',
    'petista',
    'agronegocio',
    'neoliberalismo',
    'privatismo',
    'anticomunismo',
    'anticomunista',
    'antiesquerda',
    'doutrinacao',
    'globalismo',
    'globalista',
    'nikolas',
    'zambelli',
    'marcal',
    'gayer',
    # frases específicas de direita
    'kit gay',
    'ideologia de genero',
    'familia tradicional',
    'valores conservadores',
    'escola sem partido',
    'estado minimo',
    'livre mercado',
    'voto impresso',
    'fraude eleitoral',
    'intervencao militar',
    'globo mentira',
}


# =========================
# UTILIDADES
# =========================


def normalizar_texto(texto):
    """Remove acentos e normaliza."""
    texto = texto.lower()
    acentos = {
        'á': 'a',
        'à': 'a',
        'ã': 'a',
        'â': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'õ': 'o',
        'ô': 'o',
        'ú': 'u',
        'ü': 'u',
        'ç': 'c',
    }
    for antigo, novo in acentos.items():
        texto = texto.replace(antigo, novo)
    return texto


def filtrar_resultados_username(posts, username):
    """
    Filtra resultados para garantir que pertencem ao username EXATO.
    Descarta resultados que mencionam usernames similares mas diferentes
    (ex: pesquisou 'otavioaugust' mas encontrou '_otavioaugust', 'otavioaugust98',
    'otavio_auguston', etc.).
    """
    username_lower = username.lower()
    # Normalizado: sem underscores e pontos, para detectar variações
    username_norm = username_lower.replace('_', '').replace('.', '')
    filtrados = []

    for post in posts:
        texto_lower = post.get('texto', '').lower()
        url_lower = post.get('url', '').lower()
        combinado = texto_lower + ' ' + url_lower

        # Extrair menções de @ e usernames de URLs de redes sociais
        mencoes_at = re.findall(r'@([a-zA-Z0-9_.]+)', combinado)
        mencoes_url = re.findall(
            r'(?:twitter\.com|x\.com|instagram\.com|facebook\.com)/([a-zA-Z0-9_.]+)',
            combinado,
        )

        todas_mencoes = mencoes_at + mencoes_url

        if todas_mencoes:
            tem_exato = False
            tem_confuso = False
            for mencao in todas_mencoes:
                mencao = mencao.rstrip('/').lower()
                if mencao == username_lower:
                    tem_exato = True
                    continue

                # Normalizar a menção para comparação
                mencao_norm = mencao.replace('_', '').replace('.', '')

                # Detectar usernames confusos: variações do target
                # Caso 1: um contém o outro (ex: otavioaugust98, _otavioaugust)
                if mencao_norm and username_norm and (
                    username_norm in mencao_norm or mencao_norm in username_norm
                ):
                    tem_confuso = True
                    continue

                # Caso 2: prefixo longo em comum (≥6 chars)
                prefixo_comum = 0
                for a, b in zip(mencao_norm, username_norm):
                    if a == b:
                        prefixo_comum += 1
                    else:
                        break
                if prefixo_comum >= 6:
                    tem_confuso = True

            # Se encontrou username confuso (similar mas diferente)
            # e NÃO encontrou o exato, descartar este resultado
            if tem_confuso and not tem_exato:
                continue

        filtrados.append(post)

    return filtrados


def buscar_web(query, max_results=15):
    """Busca web usando ddgs (lib) com fallback para Bing."""
    posts = []

    if HAS_DDGS:
        try:
            ddgs = DDGS()
            results = ddgs.text(query, region='br-pt', max_results=max_results)
            for r in results:
                titulo = r.get('title', '')
                body = r.get('body', '')
                texto = f'{titulo}. {body}'
                if len(texto) > 20:
                    posts.append(
                        {
                            'texto': texto,
                            'fonte': 'Busca Web',
                            'url': r.get('href', ''),
                        }
                    )
            return posts
        except Exception:
            pass

    # Fallback: Bing
    try:
        url = 'https://www.bing.com/search'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        params = {'q': query, 'setlang': 'pt-BR', 'cc': 'BR'}
        resp = requests.get(
            url, headers=headers, params=params, timeout=TIMEOUT
        )

        if resp.status_code == 200:
            results = re.findall(
                r'<h2><a[^>]*>(.*?)</a></h2>.*?<p[^>]*>(.*?)</p>',
                resp.text,
                re.DOTALL,
            )
            for titulo, snippet in results[:max_results]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                texto = f'{titulo}. {snippet}'
                if len(texto) > 20:
                    posts.append(
                        {'texto': texto, 'fonte': 'Busca Web', 'url': ''}
                    )
    except Exception:
        pass

    return posts


def buscar_noticias(nome):
    """Busca notícias via Google News RSS."""
    posts = []
    try:
        url = 'https://news.google.com/rss/search'
        params = {'q': nome, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'}
        resp = requests.get(url, params=params, timeout=TIMEOUT)

        if resp.status_code == 200:
            titulos = re.findall(
                r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text
            )
            if not titulos:
                titulos = re.findall(r'<title>(.*?)</title>', resp.text)
            for titulo in titulos[1:30]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                if len(titulo) > 15:
                    posts.append(
                        {
                            'texto': titulo,
                            'fonte': 'Google News',
                            'url': 'https://news.google.com/',
                        }
                    )
    except Exception:
        pass
    return posts


def buscar_wikipedia(nome):
    """Busca informações na Wikipédia PT."""
    posts = []
    try:
        url = 'https://pt.wikipedia.org/w/api.php'
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': nome,
            'format': 'json',
            'utf8': 1,
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)

        if resp.status_code == 200:
            resultados = resp.json().get('query', {}).get('search', [])
            if resultados:
                titulo_pagina = resultados[0]['title']
                params2 = {
                    'action': 'query',
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True,
                    'titles': titulo_pagina,
                    'format': 'json',
                }
                resp2 = requests.get(url, params=params2, timeout=TIMEOUT)

                if resp2.status_code == 200:
                    pages = resp2.json().get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract and len(extract) > 50:
                            for paragrafo in extract.split('\n')[:5]:
                                if len(paragrafo) > 30:
                                    posts.append(
                                        {
                                            'texto': paragrafo,
                                            'fonte': 'Wikipédia',
                                            'url': f"https://pt.wikipedia.org/wiki/{titulo_pagina.replace(' ', '_')}",
                                        }
                                    )
    except Exception:
        pass
    return posts


# =========================
# ANÁLISE DE TEXTO
# =========================


# Separar palavras simples de frases multi-token para análise correta
_PALAVRAS_ESQ_SIMPLES = frozenset(p for p in PALAVRAS_ESQUERDA if ' ' not in p)
_FRASES_ESQ = [p for p in PALAVRAS_ESQUERDA if ' ' in p]
_PALAVRAS_DIR_SIMPLES = frozenset(p for p in PALAVRAS_DIREITA if ' ' not in p)
_FRASES_DIR = [p for p in PALAVRAS_DIREITA if ' ' in p]


def analisar_por_palavras(posts):
    """Analisa posts por palavras-chave e nomes conhecidos."""
    total_esq = 0
    total_dir = 0
    palavras_esq = []
    palavras_dir = []

    for post in posts:
        texto_norm = normalizar_texto(post.get('texto', ''))
        palavras = re.findall(r'\b\w+\b', texto_norm)

        for palavra in palavras:
            if palavra in _PALAVRAS_ESQ_SIMPLES:
                total_esq += 1
                palavras_esq.append(palavra)
            elif palavra in _PALAVRAS_DIR_SIMPLES:
                total_dir += 1
                palavras_dir.append(palavra)

        # Frases multi-token (ex: 'saude publica', 'governo federal')
        for frase in _FRASES_ESQ:
            if frase in texto_norm:
                total_esq += 2
                palavras_esq.append(frase)
        for frase in _FRASES_DIR:
            if frase in texto_norm:
                total_dir += 2
                palavras_dir.append(frase)

        # Nomes de figuras conhecidas (substring no texto)
        for nome in NOMES_ESQUERDA:
            if nome in texto_norm:
                total_esq += 2
                palavras_esq.append(nome.strip())
        for nome in NOMES_DIREITA:
            if nome in texto_norm:
                total_dir += 2
                palavras_dir.append(nome.strip())

    return total_esq, total_dir, palavras_esq, palavras_dir


def analisar_seguidores(seguindo_politicos):
    """Analisa figuras políticas seguidas (peso MUITO forte — 5x)."""
    score_esq = 0
    score_dir = 0
    figuras_esq = []
    figuras_dir = []

    vistos = set()
    for fig in seguindo_politicos:
        # Deduplicar: mesma figura detectada em múltiplas fontes conta uma vez
        chave = fig.get('username', fig['nome'])
        if chave in vistos:
            continue
        vistos.add(chave)

        score = fig['score']
        nome = fig['nome']
        if score < 0:
            score_esq += abs(score) * 5
            figuras_esq.append(nome)
        elif score > 0:
            score_dir += score * 5
            figuras_dir.append(nome)

    return score_esq, score_dir, figuras_esq, figuras_dir


def classificar(pct_esq, pct_dir, total_pontos):
    """Gera classificação, descrição, confiança e cor."""
    if total_pontos < 3:
        return (
            'INCONCLUSIVO',
            'Dados insuficientes para esta plataforma',
            'NENHUMA',
            '#888888',
        )

    if total_pontos < 5:
        confianca = 'MUITO BAIXA'
    elif total_pontos < 15:
        confianca = 'BAIXA'
    elif total_pontos < 30:
        confianca = 'MÉDIA'
    else:
        confianca = 'ALTA'

    diff = abs(pct_esq - pct_dir)

    if diff < 12:
        return (
            'CENTRO',
            'Posicionamento equilibrado entre esquerda e direita',
            confianca,
            '#f59e0b',
        )
    elif diff < 30:
        if pct_esq > pct_dir:
            return (
                'CENTRO-ESQUERDA',
                'Tendência moderada para a esquerda',
                confianca,
                '#f97316',
            )
        else:
            return (
                'CENTRO-DIREITA',
                'Tendência moderada para a direita',
                confianca,
                '#3b82f6',
            )
    else:
        if pct_esq > pct_dir:
            return (
                'ESQUERDA',
                'Posicionamento claramente à esquerda',
                confianca,
                '#ef4444',
            )
        else:
            return (
                'DIREITA',
                'Posicionamento claramente à direita',
                confianca,
                '#2563eb',
            )


def montar_resultado_plataforma(posts, seguindo_politicos=None):
    """Analisa uma lista de posts e retorna resultado de uma plataforma."""
    if seguindo_politicos is None:
        seguindo_politicos = []

    (
        pts_esq_texto,
        pts_dir_texto,
        palavras_esq,
        palavras_dir,
    ) = analisar_por_palavras(posts)
    pts_esq_seg, pts_dir_seg, figuras_esq, figuras_dir = analisar_seguidores(
        seguindo_politicos
    )

    total_esq = pts_esq_texto + pts_esq_seg
    total_dir = pts_dir_texto + pts_dir_seg
    total = total_esq + total_dir

    if total == 0:
        return {
            'total_posts': len(posts),
            'classificacao': 'INCONCLUSIVO',
            'descricao': 'Dados insuficientes para esta plataforma',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': seguindo_politicos,
            'figuras_esq': list(set(figuras_esq))[:10],
            'figuras_dir': list(set(figuras_dir))[:10],
            'exemplos': [
                {'texto': p['texto'][:200], 'fonte': p['fonte']}
                for p in posts[:8]
            ],
        }

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    return {
        'total_posts': len(posts),
        'classificacao': classe,
        'descricao': descricao,
        'esquerda_pct': round(pct_esq, 1),
        'direita_pct': round(pct_dir, 1),
        'confianca': confianca,
        'cor': cor,
        'pontos_esq': total_esq,
        'pontos_dir': total_dir,
        'top_palavras_esq': Counter(palavras_esq).most_common(10),
        'top_palavras_dir': Counter(palavras_dir).most_common(10),
        'seguindo_politicos': seguindo_politicos,
        'figuras_esq': list(set(figuras_esq))[:10],
        'figuras_dir': list(set(figuras_dir))[:10],
        'exemplos': [
            {'texto': p['texto'][:200], 'fonte': p['fonte']} for p in posts[:8]
        ],
    }


# =====================================================
# COLETA POR PLATAFORMA
# =====================================================


def coletar_twitter(username, nome_completo):
    """Coleta dados do Twitter/X: tweets, seguidores, busca web."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}

    # 1) API oficial
    if TWITTER_BEARER_TOKEN:
        headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

        # Tweets
        logs.append({'fonte': 'X — Tweets (API)', 'status': 'buscando'})
        try:
            url_user = (
                f'https://api.twitter.com/2/users/by/username/{username}'
            )
            resp = requests.get(url_user, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200 and 'data' in resp.json():
                user_id = resp.json()['data']['id']

                url_tweets = (
                    f'https://api.twitter.com/2/users/{user_id}/tweets'
                )
                params = {
                    'max_results': 100,
                    'tweet.fields': 'created_at,text,public_metrics',
                }
                resp_tw = requests.get(
                    url_tweets, headers=headers, params=params, timeout=TIMEOUT
                )

                if resp_tw.status_code == 200:
                    for tweet in resp_tw.json().get('data', []):
                        texto = tweet.get('text', '')
                        if len(texto) > 15:
                            posts.append(
                                {
                                    'texto': texto,
                                    'fonte': 'X — Tweet',
                                    'url': f"https://x.com/{username}/status/{tweet.get('id')}",
                                }
                            )
                    fontes['X — Tweets'] = len(posts)
                    logs.append(
                        {
                            'fonte': 'X — Tweets (API)',
                            'status': 'ok',
                            'qtd': len(posts),
                        }
                    )
                else:
                    logs.append(
                        {
                            'fonte': 'X — Tweets (API)',
                            'status': 'aviso',
                            'msg': f'HTTP {resp_tw.status_code}',
                        }
                    )

                # Seguindo
                logs.append(
                    {'fonte': 'X — Seguindo (API)', 'status': 'buscando'}
                )
                url_following = (
                    f'https://api.twitter.com/2/users/{user_id}/following'
                )
                all_following = []
                next_token = None
                for _ in range(3):
                    p = {
                        'max_results': 100,
                        'user.fields': 'name,username,description',
                    }
                    if next_token:
                        p['pagination_token'] = next_token
                    resp_f = requests.get(
                        url_following,
                        headers=headers,
                        params=p,
                        timeout=TIMEOUT,
                    )
                    if resp_f.status_code != 200:
                        break
                    data = resp_f.json()
                    all_following.extend(data.get('data', []))
                    next_token = data.get('meta', {}).get('next_token')
                    if not next_token:
                        break

                for user in all_following:
                    uname = user.get('username', '').lower()
                    desc = user.get('description', '')
                    if uname in FIGURAS_POLITICAS:
                        nome_fig, score = FIGURAS_POLITICAS[uname]
                        seguindo_politicos.append(
                            {
                                'username': uname,
                                'nome': nome_fig,
                                'score': score,
                                'descricao': desc[:120] if desc else '',
                            }
                        )
                    if desc and len(desc) > 10:
                        posts.append(
                            {
                                'texto': f"{user.get('name', '')}: {desc}",
                                'fonte': 'X — Bio seguido',
                                'url': f'https://x.com/{uname}',
                            }
                        )

                if seguindo_politicos:
                    fontes['X — Figuras seguidas'] = len(seguindo_politicos)
                    logs.append(
                        {
                            'fonte': 'X — Seguindo (API)',
                            'status': 'ok',
                            'qtd': len(seguindo_politicos),
                            'msg': f'{len(seguindo_politicos)} figuras políticas',
                        }
                    )
                else:
                    logs.append(
                        {
                            'fonte': 'X — Seguindo (API)',
                            'status': 'aviso',
                            'msg': 'Nenhuma figura política identificada',
                        }
                    )
            else:
                logs.append(
                    {
                        'fonte': 'X — Tweets (API)',
                        'status': 'aviso',
                        'msg': 'Usuário não encontrado na API',
                    }
                )

        except Exception as e:
            logs.append(
                {'fonte': 'X — Tweets (API)', 'status': 'erro', 'msg': str(e)}
            )

    else:
        # Sem API — Nitter
        logs.append({'fonte': 'X — Nitter', 'status': 'buscando'})
        instancias = [
            'nitter.poast.org',
            'nitter.privacydev.net',
            'nitter.net',
            'nitter.cz',
        ]
        nitter_ok = None
        for instancia in instancias:
            try:
                url = f'https://{instancia}/{username}'
                h = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=h, timeout=TIMEOUT)
                if response.status_code == 200:
                    tweets = re.findall(
                        r'class="tweet-content[^"]*"[^>]*>([^<]+)',
                        response.text,
                    )
                    for tweet in tweets:
                        texto = re.sub(r'<[^>]+>', '', tweet).strip()
                        if len(texto) > 15:
                            posts.append(
                                {
                                    'texto': texto,
                                    'fonte': 'X — Nitter',
                                    'url': f'https://x.com/{username}',
                                }
                            )
                    if posts:
                        fontes['X — Nitter'] = len(posts)
                        logs.append(
                            {
                                'fonte': 'X — Nitter',
                                'status': 'ok',
                                'qtd': len(posts),
                            }
                        )
                        nitter_ok = instancia
                        break
            except Exception:
                continue
        if not posts:
            logs.append(
                {
                    'fonte': 'X — Nitter',
                    'status': 'aviso',
                    'msg': 'Nitter indisponível',
                }
            )

        # Nitter — tentar buscar lista de seguindo
        if nitter_ok:
            logs.append({'fonte': 'X — Seguindo (Nitter)', 'status': 'buscando'})
            try:
                url_f = f'https://{nitter_ok}/{username}/following'
                resp_f = requests.get(url_f, headers=h, timeout=TIMEOUT)
                if resp_f.status_code == 200:
                    # Extrai hrefs que parecem usernames do Twitter (2-15 chars)
                    candidatos = re.findall(
                        r'href="/([a-zA-Z0-9_]{2,15})"', resp_f.text
                    )
                    # Ignorar itens de navegação conhecidos
                    ignorar = {
                        username.lower(), 'about', 'login', 'search',
                        'settings', 'rss', 'media', 'with_replies',
                    }
                    vistos_nitter = set()
                    for uname in candidatos:
                        uname_l = uname.lower()
                        if uname_l in ignorar or uname_l in vistos_nitter:
                            continue
                        vistos_nitter.add(uname_l)
                        if uname_l in FIGURAS_POLITICAS:
                            fig_nome, fig_score = FIGURAS_POLITICAS[uname_l]
                            seguindo_politicos.append({
                                'username': uname_l,
                                'nome': fig_nome,
                                'score': fig_score,
                                'descricao': '',
                            })
                    if seguindo_politicos:
                        fontes['X — Seguindo (Nitter)'] = len(seguindo_politicos)
                        logs.append({
                            'fonte': 'X — Seguindo (Nitter)',
                            'status': 'ok',
                            'qtd': len(seguindo_politicos),
                            'msg': f'{len(seguindo_politicos)} figuras políticas detectadas',
                        })
                    else:
                        logs.append({
                            'fonte': 'X — Seguindo (Nitter)',
                            'status': 'aviso',
                            'msg': 'Nenhuma figura política na lista de seguindo',
                        })
            except Exception as e:
                logs.append({
                    'fonte': 'X — Seguindo (Nitter)',
                    'status': 'aviso',
                    'msg': f'Não foi possível buscar seguindo: {str(e)[:60]}',
                })

    # 2) Busca web específica do Twitter
    logs.append({'fonte': 'X — Busca Web', 'status': 'buscando'})
    queries = [
        f'site:x.com/{username} OR site:twitter.com/{username}',
        f'site:x.com OR site:twitter.com "@{username}" -"@{username}" política',
    ]
    posts_web = []
    for q in queries:
        posts_web.extend(buscar_web(q, max_results=8))

    # Filtrar para garantir que são do username exato
    posts_web = filtrar_resultados_username(posts_web, username)

    for p in posts_web:
        p['fonte'] = 'X — Busca Web'
    posts.extend(posts_web)
    if posts_web:
        fontes['X — Busca Web'] = len(posts_web)
        logs.append(
            {'fonte': 'X — Busca Web', 'status': 'ok', 'qtd': len(posts_web)}
        )
    else:
        logs.append(
            {
                'fonte': 'X — Busca Web',
                'status': 'aviso',
                'msg': 'Nenhum resultado',
            }
        )

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


def coletar_instagram(username, nome_completo):
    """Coleta dados do Instagram: busca web por perfil, curtidas, seguidos."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}
    privado = False

    # 1) Busca web por perfil Instagram
    logs.append({'fonte': 'Instagram — Perfil Web', 'status': 'buscando'})
    queries = [
        f'site:instagram.com/{username}',
        f'instagram.com/{username} perfil',
    ]
    # Só usar nome_completo se foi fornecido e é diferente do username
    if nome_completo and nome_completo.lower() != username.lower():
        queries.append(f'site:instagram.com "{nome_completo}"')

    for q in queries:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Instagram — Busca Web'
        posts.extend(resultados)

    # Filtrar para garantir que são do username exato
    posts = filtrar_resultados_username(posts, username)

    if posts:
        fontes['Instagram — Busca Web'] = len(posts)
        logs.append(
            {
                'fonte': 'Instagram — Perfil Web',
                'status': 'ok',
                'qtd': len(posts),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Instagram — Perfil Web',
                'status': 'aviso',
                'msg': 'Nenhum conteúdo público encontrado',
            }
        )

    # 2) Busca por curtidas e compartilhamentos com figuras políticas
    logs.append({'fonte': 'Instagram — Interações', 'status': 'buscando'})
    queries_interacoes = []
    if nome_completo and nome_completo.lower() != username.lower():
        queries_interacoes = [
            f'"{nome_completo}" instagram curtiu post político',
            f'"{nome_completo}" instagram compartilhou repostou',
        ]
    else:
        queries_interacoes = [
            f'instagram.com/{username} curtiu comentou',
        ]
    posts_interacoes = []
    for q in queries_interacoes:
        resultados = buscar_web(q, max_results=5)
        for r in resultados:
            r['fonte'] = 'Instagram — Interações'
        posts_interacoes.extend(resultados)

    # Filtrar para garantir que são do username exato
    posts_interacoes = filtrar_resultados_username(posts_interacoes, username)

    if posts_interacoes:
        posts.extend(posts_interacoes)
        fontes['Instagram — Interações'] = len(posts_interacoes)
        logs.append(
            {
                'fonte': 'Instagram — Interações',
                'status': 'ok',
                'qtd': len(posts_interacoes),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Instagram — Interações',
                'status': 'aviso',
                'msg': 'Nenhuma interação encontrada',
            }
        )

    # 3) Tentar scraping do perfil público
    logs.append({'fonte': 'Instagram — Perfil', 'status': 'buscando'})
    try:
        url = f'https://www.instagram.com/{username}/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        }
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)

        if resp.status_code == 200:
            # Detectar perfil privado
            if '"is_private":true' in resp.text:
                privado = True
                logs.append(
                    {
                        'fonte': 'Instagram — Perfil',
                        'status': 'aviso',
                        'msg': '🔒 Perfil PRIVADO — dados limitados, resultados podem não corresponder ao usuário correto',
                    }
                )

            bio_match = re.search(r'"biography":"(.*?)"', resp.text)
            if bio_match:
                bio = (
                    bio_match.group(1)
                    .encode()
                    .decode('unicode_escape', errors='ignore')
                )
                if len(bio) > 10:
                    posts.append(
                        {
                            'texto': f'Bio Instagram: {bio}',
                            'fonte': 'Instagram — Bio',
                            'url': f'https://instagram.com/{username}',
                        }
                    )
                    fontes['Instagram — Bio'] = 1

            followers = re.search(
                r'"edge_followed_by":\{"count":(\d+)\}', resp.text
            )
            following = re.search(
                r'"edge_follow":\{"count":(\d+)\}', resp.text
            )
            if followers:
                fontes['Instagram — Seguidores'] = int(followers.group(1))
            if following:
                fontes['Instagram — Seguindo'] = int(following.group(1))

            texto_page = re.sub(r'<[^>]+>', ' ', resp.text).lower()
            for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
                # Exigir word boundary e tamanho mínimo para evitar
                # falsos positivos com substrings curtas no HTML
                encontrado = False
                if len(fig_user) >= 5:
                    if re.search(r'\b' + re.escape(fig_user) + r'\b', texto_page):
                        encontrado = True
                if not encontrado and len(fig_nome) >= 5:
                    if re.search(r'\b' + re.escape(fig_nome.lower()) + r'\b', texto_page):
                        encontrado = True
                if encontrado:
                    seguindo_politicos.append(
                        {
                            'username': fig_user,
                            'nome': fig_nome,
                            'score': fig_score,
                            'descricao': '',
                        }
                    )

            logs.append(
                {
                    'fonte': 'Instagram — Perfil',
                    'status': 'ok',
                    'msg': 'Perfil público acessado',
                }
            )
        else:
            privado = True
            logs.append(
                {
                    'fonte': 'Instagram — Perfil',
                    'status': 'aviso',
                    'msg': f'HTTP {resp.status_code} — perfil pode ser privado',
                }
            )
    except Exception as e:
        privado = True
        logs.append(
            {
                'fonte': 'Instagram — Perfil',
                'status': 'aviso',
                'msg': f'Não foi possível acessar o perfil: {str(e)[:60]}',
            }
        )

    if seguindo_politicos:
        fontes['Instagram — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    resultado['privado'] = privado
    if privado:
        resultado['aviso_privado'] = (
            '🔒 O perfil do Instagram é PRIVADO. Como não há API pública, '
            'os dados foram coletados via buscas web e podem pertencer a OUTRA PESSOA '
            'com username similar. Os resultados desta rede NÃO são confiáveis — '
            'considere desmarcar o Instagram na pesquisa.'
        )
    return resultado


def coletar_facebook(username, nome_completo):
    """Coleta dados do Facebook: busca web por perfil, publicações, curtidas."""
    posts = []
    seguindo_politicos = []
    logs = []
    fontes = {}
    privado = False

    # 1) Busca web por perfil Facebook
    logs.append({'fonte': 'Facebook — Busca Web', 'status': 'buscando'})
    queries = [
        f'site:facebook.com/{username}',
    ]
    if nome_completo and nome_completo.lower() != username.lower():
        queries.append(f'site:facebook.com "{nome_completo}"')
        queries.append(f'"{nome_completo}" facebook posição opinião política')

    for q in queries:
        resultados = buscar_web(q, max_results=8)
        for r in resultados:
            r['fonte'] = 'Facebook — Busca Web'
        posts.extend(resultados)

    # Filtrar para garantir que são do username exato
    posts = filtrar_resultados_username(posts, username)

    if posts:
        fontes['Facebook — Busca Web'] = len(posts)
        logs.append(
            {
                'fonte': 'Facebook — Busca Web',
                'status': 'ok',
                'qtd': len(posts),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Facebook — Busca Web',
                'status': 'aviso',
                'msg': 'Nenhum conteúdo público encontrado',
            }
        )

    # 2) Busca por curtidas e compartilhamentos
    logs.append({'fonte': 'Facebook — Interações', 'status': 'buscando'})
    queries_interacoes = []
    if nome_completo and nome_completo.lower() != username.lower():
        queries_interacoes = [
            f'"{nome_completo}" facebook curtiu compartilhou',
            f'"{nome_completo}" facebook reação post político',
        ]
    else:
        queries_interacoes = [
            f'facebook.com/{username} curtiu compartilhou',
        ]
    posts_interacoes = []
    for q in queries_interacoes:
        resultados = buscar_web(q, max_results=5)
        for r in resultados:
            r['fonte'] = 'Facebook — Interações'
        posts_interacoes.extend(resultados)

    # Filtrar para garantir que são do username exato
    posts_interacoes = filtrar_resultados_username(posts_interacoes, username)

    if posts_interacoes:
        posts.extend(posts_interacoes)
        fontes['Facebook — Interações'] = len(posts_interacoes)
        logs.append(
            {
                'fonte': 'Facebook — Interações',
                'status': 'ok',
                'qtd': len(posts_interacoes),
            }
        )
    else:
        logs.append(
            {
                'fonte': 'Facebook — Interações',
                'status': 'aviso',
                'msg': 'Nenhuma interação encontrada',
            }
        )

    # 3) Tentar acessar perfil público
    logs.append({'fonte': 'Facebook — Perfil', 'status': 'buscando'})
    try:
        url = f'https://www.facebook.com/{username}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'pt-BR,pt;q=0.9',
        }
        resp = requests.get(
            url, headers=headers, timeout=TIMEOUT, allow_redirects=True
        )

        if resp.status_code == 200:
            texto_page = re.sub(r'<[^>]+>', ' ', resp.text)

            desc_match = re.search(r'"bio":"(.*?)"', resp.text)
            if desc_match:
                bio = (
                    desc_match.group(1)
                    .encode()
                    .decode('unicode_escape', errors='ignore')
                )
                if len(bio) > 10:
                    posts.append(
                        {
                            'texto': f'Bio Facebook: {bio}',
                            'fonte': 'Facebook — Bio',
                            'url': f'https://facebook.com/{username}',
                        }
                    )
                    fontes['Facebook — Bio'] = 1

            texto_lower = texto_page.lower()
            for fig_user, (fig_nome, fig_score) in FIGURAS_POLITICAS.items():
                # Exigir word boundary e tamanho mínimo para evitar
                # falsos positivos com substrings curtas no HTML
                encontrado = False
                if len(fig_user) >= 5:
                    if re.search(r'\b' + re.escape(fig_user) + r'\b', texto_lower):
                        encontrado = True
                if not encontrado and len(fig_nome) >= 5:
                    if re.search(r'\b' + re.escape(fig_nome.lower()) + r'\b', texto_lower):
                        encontrado = True
                if encontrado:
                    seguindo_politicos.append(
                        {
                            'username': fig_user,
                            'nome': fig_nome,
                            'score': fig_score,
                            'descricao': '',
                        }
                    )

            logs.append(
                {
                    'fonte': 'Facebook — Perfil',
                    'status': 'ok',
                    'msg': 'Página pública acessada',
                }
            )
        else:
            privado = True
            logs.append(
                {
                    'fonte': 'Facebook — Perfil',
                    'status': 'aviso',
                    'msg': f'HTTP {resp.status_code} — perfil pode ser privado',
                }
            )
    except Exception as e:
        privado = True
        logs.append(
            {
                'fonte': 'Facebook — Perfil',
                'status': 'aviso',
                'msg': f'Não foi possível acessar: {str(e)[:60]}',
            }
        )

    if seguindo_politicos:
        fontes['Facebook — Figuras detectadas'] = len(seguindo_politicos)

    resultado = montar_resultado_plataforma(posts, seguindo_politicos)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    resultado['privado'] = privado
    if privado:
        resultado['aviso_privado'] = (
            '🔒 O perfil do Facebook é PRIVADO ou inacessível. Como não há API pública, '
            'os dados foram coletados via buscas web e podem pertencer a OUTRA PESSOA '
            'com username similar. Os resultados desta rede NÃO são confiáveis — '
            'considere desmarcar o Facebook na pesquisa.'
        )
    return resultado


def coletar_geral(username, nome_completo):
    """Coleta dados gerais: Google News, Wikipédia, busca web genérica."""
    posts = []
    logs = []
    fontes = {}

    # Busca web genérica
    logs.append({'fonte': 'Busca Web Geral', 'status': 'buscando'})
    queries = [
        f'"@{username}" política posição',
    ]
    if nome_completo and nome_completo.lower() != username.lower():
        queries.append(f'"{nome_completo}" política posição')

    for q in queries:
        posts.extend(buscar_web(q, max_results=10))

    # Filtrar para garantir que são do username exato
    posts = filtrar_resultados_username(posts, username)

    if posts:
        fontes['Busca Web Geral'] = len(posts)
        logs.append(
            {'fonte': 'Busca Web Geral', 'status': 'ok', 'qtd': len(posts)}
        )
    else:
        logs.append(
            {
                'fonte': 'Busca Web Geral',
                'status': 'aviso',
                'msg': 'Nenhum resultado',
            }
        )

    # Google News
    logs.append({'fonte': 'Google News', 'status': 'buscando'})
    posts_news = buscar_noticias(nome_completo)
    if posts_news:
        posts.extend(posts_news)
        fontes['Google News'] = len(posts_news)
        logs.append(
            {'fonte': 'Google News', 'status': 'ok', 'qtd': len(posts_news)}
        )
    else:
        logs.append(
            {
                'fonte': 'Google News',
                'status': 'aviso',
                'msg': 'Nenhuma notícia',
            }
        )

    # Wikipédia
    logs.append({'fonte': 'Wikipédia', 'status': 'buscando'})
    posts_wiki = buscar_wikipedia(nome_completo)
    if posts_wiki:
        posts.extend(posts_wiki)
        fontes['Wikipédia'] = len(posts_wiki)
        logs.append(
            {'fonte': 'Wikipédia', 'status': 'ok', 'qtd': len(posts_wiki)}
        )
    else:
        logs.append(
            {'fonte': 'Wikipédia', 'status': 'aviso', 'msg': 'Nenhum artigo'}
        )

    resultado = montar_resultado_plataforma(posts)
    resultado['fontes'] = fontes
    resultado['logs'] = logs
    return resultado


# =====================================================
# FUNÇÃO PRINCIPAL
# =====================================================


def executar_analise(handle, nome_completo=None, redes_selecionadas=None):
    """
    Executa análise completa com resultados POR PLATAFORMA.
    Retorna resultado geral + resultado individual de cada rede social.
    redes_selecionadas: lista de redes para pesquisar ('twitter', 'instagram', 'facebook')
    """
    username = handle.lstrip('@').strip()
    if not username:
        return None, 'Handle vazio'

    if not nome_completo:
        nome_completo = username

    if redes_selecionadas is None:
        redes_selecionadas = ['twitter', 'instagram', 'facebook']

    # ===== Coletar por plataforma =====
    plataformas = {}

    if 'twitter' in redes_selecionadas:
        plataformas['twitter'] = {
            'nome': 'X / Twitter',
            'icone': '🐦',
            'descricao_coleta': 'Tweets publicados, perfis seguidos, bios',
            **coletar_twitter(username, nome_completo),
        }
    else:
        plataformas['twitter'] = {
            'nome': 'X / Twitter',
            'icone': '🐦',
            'descricao_coleta': 'Não selecionado pelo usuário',
            'total_posts': 0,
            'classificacao': 'NÃO PESQUISADO',
            'descricao': 'Esta rede não foi selecionada para análise',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': [],
            'figuras_esq': [],
            'figuras_dir': [],
            'exemplos': [],
            'fontes': {},
            'logs': [{'fonte': 'X / Twitter', 'status': 'aviso', 'msg': 'Rede não selecionada'}],
            'pulado': True,
        }

    if 'instagram' in redes_selecionadas:
        plataformas['instagram'] = {
            'nome': 'Instagram',
            'icone': '📸',
            'descricao_coleta': 'Perfil público, curtidas, seguidos',
            **coletar_instagram(username, nome_completo),
        }
    else:
        plataformas['instagram'] = {
            'nome': 'Instagram',
            'icone': '📸',
            'descricao_coleta': 'Não selecionado pelo usuário',
            'total_posts': 0,
            'classificacao': 'NÃO PESQUISADO',
            'descricao': 'Esta rede não foi selecionada para análise',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': [],
            'figuras_esq': [],
            'figuras_dir': [],
            'exemplos': [],
            'fontes': {},
            'logs': [{'fonte': 'Instagram', 'status': 'aviso', 'msg': 'Rede não selecionada'}],
            'pulado': True,
        }

    if 'facebook' in redes_selecionadas:
        plataformas['facebook'] = {
            'nome': 'Facebook',
            'icone': '👤',
            'descricao_coleta': 'Publicações, curtidas de páginas',
            **coletar_facebook(username, nome_completo),
        }
    else:
        plataformas['facebook'] = {
            'nome': 'Facebook',
            'icone': '👤',
            'descricao_coleta': 'Não selecionado pelo usuário',
            'total_posts': 0,
            'classificacao': 'NÃO PESQUISADO',
            'descricao': 'Esta rede não foi selecionada para análise',
            'esquerda_pct': 0,
            'direita_pct': 0,
            'confianca': 'NENHUMA',
            'cor': '#888888',
            'pontos_esq': 0,
            'pontos_dir': 0,
            'top_palavras_esq': [],
            'top_palavras_dir': [],
            'seguindo_politicos': [],
            'figuras_esq': [],
            'figuras_dir': [],
            'exemplos': [],
            'fontes': {},
            'logs': [{'fonte': 'Facebook', 'status': 'aviso', 'msg': 'Rede não selecionada'}],
            'pulado': True,
        }

    # ===== Dados gerais (News, Wiki, Web) =====
    dados_gerais = coletar_geral(username, nome_completo)
    plataformas['geral'] = {
        'nome': 'Web / Notícias',
        'icone': '🌐',
        'descricao_coleta': 'Google News, Wikipédia, busca web',
        **dados_gerais,
    }

    # ===== Resultado combinado =====
    todos_posts = []
    todos_seguindo = []
    todas_fontes = {}
    todos_logs = []

    for key, plat in plataformas.items():
        todos_posts.extend(plat.get('exemplos', []))
        todos_seguindo.extend(plat.get('seguindo_politicos', []))
        for fonte, qtd in plat.get('fontes', {}).items():
            todas_fontes[fonte] = qtd
        todos_logs.extend(plat.get('logs', []))

    total_esq = sum(p.get('pontos_esq', 0) for p in plataformas.values())
    total_dir = sum(p.get('pontos_dir', 0) for p in plataformas.values())
    total = total_esq + total_dir
    total_posts = sum(p.get('total_posts', 0) for p in plataformas.values())

    # Combinar palavras-chave
    todas_palavras_esq = []
    todas_palavras_dir = []
    for p in plataformas.values():
        for palavra, freq in p.get('top_palavras_esq', []):
            todas_palavras_esq.extend([palavra] * freq)
        for palavra, freq in p.get('top_palavras_dir', []):
            todas_palavras_dir.extend([palavra] * freq)

    # Deduplicar seguindo
    seen = set()
    seguindo_unicos = []
    for fig in todos_seguindo:
        if fig['username'] not in seen:
            seen.add(fig['username'])
            seguindo_unicos.append(fig)

    figuras_esq = list(
        set(f for p in plataformas.values() for f in p.get('figuras_esq', []))
    )[:15]
    figuras_dir = list(
        set(f for p in plataformas.values() for f in p.get('figuras_dir', []))
    )[:15]

    base = {
        'handle': f'@{username}',
        'nome': nome_completo,
        'total_posts': total_posts,
        'fontes': todas_fontes,
        'logs': todos_logs,
        'exemplos': todos_posts[:15],
        'tem_api_twitter': bool(TWITTER_BEARER_TOKEN),
        'seguindo_politicos': seguindo_unicos,
        'figuras_esq': figuras_esq,
        'figuras_dir': figuras_dir,
        'plataformas': plataformas,
    }

    if total == 0:
        base.update(
            {
                'classificacao': 'INCONCLUSIVO',
                'descricao': 'Não foi possível encontrar dados políticos suficientes.',
                'esquerda_pct': 0,
                'direita_pct': 0,
                'confianca': 'NENHUMA',
                'top_palavras_esq': [],
                'top_palavras_dir': [],
                'cor': '#888888',
                'pontos_esq': 0,
                'pontos_dir': 0,
            }
        )
        return base, None

    pct_esq = (total_esq / total) * 100
    pct_dir = (total_dir / total) * 100
    classe, descricao, confianca, cor = classificar(pct_esq, pct_dir, total)

    base.update(
        {
            'classificacao': classe,
            'descricao': descricao,
            'esquerda_pct': round(pct_esq, 1),
            'direita_pct': round(pct_dir, 1),
            'confianca': confianca,
            'top_palavras_esq': Counter(todas_palavras_esq).most_common(10),
            'top_palavras_dir': Counter(todas_palavras_dir).most_common(10),
            'cor': cor,
            'pontos_esq': total_esq,
            'pontos_dir': total_dir,
        }
    )

    return base, None
