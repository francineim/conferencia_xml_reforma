# app.py
# ------------------------------------------------------------
# Conferência XML Reforma Tributária — NF-e (IBS/CBS/IS)
# ------------------------------------------------------------
# Autor: (adicione seu nome/organização)
# Licença sugerida: MIT
#
# Funcionalidades:
#  - Upload de XML da NF-e (NT 2025.002-RTC)
#  - Quadro Resumo por Item (ICMS, PIS, COFINS, IBS, CBS, IPI, TOTAL ITEM)
#  - Checklist obrigatório com validações automáticas
#  - Exportação para Excel (quadro + checklist)
#
# Observações:
#  - Não valida ide/idDest (podem existir operações internas e interestaduais)
#  - Alíquotas de teste padrão: IBS=0,10% | CBS=0,90% (configuráveis no sidebar)
# ------------------------------------------------------------

import io
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st

# --------------------- Configuração da Página ---------------------
st.set_page_config(
    page_title="Conferência XML Reforma Tributária",
    page_icon="🧾",
    layout="wide"
)

TITLE = "Conferência XML Reforma Tributária"
st.title(TITLE)

# --------------------- Disclaimer / Aviso Legal ---------------------
DISCLAIMER = """
**Aviso importante (leia antes de usar):**

Esta ferramenta foi criada **para auxiliar** na conferência de arquivos XML de NF-e
relacionados à Reforma Tributária do Consumo. Seu objetivo é apoiar a verificação de
estrutura e consistência de cálculos (por exemplo, **IBS** e **CBS**), tomando por base as
normas atualmente publicadas, em especial:

- **EC 132/2023** (Reforma Tributária do Consumo)  
- **LC 214/2025** e regulamentações correlatas  
- **Nota Técnica NF-e 2025.002 – RTC** (e versões subsequentes)  

**Importante:** os resultados apresentados têm caráter **informativo** e **não substituem**
análise contábil/fiscal especializada, interpretação jurídica, parecer profissional, nem
as validações oficiais dos ambientes autorizadores (SEFAZ/Receita). A responsabilidade
sobre a emissão e a conformidade tributária dos documentos é **exclusivamente do usuário**.
Eventuais divergências podem decorrer de particularidades de interpretação, atualizações
normativas, regimes específicos, parametrizações de ERP, regras estaduais/municipais e
versões de schemas.

**Privacidade e dados:** os arquivos enviados são processados apenas durante a sessão. Não
há compartilhamento automático com terceiros. Evite publicar XMLs com dados sensíveis em
repositórios públicos.  
**Não há vínculo** com SEFAZ, Receita Federal, Conexos ou quaisquer órgãos/fornecedores.

Ao prosseguir, você **concorda** que esta ferramenta é um apoio operacional e **não**
configura aconselhamento fiscal/jurídico.
"""

with st.expander("📜 Aviso Legal e Contexto Normativo", expanded=True):
    st.markdown(DISCLAIMER)

# --------------------- Sidebar (Parâmetros) ---------------------
st.sidebar.header("Parâmetros de Validação (2026 - Teste)")
ibs_pct = st.sidebar.number_input(
    "Alíquota IBS (teste) %", min_value=0.0, max_value=100.0, value=0.10, step=0.01,
    help="Percentual padrão de teste para 2026 (0,10%)."
)
cbs_pct = st.sidebar.number_input(
    "Alíquota CBS (teste) %", min_value=0.0, max_value=100.0, value=0.90, step=0.01,
    help="Percentual padrão de teste para 2026 (0,90%)."
)
tolerance_centavos = st.sidebar.number_input(
    "Tolerância de arredondamento (R$)", min_value=0.00, max_value=1.00, value=0.01, step=0.01,
    help="Diferença máxima aceitável por arredondamento nas validações."
)

# --------------------- Upload do XML ---------------------
uploaded = st.file_uploader("Carregue o arquivo XML da NF-e", type=["xml"])

ns = {"nfe": "http://www.portalfiscal.inf.br/nfe", "ds": "http://www.w3.org/2000/09/xmldsig#"}

def d(s: str) -> Decimal:
    try:
        return Decimal(s)
    except Exception:
        return Decimal("0.00")

def gettext(elem, path: str) -> str:
    if elem is None:
        return ""
    found = elem.find(path, ns)
    return found.text if found is not None else ""

def parse_xml(content: bytes):
    tree = ET.parse(io.BytesIO(content))
    root = tree.getroot()
    return root

