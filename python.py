from flask import Flask, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
import time
import re


phone_pattern = r"\s*(?:\+44\s?(?:7\d{3}|\d{4})\s?\d{3}\s?\d{3}|\(?0(?:7\d{3}|\d{4})\)?\s?\d{3}\s?\d{3}|\+44\s?\d{3}\s?\d{3}\s?\d{4}|\(?0\d{3}\)?\s?\d{3}\s?\d{4}|\+44\s?\d{2}\s?\d{4}\s?\d{4}|\(?0\d{2}\)?\s?\d{4}\s?\d{4})(?:\s?\(\d{4}|\d{3})?\s*"

remote = [
    "remote", "work from home", "telecommute", "virtual", "distributed", "home-based", "offsite",
    "flexible location", "hybrid", "partially remote", "blended work", "split schedule", 
    "office/remote mix", "dual-location", "flex work", "work anywhere", "location-independent", "Hybrid work"
]



def fetch_indeed_page(start_page, location, position):
    
    modified_location = location.replace(" ", "+").replace(',', '%2C') 
    modified_position = position.replace(' ', '+')
    url = f'https://uk.indeed.com/jobs?l={modified_location}&q={modified_position}&from=searchOnDesktopSerp&vjk=1cf6e5772d4acec9&start={start_page}'
    
    print(url)
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    #driver = webdriver.Chrome()
    driver.get(url)
    page_source = driver.page_source
    driver.quit()  # Close the browser after fetching the page source
    soup = BeautifulSoup(page_source, "html.parser")
    return soup



def extract(soup):
    search_results = soup.find_all("div", class_="cardOutline")
    jobs = []
    for result in search_results:
        job = []
        title = result.h2.text
        company_name = result.find("span", class_="css-63koeb").text
        location = result.find("div", class_="css-1p0sjhy").text
        location_array = location.split(" ")
        for loc in location_array:
            if loc.istitle():
                if not loc.lower() in remote:
                    desired_loc = loc
                    break
        depka_class = result.find("div", class_="css-dekpa")
        incomplete_link = depka_class.a["href"]
        full_link: str  = "https://uk.indeed.com/" + incomplete_link 
        last_visible_concat: str = result.find("span", class_ = "css-qvloho eu4oa1w0").text
        try: 
            inner_text= result.find("span", class_="css-10pe3me").text
            last_visible = last_visible_concat.replace(str(inner_text), ' ').strip()
        except:
                last_visible = last_visible_concat
        finally:
            job.append(title.strip().replace(",", " - ") )
            job.append(company_name.strip().replace(",", " - "))
            job.append(location.strip().replace(",", " - "))
            job.append(fetch_phone_number(company_name, desired_loc))
            job.append(last_visible.strip().replace(",", " - "))
            job.append(full_link)
            #print(job)
            jobs.append(job)
            
    return jobs




def fetch_phone_number(company_name, location):
        param = company_name.replace(" ", "+").replace("&", "")
        param += f"+{location}"
        url = f'https://www.google.com/search?q={param}+phone+number&gl=uk&hl=en&pws=0'
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        #driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(1)
        try:
            clickable = driver.find_element(By.ID, "W0wltc")
            ActionChains(driver)\
                .click(clickable)\
                    .perform()
            time.sleep(2)
            try: 
               
                phone_number_div = driver.find_element(By.CLASS_NAME, "pwimAb") #returns all the elements in the div but we only need the first one
                phone = phone_number_div.find_element(By.TAG_NAME, "span")
                return phone.text
            except:
                    try: 
                         # fetching phone number from google maps 
                        phone_number_div_google_maps = driver.find_element(By.CLASS_NAME, "rllt__details").text
                        #print(phone_number_div_google_maps.text)
                        heading_google_maps = driver.find_element(By.CLASS_NAME,"dbg0pd").text
                        determining_phone_number = phone_number_div_google_maps.replace(heading_google_maps, "").strip().split('\n')
                        for element in determining_phone_number:
                            if re.search(phone_pattern, element):
                                phone_number = re.findall(phone_pattern, element)
                                return phone_number[0]
                                
                    except:
                        contact_div = driver.find_element(By.CLASS_NAME, "VwiC3b")
                        output_as_an_array = str(contact_div.text).split(".")
                        for output in output_as_an_array:
                            if re.search(phone_pattern, output): 
                                phone_number = re.findall(phone_pattern, output)
                                return phone_number[0]
                        
                        return "No contact details found"
        except:
            return "can't access website"
        finally:
            driver.quit()
        return "No contact details found"
                   
        
        
app = Flask(__name__, static_folder='../Web')
CORS(app)
@app.route('/data', methods=['GET', 'POST'])
def data():
    position = request.args.get('position')
    location = request.args.get('location')
    pages = int(request.args.get('pages'))
    start = int(request.args.get('start'))
    if request.method == 'GET':
        title = ["Title", "Company name", "Location", "Contact", "Active", "Full link"]
        all_jobs = {"title": title, "jobs": []}  # Initialize 'jobs' as an empty list
        for i in range(pages):
            page_index = ((start - 1) * 10) + (i * 10)
            soup_at_index_i = fetch_indeed_page(page_index, location, position)
            jobs = extract(soup_at_index_i)
            all_jobs['jobs'].extend(jobs)  # Extend the list with new jobs
        return all_jobs
    

if __name__ == '__main__':
    app.run(debug=False, port="0.0.0.0")
