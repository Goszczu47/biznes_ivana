import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Auto Kamiński 47", layout="wide")

# --- CSS: UKRYWANIE SIDEBARA NA DESKTOPIE ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { display: block; }
    }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICJALIZACJA BUFORA CZĘŚCI (SESSION STATE) ---
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

# --- POŁĄCZENIE Z BAZĄ ---
try:
    conn = st.connection("supabase", type=SupabaseConnection,
                         url=st.secrets["connections"]["supabase"]["url"],
                         key=st.secrets["connections"]["supabase"]["key"])
except Exception as e:
    st.error(f"❌ Problem z połączeniem: {e}")
    st.stop()

st.title("🚔 Auto Kamiński 47 🚔")

# --- SEKRETNE MENU GÓRNE (ZSUWANE) ---
with st.expander("➕ DODAJ NOWE ZLECENIE I CZĘŚCI"):
    # 1. Dane ogólne zlecenia
    c1, c2 = st.columns(2)
    klient = c1.text_input("Imię i nazwisko klienta", placeholder="np. Jan Kowalski")
    auto = c2.text_input("Marka i model auta", placeholder="np. Audi A4 B8")

    st.divider()
    st.subheader("🛠️ Lista części / Robocizna")
    
    # 2. Kreator pozycji (BOM)
    col_n, col_m, col_i, col_b = st.columns([3, 2, 1, 2])
    nazwa_p = col_n.text_input("Co kupione / robione?")
    marka_p = col_m.text_input("Marka części")
    ilosc_p = col_i.number_input("Szt.", min_value=1, value=1)
    brutto_p = col_b.number_input("Cena Brutto (1 szt.)", min_value=0.0, format="%.2f")

    # Inżynierskie przeliczenie netto (VAT 23%)
    netto_p = round(brutto_p / 1.23, 2)
    st.caption(f"💡 Cena netto (1 szt.): {netto_p} PLN | Suma brutto pozycji: {round(brutto_p * ilosc_p, 2)} PLN")

    if st.button("➕ DODAJ POZYCJĘ DO LISTY"):
        if nazwa_p:
            item = {
                "Nazwa": nazwa_p,
                "Marka": marka_p,
                "Ilość": ilosc_p,
                "Brutto": brutto_p,
                "Netto": netto_p,
                "Suma Brutto": round(brutto_p * ilosc_p, 2)
            }
            st.session_state.temp_items.append(item)
            st.rerun()
        else:
            st.error("Wpisz nazwę części, żeby ją dodać!")

    # 3. Wyświetlanie aktualnej listy części
    if st.session_state.temp_items:
        temp_df = pd.DataFrame(st.session_state.temp_items)
        st.table(temp_df)
        
        suma_czesci = temp_df["Suma Brutto"].sum()
        st.info(f"💰 Łączny koszt wszystkich części: {round(suma_czesci, 2)} PLN")

        if st.button("🗑️ WYCZYŚĆ LISTĘ CZĘŚCI"):
            st.session_state.temp_items = []
            st.rerun()

    st.divider()
    
    # 4. Finalizacja i dodatkowe koszty
    col_x, col_y, col_z = st.columns(3)
    c_podw = col_x.number_input("Podwykonawca (brutto)", min_value=0.0)
    c_laweta = col_y.number_input("Laweta (brutto)", min_value=0.0)
    cena_final = col_z.number_input("Cena dla klienta (koniec)", min_value=0.0)

    if st.button("🚀 WYŚLIJ CAŁE ZLECENIE DO BAZY"):
        if klient and auto and cena_final > 0:
            suma_czesci = sum(item["Suma Brutto"] for item in st.session_state.temp_items)
            
            payload = {
                "klient": klient,
                "auto": auto,
                "koszt_czesci": suma_czesci,
                "koszt_podwykonawcy": c_podw,
                "koszt_lawety": c_laweta,
                "cena_dla_klienta": cena_final,
                "status": "W trakcie"
            }
            
            conn.table("zlecenia").insert(payload).execute()
            st.session_state.temp_items = [] # czyścimy listę części
            st.success("Zlecenie zapisane! Ivan może pić kawę.")
            st.rerun()
        else:
            st.warning("Uzupełnij Klienta, Auto i Cenę dla klienta!")

# --- WIDOK GŁÓWNY: STATYSTYKI I TABELA ---
try:
    res = conn.table("zlecenia").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # Obliczenia zysku
        df['Zysk netto'] = df['cena_dla_klienta'] - (df['koszt_czesci'] + df['koszt_podwykonawcy'] + df['koszt_lawety'])
        
        # Górne statystyki (Metryki)
        m1, m2, m3 = st.columns(3)
        m1.metric("Całkowity zysk (netto)", f"{round(df['Zysk netto'].sum(), 2)} PLN")
        m2.metric("Auta w robocie", len(df[df['status'] != 'Gotowe']))
        
        total_cena = df['cena_dla_klienta'].sum()
        marza = (df['Zysk netto'].sum() / total_cena * 100) if total_cena > 0 else 0
        m3.metric("Średnia marża %", f"{round(marza, 1)}%")

        st.subheader("📋 Lista zleceń (kliknij w status, by zmienić)")
        
        # Edytor tabeli (tylko status jest edytowalny)
        edited_df = st.data_editor(
            df.sort_values("id", ascending=False),
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["W trakcie", "Oczekuje na części", "Do odbioru", "Gotowe"],
                    required=True,
                ),
                "id": None, # Ukrywamy ID
                "created_at": None # Ukrywamy datę systemową
            },
            disabled=["klient", "auto", "koszt_czesci", "koszt_podwykonawcy", "koszt_lawety", "cena_dla_klienta", "Zysk netto"],
            use_container_width=True,
            key="main_editor"
        )

        # Przycisk zapisu zmian statusu
        if st.button("💾 ZAPISZ ZMIANY W STATUSACH"):
            if st.session_state["main_editor"]["edited_rows"]:
                for idx_str, changes in st.session_state["main_editor"]["edited_rows"].items():
                    idx = int(idx_str) # Streamlit czasem zwraca index jako string
                    if "status" in changes:
                        # Znajdujemy ID w oryginalnym DataFrame (przed sortowaniem)
                        row_id = df.sort_values("id", ascending=False).iloc[idx]["id"]
                        new_status = changes["status"]
                        conn.table("zlecenia").update({"status": new_status}).eq("id", row_id).execute()
                st.success("Zmiany zapisane!")
                st.rerun()

    else:
        st.info("Baza jest pusta. Rozwiń panel na górze, żeby dodać pierwsze auto.")
except Exception as e:
    st.error(f"Błąd przy pobieraniu danych: {e}")