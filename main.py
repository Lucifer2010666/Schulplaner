import json, hashlib, requests, os

import flet as ft, pandas as pd

from cryptography.fernet import Fernet

DATEN_ON = {}
ID_PASSWORT = {}

Rolle = "Schueler"


def main(page : ft.Page):

    page.title = "Schulplaner"
    
    view_type1 = ft.RadioGroup(content=ft.Radio(value="Klasse", label="Klassen-Plan"), value="Klasse")
    view_type2 = ft.RadioGroup(content=ft.Row([ft.Radio(value="Klasse", label="Klassen-Plan"), ft.Radio(value="Lehrer", label="Lehrer-Plan"), ft.Radio(value="Raum", label="Raum-Plan")]), value="Klasse")

    selection_dd = ft.Dropdown(label="Auswahl", width=300)

    Schul_ID_TF = ft.TextField(label="Schul ID", input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$", replacement_string=""))
    Rolle_dd = ft.Dropdown(options=[ft.DropdownOption(key="Schüler", text="Schüler"), ft.DropdownOption(key="Lehrer", text="Lehrer"), ft.DropdownOption(key="Admin", text="Admin")], value="Schüler")
    Schul_Passwort_TF = ft.TextField(label="Passwort")

    wochen_tabelle = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Std", weight="bold")), ft.DataColumn(ft.Text("Mo")), ft.DataColumn(ft.Text("Di")), ft.DataColumn(ft.Text("Mi")), ft.DataColumn(ft.Text("Do")), ft.DataColumn(ft.Text("Fr"))],    
        column_spacing=45, border=ft.border.all(1, ft.Colors.GREY_400), border_radius=10, vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300)
    )
    

    def multi_hash(key_string):
        # Den Key in Bytes umwandeln
        data = key_string.encode('utf-8')
        
        for i in range(1000):
            
            # 1. Schritt: SHA-256
            data = hashlib.sha256(data).digest()
            
            # 2. Schritt: SHA-512
            data = hashlib.sha512(data).digest()
            
            # 3. Schritt: SHA-3-256 (moderner Standard)
            data = hashlib.sha3_256(data).digest()
            
        return data.hex()

    def get_fernet_key(schul_id):
        
        return "FE-6uuyTJxR4lxz_VIhshSqfFQiMPWlanzdCPHVeYC0="  # Überarbeiten

    def lade_und_entschluessele_plan(schul_id):
        global DATEN_ON

        url = f"https://raw.githubusercontent.com/Lucifer2010666/Schulplaner/main/{schul_id}"
        
        
        try:
            res = requests.get(url)
            if res.status_code == 200:
                verschluesselter_salat = res.content
                
                f = Fernet(get_fernet_key(schul_id).encode())
                entschluesselte_bytes = f.decrypt(verschluesselter_salat)
                
                plan_daten = json.loads(entschluesselte_bytes.decode("utf-8"))

                DATEN_ON = plan_daten
                return plan_daten

        except Exception as e:
            ...

    def get_plan(schul_id):
        
        plan_daten = lade_und_entschluessele_plan(schul_id)

        # 2. In DataFrame umwandeln
        df = pd.DataFrame(plan_daten["plan"])

        # 3. Tabelle vorbereiten
        wochen_tabelle.rows.clear()
        
        if selection_dd.value is None or df.empty: 
            page.update()
            return

        # Filter-Spalte basierend auf view_type (Klasse, Raum oder Lehrer)
        if view_type2.value == "Klasse":
            col_name = "Klasse"
        elif view_type2.value == "Raum":
            col_name = "Raum"
        else:
            col_name = "L"

        for i in range(int(plan_daten.get("anzahlstuden", 10))):
            std_nummer = int(plan_daten.get("startstunde", 0)) + i
            cells = [ft.DataCell(ft.Text(f"{std_nummer}.", weight="bold"))]
            
            for tag in plan_daten.get("tage", ["Mo", "Di", "Mi", "Do", "Fr"]):
                # Filtern nach Auswahl
                m = df[(df['Tag'] == tag) & (df['Std'] == std_nummer) & (df[col_name] == selection_dd.value)]
                
                content_controls = []
                if not m.empty:
                    for _, row in m.iterrows():
                        # HIER: Prüfung auf 'notfall' Flag für die Farbe
                        farbe = ft.Colors.RED_600 if row.get("notfall") else ft.Colors.ON_SURFACE
                        
                        if col_name == "Klasse":
                            txt = f"{row['Fach']} ({row['L']}/{row['Raum']})"
                        elif col_name == "L":
                            txt = f"{row['Fach']} ({row['Klasse']}/{row['Raum']})"
                        else:
                            txt = f"{row['Fach']} ({row['Klasse']}/{row['L']})"
                            
                        content_controls.append(ft.Text(txt, size=11, color=farbe))
                    
                    cells.append(ft.DataCell(ft.Column(controls=content_controls, spacing=2)))
                else:
                    cells.append(ft.DataCell(ft.Text("")))
            
            wochen_tabelle.rows.append(ft.DataRow(cells=cells))
        
        page.update()

    def Logintest(ID, Password):
        
        global ID_PASSWORT, Rolle

        if not ID_PASSWORT:
            ID_PASSWORT = lade_und_entschluessele_plan("ID-Passwort")

        #db.collection("Schulen").document(str(schul_id)).get()
        Rolle = Rolle_dd.value
        all_ids =  lade_und_entschluessele_plan("Schul_IDs")
        hashed_passwort = multi_hash(Password)
        if ID in all_ids:

            if ID_PASSWORT[ID]["Schueler"] == hashed_passwort:
                    

                page.client_storage.set("Schul-ID", ID)
                page.client_storage.set("User-Passwort", Password)

                get_plan(ID)
                change_screen(0)

    def Logout():

        global Rolle
        Rolle = "Schueler"
        
        page.client_storage.set("Schul-ID", "")
        page.client_storage.set("User-Passwort", "")

        change_screen(-1)
        page.update()

    main_container = ft.Container(expand=True)
    def change_screen(index):
        global DATEN_ON, Rolle
        if not DATEN_ON:
            DATEN_ON = lade_und_entschluessele_plan(page.client_storage.get("Schul-ID"))
            #print(DATEN_ON["plan"])
        if index == -1:
            main_container.content = ft.Container(padding=20, content=ft.Column([
                ft.Text("Login", size=28, weight="bold"),
                ft.Column([Schul_ID_TF, Rolle_dd, Schul_Passwort_TF, ft.ElevatedButton("Login", icon=ft.Icons.REFRESH, on_click=lambda e: (Logintest(Schul_ID_TF.value, Schul_Passwort_TF.value)))])
            ]))
        elif index == 0:
            if Rolle == "Lehrer" and Rolle_dd.value == "Lehrer":
                
                selection_dd.options = (
                    [ft.dropdown.Option(k["name"]) for k in DATEN_ON.get("klassen")] if view_type2.value == "Klasse" else
                    [ft.dropdown.Option(r["nr"]) for r in DATEN_ON.get("raeume")] if view_type2.value == "Raum" else
                    [ft.dropdown.Option(l["kzl"]) for l in DATEN_ON.get("lehrer")]
                )
                main_container.content = ft.Container(padding=20, content=ft.Column([
                    ft.Text("Wochenstundenpläne", size=28, weight="bold"),
                    ft.Row([view_type2, selection_dd, ft.ElevatedButton("Anzeigen", icon=ft.Icons.REFRESH, on_click=lambda e: (get_plan(page.client_storage.get("Schul-ID"))))]), #, bgcolor=const.COLOR_THEME[COLOR_THEME_C][5]
                    ft.Divider(), ft.Column([wochen_tabelle], scroll=ft.ScrollMode.ALWAYS, expand=True)]))

            else:
                
                selection_dd.options = (
                    [ft.dropdown.Option(k["name"]) for k in DATEN_ON.get("klassen")]
                )
                main_container.content = ft.Container(padding=20, content=ft.Column([
                    ft.Text("Wochenstundenpläne", size=28, weight="bold"),
                    ft.Row([view_type1, selection_dd, ft.ElevatedButton("Anzeigen", icon=ft.Icons.REFRESH, on_click=lambda e: (get_plan(page.client_storage.get("Schul-ID")))), ft.ElevatedButton("Logout", icon=ft.Icons.LOGOUT_ROUNDED, on_click=lambda e: (Logout()))]), #, bgcolor=const.COLOR_THEME[COLOR_THEME_C][5]
                    ft.Divider(), ft.Column([wochen_tabelle], scroll=ft.ScrollMode.ALWAYS, expand=True)
            ]))
        page.update()
    view_type1.on_change = lambda _: change_screen(0)
    view_type2.on_change = lambda _: change_screen(0)
    id = page.client_storage.get("Schul-ID")
    pw = page.client_storage.get("User-Passwort")
    
    if id and pw:
        Logintest(page.client_storage.get("Schul-ID"), page.client_storage.get("User-Passwort"))
    else:
        change_screen(-1)

    page.add(main_container)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)