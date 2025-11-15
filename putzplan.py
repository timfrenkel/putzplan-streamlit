import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

# ------------------------------
# Einstellungen
# ------------------------------
PERSONEN = ["Luca", "Angie", "Tim"]
RAEUME = ["Küche", "Bad", "Wohnzimmer"]
DATA_FILE = Path("putzplan_daten.csv")
INTERVALL_TAGE = 14         # alle 2 Wochen
ANZAHL_TERMINE = 60         # wie viele Wochenenden im Voraus


# ------------------------------
# Hilfsfunktionen
# ------------------------------
def naechster_samstag(heute=None):
    """Gibt das Datum des nächsten Samstags zurück (inkl. heute, falls heute Samstag ist)."""
    if heute is None:
        heute = date.today()
    weekday = heute.weekday()  # Montag=0 ... Sonntag=6
    tage_bis_samstag = (5 - weekday) % 7
    return heute + timedelta(days=tage_bis_samstag)


def generiere_grundplan(startdatum, anzahl_terminen=ANZAHL_TERMINE):
    daten = []
    aktuelles_datum = startdatum

    for i in range(anzahl_terminen):
        person = PERSONEN[i % len(PERSONEN)]
        raum = RAEUME[i % len(RAEUME)]

        daten.append(
            {
                "Datum": aktuelles_datum.isoformat(),
                "Raum": raum,
                "Person": person,
                "Erledigt": False,
                "Erledigt_von": "",
                "Erledigt_am": ""
            }
        )

        aktuelles_datum += timedelta(days=INTERVALL_TAGE)

    df = pd.DataFrame(daten)
    return df


def lade_oder_erzeuge_plan():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, dtype=str)
        # Typen wiederherstellen
        if "Erledigt" in df.columns:
            df["Erledigt"] = df["Erledigt"] == "True"
        else:
            df["Erledigt"] = False
        return df
    else:
        start = naechster_samstag()
        df = generiere_grundplan(start)
        df.to_csv(DATA_FILE, index=False)
        return df


def speichere_plan(df):
    df.to_csv(DATA_FILE, index=False)


# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title="Putzplan", page_icon="🧼")

st.title("🧼 Putzplan – Küche, Bad & Wohnzimmer")
st.write(
    """
    Dieser Plan verteilt **Küche**, **Bad** und **Wohnzimmer** reihum 
    auf **Luca, Angie und Tim** – jeweils **alle 2 Wochen am Wochenende** (Samstag).
    Jede*r kann hier eintragen, wenn etwas erledigt wurde.
    """
)

st.sidebar.header("Einstellungen / Infos")
benutzername = st.sidebar.selectbox(
    "Wer bist du?",
    options=["(anonym)"] + PERSONEN,
    index=0
)
st.sidebar.write("💡 Wähle deinen Namen, bevor du auf „Ich habe geputzt“ klickst.")

# Plan laden
df = lade_oder_erzeuge_plan()

# Nur zukünftige und aktuelle Termine anzeigen (optional)
heute = date.today().isoformat()
df_future = df[df["Datum"] >= heute].copy().reset_index(drop=True)

st.subheader("Nächste Putztermine (alle 2 Wochen)")
st.write("Klicke auf **„Ich habe geputzt“**, sobald du fertig bist:")

if df_future.empty:
    st.info("Keine zukünftigen Termine mehr im Plan. (Der Plan endet nach einigen Jahren.)")
else:
    # Zeige z.B. die nächsten 15 Einträge
    df_anzeigen = df_future.head(15)

    for idx, row in df_anzeigen.iterrows():
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 3])

        with col1:
            st.write(f"**Datum:** {row['Datum']}")
        with col2:
            st.write(f"**Raum:** {row['Raum']}")
        with col3:
            st.write(f"**Zuständig:** {row['Person']}")

        # Finde den echten Index im Haupt-DataFrame
        mask = (df["Datum"] == row["Datum"]) & (df["Raum"] == row["Raum"]) & (df["Person"] == row["Person"])
        global_index = df[mask].index[0]

        with col4:
            if row["Erledigt"]:
                erledigt_von = row.get("Erledigt_von", "")
                erledigt_am = row.get("Erledigt_am", "")
                text = "✅ Erledigt"
                if erledigt_von:
                    text += f" von **{erledigt_von}**"
                if erledigt_am:
                    text += f" am {erledigt_am}"
                st.write(text)
            else:
                button_label = "Ich habe geputzt"
                if st.button(button_label, key=f"done_{global_index}"):
                    df.at[global_index, "Erledigt"] = True
                    df.at[global_index, "Erledigt_am"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    df.at[global_index, "Erledigt_von"] = (
                        benutzername if benutzername != "(anonym)" else ""
                    )
                    speichere_plan(df)
                    st.experimental_rerun()

st.subheader("Übersicht (alle Einträge)")
with st.expander("Gesamten Putzplan anzeigen (Tabelle)"):
    st.dataframe(df)
