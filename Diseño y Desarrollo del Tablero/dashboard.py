import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ------------------------------
# Cargar archivos necesarios
# ------------------------------

# Ruta base
script_dir = os.path.dirname(os.path.abspath(__file__))
archivo_datos = os.path.join(script_dir, 'datos_apartamentos_rent_practicamod.csv')
archivo_coef = os.path.join(script_dir, 'coeficientes_modelo_final.csv')


# Cargar el DataFrame de coeficientes y crear el diccionario de coeficientes
df_coef = pd.read_csv(archivo_coef)
dic_coef = dict(zip(df_coef['Feature'], df_coef['Coefficient']))

# Cargar el DataFrame de datos
df_datos = pd.read_csv(archivo_datos, encoding='ISO-8859-1', on_bad_lines='skip', delimiter=';', engine='python')
df_datos.columns = df_datos.columns.str.strip()

# Establecer la intersección.
interseccion = 0

# -----------------------------------------------------------
# Identificar características continuas y categóricas
# -----------------------------------------------------------
# Variables continuas que se usan directamente:
caracteristicas_continuas = {"bathrooms", "bedrooms", "square_feet", "baños*area", "cuartos*area", "cuartos*baños"}

# Definir las opciones de mascotas.
# se mapean a df_datos.pets_allowed.
pet_options_set = {"Cats", "Cats,Dogs", "Dogs", "petsunknown"}
opciones_pets = [{"label": opt, "value": opt} for opt in ["Cats", "Dogs", "Cats,Dogs", "petsunknown"]]

