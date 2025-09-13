# 🧾 Conferência XML Reforma Tributária

Aplicação em **Python + Streamlit** para conferência dos arquivos XML da **NF-e** com os novos campos da **Reforma Tributária do Consumo** (IBS / CBS / IS).

![screenshot](docs/screenshot.png) <!-- opcional: insira imagem depois -->

---

## 🎯 Objetivo

Esta ferramenta foi desenvolvida para **auxiliar** empresas, contadores e equipes fiscais na verificação dos arquivos XML de NF-e, especialmente quanto às novas exigências da **EC 132/2023** e da **LC 214/2025**, que instituem o IBS e a CBS.

Ela permite:

- **Upload** de um arquivo XML da NF-e (layout NT 2025.002-RTC ou superior);
- Exibição de um **Quadro Resumo por Item** com:
  - CFOP, CST, NCM, ICMS, PIS, COFINS, IBS, CBS, IPI, Total do Item;
- Geração automática de um **Checklist Obrigatório** com validações:
  - Presença de tags obrigatórias (CST, cClassTrib, bases e valores);
  - Comparação matemática (ex.: vIBS = vBC × 0,10% para fase de testes 2026);
  - Validação de totais (soma dos itens = totais do XML);
- Exportação para **Excel** (quadro + checklist).

---

## ⚖️ Aviso Legal

> **IMPORTANTE:**  
> Esta aplicação é uma **ferramenta de apoio** para conferência de arquivos XML e **não substitui**:
> - a análise contábil/fiscal/jurídica profissional,
> - os validadores oficiais dos ambientes SEFAZ/Receita Federal,
> - ou as regras específicas de cada Estado/Município.
>
> O usuário permanece responsável pela conformidade das operações e pela correta parametrização dos seus sistemas de gestão/ERP.  
> As normas podem sofrer alterações, e recomenda-se sempre a verificação das versões mais recentes das Notas Técnicas e legislações aplicáveis.

---

## 🚀 Instalação e Uso

### 1. Clonar o repositório

```bash
git clone https://github.com/seuusuario/conferencia-xml-reforma-tributaria.git
cd conferencia-xml-reforma-tributaria
