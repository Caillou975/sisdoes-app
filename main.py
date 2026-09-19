import flet as ft
import psycopg2

# Tu enlace de conexión de Neon
DATABASE_URL = "postgresql://neondb_owner:npg_kj4wpIEBqd6e@ep-snowy-tooth-b41rgczx-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

# ==========================================
# 1. BASE DE DATOS Y LÓGICA DE CÁLCULO
# ==========================================
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operadores (
            nsa TEXT PRIMARY KEY, grado TEXT, especialidad TEXT, nombre TEXT,
            natacion TEXT, nota_nat REAL, planchas INTEGER, nota_pla REAL,
            abdominales INTEGER, nota_abd REAL, carrera TEXT, nota_car REAL,
            barras INTEGER, nota_bar REAL, total_puntos REAL, promedio REAL, evaluacion TEXT
        )
    ''')
    conn.commit()
    return conn

def calcular_nota_tiempo(minutos, segundos, tipo):
    m = int(minutos) if minutos else 0
    s = int(segundos) if segundos else 0
    total_segundos = (m * 60) + s
    if total_segundos == 0: return 0.0

    if tipo == 'natacion':
        if total_segundos <= 580: return 25.0
        P = 24.5
        while P >= 0:
            k = (25.0 - P) / 0.5
            max_s = 580 + (8 * k)
            if total_segundos <= max_s: return P
            P -= 0.5
        return 0.0
    elif tipo == 'carrera':
        if total_segundos <= 675: return 25.0
        P = 24.5
        while P >= 0:
            k = (25.0 - P) / 0.5
            max_s = 675 + (15 * k)
            if total_segundos <= max_s: return P
            P -= 0.5
        return 0.0
    return 0.0

def calcular_nota_reps(cantidad, tipo):
    reps = int(cantidad) if cantidad else 0
    if tipo in ['planchas', 'abdominales']:
        if reps >= 99: return 25.0
        P = 24.5
        while P >= 0:
            k = (25.0 - P) / 0.5
            min_reps = 99 - (2 * k)
            if reps >= min_reps: return P
            P -= 0.5
        return 0.0
    elif tipo == 'barras':
        if reps >= 30: return 25.0
        P = (reps * 0.5) + 10
        return P if P >= 10 else 10.0
    return 0.0

def obtener_evaluacion(puntos):
    if puntos >= 90: return "SOBRESALIENTE", ft.Colors.GREEN_400
    if puntos >= 80: return "MUY BUENO", ft.Colors.BLUE_400
    if puntos >= 70: return "BUENO", ft.Colors.YELLOW_600
    if puntos >= 60: return "REGULAR", ft.Colors.ORANGE_400
    return "DEFICIENTE", ft.Colors.RED_400

# ==========================================
# 2. INTERFAZ GRÁFICA (FLET)
# ==========================================
def main(page: ft.Page):
    page.title = "SISDOES - FAP"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1a1c1a" # Fondo oscuro táctico (verde/gris muy oscuro)
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # --- SISTEMA DE LOGIN ---
    user_input = ft.TextField(label="Usuario", width=300, prefix_icon=ft.icons.PERSON)
    pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=300, prefix_icon=ft.icons.LOCK)
    
    def intentar_login(e):
        if user_input.value == "admin" and pass_input.value == "does2026":
            iniciar_app_principal()
        else:
            snack = ft.SnackBar(ft.Text("Credenciales de acceso incorrectas", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_900)
            page.overlay.append(snack)
            snack.open = True
            page.update()

    btn_login = ft.ElevatedButton("INGRESAR AL SISTEMA", on_click=intentar_login, width=300, style=ft.ButtonStyle(bgcolor="#2e4225", color=ft.Colors.WHITE)) # Verde oliva oscuro

    def mostrar_login():
        page.controls.clear()
        vista_login = ft.Container(
            content=ft.Column(
                [
                    ft.Image(src="logo_does.jpg", width=180, height=180, fit=ft.ImageFit.CONTAIN),
                    ft.Text("SISDOES", size=32, weight=ft.FontWeight.BOLD, color="#bfa15f"), # Dorado apagado
                    ft.Text("GRUPO DE FUERZAS ESPECIALES FAP", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    user_input,
                    pass_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    btn_login
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        page.add(vista_login)
        page.update()

    # --- APLICACIÓN PRINCIPAL ---
    def iniciar_app_principal():
        page.controls.clear()
        conn = init_db()

        nsa_input = ft.TextField(label="NSA", max_length=6, width=150)
        grado_input = ft.Dropdown(label="Grado", options=[ft.dropdown.Option("AL1"), ft.dropdown.Option("AL2"), ft.dropdown.Option("AL3"), ft.dropdown.Option("OM")], width=150)
        esp_input = ft.TextField(label="Especialidad", width=200)
        nombre_input = ft.TextField(label="Apellidos y Nombres", expand=True)

        nat_m = ft.TextField(label="Natación (Min)", width=120)
        nat_s = ft.TextField(label="Nat (Seg)", width=100)
        pla_input = ft.TextField(label="Planchas", width=120)
        abd_input = ft.TextField(label="Abdominales", width=120)
        car_m = ft.TextField(label="Carrera (Min)", width=120)
        car_s = ft.TextField(label="Car (Seg)", width=100)
        barras_input = ft.TextField(label="Barras", width=120)

        tabla_datos = ft.DataTable(
            heading_row_color="#2e4225", # Cabecera de tabla verde oliva
            columns=[
                ft.DataColumn(ft.Text("NSA", color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Grado", color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Nombre", color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Puntos", color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Evaluación", color=ft.Colors.WHITE)),
            ],
            rows=[]
        )

        def cargar_tabla():
            tabla_datos.rows.clear()
            cursor = conn.cursor()
            cursor.execute("SELECT nsa, grado, nombre, total_puntos, evaluacion FROM operadores ORDER BY total_puntos DESC")
            for row in cursor.fetchall():
                texto_eval, color_eval = obtener_evaluacion(row[3])
                tabla_datos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(row[0], weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(row[1])),
                        ft.DataCell(ft.Text(row[2])),
                        ft.DataCell(ft.Text(f"{row[3]:.1f}")),
                        ft.DataCell(ft.Text(row[4], color=color_eval, weight=ft.FontWeight.BOLD)),
                    ])
                )
            page.update()

        def guardar_registro(e):
            try:
                nota_nat = calcular_nota_tiempo(nat_m.value, nat_s.value, 'natacion')
                nota_pla = calcular_nota_reps(pla_input.value, 'planchas')
                nota_abd = calcular_nota_reps(abd_input.value, 'abdominales')
                nota_car = calcular_nota_tiempo(car_m.value, car_s.value, 'carrera')
                nota_bar = calcular_nota_reps(barras_input.value, 'barras')

                total_puntos = nota_nat + nota_pla + nota_abd + nota_car + nota_bar
                promedio = total_puntos / 5
                eval_texto, _ = obtener_evaluacion(total_puntos)
                
                marca_nat = f"{(nat_m.value or '0').zfill(2)}:{(nat_s.value or '0').zfill(2)}"
                marca_car = f"{(car_m.value or '0').zfill(2)}:{(car_s.value or '0').zfill(2)}"
                nombre_upper = (nombre_input.value or "").upper()
                planchas_val = int(pla_input.value or 0)
                abd_val = int(abd_input.value or 0)
                barras_val = int(barras_input.value or 0)

                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO operadores 
                    (nsa, grado, especialidad, nombre, natacion, nota_nat, planchas, nota_pla, abdominales, nota_abd, carrera, nota_car, barras, nota_bar, total_puntos, promedio, evaluacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (nsa) DO UPDATE SET
                    grado = EXCLUDED.grado, especialidad = EXCLUDED.especialidad, nombre = EXCLUDED.nombre,
                    natacion = EXCLUDED.natacion, nota_nat = EXCLUDED.nota_nat, planchas = EXCLUDED.planchas,
                    nota_pla = EXCLUDED.nota_pla, abdominales = EXCLUDED.abdominales, nota_abd = EXCLUDED.nota_abd,
                    carrera = EXCLUDED.carrera, nota_car = EXCLUDED.nota_car, barras = EXCLUDED.barras,
                    nota_bar = EXCLUDED.nota_bar, total_puntos = EXCLUDED.total_puntos, promedio = EXCLUDED.promedio,
                    evaluacion = EXCLUDED.evaluacion
                ''', (nsa_input.value, grado_input.value, esp_input.value, nombre_upper, marca_nat, nota_nat, planchas_val, nota_pla, abd_val, nota_abd, marca_car, nota_car, barras_val, nota_bar, total_puntos, promedio, eval_texto))
                conn.commit()
                
                snack_exito = ft.SnackBar(ft.Text("Operador registrado con éxito"), bgcolor="#2e4225")
                page.overlay.append(snack_exito)
                snack_exito.open = True
                cargar_tabla()
            
            except Exception as ex:
                snack_error = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED_900)
                page.overlay.append(snack_error)
                snack_error.open = True
                page.update()

        def cerrar_sesion(e):
            mostrar_login()

        # Cabecera Institucional
        cabecera = ft.Row([
            ft.Image(src="logo_does.jpg", width=80, height=80),
            ft.Column([
                ft.Text("SISDOES - FAP", size=24, weight=ft.FontWeight.BOLD, color="#bfa15f"),
                ft.Text("EVALUACIÓN FÍSICA - FUERZAS ESPECIALES", size=14, color=ft.Colors.GREY_400)
            ], expand=True),
            ft.IconButton(icon=ft.icons.LOGOUT, tooltip="Cerrar Sesión", on_click=cerrar_sesion, icon_color=ft.Colors.RED_400)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        page.add(
            cabecera,
            ft.Divider(color=ft.Colors.GREY_800),
            
            ft.Text("1. DATOS DEL OPERADOR", size=16, weight=ft.FontWeight.BOLD, color="#bfa15f"),
            ft.Row([nsa_input, grado_input, esp_input]),
            ft.Row([nombre_input]),
            
            ft.Text("2. MARCAS FÍSICAS", size=16, weight=ft.FontWeight.BOLD, color="#bfa15f"),
            ft.Row([nat_m, nat_s, pla_input, abd_input]),
            ft.Row([car_m, car_s, barras_input]),
            
            ft.Button("CALCULAR Y GUARDAR", on_click=guardar_registro, style=ft.ButtonStyle(bgcolor="#2e4225", color=ft.Colors.WHITE), width=400),
            ft.Divider(color=ft.Colors.GREY_800),
            
            ft.Text("REGISTRO DE OPERADORES", size=16, weight=ft.FontWeight.BOLD, color="#bfa15f"),
            tabla_datos
        )
        cargar_tabla()

    # Iniciar aplicación mostrando el login primero
    mostrar_login()

# Se añade assets_dir para que Flet sepa dónde buscar la imagen al probar localmente
ft.app(target=main, assets_dir="assets")