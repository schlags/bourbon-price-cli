from typing import Optional
import datetime
import json
import requests
import os
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()

# Start URL builder vars
CSV_BASE_URL = "https://wix-visual-data.appspot.com/api/file"
COMP_ID = "comp-l5cg5rmf"
IS_SITE = False
# End URL builder vars

interchangeable_values = {
    "single barrel": ["single barrel", "sib"],
    "sib": ["single barrel", "sib"],
    "small batch": ["small batch", "smb"],
    "smb": ["small batch", "smb"],
    "barrel proof": ["barrel proof", "bp"],
    "bp": ["barrel proof", "bp"],
    "bottled in bond": ["bottled in bond", "bib"],
    "bib": ["bottled in bond", "bib"],
    "full proof": ["full proof", "fp"],
    "fp": ["full proof", "fp"],
    "store pick": ["store pick", "sp"],
    "sp": ["store pick", "sp"],
}


def update_csv_file():
    file_path = os.path.join(os.path.dirname(__file__), "data/bourbon.csv")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(get_external_data())
    console.print("[green][bold]Bourbon bottles and prices updated successfully to the latest data as of {}[/bold][/green]".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def get_csv_data():
    file_path = os.path.join(os.path.dirname(__file__), "data/bourbon.csv")
    if not os.path.exists(file_path):
        console.print("CSV file not found. Downloading latest data...")
        update_csv_file()
    return pd.read_csv(file_path)

def query_data(search_query):
    # Parse the CSV data
    data = get_csv_data()

    

    # Build a preprocessed query string that checks for all interchangeable values
    query_items = []
    
    # Build a single list of all items in the interchangeable_values dict
    interchangeable_values_list = []
    for value in interchangeable_values.values():
        interchangeable_values_list += value
    
    # Remove the interchangeable values from the search query and populate them in the query_items list since they can have spaces
    for value in interchangeable_values_list:
        if value in search_query:
            search_query = search_query.replace(value, "")
            query_items.append(value)

    for word in search_query.split():
        query_items.append(word)

    preprocessed_query = ""
    for query_item in query_items:
        preprocessed_query += " & " if preprocessed_query else ""
        if query_item in interchangeable_values_list:
            interchangeable_query = " | ".join(f"Bottle.str.contains('{value}', case=False)" for value in interchangeable_values.get(query_item, [query_item]))
            preprocessed_query += f"({interchangeable_query})"
        else:
            preprocessed_query += f"Bottle.str.contains('{query_item}', case=False)"

    filtered_data = data[data.eval(preprocessed_query)]

    # Sort the data
    return(filtered_data.sort_values(by=["Average"], ascending=False))

def print_table(row_data, title):
    bg = Style(bgcolor="rgb(40,40,40)")
    table = Table(title=title, row_styles=['', bg])
    if len(row_data) == 0:
        console.print(f"[bold][yellow]No bottles found.[/bold] Try `bourbon update`?")
        return
    console.print(df_to_table(row_data, table, show_index=False))

def get_header_and_jwt():
    file_path = os.path.join(os.path.dirname(__file__), "data/auth.json")
    if not os.path.exists(file_path):
        console.print("[red][bold]Error: auth.json file not found. Please create an auth.json file in the data folder and add your JWT details.[/bold][/red]")
        raise SystemExit()
    with open(file_path, "r") as f:
        auth_data = json.load(f)
    return auth_data["JWT_HEADER"], auth_data["JWT_PAYLOAD"]

def get_external_data():
    HEADER, PAYLOAD = get_header_and_jwt()
    url = f"{CSV_BASE_URL}?instance={HEADER}.{PAYLOAD}&compId={COMP_ID}&isSite={IS_SITE}"

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Getting latest prices...", total=None)
            response = requests.get(url)
    except Exception as e:
        raise SystemExit(e)
    if response.status_code == 401:
        console.print("[red][bold]Error: JWT is expired or invalid. Please update the JWT in the script.")
        raise SystemExit(f"Status code 401: {response.text}")
    elif response.status_code != 200:
        raise SystemExit(f"Status code {response.status_code} {response.text}")

    response_text = response.json()

    return response_text["csvData"]

def df_to_table(
    pandas_dataframe: pd.DataFrame,
    rich_table: Table,
    show_index: bool = True,
    index_name: Optional[str] = None,
) -> Table:
    """Convert a pandas.DataFrame obj into a rich.Table obj.
    Args:
        pandas_dataframe (DataFrame): A Pandas DataFrame to be converted to a rich Table.
        rich_table (Table): A rich Table that should be populated by the DataFrame values.
        show_index (bool): Add a column with a row count to the table. Defaults to True.
        index_name (str, optional): The column name to give to the index column. Defaults to None, showing no value.
    Returns:
        Table: The rich Table instance passed, populated with the DataFrame values."""

    if show_index:
        index_name = str(index_name) if index_name else ""
        rich_table.add_column(index_name)

    for column in pandas_dataframe.columns:
        rich_table.add_column(str(column))

    for index, value_list in enumerate(pandas_dataframe.values.tolist()):
        row = [str(index)] if show_index else []
        row += [f"{str(x)}" for x in value_list]
        rich_table.add_row(*row)

    return rich_table
