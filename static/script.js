
document.getElementById('formAnalise').addEventListener('submit', function() {
    var btn = document.getElementById('btnSubmit');
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loading').style.display = 'inline-flex';
    btn.disabled = true;
    // Mostrar modal
    mostrarModalAnalise();
});

// ─── Modal de Análise em Progresso ────────────────────────────────────────
var intervaloCarrossel = null;
var cartasVistas = [];

function mostrarModalAnalise() {
    document.getElementById('modalAnalise').style.display = 'flex';
    cartasVistas = [];
    exibirCartaAleatoria();
    // Trocar carta a cada 5 segundos
    if (intervaloCarrossel) clearInterval(intervaloCarrossel);
    intervaloCarrossel = setInterval(exibirCartaAleatoria, 10000);
}

function fecharModalAnalise() {
    document.getElementById('modalAnalise').style.display = 'none';
    if (intervaloCarrossel) clearInterval(intervaloCarrossel);
}

function exibirCartaAleatoria() {
    var cartas = document.querySelectorAll('.curiosidade-card');
    var cartasDisponiveis = Array.from(cartas).filter(function(c) {
        return !cartasVistas.includes(c.dataset.index);
    });
    
    // Se já viu todas, reseta
    if (cartasDisponiveis.length === 0) {
        cartasVistas = [];
        cartasDisponiveis = Array.from(cartas);
    }
    
    // Sortear carta aleatória
    var indiceAleatorio = Math.floor(Math.random() * cartasDisponiveis.length);
    var cartaSelecionada = cartasDisponiveis[indiceAleatorio];
    var index = cartaSelecionada.dataset.index;
    cartasVistas.push(index);
    
    // Mostrar apenas a carta selecionada
    cartas.forEach(function(c) { c.style.display = 'none'; });
    cartaSelecionada.style.display = 'block';
}


// ─── Busca de Deputado Federal ────────────────────────────────────────────
function toggleDepSearch() {
    var panel = document.getElementById('depSearchPanel');
    var icon  = document.getElementById('depToggleIcon');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        icon.textContent = '▲';
        document.getElementById('depNomeInput').focus();
    } else {
        panel.style.display = 'none';
        icon.textContent = '▼';
    }
}

async function buscarDeputado() {
    var nome = document.getElementById('depNomeInput').value.trim();
    if (nome.length < 3) {
        document.getElementById('depResultsContainer').innerHTML =
            '<div class="dep-error">⚠️ Digite pelo menos 3 letras do nome.</div>';
        return;
    }
    var container = document.getElementById('depResultsContainer');
    container.innerHTML = '<div class="dep-loading">🔄 Buscando na API da Câmara...</div>';
    try {
        var resp = await fetch('/api/buscar_deputado?nome=' + encodeURIComponent(nome));
        var data = await resp.json();
        if (data.erro) {
            container.innerHTML = '<div class="dep-error">⚠️ ' + data.erro + '</div>';
            return;
        }
        if (!data.deputados || data.deputados.length === 0) {
            container.innerHTML = '<div class="dep-error">Nenhum deputado encontrado com esse nome.</div>';
            return;
        }
        container.innerHTML = data.deputados.map(function(dep) {
            var handle = dep.twitter || dep.instagram || '';
            var plat   = dep.twitter ? 'twitter' : (dep.instagram ? 'instagram' : '');
            var platLabel = dep.twitter ? '🐦 X/Twitter' : (dep.instagram ? '📸 Instagram' : '');
            var disabled  = handle ? '' : 'dep-card-disabled';
            var onclick   = handle
                ? 'selecionarDeputado("' + handle + '","' + dep.nome.replace(/"/g, '&quot;') + '","' + plat + '")'
                : '';
            var fotoHtml = dep.foto
                ? '<img class="dep-foto" src="' + dep.foto + '" alt="' + dep.nome + '" loading="lazy">'
                : '<div class="dep-foto-placeholder">👤</div>';
            var handleHtml = handle
                ? '<span class="dep-handle">@' + handle + ' <small>' + platLabel + '</small></span>'
                : '<span class="dep-handle dep-sem-rede">Sem redes cadastradas</span>';
            return '<div class="dep-card ' + disabled + '" ' + (onclick ? 'onclick="' + onclick + '"' : '') + '>' +
                fotoHtml +
                '<div class="dep-info">' +
                    '<strong class="dep-nome">' + dep.nome + '</strong>' +
                    '<span class="dep-partido">' + dep.partido + '/' + dep.uf + '</span>' +
                    handleHtml +
                '</div>' +
                '</div>';
        }).join('');
    } catch(e) {
        container.innerHTML = '<div class="dep-error">⚠️ Erro ao buscar deputados. Tente novamente.</div>';
    }
}

function selecionarDeputado(handle, nome, plat) {
    document.getElementById('handle').value = handle;
    document.getElementById('nome').value = nome;
    // Marca apenas a rede correspondente
    document.querySelectorAll('input[name="redes"]').forEach(function(cb) {
        cb.checked = (cb.value === plat);
    });
    // Fecha o painel
    document.getElementById('depSearchPanel').style.display = 'none';
    document.getElementById('depToggleIcon').textContent = '▼';
    // Foca no campo de handle
    document.getElementById('handle').scrollIntoView({behavior: 'smooth', block: 'center'});
    document.getElementById('handle').focus();
}