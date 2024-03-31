from pydantic import BaseModel


# Define request body model
class URLRequest(BaseModel):

    website: str
