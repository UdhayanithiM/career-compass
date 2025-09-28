import requests
from bs4 import BeautifulSoup
import json

def scrape_jobs():
    """Scrapes job postings from a sample website."""
    print("Scraping job postings...")
    URL = "https://realpython.github.io/fake-jobs/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="ResultsContainer")
    job_elements = results.find_all("div", class_="card-content")
    jobs_data = []

    for job_element in job_elements:
        title_element = job_element.find("h2", class_="title")
        company_element = job_element.find("h3", class_="company")
        location_element = job_element.find("p", class_="location")
        content = job_element.find("div", class_="content")

        if None in (title_element, company_element, location_element, content):
            continue

        jobs_data.append({
            "title": title_element.text.strip(),
            "company": company_element.text.strip(),
            "location": location_element.text.strip(),
            "content": content.text.strip(),
            "source_url": URL, # In a real scraper, this would be the specific job post URL
            "category": "job_description"
        })
    print(f"Found {len(jobs_data)} job postings.")
    return jobs_data

def scrape_career_articles():
    """Scrapes career advice articles from a blog."""
    print("Scraping career articles...")
    URL = "https://www.themuse.com/advice"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    # NOTE: Website structures change. This class name might be different in the future.
    article_links = soup.find_all("a", class_="article-card_link__D22OK")

    articles_data = []

    # Loop through the first 5 articles to get a sample.
    for link in article_links[:5]:
        article_url = "https://www.themuse.com" + link['href']
        try:
            article_page = requests.get(article_url, timeout=10)
            article_soup = BeautifulSoup(article_page.content, "html.parser")

            title_element = article_soup.find("h1")
            # NOTE: This class name might also change.
            content_element = article_soup.find("div", class_="article-body_body__o_LAQ")

            if title_element and content_element:
                articles_data.append({
                    "title": title_element.text.strip(),
                    "content": content_element.text.strip(),
                    "source_url": article_url,
                    "category": "career_article"
                })
        except requests.RequestException as e:
            print(f"Could not fetch article {article_url}: {e}")

    print(f"Found {len(articles_data)} articles.")
    return articles_data

if __name__ == '__main__':
    # Create a single list to hold all our data
    all_career_data = []

    # Run the job scraper and add its data to our list
    all_career_data.extend(scrape_jobs())

    # Run the article scraper and add its data to our list
    all_career_data.extend(scrape_career_articles())

    # Save the combined data into a single file
    output_filename = 'career_data.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_career_data, f, indent=4, ensure_ascii=False)

    print(f"\nData scraping complete. All data saved to {output_filename}")