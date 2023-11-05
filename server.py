from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

from utils import APIHandler, get_access_token, filter_hu_field, merge_external_data, resolve_label_color

app = FastAPI()


@app.post("/process-vehicles/")
async def process_vehicles(data: dict,
                           access_token: str = Depends(get_access_token)):
    """Process vehicle data."""
    try:
        json_data = data.get('data')
        df = pd.read_json(json_data, orient='split')
        print("Data received successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing JSON data: {str(e)}")

    print(access_token)
    api_handler = APIHandler(access_token)

    merged_df = merge_external_data(api_handler, df_csv=df)
    print("External data merged.")
    merged_df = filter_hu_field(merged_df)
    print("Empty hu fields removed.")
    try:
        merged_df['resolved_colorCode'] = merged_df['labelIds'].apply(lambda labelId: resolve_label_color(labelId, api_handler))
    except Exception as e:
        print(f"An error occurred during label resolution: {str(e)}")
    merged_df_json = merged_df.to_json(orient='records')
    
    return JSONResponse(content=merged_df_json)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)