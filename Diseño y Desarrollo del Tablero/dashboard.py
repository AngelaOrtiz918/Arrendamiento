import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# ------------------------------
# Cargar archivos necesarios
# ------------------------------

# Ruta base
ruta_base = os.path.abspath(os.path.join(os.getcwd(), '..', 'Proyecto 1', 'Arrendamiento', 'Modelamiento'))
ruta_datos = os.path.join(ruta_base, 'datos_apartamentos_rent_practicamod.csv')
ruta_modelo = os.path.join(ruta_base, 'final_linear_regression_model_int.pkl')
archivo_coef = os.path.join(ruta_base, 'coeficientes_modelo_final.csv')

# Cargar el DataFrame de coeficientes y crear el diccionario de coeficientes
df_coef = pd.read_csv(archivo_coef)
dic_coef = dict(zip(df_coef['Feature'], df_coef['Coefficient']))

# Cargar el DataFrame de datos
df_datos = pd.read_csv(ruta_datos, encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';', engine='python')

# Establecer la intersección.
interseccion = 0

# -----------------------------------------------------------
# Identificar características continuas y categóricas
# -----------------------------------------------------------
# Variables continuas que se usan directamente:
#   "bathrooms", "bedrooms", "square_feet", "baños*area", "cuartos*area", "cuartos*baños"
caracteristicas_continuas = {"bathrooms", "bedrooms", "square_feet", "baños*area", "cuartos*area", "cuartos*baños"}

# Definir las opciones de mascotas.
# se mapean a df_datos.pets_allowed.
pet_options_set = {"Cats", "Cats,Dogs", "Dogs", "petsunknown"}
opciones_pets = [{"label": opt, "value": opt} for opt in ["Cats", "Dogs", "Cats,Dogs", "petsunknown"]]

# Servicios (amenities): se toman de dic_coef, eliminando las opciones de mascotas y "noamenities".
servicios = [car for car in dic_coef.keys() 
             if (not car.startswith("state_")) 
             and (car not in caracteristicas_continuas) 
             and (car != "noamenities") 
             and (car not in pet_options_set)]
opciones_servicios = [{"label": car, "value": car} for car in servicios]

# Estados: extraer el código (después del "state_")
caracteristicas_estados = [car for car in dic_coef.keys() if car.startswith("state_")]
codigos_estados = [car.split("_")[1] for car in caracteristicas_estados]
opciones_estados = [{"label": codigo, "value": codigo} for codigo in codigos_estados]

# Opciones para número de cuartos y baños
opciones_cuartos = [{"label": str(i), "value": i} for i in range(1, 11)]
opciones_banios = [{"label": str(i), "value": i} for i in range(1, 11)]

