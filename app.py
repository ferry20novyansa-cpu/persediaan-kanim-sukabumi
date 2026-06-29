import streamlit as st
import pandas as pd
import requests
import qrcode
from io import BytesIO
from datetime import datetime

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Form Pengambilan ATK - Kanim Sukabumi",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────
SPREADSHEET_ID   = "1HAkMbdIk6rhHLEVRDzIvWfKrsNKzUTG-tzerytoKPYA"
GID_MASTER       = "1337233070"
GID_REKAPITULASI = "0"
STREAMLIT_URL    = "https://persediaan-kanim-sukabumi-fdt4geo532o3xht2rctcwd.streamlit.app"

# URL baca CSV langsung dari Google Sheets (tanpa OAuth, cukup sheet di-share publik)
MASTER_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    f"/export?format=csv&gid={GID_MASTER}"
)
REKAP_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    f"/export?format=csv&gid={GID_REKAPITULASI}"
)

# URL Google Sheets API untuk write (via Apps Script Web App)
# Diisi nanti setelah deploy Apps Script
APPS_SCRIPT_URL = st.secrets.get("APPS_SCRIPT_URL", "")

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

.main-header { text-align: center; padding: 10px 0 20px 0; }
.main-header h1 { font-size: 24px; color: #0068c9; margin-bottom: 4px; }
.main-header p  { font-size: 16px; color: #666; }

.stSelectbox label, .stNumberInput label {
    font-size: 18px !important;
    font-weight: 600 !important;
}

.stFormSubmitButton > button {
    width: 100%; height: 60px;
    font-size: 22px; font-weight: 700;
    border-radius: 12px;
    background-color: #0068c9;
    color: white; border: none;
}
.stFormSubmitButton > button:hover { background-color: #0053a8; }

.success-msg {
    background-color: #d4edda;
    border: 1px solid #28a745;
    border-radius: 8px; padding: 16px;
    font-size: 18px; font-weight: 600;
    color: #155724; text-align: center; margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📦 FORM PENGAMBILAN ATK & DOKIM</h1>
    <p>Kantor Imigrasi Kelas I Non TPI Sukabumi</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# LOAD MASTER DATA (baca langsung via CSV export)
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_master_data():
    try:
        df = pd.read_csv(MASTER_CSV_URL)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data master: {e}")
        return None

def get_items(master_df):
    if master_df is not None and "Nama Barang" in master_df.columns:
        items = master_df["Nama Barang"].dropna().unique().tolist()
        items = [str(i).strip() for i in items if str(i).strip()]
        return sorted(items)
    return []

SECTIONS = [
    "TATA USAHA",
    "INTELDAKIM",
    "INTALTUSKIM",
    "YANVERDOKJAL",
    "TIKKIM",
]

# ──────────────────────────────────────────────
# SUBMIT DATA via Google Apps Script
# ──────────────────────────────────────────────
def submit_data(tanggal_str, seksi, nama_barang, jumlah):
    if not APPS_SCRIPT_URL:
        return False, "APPS_SCRIPT_URL belum dikonfigurasi di Secrets."
    try:
        payload = {
            "tanggal"     : tanggal_str,
            "seksi"       : seksi,
            "nama_barang" : nama_barang,
            "jumlah"      : int(jumlah),
            "status"      : "Pending",
        }
        resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        if resp.status_code == 200:
            return True, "Berhasil disimpan!"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)

# ──────────────────────────────────────────────
# QR CODE
# ──────────────────────────────────────────────
def generate_qr(url: str) -> bytes:
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def show_qr_section():
    st.markdown("---")
    st.markdown("### 📱 SCAN QR CODE UNTUK MENGAKSES FORM")
    st.markdown("Arahkan kamera ponsel ke QR Code di bawah untuk langsung membuka form pengambilan barang.")
    qr_img = generate_qr(STREAMLIT_URL)
    st.image(qr_img, caption="QR Code Form Pengambilan ATK", width=250)

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    master_df = load_master_data()
    items     = get_items(master_df)

    if not items:
        st.warning("⚠️ Data barang belum tersedia di sheet 'Master Data'.")
        st.info("Pastikan Google Sheet sudah dibagikan publik (Anyone with the link → Viewer).")
        show_qr_section()
        return

    with st.form("form_pengambilan", clear_on_submit=True):
        st.markdown("**Isi data di bawah untuk pengambilan barang:**")

        tanggal = st.date_input(
            "📅 Tanggal Pengambilan",
            value=datetime.now(),
            format="DD/MM/YYYY",
        )
        seksi = st.selectbox(
            "🏢 Seksi / Bagian",
            options=SECTIONS,
            index=None,
            placeholder="Pilih seksi...",
        )
        nama_barang = st.selectbox(
            "📦 Nama Barang",
            options=items,
            index=None,
            placeholder="Pilih barang...",
        )
        jumlah = st.number_input(
            "🔢 Jumlah",
            min_value=1, max_value=10000, value=1, step=1,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 KONFIRMASI AMBIL BARANG", use_container_width=True)

        if submitted:
            if not seksi:
                st.error("❌ Mohon pilih seksi / bagian!")
                return
            if not nama_barang:
                st.error("❌ Mohon pilih nama barang!")
                return

            tanggal_str = tanggal.strftime("%d/%m/%Y")
            success, message = submit_data(tanggal_str, seksi, nama_barang, jumlah)

            if success:
                st.markdown(f"""
                <div class="success-msg">
                    ✅ BERHASIL DISIMPAN!<br>
                    Tanggal: {tanggal_str}<br>
                    Seksi: {seksi}<br>
                    Barang: {nama_barang} × {jumlah}
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            else:
                st.error(f"❌ Gagal menyimpan: {message}")

    show_qr_section()

if __name__ == "__main__":
    main()
