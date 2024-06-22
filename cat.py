from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def fetch_subcategories():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://petrovich.ru/catalog/")
    subcategories = {}

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "section-catalog-list-item-link")))
        elements = driver.find_elements(By.CLASS_NAME, "section-catalog-list-item-link")
        for element in elements:
            try:
                name = element.text
                url = element.get_attribute("href")
                subcategories[name] = url
            except Exception as e:
                print(f"Ошибка при обработке элемента: {str(e)}")
    except Exception as e:
        print(f"Ошибка при загрузке каталога: {str(e)}")
    finally:
        driver.quit()

    return subcategories


subcategories = fetch_subcategories()
for name, url in subcategories.items():
    print(f"{name}: {url}")
