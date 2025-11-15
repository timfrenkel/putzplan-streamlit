import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta

# ------------------------------
# Einstellungen
# ------------------------------
# Reihenfolge passend zum Beispiel:
# Woche 1: Tim -> Bad, Luca -> Küche, Angie -> Wohnzimmer
PERSONEN = ["Tim", "Luca", "Angie"]
RAEUME = ["Bad", "Küche", "Wohnzimmer"]

DATA_FILE = Path("putzplan_daten.csv")
ANZAHL_WOCHEN = 80  # wie viele Wochenenden im Voraus (ca. 1,5 Jahre)


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


def generiere_grundplan(startdatum, anzahl_wochen=ANZAHL_WOCHEN):
    """
    Erzeugt einen Plan, in dem JEDES Wochenende alle 3 Räume
    von Tim, Luca und Angie im Rotationsprinzip geputzt werden.
    """
    daten = []
    aktuelles_datum = startdatum

    for woche in range(anzahl_wochen):
        for i, person in enumerate(PERSONEN):
            # Rotation: Person i bekommt Raum (i + woche) mod len(RAEUME)
            raum = RAEUME[(i + woche) % len(RAEUME)]
            daten.append(
                {
                    "Datum": aktuelles_datum.isoformat(),
                    "Woche": woche + 1,
                    "Raum": raum,
                    "Person": person,
                    "Erledigt": False,
                    "Erledigt_von": "",
                    "Erledigt_am": ""
                }
            )

        # nächstes Wochenende (Samstag)
        aktuelles_datum += timedelta(days=7)

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

        # Falls es alte Pläne mit anderen Spalten gibt, fehlende Spalten ergänzen
        for col in ["Woche", "Erledigt_von", "Erledigt_am"]:
            if col not in df.columns:
                df[col] = "" if col != "Woche" else 0

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
    Dieser Putzplan verteilt **Bad**, **Küche** und **Wohnzimmer** an **Tim, Luca und Angie**.
    
    - **JEDES Wochenende** (Samstag) werden alle drei Räume geputzt.  
    - Die Aufgaben rotieren so, dass jede Person reihum alle Räume bekommt.  
    - Wähle zuerst deinen Namen, dann siehst du **deine Aufgaben**.
    """
)

# --- Name auswählen ---
st.sidebar.header("Wer bist du?")
benutzername = st.sidebar.selectbox(
    "Bitte Namen auswählen:",
    options=["(bitte auswählen)"] + PERSONEN,
    index=0
)

st.sidebar.markdown(
    """
    💡 Nach der Auswahl siehst du:
    - deine nächsten Putztermine
    - was du wann putzen musst
    """
)

df = lade_oder_erzeuge_plan()

heute_iso = date.today().isoformat()
df_future = df[df["Datum"] >= heute_iso].copy().reset_index(drop=True)

if benutzername == "(bitte auswählen)":
    st.warning("Bitte wähle links in der Seitenleiste zuerst deinen Namen aus.")
else:
    # ------------------------------
    # Deine nächsten Aufgaben
    # ------------------------------
    st.subheader(f"Deine nächsten Aufgaben, {benutzername}:")
    df_user = df_future[df_future["Person"] == benutzername].copy().reset_index(drop=True)

    if df_user.empty:
        st.info("Für dich sind aktuell keine zukünftigen Aufgaben im Plan.")
    else:
        # Nur die nächsten z.B. 12 Aufgaben anzeigen
        df_user_anzeige = df_user.head(12)

        for idx, row in df_user_anzeige.iterrows():
            st.markdown("---")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 3])

            with col1:
                st.write(f"**Datum:** {row['Datum']}")
                woche_info = row.get("Woche", "")
                if woche_info != "":
                    st.caption(f"Kalenderwoche im Plan: {woche_info}")
            with col2:
                st.write(f"**Raum:** {row['Raum']}")
            with col3:
                status_text = "❌ Noch offen"
                if bool(row["Erledigt"]):
                    status_text = "✅ Erledigt"
                st.write(f"**Status:** {status_text}")

            # Echten Index im Haupt-DataFrame finden
            mask = (
                (df["Datum"] == row["Datum"])
                & (df["Raum"] == row["Raum"])
                & (df["Person"] == row["Person"])
            )
            global_index = df[mask].index[0]

            with col4:
                if bool(row["Erledigt"]):
                    erledigt_von = row.get("Erledigt_von", "")
                    erledigt_am = row.get("Erledigt_am", "")
                    info_text = ""
                    if erledigt_von:
                        info_text += f"von **{erledigt_von}** "
                    if erledigt_am:
                        info_text += f"am {erledigt_am}"
                    if info_text:
                        st.caption(info_text)
                else:
                    if st.button("Ich habe geputzt", key=f"user_done_{global_index}"):
                        df.at[global_index, "Erledigt"] = True
                        df.at[global_index, "Erledigt_am"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                        df.at[global_index, "Erledigt_von"] = benutzername
                        speichere_plan(df)
                        st.rerun()

    # ------------------------------
    # Übersicht pro Wochenende
    # ------------------------------
    st.subheader("Übersicht: alle Aufgaben nach Datum")

    st.write(
        "Hier siehst du alle Aufgaben pro Wochenende. "
        "So kannst du auch prüfen, was die anderen machen."
    )

    # Tabelle der zukünftigen Termine (nächsten 12 Wochenenden)
    df_future_sorted = df_future.sort_values(["Datum", "Person"])
    naechste_termine = (
        df_future_sorted.groupby("Datum")
        .head(3)  # pro Datum max. 3 Zeilen (Bad/Küche/Wohnzimmer)
        .reset_index(drop=True)
    )

    with st.expander("Nächste Wochenenden anzeigen"):
        st.dataframe(
            naechste_termine[["Datum", "Person", "Raum", "Erledigt"]],
            use_container_width=True,
        )

# ------------------------------
# Vollständiger Plan (optional)
# ------------------------------
st.subheader("Gesamter Putzplan (komplette Tabelle)")
with st.expander("Hier klicken, um den kompletten Plan zu sehen"):
    st.dataframe(df, use_container_width=True)
