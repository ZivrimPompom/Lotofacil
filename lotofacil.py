import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from pathlib import Path
from io import BytesIO

# =====================================
# CONFIGURAÇÕES INICIAIS
# =====================================
st.set_page_config(
    page_title="Lotofácil Inteligente",
    layout="wide"
)

st.title("🍀 Analisador Inteligente da Lotofácil")

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_PADRAO = BASE_DIR / "Lotofácil.xlsx"

# CSS para centralizar tabelas
st.markdown("""
    <style>
    /* Centralizar conteúdo das células das tabelas */
    [data-testid="stDataFrame"] td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    [data-testid="stDataFrame"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    /* Garantir que números fiquem centralizados */
    [data-testid="stDataFrame"] div[data-testid="stMarkdownContainer"] {
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================
# INICIALIZAR SESSION STATE
# =====================================
if 'quentissimas' not in st.session_state:
    st.session_state.quentissimas = []
if 'quentes' not in st.session_state:
    st.session_state.quentes = []
if 'mornas' not in st.session_state:
    st.session_state.mornas = []
if 'frias' not in st.session_state:
    st.session_state.frias = []
if 'geladas' not in st.session_state:
    st.session_state.geladas = []
if 'analise_feita' not in st.session_state:
    st.session_state.analise_feita = False

# =====================================
# FUNÇÕES
# =====================================

def carregar_dados():
    if not ARQUIVO_PADRAO.exists():
        st.error(f"❌ Arquivo {ARQUIVO_PADRAO.name} não encontrado na pasta do app.")
        st.info(f"📁 Procurando em: {ARQUIVO_PADRAO.parent}")
        st.info(f"📄 Nome esperado: **{ARQUIVO_PADRAO.name}**")
        st.warning("💡 Certifique-se de que o arquivo está na mesma pasta do script Python e tem exatamente este nome (com acento no 'a')")
        
        # Listar arquivos .xlsx na pasta
        arquivos_excel = list(ARQUIVO_PADRAO.parent.glob("*.xlsx"))
        if arquivos_excel:
            st.info(f"📋 Arquivos .xlsx encontrados na pasta:")
            for arq in arquivos_excel:
                st.write(f"  - {arq.name}")
        
        st.stop()
    
    try:
        df = pd.read_excel(ARQUIVO_PADRAO)
        st.success(f"✅ Arquivo carregado: {len(df)} concursos encontrados")
        return df
    except Exception as e:
        st.error(f"❌ Erro ao ler o arquivo: {str(e)}")
        st.stop()


def obter_colunas_dezenas(df):
    """
    Identifica as 15 colunas de dezenas sorteadas, ignorando outras colunas.
    Aceita vários formatos: Bola1-Bola15, D1-D15, 1-15, Dezena1-Dezena15, etc.
    """
    # Padrões possíveis para colunas de dezenas
    colunas_bola = [c for c in df.columns if str(c).lower().startswith('bola') and str(c)[4:].strip().isdigit()]
    colunas_d = [c for c in df.columns if str(c).upper().startswith('D') and len(str(c)) <= 4 and str(c)[1:].isdigit()]
    colunas_dezena = [c for c in df.columns if 'dezena' in str(c).lower() and any(char.isdigit() for char in str(c))]
    colunas_num = [c for c in df.columns if str(c).strip().isdigit() and 1 <= int(str(c).strip()) <= 15]
    
    # Tentar identificar colunas na ordem de prioridade
    if colunas_bola and len(colunas_bola) >= 15:
        colunas = colunas_bola[:15]
        chave = lambda x: int(''.join(filter(str.isdigit, str(x))))
    elif colunas_d and len(colunas_d) >= 15:
        colunas = colunas_d[:15]
        chave = lambda x: int(str(x).replace('D', '').replace('d', ''))
    elif colunas_dezena and len(colunas_dezena) >= 15:
        colunas = colunas_dezena[:15]
        chave = lambda x: int(''.join(filter(str.isdigit, str(x))))
    elif colunas_num and len(colunas_num) >= 15:
        colunas = colunas_num[:15]
        chave = lambda x: int(str(x))
    else:
        st.error(f"❌ Não foi possível identificar as 15 colunas de dezenas.")
        st.info(f"📋 Colunas disponíveis no arquivo: {', '.join(map(str, df.columns[:20]))}")
        st.info("💡 O arquivo deve ter 15 colunas com os números sorteados (ex: Bola1-Bola15, D1-D15, ou 1-15)")
        st.stop()
    
    colunas_ordenadas = sorted(colunas, key=chave)[:15]
    
    if len(colunas_ordenadas) != 15:
        st.error(f"❌ Esperado 15 colunas de dezenas, encontrei {len(colunas_ordenadas)}.")
        st.info(f"📋 Colunas identificadas: {', '.join(map(str, colunas_ordenadas))}")
        st.stop()
    
    return colunas_ordenadas


def analisar_frequencia(df, concursos):
    """
    Analisa frequência e divide em 5 categorias baseadas em faixas de frequência.
    Dezenas com a MESMA frequência ficam SEMPRE na MESMA categoria.
    """
    colunas = obter_colunas_dezenas(df)
    dados = df.tail(concursos)[colunas].values.flatten()
    contagem = Counter(map(int, dados))

    todas = list(range(1, 26))
    frequencias = {d: contagem.get(d, 0) for d in todas}

    # Agrupar dezenas por frequência
    freq_grupos = defaultdict(list)
    for dezena, freq in frequencias.items():
        freq_grupos[freq].append(dezena)
    
    # Ordenar frequências (maior para menor)
    frequencias_unicas = sorted(freq_grupos.keys(), reverse=True)
    
    if len(frequencias_unicas) == 0:
        return [], [], [], [], []
    
    # Se houver 5 ou mais níveis de frequência diferentes
    if len(frequencias_unicas) >= 5:
        # Dividir os níveis de frequência em 5 grupos
        num_freq = len(frequencias_unicas)
        tamanho = num_freq / 5
        
        idx1 = max(1, int(tamanho * 1))
        idx2 = max(2, int(tamanho * 2))
        idx3 = max(3, int(tamanho * 3))
        idx4 = max(4, int(tamanho * 4))
        
        freqs_quentissimas = frequencias_unicas[:idx1]
        freqs_quentes = frequencias_unicas[idx1:idx2]
        freqs_mornas = frequencias_unicas[idx2:idx3]
        freqs_frias = frequencias_unicas[idx3:idx4]
        freqs_geladas = frequencias_unicas[idx4:]
    
    elif len(frequencias_unicas) == 4:
        # 4 níveis: distribuir como Qt, Q, M, F+G
        freqs_quentissimas = [frequencias_unicas[0]]
        freqs_quentes = [frequencias_unicas[1]]
        freqs_mornas = [frequencias_unicas[2]]
        freqs_frias = []
        freqs_geladas = [frequencias_unicas[3]]
    
    elif len(frequencias_unicas) == 3:
        # 3 níveis: distribuir como Qt, M, G
        freqs_quentissimas = [frequencias_unicas[0]]
        freqs_quentes = []
        freqs_mornas = [frequencias_unicas[1]]
        freqs_frias = []
        freqs_geladas = [frequencias_unicas[2]]
    
    elif len(frequencias_unicas) == 2:
        # 2 níveis: Qt e G
        freqs_quentissimas = [frequencias_unicas[0]]
        freqs_quentes = []
        freqs_mornas = []
        freqs_frias = []
        freqs_geladas = [frequencias_unicas[1]]
    
    else:
        # 1 nível: todas mornas
        freqs_quentissimas = []
        freqs_quentes = []
        freqs_mornas = frequencias_unicas
        freqs_frias = []
        freqs_geladas = []
    
    # Construir listas de dezenas para cada categoria
    quentissimas = []
    for freq in freqs_quentissimas:
        for dez in freq_grupos[freq]:
            quentissimas.append((dez, freq))
    
    quentes = []
    for freq in freqs_quentes:
        for dez in freq_grupos[freq]:
            quentes.append((dez, freq))
    
    mornas = []
    for freq in freqs_mornas:
        for dez in freq_grupos[freq]:
            mornas.append((dez, freq))
    
    frias = []
    for freq in freqs_frias:
        for dez in freq_grupos[freq]:
            frias.append((dez, freq))
    
    geladas = []
    for freq in freqs_geladas:
        for dez in freq_grupos[freq]:
            geladas.append((dez, freq))
    
    return sorted(quentissimas), sorted(quentes), sorted(mornas), sorted(frias), sorted(geladas)


def obter_jogos_historicos(df):
    colunas = obter_colunas_dezenas(df)
    jogos = set(df[colunas].apply(lambda row: tuple(sorted(row.astype(int))), axis=1))
    return jogos


def gerar_jogos(quentissimas, quentes, mornas, frias, geladas, n_jogos, qt, q, m, f, g, historico, pares_min=6, pares_max=9):
    # Validar se há dezenas suficientes
    if qt > len(quentissimas):
        st.error(f"❌ Não há {qt} dezenas quentíssimas disponíveis (apenas {len(quentissimas)})")
        return []
    if q > len(quentes):
        st.error(f"❌ Não há {q} dezenas quentes disponíveis (apenas {len(quentes)})")
        return []
    if m > len(mornas):
        st.error(f"❌ Não há {m} dezenas mornas disponíveis (apenas {len(mornas)})")
        return []
    if f > len(frias):
        st.error(f"❌ Não há {f} dezenas frias disponíveis (apenas {len(frias)})")
        return []
    if g > len(geladas):
        st.error(f"❌ Não há {g} dezenas geladas disponíveis (apenas {len(geladas)})")
        return []
    
    def agrupar_por_frequencia(dados):
        grupos = defaultdict(list)
        for dezena, freq in dados:
            grupos[freq].append(dezena)
        return [grupos[freq] for freq in sorted(grupos.keys(), reverse=True)]
    
    grupos_quentissimas = agrupar_por_frequencia(quentissimas)
    grupos_quentes = agrupar_por_frequencia(quentes)
    grupos_mornas = agrupar_por_frequencia(mornas)
    grupos_frias = agrupar_por_frequencia(frias)
    grupos_geladas = agrupar_por_frequencia(geladas)
    
    jogos = []
    tentativas = 0
    max_tentativas = 50000

    while len(jogos) < n_jogos and tentativas < max_tentativas:
        tentativas += 1
        jogo = set()
        
        # Quentíssimas
        if qt > 0:
            dezenas_disponiveis = []
            for grupo in grupos_quentissimas:
                dezenas_disponiveis.extend(grupo)
                if len(dezenas_disponiveis) >= qt:
                    break
            jogo.update(random.sample(dezenas_disponiveis[:max(qt*3, len(dezenas_disponiveis))], qt))
        
        # Quentes
        if q > 0:
            dezenas_disponiveis = []
            for grupo in grupos_quentes:
                dezenas_disponiveis.extend(grupo)
                if len(dezenas_disponiveis) >= q:
                    break
            jogo.update(random.sample(dezenas_disponiveis[:max(q*3, len(dezenas_disponiveis))], q))
        
        # Mornas
        if m > 0:
            dezenas_disponiveis = []
            for grupo in grupos_mornas:
                dezenas_disponiveis.extend(grupo)
                if len(dezenas_disponiveis) >= m:
                    break
            jogo.update(random.sample(dezenas_disponiveis[:max(m*3, len(dezenas_disponiveis))], m))
        
        # Frias
        if f > 0:
            dezenas_disponiveis = []
            for grupo in grupos_frias:
                dezenas_disponiveis.extend(grupo)
                if len(dezenas_disponiveis) >= f:
                    break
            jogo.update(random.sample(dezenas_disponiveis[:max(f*3, len(dezenas_disponiveis))], f))
        
        # Geladas
        if g > 0:
            dezenas_disponiveis = []
            for grupo in grupos_geladas:
                dezenas_disponiveis.extend(grupo)
                if len(dezenas_disponiveis) >= g:
                    break
            jogo.update(random.sample(dezenas_disponiveis[:max(g*3, len(dezenas_disponiveis))], g))

        if len(jogo) != 15:
            continue
        
        qtd_pares = sum(1 for n in jogo if n % 2 == 0)
        
        if qtd_pares < pares_min or qtd_pares > pares_max:
            continue

        jogo_ordenado = tuple(sorted(jogo))
        if jogo_ordenado not in historico and jogo_ordenado not in jogos:
            jogos.append(jogo_ordenado)

    if len(jogos) < n_jogos:
        st.warning(f"⚠️ Apenas {len(jogos)} jogos inéditos foram gerados (solicitado: {n_jogos})")
    
    return jogos


def exportar_excel(quentissimas, quentes, mornas, frias, geladas, jogos):
    buffer = BytesIO()

    try:
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            pd.DataFrame(quentissimas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Quentíssimas", index=False
            )
            pd.DataFrame(quentes, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Quentes", index=False
            )
            pd.DataFrame(mornas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Mornas", index=False
            )
            pd.DataFrame(frias, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Frias", index=False
            )
            pd.DataFrame(geladas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Geladas", index=False
            )
            pd.DataFrame(jogos).to_excel(
                writer, sheet_name="Jogos Gerados", index=False,
                header=[f"Bola {i+1}" for i in range(15)]
            )
    except ImportError:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            pd.DataFrame(quentissimas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Quentíssimas", index=False
            )
            pd.DataFrame(quentes, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Quentes", index=False
            )
            pd.DataFrame(mornas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Mornas", index=False
            )
            pd.DataFrame(frias, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Frias", index=False
            )
            pd.DataFrame(geladas, columns=["Dezena", "Frequência"]).to_excel(
                writer, sheet_name="Geladas", index=False
            )
            pd.DataFrame(jogos).to_excel(
                writer, sheet_name="Jogos Gerados", index=False,
                header=[f"Bola {i+1}" for i in range(15)]
            )

    buffer.seek(0)
    return buffer


# =====================================
# FLUXO PRINCIPAL
# =====================================

df = carregar_dados()
historico = obter_jogos_historicos(df)

st.subheader("📊 Análise Estatística")

col_config1, col_config2 = st.columns([2, 1])

with col_config1:
    concursos = st.number_input(
        "Quantos concursos deseja analisar?",
        min_value=2,
        max_value=len(df),
        step=2,
        value=50
    )

with col_config2:
    st.metric("Total de Concursos", len(df))

if st.button("🔍 Analisar Frequência", type="primary"):
    with st.spinner("Analisando frequências..."):
        quentissimas, quentes, mornas, frias, geladas = analisar_frequencia(df, concursos)
        
        st.session_state.quentissimas = quentissimas
        st.session_state.quentes = quentes
        st.session_state.mornas = mornas
        st.session_state.frias = frias
        st.session_state.geladas = geladas
        st.session_state.analise_feita = True

if st.session_state.analise_feita:
    
    def formatar_por_frequencia(dados):
        if not dados:
            return pd.DataFrame(columns=["Frequência", "Dezenas"])
        
        grupos = defaultdict(list)
        for dezena, freq in dados:
            grupos[freq].append(dezena)
        
        resultado = []
        for freq in sorted(grupos.keys(), reverse=True):
            dezenas_str = ", ".join(map(str, sorted(grupos[freq])))
            resultado.append({"Frequência": freq, "Dezenas": dezenas_str})
        
        return pd.DataFrame(resultado)
    
    # 5 colunas para as 5 categorias
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("🔥🔥 **Quentíssimas**")
        df_quentissimas = formatar_por_frequencia(st.session_state.quentissimas)
        st.dataframe(df_quentissimas, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("🔥 **Quentes**")
        df_quentes = formatar_por_frequencia(st.session_state.quentes)
        st.dataframe(df_quentes, use_container_width=True, hide_index=True)

    with col3:
        st.markdown("🌡️ **Mornas**")
        df_mornas = formatar_por_frequencia(st.session_state.mornas)
        st.dataframe(df_mornas, use_container_width=True, hide_index=True)

    with col4:
        st.markdown("❄️ **Frias**")
        df_frias = formatar_por_frequencia(st.session_state.frias)
        st.dataframe(df_frias, use_container_width=True, hide_index=True)

    with col5:
        st.markdown("🧊 **Geladas**")
        df_geladas = formatar_por_frequencia(st.session_state.geladas)
        st.dataframe(df_geladas, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### ⚖️ Análise Par/Ímpar por Segmento")
    
    def calcular_par_impar(dados):
        if not dados:
            return 0, 0, 0
        dezenas = [d for d, _ in dados]
        total = len(dezenas)
        pares = sum(1 for d in dezenas if d % 2 == 0)
        impares = total - pares
        return total, pares, impares
    
    total_qt, pares_qt, impares_qt = calcular_par_impar(st.session_state.quentissimas)
    total_q, pares_q, impares_q = calcular_par_impar(st.session_state.quentes)
    total_m, pares_m, impares_m = calcular_par_impar(st.session_state.mornas)
    total_f, pares_f, impares_f = calcular_par_impar(st.session_state.frias)
    total_g, pares_g, impares_g = calcular_par_impar(st.session_state.geladas)
    
    total_geral = total_qt + total_q + total_m + total_f + total_g
    pares_geral = pares_qt + pares_q + pares_m + pares_f + pares_g
    impares_geral = impares_qt + impares_q + impares_m + impares_f + impares_g
    
    dados_analise = {
        "Segmento": ["🔥🔥 Quentíssimas", "🔥 Quentes", "🌡️ Mornas", "❄️ Frias", "🧊 Geladas", "📊 TOTAL"],
        "Pares": [pares_qt, pares_q, pares_m, pares_f, pares_g, pares_geral],
        "% Pares": [
            f"{(pares_qt/total_qt*100):.1f}%" if total_qt > 0 else "0%",
            f"{(pares_q/total_q*100):.1f}%" if total_q > 0 else "0%",
            f"{(pares_m/total_m*100):.1f}%" if total_m > 0 else "0%",
            f"{(pares_f/total_f*100):.1f}%" if total_f > 0 else "0%",
            f"{(pares_g/total_g*100):.1f}%" if total_g > 0 else "0%",
            f"{(pares_geral/total_geral*100):.1f}%" if total_geral > 0 else "0%"
        ],
        "Ímpares": [impares_qt, impares_q, impares_m, impares_f, impares_g, impares_geral],
        "% Ímpares": [
            f"{(impares_qt/total_qt*100):.1f}%" if total_qt > 0 else "0%",
            f"{(impares_q/total_q*100):.1f}%" if total_q > 0 else "0%",
            f"{(impares_m/total_m*100):.1f}%" if total_m > 0 else "0%",
            f"{(impares_f/total_f*100):.1f}%" if total_f > 0 else "0%",
            f"{(impares_g/total_g*100):.1f}%" if total_g > 0 else "0%",
            f"{(impares_geral/total_geral*100):.1f}%" if total_geral > 0 else "0%"
        ],
        "Total": [total_qt, total_q, total_m, total_f, total_g, total_geral]
    }
    
    df_analise_parimpar = pd.DataFrame(dados_analise)
    st.dataframe(df_analise_parimpar, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🎲 Geração de Jogos")
    
    st.info("💡 **Dica:** A Lotofácil tem 15 números por jogo (de 1 a 25)")

    # 5 inputs para as 5 categorias
    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
    
    with col_a:
        n_jogos = st.number_input("Quantidade de jogos", 1, 50, 5)
    with col_b:
        qt = st.number_input("Quentíssimas", 0, 15, 3)
    with col_c:
        q = st.number_input("Quentes", 0, 15, 3)
    with col_d:
        m = st.number_input("Mornas", 0, 15, 3)
    with col_e:
        f = st.number_input("Frias", 0, 15, 3)
    with col_f:
        g = st.number_input("Geladas", 0, 15, 3)

    st.markdown("### ⚖️ Balanceamento Par/Ímpar")
    col_par1, col_par2 = st.columns(2)
    
    with col_par1:
        pares_min = st.slider(
            "Mínimo de pares por jogo",
            min_value=5, max_value=10, value=6,
            help="Baseado em análise: 30% dos jogos têm 8 pares"
        )
    with col_par2:
        pares_max = st.slider(
            "Máximo de pares por jogo",
            min_value=5, max_value=10, value=9,
            help="Baseado em análise: 60% dos jogos entre 8-9 pares"
        )
    
    impares_min = 15 - pares_max
    impares_max = 15 - pares_min
    
    st.caption(f"📊 Isso resulta em: **{pares_min}-{pares_max} pares** e **{impares_min}-{impares_max} ímpares** por jogo")

    total = qt + q + m + f + g
    
    if total != 15:
        st.warning(f"⚠️ A soma das dezenas deve ser exatamente 15 (atual: {total})")
    else:
        st.success(f"✅ Configuração válida: {qt} quentíssimas + {q} quentes + {m} mornas + {f} frias + {g} geladas = 15 dezenas")
        
        if st.button("🎯 Gerar Jogos", type="primary"):
            with st.spinner("Gerando jogos inéditos com balanceamento par/ímpar..."):
                jogos = gerar_jogos(
                    st.session_state.quentissimas,
                    st.session_state.quentes,
                    st.session_state.mornas,
                    st.session_state.frias,
                    st.session_state.geladas,
                    n_jogos, qt, q, m, f, g, historico,
                    pares_min, pares_max
                )

            if jogos:
                st.success(f"✅ {len(jogos)} jogos gerados com sucesso!")
                
                df_jogos = pd.DataFrame(jogos, columns=[f"Bola {i+1}" for i in range(15)])
                df_jogos['Pares'] = df_jogos.apply(lambda row: sum(1 for x in row if x % 2 == 0), axis=1)
                df_jogos['Ímpares'] = 15 - df_jogos['Pares']
                
                df_jogos.index = range(1, len(df_jogos) + 1)
                df_jogos.index.name = "Jogo"
                
                st.dataframe(df_jogos, use_container_width=True)

                excel = exportar_excel(
                    st.session_state.quentissimas,
                    st.session_state.quentes,
                    st.session_state.mornas,
                    st.session_state.frias,
                    st.session_state.geladas,
                    jogos
                )
                st.download_button(
                    "📥 Baixar Excel Completo",
                    data=excel,
                    file_name="resultado_lotofacil.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Não foi possível gerar jogos inéditos com os critérios selecionados.")
                st.info("💡 Tente aumentar o intervalo de pares/ímpares ou ajustar as quantidades de dezenas.")

else:
    st.info("👆 Clique em 'Analisar Frequência' para começar")

st.divider()
st.caption("🍀 Analisador Inteligente da Lotofácil | Desenvolvido para análise estatística de resultados")