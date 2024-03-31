from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
import openai
import os
import json
from schema import URLRequest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


# Initialize FastAPI app
app = FastAPI()

# Set up NLTK
nltk.download('punkt')

openai.api_type     = "azure"
openai.api_base     = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version  = "2023-09-15-preview"
openai.api_key      = os.getenv("AZURE_OPENAI_API_KEY")



def scrape_webpage(url):
    try:
        # Send GET request with a custom User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title = soup.title.string.strip()

        # Extract meta description
        meta_description = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_description = meta_tag['content'].strip()

        return title, meta_description

    except requests.HTTPError as e:
        # Handle HTTP errors
        if e.response.status_code == 403:
            # Website is blocking access, handle accordingly
            print("Access to the website is forbidden.")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP Error: {e}")

    except Exception as e:
        # Handle other exceptions
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
        if os.path.exists(filename):
            # Read existing JSON data from the file, if any
            with open(filename, 'r') as file:
                existing_data = file.read().strip()
            
            # Check if data already exists in the file
            if existing_data:
                # Remove the closing square bracket ']' from the end
                existing_data = existing_data[:-1]
                # Add a comma if necessary
                if existing_data.endswith(','):
                    existing_data += '\n'
                else:
                    existing_data += ',\n'
            
            # Write the updated JSON data to the file
            with open(filename, 'w') as file:
                # If data already exists, write it back along with a comma
                if existing_data:
                    file.write(existing_data)
                # Add the new data
                json.dump(data, file)
                # Add a closing square bracket to complete the JSON array
                file.write(']')
        else:
            with open(filename, 'w') as file:
                file.write('[')
                json.dump(data,file)
                file.write(']')
                file.close()

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
    website = website.lower()
    cache_filename = 'cached_data.json'
    if os.path.exists(cache_filename):
        cached_data = load_cached_data(cache_filename)
        # print(cached_data)
        if cached_data:
            for data in cached_data:
                # print(data)
                if data['website'] == website:
                    # If found, load data into variables
                    website = data['website']
                    title = data['title']
                    meta_description = data['meta_description']
                    keywords = data['keywords']
                    print("Getting data from cache file")
                    break
            
            else:
                # Step 1: Scrape webpage content
                title, meta_description = scrape_webpage(website)

                # Step 2: Extract keywords
                if title and meta_description:
                    keywords = extract_keywords_nltk(title + ' ' + meta_description)

                    # Step 3: Cache scraped data and keywords
                    cache_data({"website":website, "title": title, "meta_description": meta_description, "keywords": keywords}, cache_filename)
                    print("data added to cached file")
                else:
                    raise HTTPException(status_code=500, detail="Error processing webpage content")
        
        else:
            # Step 1: Scrape webpage content
            title, meta_description = scrape_webpage(website)

            # Step 2: Extract keywords
            if title and meta_description:
                keywords = extract_keywords_nltk(title + ' ' + meta_description)

                # Step 3: Cache scraped data and keywords
                cache_data({"website":website, "title": title, "meta_description": meta_description, "keywords": keywords}, cache_filename)
                print("data added to cached file")
            else:
                raise HTTPException(status_code=500, detail="Error processing webpage content")
    else:
        # Step 1: Scrape webpage content
        title, meta_description = scrape_webpage(website)

        # Step 2: Extract keywords
        if title and meta_description:
            keywords = extract_keywords_nltk(title + ' ' + meta_description)

            # Step 3: Cache scraped data and keywords
            cache_data({"website":website, "title": title, "meta_description": meta_description, "keywords": keywords}, cache_filename)
            print("data added to cached file")
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

    website = request_data.website

    title, meta_description = scrape_webpage(website)

    ad_copy = generate_dynamic_ad_copy(title, meta_description, website )
    ad_copy = ad_copy.replace("\n", " ")
    return {"ad_copy": ad_copy}