# Servicios (amenities): se toman de dic_coef, eliminando las opciones de mascotas y "noamenities".
servicios = [
    car for car in dic_coef.keys() 
    if (not car.startswith("state_")) 
    and (car not in caracteristicas_continuas) 
    and (car != "noamenities") 
    and (car not in pet_options_set)
]
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
    html.H1(
        "Tablero de predicción de precios inmobiliarios",
        style={'textAlign': 'center', 'marginBottom': '30px'}
    ),
    
    # Contenedor para los menús con márgenes laterales
    html.Div([
        # Fila 1: Número de cuartos, baños y mascotas
        html.Div([
            html.Div([
                html.Label("Número de Cuartos"),
                dcc.Dropdown(
                    id="bedrooms-dropdown",
                    options=opciones_cuartos,
                    value=3,
                    clearable=False
                )
            ], style={'width': '20%', 'marginRight': '5%'}),
            
            html.Div([
                html.Label("Número de Baños"),
                dcc.Dropdown(
                    id="bathrooms-dropdown",
                    options=opciones_banios,
                    value=2,
                    clearable=False
                )
            ], style={'width': '20%', 'marginRight': '5%'}),
            html.Div([
                html.Label("Seleccione opción de mascotas"),
                dcc.Dropdown(
                    id="pet-dropdown",
                    options=opciones_pets,
                    value="petsunknown",
                    clearable=False
                )
            ], style={'width': '20%', 'marginBottom': '20px'})
        ], style={
            'display': 'flex', 
            'flexWrap': 'wrap',
            'justifyContent': 'start',
            'marginBottom': '20px'
        }),
        
        # Fila 2: Servicios (amenities) y Estados
        html.Div([
            html.Div([
                html.Label("Seleccione servicios (amenities)"),
                dcc.Dropdown(
                    id="amenities-dropdown",
                    options=opciones_servicios,
                    multi=True,
                    placeholder="Servicios..."
                )
            ], style={'width': '45%', 'marginRight': '5%'}),
            
            html.Div([
                html.Label("Seleccione Estados"),
                dcc.Dropdown(
                    id="states-dropdown",
                    options=opciones_estados,
                    multi=True,
                    placeholder="Seleccione Estados..."
                )
            ], style={'width': '45%'})
        ], style={
            'display': 'flex',
            'flexWrap': 'wrap',
            'justifyContent': 'start',
            'marginBottom': '20px'
        }),
        
        # Fila 4: Selección de unidad de área
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
        ], style={'marginBottom': '20px'}),
        
        # Fila 5: Slider para Área
        html.Div([
            html.Label("Seleccione Área"),
            dcc.RangeSlider(
                id="area-slider",
                min=500,
                max=5000,
                step=50,
                value=[1500, 2500],
                marks={i: str(i) for i in range(500, 5001, 500)}
            )
        ], style={'marginBottom': '20px'})
        
    ], style={'marginLeft': '50px', 'marginRight': '50px'}),
    
    html.Br(),
    
    # Mapa de EE.UU. (aumentado de tamaño)
    dcc.Graph(
        id="us-map", 
        style={'height': '600px', 'width': '100%'}
    ),
    
    html.Br(),
    
    # Sección para mostrar el Top 10 de propiedades
    html.H2(
        "Top 10 Propiedades", 
        style={'textAlign': 'center', 'marginBottom': '20px'}
    ),
    html.Div(
        id="top10-div", 
        style={'marginLeft': '50px', 'marginRight': '50px'}
    )
], style={'margin': '20px'})

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
    if not servicios_seleccionados:
        servicios_seleccionados = ["noamenities"]
    
    # rango minimo y maximo para el area
    lower_area = rango_area[0]
    upper_area = rango_area[1]
    
    # Calcular precio base min y max para el rango de área seleccionado
    precio_base_lower = interseccion
    precio_base_lower += cuartos * dic_coef.get("bedrooms", 0)
    precio_base_lower += banios * dic_coef.get("bathrooms", 0)
    precio_base_lower += lower_area * dic_coef.get("square_feet", 0)
    precio_base_lower += (banios * lower_area) * dic_coef.get("baños*area", 0)
    precio_base_lower += (cuartos * lower_area) * dic_coef.get("cuartos*area", 0)
    precio_base_lower += (cuartos * banios) * dic_coef.get("cuartos*baños", 0)
    
    precio_base_upper = interseccion
    precio_base_upper += cuartos * dic_coef.get("bedrooms", 0)
    precio_base_upper += banios * dic_coef.get("bathrooms", 0)
    precio_base_upper += upper_area * dic_coef.get("square_feet", 0)
    precio_base_upper += (banios * upper_area) * dic_coef.get("baños*area", 0)
    precio_base_upper += (cuartos * upper_area) * dic_coef.get("cuartos*area", 0)
    precio_base_upper += (cuartos * banios) * dic_coef.get("cuartos*baños", 0)
    
    # Agregar contribución de los servicios (amenities) seleccionados
    for servicio in servicios_seleccionados:
        precio_base_lower += dic_coef.get(servicio, 0)
        precio_base_upper += dic_coef.get(servicio, 0)
    
    if pet_option is None:
        pet_option = "petsunknown"
    precio_base_lower += dic_coef.get(pet_option, 0)
    precio_base_upper += dic_coef.get(pet_option, 0)
    
    if estados_seleccionados:
        lista_estados = estados_seleccionados
    else:
        lista_estados = codigos_estados
    
    datos_estados = []
    for estado in lista_estados:
        clave_estado = "state_" + estado
        coef_estado = dic_coef.get(clave_estado, 0)
        precio_pred_lower = precio_base_lower + coef_estado
        precio_pred_upper = precio_base_upper + coef_estado
        precio_pred_avg = (precio_pred_lower + precio_pred_upper) / 2.0
        datos_estados.append({
            "state": estado, 
            "predicted_price_lower": precio_pred_lower,
            "predicted_price_upper": precio_pred_upper,
            "predicted_price_avg": precio_pred_avg
        })
    
    df_estados = pd.DataFrame(datos_estados)
    
    # Verificar si df_estados está vacío
    if df_estados.empty:
        fig = go.Figure()
        fig.update_layout(
            title_text="No hay datos para mostrar en el mapa",
            title_x=0.5
        )
    else:
        overall_min = df_estados["predicted_price_lower"].min()
        overall_max = df_estados["predicted_price_upper"].max()
        
        fig = px.choropleth(
            df_estados,
            locations="state",
            locationmode="USA-states",
            color="predicted_price_avg",
            range_color=[overall_min, overall_max],
            color_continuous_scale="RdBu_r",
            scope="usa",
            labels={"predicted_price_avg": "Precio estimado"}
        )
        fig.update_traces(
            hovertemplate="<b>%{location}</b><br>" +
                          "Precio mínimo: %{customdata[0]}<br>" +
                          "Precio máximo: %{customdata[1]}<extra></extra>",
            customdata=df_estados[["predicted_price_lower", "predicted_price_upper"]].values
        )
        fig.update_layout(title_text="Predicción de precio inmobiliario por estado", title_x=0.5)
    
    # --- PARTE 2: FILTRADO Y TOP 10 ---
    datos_filtrados = df_datos.copy()
    datos_filtrados['pets_allowed'] = datos_filtrados['pets_allowed'].fillna('petsunknown')
    
    # Filtrar por número de cuartos, baños y área (square_feet)
    datos_filtrados = datos_filtrados[
        (datos_filtrados['bedrooms'] == int(cuartos)) &
        (datos_filtrados['bathrooms'] == int(banios)) &
        (datos_filtrados['square_feet'].between(rango_area[0], rango_area[1]))
    ]
    
    # Filtrar por estados (si se especifica)
    if estados_seleccionados:
        datos_filtrados = datos_filtrados[datos_filtrados['state'].isin(estados_seleccionados)]
    
    # Filtrar por la opción de mascotas (pet-dropdown)
    datos_filtrados = datos_filtrados[datos_filtrados['pets_allowed'] == pet_option]
    
    # Asegurarse de que la columna "amenities" sea de tipo string y rellenar los valores faltantes
    datos_filtrados['amenities'] = datos_filtrados['amenities'].fillna('noamenities').astype(str)
    
    # Filtrar por servicios (amenities) si se han seleccionado
    if servicios_seleccionados:
        datos_filtrados = datos_filtrados[datos_filtrados['amenities'].apply(
            lambda x: all(amenity.lower() in [a.strip().lower() for a in x.split(',')]
                          for amenity in servicios_seleccionados)
        )]
    
    columnas_seleccionadas = ['title', 'body', 'bedrooms', 'bathrooms', 'square_feet', 'state', 'pets_allowed', 'amenities', 'price']
    # Si no hay datos o la columna 'price' no está presente, se crea un DataFrame vacío con las columnas esperadas.
    if datos_filtrados.empty or 'price' not in datos_filtrados.columns:
        top10_df = pd.DataFrame(columns=columnas_seleccionadas)
    else:
        top10_df = datos_filtrados.sort_values('price').head(10)[columnas_seleccionadas]
    
    if not top10_df.empty:
        header_cells = [
            html.Th(col, style={'textAlign': 'center', 'padding': '8px', 'border': '1px solid black'}) 
            for col in top10_df.columns
        ]
        table_header = html.Thead(html.Tr(header_cells))
        
        body_rows = []
        for i in range(len(top10_df)):
            row = html.Tr([
                html.Td(top10_df.iloc[i][col], style={'textAlign': 'center', 'padding': '8px', 'border': '1px solid black'})
                for col in top10_df.columns
            ])
            body_rows.append(row)
        
        table_body = html.Tbody(body_rows)
        table = html.Table(
            [table_header, table_body],
            style={
                'width': '100%', 
                'border': '1px solid black', 
                'borderCollapse': 'collapse', 
                'margin': '0 auto'
            }
        )
    else:
        table = "No hay propiedades que cumplan con todos los criterios seleccionados."
    
    return fig, table

# -----------------------------------------------------------
# Ejecutar la aplicación Dash.
# -----------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
