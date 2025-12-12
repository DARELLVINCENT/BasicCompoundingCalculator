import streamlit as st
import pandas as pd
import numpy as np
from typing import Any

# -----------------------------
# Helpers
# -----------------------------
def fv_annuity_ordinary(P: float, r: float, n: int) -> float:
    """
    Future value of an ordinary annuity (setor di akhir bulan).
    P: setoran per bulan
    r: suku bunga per bulan (mis. 0.01 untuk 1%)
    n: jumlah bulan
    """
    if r == 0:
        return P * n
    return P * ((1 + r) ** n - 1) / r

def fv_annuity(P: float, r: float, n: int, due: bool = False) -> float:
    """
    General annuity.
    due=False  -> ordinary annuity (akhir bulan)
    due=True   -> annuity due (awal bulan) => dikali (1+r)
    """
    base = fv_annuity_ordinary(P, r, n)
    return base * (1 + r) if due else base

def fmt_rp(x: Any) -> str:
    try:
        val = float(x)
    except (ValueError, TypeError):
        return str(x)
    return f"Rp{int(round(val)):,.0f}".replace(",", ".")

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Future Value Tabungan", page_icon="💰", layout="centered")

st.title("💰 Simulasi Future Value Tabungan Bulanan")
st.write("Hitung nilai masa depan tabungan dengan setoran **bulanan**, durasi **tahun/bulan**, dan return **per bulan** atau **per tahun**.")

col1, col2 = st.columns(2)
with col1:
    P = st.number_input("Setoran bulanan (Rp)", min_value=0, step=10_000, value=400_000, format="%d")

    durasi_unit = st.radio("Input durasi dalam", ["Tahun", "Bulan"], horizontal=True)
    if durasi_unit == "Tahun":
        years = st.number_input("Durasi (tahun)", min_value=1, max_value=50, value=8, step=1)
        months = int(years * 12)
    else:
        months = st.number_input("Durasi (bulan)", min_value=1, max_value=600, value=24, step=1)
        years = months // 12  # untuk tabel tahunan opsional

with col2:
    period_choice = st.radio("Periode return", ["Per Bulan", "Per Tahun"], index=1, horizontal=True)
    r_percent = st.slider("Return (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1,
                          help="Geser untuk memilih tingkat return (dalam persen).")

    timing = st.radio("Waktu setoran tiap bulan", ["Akhir Bulan (Ordinary)", "Awal Bulan (Annuity Due)"], index=0, horizontal=False)
    is_due = (timing == "Awal Bulan (Annuity Due)")

# Konversi ke suku bunga bulanan
if period_choice == "Per Bulan":
    r_month = r_percent / 100.0
else:  # Per Tahun
    r_month = (r_percent / 100.0) / 12.0

# -----------------------------
# Perhitungan
# -----------------------------
FV = fv_annuity(P, r_month, int(months), due=is_due)
principal = P * int(months)
interest = FV - principal

st.subheader("Hasil Ringkas")
colA, colB, colC = st.columns(3)
colA.metric("Total Setoran", fmt_rp(principal))
colB.metric("Future Value", fmt_rp(FV))
colC.metric("Total Bunga/Return", fmt_rp(interest))

# -----------------------------
# Tabel per tahun (jika ada ≥ 12 bulan)
# -----------------------------
if years >= 1:
    records = []
    for y in range(1, years + 1):
        m = y * 12
        fv_y = fv_annuity(P, r_month, m, due=is_due)
        principal_y = P * m
        interest_y = fv_y - principal_y
        records.append(
            {"Tahun": y, "Setoran Kumulatif": principal_y, "Future Value": fv_y, "Bunga/Return": interest_y}
        )
    df_yearly = pd.DataFrame(records)
    st.markdown("### Tabel Per Tahun")
    st.dataframe(
        df_yearly.style.format({"Setoran Kumulatif": fmt_rp, "Future Value": fmt_rp, "Bunga/Return": fmt_rp}),
        use_container_width=True,
    )

# -----------------------------
# Grafik & Tabel perkembangan per bulan
# -----------------------------
progress = [fv_annuity(P, r_month, m, due=is_due) for m in range(1, int(months) + 1)]
df_progress = pd.DataFrame({"Bulan": np.arange(1, int(months) + 1), "Future Value": progress}).set_index("Bulan")

st.markdown("### Grafik Perkembangan (per Bulan)")
st.line_chart(df_progress["Future Value"], height=380)

st.markdown("### Tabel Per Bulan (ringkas)")
df_progress_tbl = df_progress.reset_index()
df_progress_tbl["Setoran Kumulatif"] = df_progress_tbl["Bulan"] * P
df_progress_tbl["Bunga/Return"] = df_progress_tbl["Future Value"] - df_progress_tbl["Setoran Kumulatif"]
st.dataframe(
    df_progress_tbl.style.format({"Setoran Kumulatif": fmt_rp, "Future Value": fmt_rp, "Bunga/Return": fmt_rp}),
    use_container_width=True,
)

# -----------------------------
# Catatan & Rumus
# -----------------------------
with st.expander("Catatan & Rumus"):
    st.write(r"""
**Ordinary annuity (setor di akhir bulan):**
\[
FV = P \times \frac{(1+r)^n - 1}{r}
\]
Pada **bulan pertama**: \(FV(1) = P\) → **tidak ada bunga** di bulan pertama.

**Annuity due (setor di awal bulan):**
\[
FV_\text{due} = \left(P \times \frac{(1+r)^n - 1}{r}\right)\times(1+r)
\]
Pada **bulan pertama**: \(FV_\text{due}(1) = P\times(1+r)\) → **langsung dapat bunga** bulan pertama.

Keterangan:
- \(P\) = setoran bulanan  
- \(r\) = return per bulan *(jika input tahunan, gunakan \(r = \text{return tahunan}/12\))*  
- \(n\) = jumlah bulan
Jika \(r=0\), maka \(FV=P\times n\).
    """)
