from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
import openai
import os
import json
from schema import URLRequest


# Initialize FastAPI app
app = FastAPI()

# Set up NLTK
nltk.download('punkt')

openai.api_type     = "azure"
openai.api_base     = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version  = "2023-09-15-preview"
openai.api_key      = os.getenv("AZURE_OPENAI_API_KEY")


# Function to scrape webpage content
def scrape_webpage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip()
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            meta_description = meta_description['content'].strip()
        else:
            meta_description = ""
        return title, meta_description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping webpage: {e}")

# Function to extract keywords using NLTK
def extract_keywords_nltk(text):
    tokens = word_tokenize(text)
    keywords = nltk.FreqDist(tokens)
    return keywords.most_common()

# Function to generate ad copy using OpenAI
def generate_ad_copy(prompt):
    try:
        response = openai.Completion.create(
        engine="anycopychatgpt35",
        prompt=prompt,
        temperature=0.7,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
        return response.choices[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating ad copy: {e}")

# Function to cache data locally
def cache_data(data, filename):
    try:
        with open(filename, 'w') as file:
            json.dump(data, file)
    except Exception as e:
        print(f"Error caching data: {e}")

# Function to load cached data
def load_cached_data(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading cached data: {e}")
        return None

# Main function
def generate_dynamic_ad_copy(title, meta_description, website):
    # Step 1: Check if cached data exists
    cache_filename = 'cached_data.json'
    if os.path.exists(cache_filename):
        cached_data = load_cached_data(cache_filename)
        if cached_data:
            title, meta_description, keywords = cached_data
    else:
        # Step 1: Scrape webpage content
        title, meta_description = scrape_webpage(website)

        # Step 2: Extract keywords
        if title and meta_description:
            keywords = extract_keywords_nltk(title + ' ' + meta_description)

            # Step 3: Cache scraped data and keywords
            cache_data((title, meta_description, keywords), cache_filename)
        else:
            raise HTTPException(status_code=500, detail="Error processing webpage content")

    # Step 4: Prepare prompt for OpenAI 
    prompt = f"""
                Create engaging ad copies suitable for Instagram, Facebook, Google Ads, Bing Ads, and Twitter based on the content of the provided webpage. Extract the following details from the webpage:

                Title: {title}.
                Meta Description: {meta_description}
                Website: {website}
                Craft persuasive ad copies tailored to each platform, ensuring they effectively capture the essence of the webpage and entice users to engage further.

                Format the output as follows:

                Instagram Ad Copy:

                Caption: [Title]
                Description: [Meta Description]
                Link: [Website]
                Facebook Ad Copy:

                Headline: [Title]
                Text: [Meta Description]
                Link: [Website]
                Google Ads Copy:

                Headline 1: [Title]
                Headline 2: [Meta Description]
                Description: [Meta Description]
                URL: [Website]
                Bing Ads Copy:

                Title: [Title]
                Description 1: [Meta Description]
                URL: [Website]
                Twitter Ad Copy:

                Tweet: [Title] [Meta Description] [Website]
                Experiment with different ad angles, calls-to-action, and platform-specific optimizations to maximize engagement. Ensure compliance with each platform's ad policies and character limits.
"""

    # Step 5: Generate ad copy using OpenAI
    ad_copy = generate_ad_copy(prompt)
    if ad_copy:
        return ad_copy
    else:
        raise HTTPException(status_code=500, detail="Error generating ad copy")

# Define POST endpoint
@app.post("/generate-ad-copy")
async def generate_ad_copy_from_url(request_data: URLRequest):
    # need_to_write = request_data.need_to_write
    # how_often = request_data.how_often
    # company_name = request_data.company_name
    website = request_data.website
    # industry = request_data.industry
    # business_size = request_data.business_size
    # service_name = request_data.service_name
    # description = request_data.description
    # audience = request_data.audience
    # keywords = request_data.keywords
    title, meta_description = scrape_webpage(website)

    ad_copy = generate_dynamic_ad_copy(title, meta_description, website )
    ad_copy = ad_copy.replace("\n", " ")
    return {"ad_copy": ad_copy}
