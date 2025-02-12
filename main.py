import json
import os.path
import random
import re
import time
import csv
from pathlib import Path
from selenium_stealth import stealth
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ChromeOptions
from lxml.html import fromstring

# from seleniumwire import webdriver as uc_wire

BASE_DIR = Path(__file__).resolve().parent


def get_uc_selenium_wire(headless=False):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36")
        options.add_argument('--no-sandbox')
        options.add_argument("--log-level=3")
        if headless:
            options.add_argument('--headless')
        options.add_argument('--start-maximized')

        chrome_exe_path = ChromeDriverManager().install()
        driver = webdriver.Chrome(service=Service(executable_path=chrome_exe_path), options=options)
        stealth(driver,
                user_agent='DN',
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        driver.get("https://bnifrance.fr/fr/findachapter")
        return driver
    except Exception as e:
        print(e)
        print('------------------- Generation the New Driver')
        get_uc_selenium_wire(headless=False)


def accept_cookies(driver):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[text()='Tout autoriser']")))
        element.click()
    except Exception as e:
        print(e)


def click_zoom_in_button(driver):
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@title='Zoom in']")))
    element.click()


def click_zoom_out_button(driver):
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@title='Zoom out']")))
    element.click()


def check_if_zoomed_out(driver):
    try:
        element = driver.find_element(By.XPATH, "//button[@title='Zoom out']")
        if element.is_enabled():
            print("The element is enabled")
            return False
        else:
            print("The element is disabled")
            return True
    except Exception as e:
        print(e)


def get_maps_m3_points(driver, m_position):
    try:
        xpath = f'''//div[contains(@style, 'background-image: url("/web/images/map/map_m{m_position}')]'''
        elements = driver.find_elements(By.XPATH, xpath)
        return elements
    except Exception as e:
        print(e)


def get_markers(driver):
    try:
        xpath = '''//div[contains(@aria-describedby, 'D3B1BBCA')] | //img[contains(@src, 'https://maps.gstatic.com/mapfiles/transparent.png')]/parent::div'''
        elements = driver.find_elements(By.XPATH, xpath)
        return elements
    except Exception as e:
        print(e)


def get_group_details_link(driver):
    try:
        xpath = '''//*[text()='Group Details' or text()='Détails du Groupe']'''
        element = driver.find_element(By.XPATH, xpath)
        return element.get_attribute('href')
    except Exception as e:
        print(e)


def get_chapter_id(url):
    match = re.search(r'chapterId=([^&]+)', url)

    if match:
        chapter_id = match.group(1)
        return chapter_id


def done_chapters(mode='a', chapter_id=None):
    file_path = os.path.join(BASE_DIR, '../done_chapters.txt')
    if mode == 'r':
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                done_chapters = f.read().splitlines()

            return done_chapters
        else:
            return []

    if mode == 'a':
        with open(file_path, 'a') as f:
            f.write(chapter_id + '\n')


def execute_script_based_click(driver, xpath=None, el=None,timeout=10):
    if xpath:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", el)

def get_chapter_details(driver):
    xpath = '''//div[contains(@aria-describedby, 'D3B1BBCA')] | //img[contains(@src, 'https://maps.gstatic.com/mapfiles/transparent.png')]/parent::div'''
    markers = driver.find_elements(By.XPATH, xpath)
    print("total markers: ", len(markers))
    if markers:
        for marker in markers:
            marker.click()
            time.sleep(2)
            group_details_link = get_group_details_link(driver)
            print(group_details_link)
            chapter_id = get_chapter_id(group_details_link)
            if chapter_id in done_chapters(mode='r'):
                print("Chapter already done")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
            print(chapter_id)
            time.sleep(5)
            # Open the group details link in a new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(group_details_link)
            time.sleep(5)
            # Click on the members button
            if not driver.find_elements(By.XPATH, "//a[@id='members_tab']"):
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@id='members_tab']")))
            element.click()
            time.sleep(5)
            # Get the members
            page_source = driver.page_source
            tree = fromstring(page_source)
            all_members = tree.xpath("//tbody/tr")
            for member in all_members:
                member_name = member.xpath(".//td[1]/a/text()")[0]
                company = member.xpath(".//td[2]/text()")[0]
                department = member.xpath(".//td[3]/text()")[0]
                phone = member.xpath(".//td[4]/bdi/text()")[0]
                fileexists = os.path.isfile('../chapter_details.csv')
                with open('../chapter_details.csv', mode='a+', newline='', encoding='utf-16') as file:
                    writer = csv.writer(file)
                    if not fileexists:
                        writer.writerow(['Chapter ID', 'Member Name', 'Company', 'Department', 'Phone'])
                    writer.writerow([chapter_id, member_name, company, department, phone])

            done_chapters(mode='a', chapter_id=chapter_id)


def main():
    driver = get_uc_selenium_wire()
    time.sleep(10)
    try:
        accept_cookies(driver)
        # time.sleep(5)
        # zoomed_out = check_if_zoomed_out(driver)
        # while not zoomed_out:
        #     click_zoom_out_button(driver)
        #     time.sleep(5)
        #     zoomed_out = check_if_zoomed_out(driver)
        try:
            get_chapter_details(driver)
        except:
            window_handles = driver.window_handles
            if len(window_handles) > 1:
                driver.close()
                driver.switch_to.window(window_handles[0])
            driver.switch_to.window(window_handles[0])
        print("Done")
        try:
            get_chapter_details(driver)
        except:
            window_handles = driver.window_handles
            if len(window_handles) > 1:
                driver.close()
                driver.switch_to.window(window_handles[0])
            driver.switch_to.window(window_handles[0])
        try:
            get_chapter_details(driver)
        except:
            window_handles = driver.window_handles
            if len(window_handles) > 1:
                driver.close()
                driver.switch_to.window(window_handles[0])
            driver.switch_to.window(window_handles[0])

        try:
            get_chapter_details(driver)
        except:
            window_handles = driver.window_handles
            if len(window_handles) > 1:
                driver.close()
                driver.switch_to.window(window_handles[0])
            driver.switch_to.window(window_handles[0])


    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
