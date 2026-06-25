import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import qrcode
from io import BytesIO

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
# CUSTOM CSS FOR MOBILE-FRIENDLY UI
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide Streamlit default padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* Instruction text styling */
    .instruction-text {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 8px;
        line-height: 1.5;
    }

    .sub-instruction {
        font-size: 17px;
        color: #444;
        margin-bottom: 20px;
    }

    /* Form labels */
    .stSelectbox label,
    .stNumberInput label {
        font-size: 18px !important;
        font-weight: 600 !important;
    }

    /* Submit button styling */
    .stFormSubmitButton > button {
        width: 100%;
        height: 60px;
        font-size: 22px;
        font-weight: 700;
        border-radius: 12px;
        background-color: #0068c9;
        color: white;
        border: none;
        transition: background-color 0.2s;
    }

    .stFormSubmitButton > button:hover {
        background-color: #0053a8;
    }

    .stFormSubmitButton > button:active {
        background-color: #004080;
    }

    /* Success message */
    .success-msg {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 16px;
        font-size: 18px;
        font-weight: 600;
        color: #155724;
        text-align: center;
        margin: 10px 0;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 10px 0 20px 0;
    }

    .main-header h1 {
        font-size: 24px;
        color: #0068c9;
        margin-bottom: 4px;
    }

    .main-header p {
        font-size: 16px;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
        <h1>📦 FORM PENGAMBILAN ATK & DOKIM</h1>
        <p>Kantor Imigrasi Kelas I Non TPI Sukabumi</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# GOOGLE SHEETS CONNECTION
# ──────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789/edit"

# ──────────────────────────────────────────────
# READ MASTER DATA
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_master_data():
    try:
        df = conn.read(worksheet="Master Data", spreadsheet=SPREADSHEET_URL)
        return df
    except Exception as e:
        st.error(f"Gagal memuat data master: {e}")
        return None


def load_sections():
    return [
        "Tata Usaha",
        "Intelijen dan Penindakan Keimigrasian",
        "Izin Tinggal dan Status Keimigrasian",
        "Pelayanan dan Verifikasi Dokumen Keimigrasian",
        "Teknologi Informasi dan Komunikasi Keimigrasian",
    ]


def load_items(master_df):
    if master_df is not None and "Nama Barang" in master_df.columns:
        items = master_df["Nama Barang"].dropna().unique().tolist()
        items = [i.strip() for i in items if str(i).strip()]
        return sorted(items)
    return []


# ──────────────────────────────────────────────
# SUBMIT DATA TO REKAPITULASI
# ──────────────────────────────────────────────
def submit_to_rekapitulasi(tanggal, seksi, nama_barang, jumlah):
    try:
        new_data = {
            "Tanggal Pengambilan": tanggal,
            "Seksi Pengambil": seksi,
            "Nama Barang": nama_barang,
            "Jumlah": int(jumlah),
            "Status": "Pending",
        }

        existing_df = conn.read(worksheet="Rekapitulasi", spreadsheet=SPREADSHEET_URL)

        import pandas as pd
        new_row = pd.DataFrame([new_data])

        if existing_df.empty:
            combined_df = new_row
        else:
            combined_df = pd.concat([existing_df, new_row], ignore_index=True)

        conn.write(
            data=combined_df,
            worksheet="Rekapitulasi",
            spreadsheet=SPREADSHEET_URL,
            reset_index=False,
        )
        return True, "Berhasil disimpan!"
    except Exception as e:
        return False, str(e)


# ──────────────────────────────────────────────
# QR CODE GENERATOR
# ──────────────────────────────────────────────
def generate_qr_code(data_str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ──────────────────────────────────────────────
# DISPLAY QR CODE SECTION
# ──────────────────────────────────────────────
def show_qr_section():
    st.markdown("---")
    st.markdown(
        '<p class="instruction-text">📱 SCAN QR CODE UNTUK MENGAKSES FORM</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-instruction">Arahkan kamera ponsel ke QR Code di bawah untuk langsung membuka form pengambilan barang.</p>',
        unsafe_allow_html=True,
    )

    current_url = "https://your-streamlit-app-url.streamlit.app"
    qr_img = generate_qr_code(current_url)
    st.image(qr_img, caption="QR Code Form Pengambilan ATK", width=250)


# ──────────────────────────────────────────────
# MAIN FORM
# ──────────────────────────────────────────────
def main():
    master_df = load_master_data()
    sections = load_sections()
    items = load_items(master_df)

    if not items:
        st.warning("⚠️ Data barang belum tersedia di sheet 'Master Data'.")
        st.info("Pastikan sheet 'Master Data' memiliki kolom 'Nama Barang' dengan data yang benar.")
        show_qr_section()
        return

    # ── FORM ──
    with st.form("form_pengambilan", clear_on_submit=True):
        st.markdown(
            '<p class="instruction-text">Isi data di bawah untuk pengambilan barang:</p>',
            unsafe_allow_html=True,
        )

        # Date field
        tanggal = st.date_input(
            "📅 Tanggal Pengambilan",
            value=datetime.now(),
            format="DD/MM/YYYY",
        )

        # Section dropdown
        seksi = st.selectbox(
            "🏢 Seksi / Bagian",
            options=sections,
            index=None,
            placeholder="Pilih seksi...",
        )

        # Item dropdown
        nama_barang = st.selectbox(
            "📦 Nama Barang",
            options=items,
            index=None,
            placeholder="Pilih barang...",
        )

        # Quantity
        jumlah = st.number_input(
            "🔢 Jumlah",
            min_value=1,
            max_value=10000,
            value=1,
            step=1,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🚀 KONFIRMASI AMBIL BARANG",
            use_container_width=True,
        )

        if submitted:
            # Validation
            if not seksi:
                st.error("❌ Mohon pilih seksi / bagian!")
                return
            if not nama_barang:
                st.error("❌ Mohon pilih nama barang!")
                return

            # Format date as DD/MM/YYYY
            tanggal_str = tanggal.strftime("%d/%m/%Y")

            # Submit data
            success, message = submit_to_rekapitulasi(
                tanggal=tanggal_str,
                seksi=seksi,
                nama_barang=nama_barang,
                jumlah=jumlah,
            )

            if success:
                st.markdown(
                    f"""
                    <div class="success-msg">
                        ✅ BERHASIL DISIMPAN!<br>
                        Tanggal: {tanggal_str}<br>
                        Seksi: {seksi}<br>
                        Barang: {nama_barang} x {jumlah}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.balloons()
            else:
                st.error(f"❌ Gagal menyimpan: {message}")

    # ── QR CODE SECTION ──
    show_qr_section()


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
