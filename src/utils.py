import os
import typing
from pathlib import Path
import json
import requests
from . import parse
from rich import print


# Set directories we'll use all over
THIS_DIR = Path(__file__).parent.absolute()
ROOT_DIR = THIS_DIR.parent
PDF_DIR = ROOT_DIR / "pdfs"
BASE_MONGO_URL = "https://us-west-2.aws.data.mongodb-api.com/app/data-wpkwm/endpoint/data/v1"
MONGO_KEY = os.getenv("MONGO_KEY")
assert MONGO_KEY

def format_pdf_url(dt):
    """Format the provided datetime to fit the PDF URL expected on our source."""
    return f'https://dps.usc.edu/wp-content/uploads/{dt.strftime("%Y")}/{dt.strftime("%m")}/{dt.strftime("%m%d%y")}.pdf'


def download_url(url: str, output_path: Path, timeout: int = 180):
    """Download the provided URL to the provided path."""
    print(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=timeout) as r:
        if r.status_code == 404:
            print(f"404: {url}")
            return
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def upload_pdf(
    pdf_name: str, verbose: bool = False
) -> tuple[typing.Optional[str], bool]:
    """Upload the provided object's PDF to MongoDB.

    Returns tuple with document URL and boolean indicating if it was uploaded.
    """
    # Get PDF path
    pdf_path = PDF_DIR / pdf_name

    # Make sure it exists
    assert pdf_path.exists()

    # Parse the PDF to JSON
    json_data = parse.read_and_parse(pdf_path)
    data = json.loads(json_data)

    #Check if document exists in MongoDB
    #DISABLE CHECK FOR TESTING|
    exists = check_exists(data)
    #exists = False
    # If it is, we're done
    if exists:
        print(f"{pdf_name} already uploaded")
        return False

    # If it isn't, upload it now
    else:
        print(f"Uploading {pdf_path}")
    try:
        upload_json(data)
    except APIError as e:
        if verbose:
            print(f"API error {e}")
        return None, False
    
def upload_json(data):
    url = f"{BASE_MONGO_URL}/action/insertMany"
    headers = {
        "apiKey": MONGO_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "dataSource": "USC-AnnMedia-WebTeam",
        "database": "dps",
        "collection": "dps-json",
        "documents": data,
    }
    
    response = requests.request("POST", url, headers=headers, json=payload)
    print("UPLOAD STATUS CODE: ", response.status_code)
    print("UPLOAD RESPONSE: ", response.json())
    return response

def check_exists(data):
    url = f"{BASE_MONGO_URL}/action/findOne"
    headers = {
        "apiKey": MONGO_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "dataSource": "USC-AnnMedia-WebTeam",
        "database": "dps",
        "collection": "dps-json",
        "filter": {
            "Event#": data[0].get("Event#")
        },
        "projection": {
            "status": 1,
            "text": 1
        }
    }

    response = requests.request("POST", url, headers=headers, json=payload)
    print("CHECK STATUS CODE: ", response.status_code)
    #if response is 200 then return true else return false
    if response.status_code == 200:
        return True
    else:
        return False
    
