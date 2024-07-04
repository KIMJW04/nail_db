from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
import urllib.parse
import re
import time

# JSON 파일들이 있는 디렉터리
json_dir = 'C:\\Users\\KJW04\\OneDrive\\Documents\\GitHub\\nail_db\\missing_list\\'

# JSON 파일 목록 생성
json_files = [f for f in os.listdir(json_dir) if f.endswith('_missing_nail_shops.json')]

# 웹드라이브 설치
service = ChromeService(executable_path=ChromeDriverManager().install())
options = ChromeOptions()
options.add_argument("--headless")

def extract_shop_data(browser):
    shop_data = {
        'search_url': browser.current_url,
        'title': '',
        'category': '',
        'human_review': '',
        'blog_review': '',
        'addresses': '',
        'x': '',
        'y': '',
        'introduction': '',
        'facilities': [],
        'image_urls': [],
        'operating_hours': {},
        'price_info': {}
    }

    try:
        # 페이지 소스를 가져와서 파싱
        html_source = browser.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 이미지
        image_selectors = [
            "#app-root > div > div > div > div.CB8aP > div > div:nth-child(1) > div > a > img",
            "#app-root > div > div > div > div.CB8aP > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div > a > img",
            "#app-root > div > div > div > div.CB8aP > div > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div > a > img",
            "#app-root > div > div > div > div.CB8aP > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div > a > img",
            "#app-root > div > div > div > div.CB8aP > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div > a > img"
        ]
        for selector in image_selectors:
            image_element = soup.select_one(selector)
            if image_element:
                shop_data['image_urls'].append(image_element['src'])

        # 가게 이름
        name_element = soup.select_one("#_title > div > span.GHAhO")
        if name_element:
            shop_data['title'] = name_element.text.strip()

        # 가게 업종
        category_element = soup.select_one("#_title > div > span.lnJFt")
        if category_element:
            shop_data['category'] = category_element.text.strip()

        # 방문자 리뷰
        human_review_element = soup.select_one("#app-root > div > div > div > div.place_section.no_margin.OP4V8 > div.zD5Nm.undefined > div.dAsGb > span:nth-child(1) > a")
        if human_review_element:
            shop_data['human_review'] = human_review_element.text.strip()

        # 블로그 리뷰
        blog_review_element = soup.select_one("#app-root > div > div > div > div.place_section.no_margin.OP4V8 > div.zD5Nm.undefined > div.dAsGb > span:nth-child(2) > a")
        if blog_review_element:
            shop_data['blog_review'] = blog_review_element.text.strip()

        # 주소
        addresses_element = soup.select_one('span.LDgIH')
        if addresses_element:
            shop_data['addresses'] = addresses_element.text.strip()

        # 좌표 추출
        script_element = soup.find('script', string=re.compile(r'window\.__APOLLO_STATE__'))
        if script_element:
            script_text = script_element.string
            x_match = re.search(r'"x":"(.*?)"', script_text)
            y_match = re.search(r'"y":"(.*?)"', script_text)
            if x_match:
                shop_data['x'] = x_match.group(1)
            if y_match:
                shop_data['y'] = y_match.group(1)

        # 영업시간 정보 버튼 클릭
        try:
            hours_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#app-root > div > div > div > div:nth-child(5) > div > div:nth-child(2) > div.place_section_content > div > div.O8qbU.pSavy > div > a"))
            )
            hours_button.click()
            time.sleep(2)  # 데이터 로드를 위해 대기

            # 다시 페이지 소스를 가져와서 파싱
            html_source = browser.page_source
            soup = BeautifulSoup(html_source, 'html.parser')

            # 영업시간 추출
            hours_elements = soup.select("div.w9QyJ")
            for element in hours_elements:
                day_element = element.select_one("span.i8cJw")
                hours_element = element.select_one("div.H3ua4")
                if day_element and hours_element:
                    day = day_element.text.strip()
                    hours = hours_element.text.strip()
                    shop_data['operating_hours'][day] = hours
        except Exception as e:
            print(f"Error extracting operating hours: {e}")

        # '정보' 탭 클릭
        info_tab = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href$='/information']"))
        )
        info_tab.click()
        time.sleep(2)  # 데이터 로드를 위해 대기

        # 페이지 소스를 다시 가져와서 파싱
        html_source = browser.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 가게 소개
        intro_element = soup.select_one("#app-root > div > div > div > div:nth-child(6) > div > div.place_section.no_margin.Od79H > div > div > div.Ve1Rp > div")
        if intro_element:
            shop_data['introduction'] = intro_element.text.strip()

        # 편의시설 및 서비스
        facilities_elements = soup.select("#app-root > div > div > div > div:nth-child(6) > div > div.place_section.VMtyJ.no_margin > div > div > ul > li")
        for facility in facilities_elements:
            facility_name = facility.select_one('.owG4q').text.strip()
            shop_data['facilities'].append(facility_name)

        # '가격' 탭 클릭
        price_tab = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href$='/price']"))
        )
        price_tab.click()
        time.sleep(2)  # 데이터 로드를 위해 대기

        # 페이지 소스를 다시 가져와서 파싱
        html_source = browser.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 가격 정보 추출
        price_categories = soup.select("#app-root > div > div > div > div:nth-child(6) > div > div > ul > li.F7pMw")
        for category in price_categories:
            category_name = category.select_one("div.TVniT").text.strip()
            items = category.select("ul.JToq_ > li")
            items_list = []
            for item in items:
                item_name = item.select_one("div.OJVMR > div.NdE7m > span.gqmxb")
                item_price = item.select_one("div.dELze > em")
                if item_name:
                    name = item_name.text.strip()
                    price = item_price.text.strip() if item_price else "상담"
                    items_list.append({
                        "name": name,
                        "price": price
                    })
            shop_data['price_info'][category_name] = items_list

    except Exception as e:
        print(f"Error extracting data: {e}")

    return shop_data

