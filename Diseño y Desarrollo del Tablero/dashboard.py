import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# ------------------------------
# Cargar el archivo CSV de coeficientes
# ------------------------------

# Ruta base
ruta_base = os.path.abspath(os.path.join(os.getcwd(), '..', 'Proyecto 1', 'Arrendamiento', 'Modelamiento'))
ruta_datos = os.path.join(ruta_base, 'datos_filtrados.csv')
ruta_modelo = os.path.join(ruta_base, 'final_linear_regression_model_int.pkl')
archivo_coef = os.path.join(ruta_base, 'coeficientes_modelo_final.csv')
print(archivo_coef)

# Cargar el DataFrame de coeficientes
df_coef = pd.read_csv(archivo_coef)

# Crear un diccionario que asocia nombres de características a coeficientes
dic_coef = dict(zip(df_coef['Feature'], df_coef['Coefficient']))

# Establecer la intersección.
interseccion = 0

# -----------------------------------------------------------
# Identificar las características continuas y categóricas del modelo.
# -----------------------------------------------------------
# Variables continuas que se usan directamente:
#   - "bathrooms", "bedrooms", "square_feet", "baños*area", "cuartos*area", "cuartos*baños"
caracteristicas_continuas = {"bathrooms", "bedrooms", "square_feet", "baños*area", "cuartos*area", "cuartos*baños"}

# Para las características categóricas, se asumen dos grupos:
# 1. Servicios (características categóricas que no corresponden a estados)
# Se elimina "noamenities" de las opciones, ya que se utilizará como valor por defecto.
servicios = [car for car in dic_coef.keys() 
             if (not car.startswith("state_")) and (car not in caracteristicas_continuas) and (car != "noamenities")]
opciones_servicios = [{"label": car, "value": car} for car in servicios]

# 2. Estados (características que comienzan con "state_"). Se extrae el código del estado.
caracteristicas_estados = [car for car in dic_coef.keys() if car.startswith("state_")]
codigos_estados = [car.split("_")[1] for car in caracteristicas_estados]
opciones_estados = [{"label": codigo, "value": codigo} for codigo in codigos_estados]

# -----------------------------------------------------------
# Definir opciones para los desplegables de entradas continuas.
# -----------------------------------------------------------
opciones_cuartos = [{"label": str(i), "value": i} for i in range(1, 11)]  # De 1 a 10 cuartos
opciones_banios = [{"label": str(i), "value": i} for i in range(1, 11)]   # De 1 a 10 baños

# -----------------------------------------------------------
# Construir el layout de la aplicación Dash.
# -----------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.H1("Tablero de predicción de precios inmobiliarios"),
    
    # Fila para características categóricas: servicios y estados
    html.Div([
        html.Div([
            html.Label("Seleccione servicios"),
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
    
    # Fila para entradas continuas: número de cuartos y baños
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
    
    # Gráfico: Mapa de EE.UU. para mostrar precios predichos por estado.
    dcc.Graph(id="us-map")
])

# -----------------------------------------------------------
# Callback para actualizar las marcas (marks) del control deslizante de área según la unidad.
# -----------------------------------------------------------
@app.callback(
    Output("area-slider", "marks"),
    Input("unit-radio", "value")
)
def actualizar_marcas(unidad):
    # Los valores internos siempre están en pies cuadrados.
    # Si se selecciona m², se convierten los valores para mostrar en la interfaz.
    if unidad == "ft2":
        return {i: str(i) for i in range(500, 5001, 500)}
    elif unidad == "m2":
        # Conversión: 1 m² = 10.7639 ft²
        return {i: str(round(i / 10.7639, 1)) for i in range(500, 5001, 500)}
    else:
        return {i: str(i) for i in range(500, 5001, 500)}

# -----------------------------------------------------------
# Callback para actualizar el mapa según las entradas del usuario.
# -----------------------------------------------------------
@app.callback(
    Output("us-map", "figure"),
    Input("amenities-dropdown", "value"),
    Input("states-dropdown", "value"),
    Input("bedrooms-dropdown", "value"),
    Input("bathrooms-dropdown", "value"),
    Input("area-slider", "value")
)
def actualizar_mapa(servicios_seleccionados, estados_seleccionados, cuartos, banios, rango_area):
    # Si no se selecciona ningún servicio, usar "noamenities" por defecto.
    if not servicios_seleccionados:
        servicios_seleccionados = ["noamenities"]

    # Usar el punto medio del rango de área seleccionado para la predicción.
    # Nota: El valor del slider está en pies cuadrados.
    valor_area = sum(rango_area) / 2.0

    # Calcular la predicción base utilizando las entradas continuas.
    precio_base = interseccion
    precio_base += cuartos * dic_coef.get("bedrooms", 0)
    precio_base += banios * dic_coef.get("bathrooms", 0)
    precio_base += valor_area * dic_coef.get("square_feet", 0)
    precio_base += (banios * valor_area) * dic_coef.get("baños*area", 0)
    precio_base += (cuartos * valor_area) * dic_coef.get("cuartos*area", 0)
    precio_base += (cuartos * banios) * dic_coef.get("cuartos*baños", 0)
    
    # Agregar las contribuciones de los servicios seleccionados.
    for servicio in servicios_seleccionados:
        precio_base += dic_coef.get(servicio, 0)
    
    # Determinar para qué estados se calcularán las predicciones.
    # Si no se selecciona ningún estado, se utilizan todos los estados disponibles.
    if estados_seleccionados:
        lista_estados = estados_seleccionados
    else:
        lista_estados = codigos_estados
    
    # Calcular el precio predicho por estado sumando el coeficiente específico del estado.
    datos_estados = []
    for estado in lista_estados:
        clave_estado = "state_" + estado
        coef_estado = dic_coef.get(clave_estado, 0)
        precio_predicho = precio_base + coef_estado
        datos_estados.append({"state": estado, "predicted_price": precio_predicho})
    
    df_estados = pd.DataFrame(datos_estados)
    
    # Crear un mapa coroplético.
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
    return fig

# -----------------------------------------------------------
# Ejecutar la aplicación Dash.
# -----------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
