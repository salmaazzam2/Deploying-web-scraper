from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

phone_pattern = r"\s*(?:\+44\s?(?:7\d{3}|\d{4})\s?\d{3}\s?\d{3}|\(?0(?:7\d{3}|\d{4})\)?\s?\d{3}\s?\d{3}|\+44\s?\d{3}\s?\d{3}\s?\d{4}|\(?0\d{3}\)?\s?\d{3}\s?\d{4}|\+44\s?\d{2}\s?\d{4}\s?\d{4}|\(?0\d{2}\)?\s?\d{4}\s?\d{4})(?:\s?\(\d{4}|\d{3})?\s*"

remote_keywords = [
    "remote", "work from home", "telecommute", "virtual", "distributed", "home-based", "offsite",
    "flexible location", "hybrid", "partially remote", "blended work", "split schedule", 
    "office/remote mix", "dual-location", "flex work", "work anywhere", "location-independent", "Hybrid work"
]

# Set up browser options and WebDriver
options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
wait = WebDriverWait(driver, 10)  # Explicit wait

def fetch_indeed_page(start_page, location, position):
    modified_location = location.replace(" ", "+").replace(',', '%2C')
    modified_position = position.replace(' ', '+')
    url = f'https://uk.indeed.com/jobs?l={modified_location}&q={modified_position}&from=searchOnDesktopSerp&vjk=1cf6e5772d4acec9&start={start_page}'
    
    driver.get(url)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    return soup

def extract(soup):
    search_results = soup.find_all("div", class_="cardOutline")
    jobs = []
    for result in search_results:
        job = []
        title = result.h2.text.strip().replace(",", " - ")
        company_name = result.find("span", class_="css-63koeb").text.strip().replace(",", " - ")
        location = result.find("div", class_="css-1p0sjhy").text.strip().replace(",", " - ")

        location_array = location.split(" ")
        desired_loc = next((loc for loc in location_array if loc.istitle() and loc.lower() not in remote_keywords), "")
        
        depka_class = result.find("div", class_="css-dekpa")
        incomplete_link = depka_class.a["href"]
        full_link = "https://uk.indeed.com/" + incomplete_link
        
        last_visible_concat = result.find("span", class_="css-qvloho eu4oa1w0").text
        inner_text = result.find("span", class_="css-10pe3me")
        last_visible = last_visible_concat.replace(str(inner_text.text), ' ').strip() if inner_text else last_visible_concat
        
        job.append(title)
        job.append(company_name)
        job.append(location)
        job.append(fetch_phone_number(company_name, desired_loc))
        job.append(last_visible)
        job.append(full_link)
        jobs.append(job)
    return jobs

def fetch_phone_number(company_name, location):
    param = company_name.replace(" ", "+").replace("&", "") + f"+{location}"
    url = f'https://www.google.com/search?q={param}+phone+number&gl=uk&hl=en&pws=0'
    
    driver.get(url)
    try:
        clickable = wait.until(EC.element_to_be_clickable((By.ID, "W0wltc")))
        clickable.click()
        phone_number_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pwimAb")))
        phone = phone_number_div.find_element(By.TAG_NAME, "span").text
        return phone
    except:
        try:
            phone_number_div_google_maps = driver.find_element(By.CLASS_NAME, "rllt__details").text
            heading_google_maps = driver.find_element(By.CLASS_NAME, "dbg0pd").text
            phone_numbers = [re.findall(phone_pattern, element)[0] for element in phone_number_div_google_maps.replace(heading_google_maps, "").strip().split('\n') if re.search(phone_pattern, element)]
            if phone_numbers:
                return phone_numbers[0]
        except:
            contact_div = driver.find_element(By.CLASS_NAME, "VwiC3b")
            phone_numbers = [re.findall(phone_pattern, output)[0] for output in contact_div.text.split(".") if re.search(phone_pattern, output)]
            if phone_numbers:
                return phone_numbers[0]
    return "No contact details found"

@app.route('/')
def home():
    return "Welcome to the Job Scraper API! Use /data endpoint to get job data."

@app.route('/data', methods=['GET'])
def data():
    try:
        position = request.args.get('position')
        location = request.args.get('location')
        pages = request.args.get('pages', default=1, type=int)
        start = request.args.get('start', default=1, type=int)

        if not position or not location:
            return jsonify({"error": "Missing required query parameters: 'position' and 'location'"}), 400

        title = ["Title", "Company name", "Location", "Contact", "Active", "Full link"]
        all_jobs = {"title": title, "jobs": []}

        for i in range(pages):
            page_index = ((start - 1) * 10) + (i * 10)
            soup_at_index_i = fetch_indeed_page(page_index, location, position)
            jobs = extract(soup_at_index_i)
            all_jobs['jobs'].extend(jobs)

        return jsonify(all_jobs)
    except Exception as e:
        app.logger.error(f'Error occurred: {e}')
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=False, host="0.0.0.0")
    finally:
        driver.quit()

