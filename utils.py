import requests
import pandas as pd


class APIHandler:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }

    def make_api_request(self, url):
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response
        else:
            print(f"Request failed with status code {response.status_code}")
            return None
        

def get_access_token() -> str:
    """Get the access token."""

    url = "https://api.baubuddy.de/index.php/login"

    auth_headers = {
    "Authorization": "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
    "Content-Type": "application/json"
    }
    payload = {
        "username": "365",
        "password": "1",
    }
    response = requests.post(url, json=payload, headers=auth_headers)
    access_token = response.json()["oauth"]["access_token"]
    return access_token


def filter_hu_field(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with None values in the 'hu' field."""
    return df[pd.notna(df['hu'])]


def _merge_columns(row, colname: str):
    """Merge columns based on specific criteria."""
    col1 = f"{colname}_df1"
    col2 = f"{colname}_df2"

    #if they are the same choose one
    if row[col1] == row[col2]:
        return row[col1]
    #if one of them is null and the other is not null, chose the one which is not null
    elif not pd.isna(row[col1]) and pd.isna(row[col2]):
        return row[col1]
    elif pd.isna(row[col1]) and not pd.isna(row[col2]):
        return row[col2]
    #if both of them are null, return None
    elif pd.isna(row[col1]) and pd.isna(row[col2]):
        return None
    else:
        #if they are not the same check for similarity and choose the longer one to preserve data
        if row[col1] != row[col2]:

            try:
                #if they are the same integers choose one
                row[col1] = int(row[col1])
                row[col2] = int(row[col2])

                if row[col1] == row[col2]:
                    return row[col1]
            except:
                pass

            row[col1] = str(row[col1])
            row[col2] = str(row[col2])

            similarity_threshold = 0.5
            similarity = jaccard_similarity(row[col1], row[col2])

            if similarity >= similarity_threshold:
                longer = row[col1] if len(row[col1]) >= len(row[col2]) else row[col2]
                return longer
            #if they contain different info, combine them
            else:
                return f"{row[col1]}/{row[col2]}"


def jaccard_similarity(str1: str, str2: str) -> float:
    """Calculate Jaccard similarity between two strings."""
    words1 = set(str1.split())
    words2 = set(str2.split())

    intersection = len(words1.intersection(words2))
    union = len(words1) + len(words2) - intersection
    similarity = intersection / union

    return similarity


def merge_external_data(api_handler: APIHandler, df_csv: pd.DataFrame) -> pd.DataFrame:
    """Merge external data with csv data."""
    
    url = "https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active"
    response = api_handler.make_api_request(url=url)
    api_data = pd.DataFrame(response.json())

    merged_df = api_data.merge(df_csv, on='kurzname', how='outer', suffixes=('_df1', '_df2'))
    common_columns = [col.removesuffix('_df2') for col in merged_df.columns if col.endswith('_df2')]
    suffix_cols1 = [col for col in merged_df.columns if col.endswith('_df1')]
    suffix_cols2 = [col for col in merged_df.columns if col.endswith('_df2')]

    for col in common_columns:
        merged_df[f'{col}'] = merged_df.apply(lambda row: _merge_columns(row, col), axis=1)

    merged_df.drop(suffix_cols1, axis=1, inplace=True)
    merged_df.drop(suffix_cols2, axis=1, inplace=True)

    return merged_df


def resolve_label_color(labelId: int, api_handler: APIHandler) -> str:
    """Resolve label color using labelId."""
    base_url = "https://api.baubuddy.de/dev/index.php/v1/labels/"

    if labelId is None:
        return None
    
    try:
        response = api_handler.make_api_request(url=f"{base_url}{labelId}")
        colorCode = response.json()[0].get("colorCode")
        return colorCode
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None