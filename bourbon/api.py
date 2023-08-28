
import bourbon.cli as bourbon
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

def convert_dt_to_json(dt):
    # Get unique row indices
    row_indices = set()
    for column_values in dt.columns:
        row_indices.update(column_values.keys())

    # Reformat data into a list of dictionaries
    reformatted_data = []
    for row_index in row_indices:
        row_data = {}
        for column_name, column_values in dt.items():
            row_data[column_name] = column_values.get(row_index, None)
        reformatted_data.append(row_data)
    
    return reformatted_data

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/search")
async def search(search_query: str):
    return bourbon.search(search_query).to_dict(orient="records")

@app.get("/pricecheck")
async def pricecheck(search_query: str, asking_price: float):
    return bourbon.pricecheck(search_query, asking_price).to_dict(orient="records")

@app.get("/budget")
async def budget(lower_bound: float, upper_bound: float, search_query: str = None):
    return bourbon.budget(lower_bound, upper_bound, search_query).to_dict(orient="records")
