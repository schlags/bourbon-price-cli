import datetime
import os
from typing_extensions import Annotated
import typer
from rich.console import Console
import bourbon.lib as lib




app = typer.Typer()
console = Console()


@app.command()
def all_bourbon():
    all_data = lib.get_csv_data().sort_values(by=["Average"], ascending=False)
    lib.print_table(all_data, "All Bourbon")
    return all_data

@app.command()
def update():
    lib.update_csv_file()


@app.command()
def pricecheck(
    query: str = typer.Option(..., help="Search query", prompt="Search query"),
    asking_price: Annotated[float, typer.Option(..., prompt="Asking price")] = None,
):

    sorted_data = lib.query_data(query)


    # Format the Percentage Difference column
    sorted_data["Percentage Difference"] = (((asking_price - sorted_data["Average"]) / asking_price) * 100).apply(lambda x: f"{'[bold red]' if x > 0 else '[bold green]'}{abs(x):.2f}% {'above' if x > 0 else 'below'} average{'[/bold red]' if x > 0 else '[/bold green]'}")

    lib.print_table(sorted_data, "Price Check Results")

    return sorted_data

@app.command()
def search(
    query: str = typer.Option(..., help="Search query", prompt="Search query")
):
    sorted_data = lib.query_data(query)
    lib.print_table(sorted_data, "Search Results")
    return sorted_data

@app.command()
def budget(
    lowest_price: Annotated[float, typer.Option(..., prompt="Low price")] = None,
    highest_price: Annotated[float, typer.Option(..., prompt="High price")] = None,
    query: str = typer.Option("", help="Optional search query (hit enter to search all)", prompt="Optional search query")
):
    if query:
        data = lib.query_data(query)
    else:
        data = lib.get_csv_data()
    filtered_data = data[(data["Average"] >= lowest_price) & (data["Average"] <= highest_price)]
    sorted_data = filtered_data.sort_values(by=["Average"], ascending=False)
    lib.print_table(sorted_data, "Budget Results")
    return sorted_data

def cli():
    # Check if the CSV file was updated in the last 24 hours
    file_path = os.path.join(os.path.dirname(__file__), "data/bourbon.csv")
    if os.path.exists(file_path):
        file_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        if (datetime.datetime.now() - file_modified_time).days > 0:
            console.print("[yellow]Warning: CSV file is more than 24 hours old. Running [bold]bourbon update[/bold] to update to the latest data...[/yellow]")
            lib.update_csv_file()
    app()

if __name__ == "__main__":
    typer.run(cli)