# -----------------------------------------------------------
# Construir el layout de la aplicación Dash.
# -----------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.H1("Tablero de predicción de precios inmobiliarios"),
    
    # Fila para seleccionar servicios (amenities) y estados
    html.Div([
        html.Div([
            html.Label("Seleccione servicios (amenities)"),
            dcc.Dropdown(
                id="amenities-dropdown",
                options=opciones_servicios,
                multi=True,
                placeholder="Servicios..."
            )
        ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '2%'}),
        html.Div([
            html.Label("Seleccione Estados"),
            dcc.Dropdown(
                id="states-dropdown",
                options=opciones_estados,
                multi=True,
                placeholder="Seleccione Estados... (Se muestran todos si no se selecciona ninguno)"
            )
        ], style={'width': '45%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ]),
    
    html.Br(),
    
    # Nueva fila para seleccionar opción de mascotas (única selección)
    html.Div([
        html.Label("Seleccione opción de mascotas"),
        dcc.Dropdown(
            id="pet-dropdown",
            options=opciones_pets,
            value="petsunknown",  # Valor por defecto
            clearable=False
        )
    ], style={'width': '45%', 'padding': '10px'}),
    
    html.Br(),
    
    # Fila para número de cuartos y baños
    html.Div([
        html.Div([
            html.Label("Número de Cuartos"),
            dcc.Dropdown(
                id="bedrooms-dropdown",
                options=opciones_cuartos,
                value=3
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
        html.Div([
            html.Label("Número de Baños"),
            dcc.Dropdown(
                id="bathrooms-dropdown",
                options=opciones_banios,
                value=2
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'})
    ]),
    
    html.Br(),
    
    # Selector de unidad para Área
    html.Div([
        html.Label("Seleccione unidad de área"),
        dcc.RadioItems(
            id="unit-radio",
            options=[
                {"label": "Pies cuadrados (ft²)", "value": "ft2"},
                {"label": "Metros cuadrados (m²)", "value": "m2"}
            ],
            value="ft2",
            labelStyle={'display': 'inline-block', 'margin-right': '10px'}
        )
    ], style={'width': '90%', 'padding': '20px'}),
    
    html.Br(),
    
    # Control deslizante para Área (valores internos en pies cuadrados)
    html.Div([
        html.Label("Seleccione Área"),
        dcc.RangeSlider(
            id="area-slider",
            min=500,
            max=5000,
            step=50,
            value=[1500, 2500],
            marks={i: str(i) for i in range(500, 5001, 500)}  # Se actualizará según la unidad seleccionada
        )
    ], style={'width': '90%', 'padding': '20px'}),
    
    html.Br(),
    
    # Mapa de EE.UU. para mostrar la predicción por estado
    dcc.Graph(id="us-map"),
    
    html.Br(),
    
    # Sección para mostrar el Top 10 de propiedades
    html.H2("Top 10 Propiedades"),
    html.Div(id="top10-div")
])

# -----------------------------------------------------------
# Callback para actualizar las marcas del slider según la unidad seleccionada.
# -----------------------------------------------------------
@app.callback(
    Output("area-slider", "marks"),
    Input("unit-radio", "value")
)
def actualizar_marcas(unidad):
    if unidad == "ft2":
        return {i: str(i) for i in range(500, 5001, 500)}
    elif unidad == "m2":
        # Conversión: 1 m² = 10.7639 ft²
        return {i: str(round(i / 10.7639, 1)) for i in range(500, 5001, 500)}
    else:
        return {i: str(i) for i in range(500, 5001, 500)}

# -----------------------------------------------------------
# Callback para actualizar el mapa y el Top 10 según las entradas del usuario.
# -----------------------------------------------------------
@app.callback(
    Output("us-map", "figure"),
    Output("top10-div", "children"),
    Input("amenities-dropdown", "value"),
    Input("states-dropdown", "value"),
    Input("pet-dropdown", "value"),
    Input("bedrooms-dropdown", "value"),
    Input("bathrooms-dropdown", "value"),
    Input("area-slider", "value"),
    Input("unit-radio", "value")
)
def actualizar_dashboard(servicios_seleccionados, estados_seleccionados, pet_option, cuartos, banios, rango_area, unidad):
    # --- PARTE 1: MAPA (PREDICCIÓN POR ESTADO) ---
    # Si no se selecciona ningún servicio (amenities), usar "noamenities" por defecto.
    if not servicios_seleccionados:
        servicios_seleccionados = ["noamenities"]
    
    # El valor del slider está en ft² (independientemente de la unidad de visualización)
    valor_area = sum(rango_area) / 2.0
    
    # Calcular el precio base usando entradas continuas
    precio_base = interseccion
    precio_base += cuartos * dic_coef.get("bedrooms", 0)
    precio_base += banios * dic_coef.get("bathrooms", 0)
    precio_base += valor_area * dic_coef.get("square_feet", 0)
    precio_base += (banios * valor_area) * dic_coef.get("baños*area", 0)
    precio_base += (cuartos * valor_area) * dic_coef.get("cuartos*area", 0)
    precio_base += (cuartos * banios) * dic_coef.get("cuartos*baños", 0)
    
    # Agregar contribución de los servicios (amenities) seleccionados
    for servicio in servicios_seleccionados:
        precio_base += dic_coef.get(servicio, 0)
    
    # Agregar la contribución del valor de mascotas seleccionado
    if pet_option is None:
        pet_option = "petsunknown"
    precio_base += dic_coef.get(pet_option, 0)
    
    # Determinar para qué estados se calcularán las predicciones.
    if estados_seleccionados:
        lista_estados = estados_seleccionados
    else:
        lista_estados = codigos_estados
    
    datos_estados = []
    for estado in lista_estados:
        clave_estado = "state_" + estado
        coef_estado = dic_coef.get(clave_estado, 0)
        precio_predicho = precio_base + coef_estado
        datos_estados.append({"state": estado, "predicted_price": precio_predicho})
    
    df_estados = pd.DataFrame(datos_estados)
    
    fig = px.choropleth(
        df_estados,
        locations="state",
        locationmode="USA-states",
        color="predicted_price",
        color_continuous_scale="RdBu_r",
        scope="usa",
        labels={"predicted_price": "Precio estimado"}
    )
    fig.update_layout(title_text="Predicción de precio inmobiliario por estado", title_x=0.5)
    
    # --- PARTE 2: FILTRADO Y TOP 10 OPCIONES ---
    datos_filtrados = df_datos.copy()
    # Rellenar valores faltantes en 'pets_allowed'
    datos_filtrados['pets_allowed'] = datos_filtrados['pets_allowed'].fillna('petsunknown')
    
    # Filtrar por número de cuartos, baños y área (square_feet)
    datos_filtrados = datos_filtrados[
        (datos_filtrados['bedrooms'] == int(cuartos)) &
        (datos_filtrados['bathrooms'] == int(banios)) &
        (datos_filtrados['square_feet'].between(rango_area[0], rango_area[1]))
    ]
    
    # Filtrar por estados (si se especifica)
    if estados_seleccionados:
        lista_estados_filtro = [s.strip() for s in estados_seleccionados]
        datos_filtrados = datos_filtrados[datos_filtrados['state'].isin(lista_estados_filtro)]
    
    # Filtrar por la opción de mascotas (pet-dropdown)
    if pet_option is None:
        pet_option = "petsunknown"
    datos_filtrados = datos_filtrados[datos_filtrados['pets_allowed'] == pet_option]
    
    # Filtrar por servicios (amenities) si se han seleccionado
    if servicios_seleccionados:
        datos_filtrados['amenities'] = datos_filtrados['amenities'].fillna('noamenities')
        datos_filtrados = datos_filtrados[datos_filtrados['amenities'].apply(
            lambda x: all(amenity.lower() in [a.strip().lower() for a in x.split(',')]
                          for amenity in servicios_seleccionados)
        )]
    
    # Seleccionar las 10 propiedades más baratas según 'price'
    top10_df = datos_filtrados.sort_values('price').head(10)[[
        'bedrooms', 'bathrooms', 'square_feet', 'state', 
        'pets_allowed', 'amenities', 'price'
    ]]
    
    # Crear tabla HTML para mostrar el Top 10
    if not top10_df.empty:
        table_header = html.Thead(html.Tr([html.Th(col) for col in top10_df.columns]))
        table_body = html.Tbody([
            html.Tr([html.Td(top10_df.iloc[i][col]) for col in top10_df.columns])
            for i in range(len(top10_df))
        ])
        table = html.Table([table_header, table_body],
                           style={'width': '100%', 'border': '1px solid black', 'borderCollapse': 'collapse'})
    else:
        table = "No hay propiedades que cumplan con todos los criterios."
    
    return fig, table

# -----------------------------------------------------------
# Ejecutar la aplicación Dash.
# -----------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
