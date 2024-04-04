import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import base64
import io
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
# Add this import statement at the beginning of your Python script
import urllib.parse


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Button('Process Data', id='process-data', n_clicks=0),
    html.Div(id='output-data-upload'),
    dcc.Download(id='download-dataframe-csv')
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        return html.Div([
            'There was an error processing this file: ' + str(e)
        ])
    return df

def hex_to_binary(hex_val):
    return bin(int(hex_val, 16))[2:].zfill(16)

def hex_to_decimal(hex_val):
    return str(int(hex_val, 16))

def calculate_timestamp_difference(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Timestamp Difference'] = df['Timestamp'].diff().fillna(pd.Timedelta(seconds=0)).dt.total_seconds()
    return df

@app.callback(
    Output('output-data-upload', 'children'),
    [Input('upload-data', 'contents'),
     Input('process-data', 'n_clicks')],
    [State('upload-data', 'filename')]
)
def update_output(contents, process_clicks, filename):
    ctx = dash.callback_context
    if not contents:
        raise PreventUpdate

    df = parse_contents(contents, filename)
    if df is None:
        return html.Div("There was an error processing the file.")

    # Get the ID of the button that triggered the callback
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'process-data' and process_clicks > 0:
        df['Binary'] = df['Hex'].apply(hex_to_binary)
        df['Decimal'] = df['Hex'].apply(hex_to_decimal)
        df = calculate_timestamp_difference(df)

    data_table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in df.columns],
        export_format="csv",
        style_table={'overflowX': 'scroll'},
        style_cell={
            'height': 'auto',
            'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
            'whiteSpace': 'normal'
        }
    )

    # Update download-dataframe-csv data and trigger download
    if trigger_id == 'process-data':
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        download_button = html.A(
            "Download CSV",
            id='download-link',
            download="processed_data.csv",
            href=csv_string,
            target="_blank"
        )
        return html.Div([data_table, download_button])

    return html.Div([data_table])

if __name__ == '__main__':
    app.run_server(debug=True)
