import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Ivan & Co. - Warsztat", layout="wide")

# --- DEBUG: SPRAWDZANIE SEKRETÓW ---
# Te kilka linii powie nam, czy Streamlit w ogóle widzi Twoje dane
if "connections" not in st.secrets:
    st.error("❌ BŁĄD: Streamlit nie widzi sekcji [connections] w pliku secrets.toml!")
    st.stop()
if "supabase" not in st.secrets.connections:
    st.error("❌ BŁĄD: Brakuje podsekcji [connections.supabase]!")
    st.stop()

# --- POŁĄCZENIE Z BAZĄ ---
try:
    conn = st.connection("supabase", type=SupabaseConnection,url=st.secrets["connections"]["supabase"]["url"],
    key=st.secrets["connections"]["supabase"]["key"])
except Exception as e:
    st.error(f"❌ Problem z połączeniem: {e}")
    st.stop()

st.title("🚔Auto Kamiński 47🚔")

# --- PANEL BOCZNY: DODAWANIE ---
with st.sidebar:
    st.header("Nowa fucha")
    with st.form("dodaj_form"):
        klient = st.text_input("Klient")
        auto = st.text_input("Bryka")
        c_czesci = st.number_input("Części (koszt)", min_value=0.0)
        c_podw = st.number_input("Podwykonawca (koszt)", min_value=0.0)
        c_laweta = st.number_input("Laweta (koszt)", min_value=0.0)
        cena = st.number_input("Cena dla klienta", min_value=0.0)
        
        if st.form_submit_button("Wyślij do Ivana"):
            if klient and auto:
                data = {
                    "klient": klient,
                    "auto": auto,
                    "koszt_czesci": c_czesci,
                    "koszt_podwykonawcy": c_podw,
                    "koszt_lawety": c_laweta,
                    "cena_dla_klienta": cena,
                    "status": "W trakcie"
                }
                conn.table("zlecenia").insert(data).execute()
                st.success("Wpadło do bazy! Odśwież stronę (R).")
            else:
                st.warning("Wpisz chociaż kto i czym przyjechał!")

# --- WIDOK GŁÓWNY: TABELA ---
try:
    # Pobieramy dane
    res = conn.table("zlecenia").select("*").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # Matematyka inżynierska - liczymy hajs
        df['Zysk netto'] = df['cena_dla_klienta'] - (df['koszt_czesci'] + df['koszt_podwykonawcy'] + df['koszt_lawety'])
        df['Marża %'] = (df['Zysk netto'] / df['cena_dla_klienta'] * 100).round(1)

        st.subheader("📋 Lista zleceń")
        st.dataframe(df.sort_values("id", ascending=False), use_container_width=True)

        # Statystyki na górze
        c1, c2 = st.columns(2)
        c1.metric("Łączny zysk na czysto", f"{df['Zysk netto'].sum()} PLN")
        c2.metric("Liczba aut w robocie", len(df))
    else:
        st.info("Baza jest pusta. Dodaj coś w panelu bocznym!")
except Exception as e:
    st.error(f"Nie udało się pobrać danych: {e}")