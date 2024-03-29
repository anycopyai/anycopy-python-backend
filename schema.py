from pydantic import BaseModel


# Define request body model
class URLRequest(BaseModel):
    # need_to_write: str
    # how_often: str
    # company_name: str
    website: str
    # industry: str
    # business_size: str
    # service_name: str
    # description: str
    # audience: list
    # keywords: list