def build_quadro(root) -> pd.DataFrame:
    rows = []
    for det in root.findall(".//nfe:det", ns):
        nItem = det.attrib.get("nItem", "")
        prod = det.find("nfe:prod", ns)
        imposto = det.find("nfe:imposto", ns)

        # Valores base p/ total do item
        vProd = d(gettext(prod, "nfe:vProd"))
        vFrete = d(gettext(prod, "nfe:vFrete"))
        vSeg = d(gettext(prod, "nfe:vSeg"))
        vDesc = d(gettext(prod, "nfe:vDesc"))
        vOutro = d(gettext(prod, "nfe:vOutro"))

        cProd = gettext(prod, "nfe:cProd")
        ncm = gettext(prod, "nfe:NCM")
        cfop = gettext(prod, "nfe:CFOP")

        # --- ICMS ---
        icms_parent = imposto.find("nfe:ICMS", ns) if imposto is not None else None
        icms_node = list(icms_parent)[0] if (icms_parent is not None and len(icms_parent)) else None
        cst_icms = gettext(icms_node, "nfe:CST")
        vBC_icms = d(gettext(icms_node, "nfe:vBC"))
        pICMS = d(gettext(icms_node, "nfe:pICMS"))
        vICMS = d(gettext(icms_node, "nfe:vICMS"))

        # --- PIS ---
        pis_parent = imposto.find("nfe:PIS", ns) if imposto is not None else None
        pis_node = list(pis_parent)[0] if (pis_parent is not None and len(pis_parent)) else None
        cst_pis = gettext(pis_node, "nfe:CST")
        vBC_pis = d(gettext(pis_node, "nfe:vBC"))
        pPIS = d(gettext(pis_node, "nfe:pPIS"))
        vPIS = d(gettext(pis_node, "nfe:vPIS"))

        # --- COFINS ---
        cof_parent = imposto.find("nfe:COFINS", ns) if imposto is not None else None
        cof_node = list(cof_parent)[0] if (cof_parent is not None and len(cof_parent)) else None
        cst_cof = gettext(cof_node, "nfe:CST")
        vBC_cof = d(gettext(cof_node, "nfe:vBC"))
        pCOFINS = d(gettext(cof_node, "nfe:pCOFINS"))
        vCOFINS = d(gettext(cof_node, "nfe:vCOFINS"))

        # --- IPI ---
        ipi_parent = imposto.find("nfe:IPI", ns) if imposto is not None else None
        ipi_node = None
        if ipi_parent is not None and len(ipi_parent):
            for ch in list(ipi_parent):
                tag = ch.tag.split("}")[1] if "}" in ch.tag else ch.tag
                if tag in ("IPITrib", "IPINT"):
                    ipi_node = ch
                    break
        vBC_ipi = d(gettext(ipi_node, "nfe:vBC"))
        vIPI = d(gettext(ipi_node, "nfe:vIPI"))

        # --- IBSCBS ---
        ibscbs = imposto.find("nfe:IBSCBS", ns) if imposto is not None else None
        cst_ibs = gettext(ibscbs, "nfe:CST")
        cclass = gettext(ibscbs, "nfe:cClassTrib")
        g = ibscbs.find("nfe:gIBSCBS", ns) if ibscbs is not None else None
        vBC_ibs = d(gettext(g, "nfe:vBC"))
        vIBS = d(gettext(g, "nfe:vIBS"))
        gCBS = g.find("nfe:gCBS", ns) if g is not None else None
        cst_cbs = cst_ibs   # alguns schemas não separam CST para CBS; ajuste se necessário
        cclass_cbs = cclass
        vBC_cbs = vBC_ibs
        vCBS = d(gettext(gCBS, "nfe:vCBS") if gCBS is not None else "")

        # TOTAL ITEM (NT-style)
        total_item = (vProd + vFrete + vSeg + vOutro - vDesc + vIPI).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rows.append({
            "Ordem": int(nItem) if nItem else None,
            "Código do produto": cProd,
            "NCM": ncm,
            "CFOP": cfop,
            "CST ICMS": cst_icms,
            "BC ICMS": float(vBC_icms),
            "ALÍQUOTA ICMS": float(pICMS),
            "VALOR ICMS": float(vICMS),
            "CST PIS": cst_pis,
            "BASE PIS": float(vBC_pis),
            "ALÍQUOTA PIS": float(pPIS),
            "VALOR PIS": float(vPIS),
            "CST COFINS": cst_cof,
            "BASE COFINS": float(vBC_cof),
            "ALÍQUOTA COFINS": float(pCOFINS),
            "VALOR COFINS": float(vCOFINS),
            "CST IBS": cst_ibs,
            "CLASSETRIB (IBS)": cclass,
            "BASE IBS": float(vBC_ibs),
            "VALOR IBS": float(vIBS),
            "CST CBS": cst_cbs,
            "CLASSETRIB (CBS)": cclass_cbs,
            "BASE CBS": float(vBC_cbs),
            "VALOR CBS": float(vCBS),
            "BASE IPI": float(vBC_ipi),
            "VALOR IPI": float(vIPI),
            "TOTAL ITEM (NT)": float(total_item),
        })

    df = pd.DataFrame(rows).sort_values("Ordem")
    # linha TOTAL
    numeric_cols = [
        "BC ICMS","ALÍQUOTA ICMS","VALOR ICMS","BASE PIS","ALÍQUOTA PIS","VALOR PIS",
        "BASE COFINS","ALÍQUOTA COFINS","VALOR COFINS","BASE IBS","VALOR IBS",
        "BASE CBS","VALOR CBS","BASE IPI","VALOR IPI","TOTAL ITEM (NT)"
    ]
    totals = {col: Decimal(str(df[col].sum())).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for col in numeric_cols}
    totals_row = {k: "" for k in df.columns}
    totals_row.update({"Ordem": "TOTAL"})
    for col, val in totals.items():
        totals_row[col] = float(val)
    df_total = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)
    return df_total