def search_shop(shop, browser):
    address_parts = shop['도로명전체주소'].split()[:2]
    search_address = " ".join(address_parts)
    full_address = f"{search_address} {shop['사업장명']}"
    encoded_query = urllib.parse.quote(full_address)
    url = f"https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={encoded_query}"

    browser.get(url)

    try:
        # 검색 결과가 로드될 때까지 대기
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "place-app-root")))

        # place-app-root에서 첫 번째 링크의 href 속성 추출
        first_link = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#loc-main-section-root > section > div > div.rdX0R.HXTER > ul > li:nth-child(1) > div.qbGlu > div.ouxiq > a:nth-child(3)"))
        )
        first_link_href = first_link.get_attribute('href')

        # place_id 추출
        place_id_match = re.search(r'/place/(\d+)', first_link_href)
        if not place_id_match:
            print(f"Place ID not found for {shop['사업장명']}")
            return None

        place_id = place_id_match.group(1)
        print(f"Place ID: {place_id}, 검색어: {full_address}")  # 검색어와 place_id 출력

        place_url = f"https://pcmap.place.naver.com/place/{place_id}/home"

        # 실제 장소 페이지로 이동
        browser.get(place_url)

        # 데이터 추출
        shop_data = extract_shop_data(browser)
        return shop_data

    except Exception as e:
        print(f"Error navigating to search result for {shop['사업장명']}: {e}")
        return None

for json_file in json_files:
    file_path = os.path.join(json_dir, json_file)

    # 파일 경로가 존재하는지 확인
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        continue

    # JSON 데이터를 파일에서 읽어오기
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 파일명에서 폴더명 생성
    folder_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(folder_name, exist_ok=True)

    extracted_data = []
    missing_data = []
    file_counter = 1

    for shop in data:
        browser = webdriver.Chrome(service=service, options=options)
        shop_data = search_shop(shop, browser)

        if shop_data:
            extracted_data.append(shop_data)
        else:
            # 가게명을 없음으로 표시하고 따로 모음
            missing_data.append(shop)

        # 1000개마다 파일 저장
        if len(extracted_data) >= 1000:
            filename = os.path.join(folder_name, f"shops_{file_counter}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=4)
            extracted_data = []
            file_counter += 1

        browser.quit()

    # 남은 데이터 저장
    if extracted_data:
        filename = os.path.join(folder_name, f"shops_{file_counter}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    # 가게명 없음으로 표시된 데이터 저장
    if missing_data:
        filename = os.path.join(folder_name, f"missing_shops.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(missing_data, f, ensure_ascii=False, indent=4)