def build_checklist(root, ibs_pct: float, cbs_pct: float, tol: float) -> pd.DataFrame:
    checks = []
    def add(grupo, campo, regra, ok, encontrado=None, esperado=None):
        checks.append({
            "Grupo": grupo,
            "Campo": campo,
            "Regra": regra,
            "Status": "✅" if ok else "❌",
            "Encontrado": "" if encontrado is None else str(encontrado),
            "Esperado": "" if esperado is None else str(esperado)
        })

    # Cabeçalho
    tpAmb = gettext(root, ".//nfe:ide/nfe:tpAmb")
    add("Cabeçalho", "ide/tpAmb", "Deve ser 2 (homologação)", tpAmb == "2", tpAmb, "2")

    # Partes
    emit_cnpj = gettext(root, ".//nfe:emit/nfe:CNPJ")
    emit_ie   = gettext(root, ".//nfe:emit/nfe:IE")
    dest_cnpj = gettext(root, ".//nfe:dest/nfe:CNPJ")
    dest_ie   = gettext(root, ".//nfe:dest/nfe:IE")
    dest_uf   = gettext(root, ".//nfe:dest/nfe:enderDest/nfe:UF")
    indIEDest = gettext(root, ".//nfe:dest/nfe:indIEDest")

    add("Partes", "emit/CNPJ", "Preenchido", bool(emit_cnpj), emit_cnpj)
    add("Partes", "emit/IE",   "Preenchido", bool(emit_ie),   emit_ie)
    add("Partes", "dest/CNPJ", "Preenchido", bool(dest_cnpj), dest_cnpj)
    add("Partes", "dest/IE",   "Preenchido", bool(dest_ie),   dest_ie)
    add("Partes", "dest/UF",   "Preenchido", bool(dest_uf),   dest_uf)
    add("Partes", "dest/indIEDest", "Deve ser 1 (contribuinte)", indIEDest == "1", indIEDest, "1")

    # Itens + matemática
    sum_vBC = Decimal("0.00")
    sum_vIBS = Decimal("0.00")
    sum_vCBS = Decimal("0.00")
    tol_dec = Decimal(str(tol))
    p_ibs = Decimal(str(ibs_pct/100.0))
    p_cbs = Decimal(str(cbs_pct/100.0))

    for idx, det in enumerate(root.findall(".//nfe:det", ns), start=1):
        imp = det.find("nfe:imposto", ns)
        ibscbs = imp.find("nfe:IBSCBS", ns) if imp is not None else None
        cst = gettext(ibscbs, "nfe:CST")
        cclass = gettext(ibscbs, "nfe:cClassTrib")
        g = ibscbs.find("nfe:gIBSCBS", ns) if ibscbs is not None else None
        vBC = d(gettext(g, "nfe:vBC"))
        vIBS = d(gettext(g, "nfe:vIBS"))
        gCBS = g.find("nfe:gCBS", ns) if g is not None else None
        vCBS = d(gettext(gCBS, "nfe:vCBS") if gCBS is not None else "")

        add(f"Item {idx}", "IBSCBS/CST", "Preenchido", bool(cst), cst)
        add(f"Item {idx}", "IBSCBS/cClassTrib", "Preenchido", bool(cclass), cclass)
        add(f"Item {idx}", "IBSCBS/vBC", "Preenchido (>0 quando tributado)", vBC > 0, vBC)

        # checagem por item: vIBS = vBC * p_ibs; vCBS = vBC * p_cbs (2 casas)
        expected_vIBS = (vBC * p_ibs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        expected_vCBS = (vBC * p_cbs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ok_ibs = abs(vIBS - expected_vIBS) <= tol_dec
        ok_cbs = abs(vCBS - expected_vCBS) <= tol_dec
        add(f"Item {idx}", "VALOR IBS", f"vBC × {ibs_pct:.2f}% (2 casas)", ok_ib
