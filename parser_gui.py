import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import pandas as pd
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

# Глобальные переменные
subcategories = {}
last_update_date = None


# Функция для сбора подкатегорий и их URL с помощью Selenium
def fetch_subcategories():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://petrovich.ru/catalog/")
    subcategories.clear()

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

    global last_update_date
    last_update_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Функция для сохранения категорий в файл JSON
def save_categories_to_file():
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"categories_{current_datetime}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(subcategories, f, ensure_ascii=False, indent=4)
    messagebox.showinfo("Сохранение категорий", f"Категории сохранены в файл: {filename}")


# Функция для загрузки категорий из файла JSON
def load_categories_from_file():
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if filename:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                global subcategories
                subcategories = json.load(f)
            update_interface_with_subcategories()
            messagebox.showinfo("Загрузка категорий", f"Категории успешно загружены из файла: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Ошибка при загрузке категорий из файла: {str(e)}")


# Функция для загрузки списка подкатегорий
def load_subcategories():
    fetch_subcategories()
    update_interface_with_subcategories()


# Инициализация приложения tkinter
app = tk.Tk()
app.title("Парсер товаров")


# Функция для обновления интерфейса с новыми подкатегориями
def update_interface_with_subcategories():
    subcategory_dropdown['values'] = list(subcategories.keys())


# Функция для сохранения данных в Excel
def save_to_excel(products, filename):
    df = pd.DataFrame(products)
    df.to_excel(filename, index=False)
    messagebox.showinfo("Сохранение данных", f"Данные успешно сохранены в файл {filename}")


# Функция для парсинга данных по товару
def fetch_product_details(product_link):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    product_details = {}

    try:
        driver.get(product_link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-details")))

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Пример парсинга названия товара
        name_tag = soup.find('h1', class_='product-title')
        product_details['Название'] = name_tag.text.strip() if name_tag else 'N/A'

        # Пример парсинга цены товара
        price_tag = soup.find('span', class_='product-price')
        product_details['Цена'] = price_tag.text.strip() if price_tag else 'N/A'

        # Пример парсинга описания товара
        description_tag = soup.find('div', class_='product-description')
        product_details['Описание'] = description_tag.text.strip() if description_tag else 'N/A'

        # Добавьте здесь другой код для парсинга дополнительных данных о товаре

    except Exception as e:
        print(f"Ошибка при парсинге данных о товаре: {str(e)}")
    finally:
        driver.quit()

    return product_details


# Функция для запуска парсинга данных по ссылке на товар
def start_parsing_product_link():
    product_link = product_link_entry.get()
    if not product_link:
        messagebox.showwarning("Ввод ссылки", "Пожалуйста, введите ссылку на товар.")
        return

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Парсинг данных, пожалуйста, подождите...\n")

    def run_parsing():
        product_details = fetch_product_details(product_link)
        if product_details:
            df = pd.DataFrame([product_details])
            filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
            if filename:
                save_to_excel([product_details], filename)
            output_text.insert(tk.END, f"Данные о товаре:\n{product_details}\n")
        else:
            output_text.insert(tk.END, "Не удалось получить данные о товаре.\n")

    parsing_thread = threading.Thread(target=run_parsing)
    parsing_thread.start()


# Кнопка для обновления списка подкатегорий
update_button = tk.Button(app, text="Обновить список подкатегорий", command=load_subcategories)
update_button.pack(pady=10)

# Кнопка для сохранения категорий в файл JSON
save_categories_button = tk.Button(app, text="Сохранить категории", command=save_categories_to_file)
save_categories_button.pack(pady=10)

# Кнопка для загрузки категорий из файла JSON
load_categories_button = tk.Button(app, text="Загрузить категории", command=load_categories_from_file)
load_categories_button.pack(pady=10)

# Переменные для отслеживания прогресса и общего количества товаров
progress = tk.IntVar()
total_items = tk.IntVar()

# Добавление виджетов для выбора подкатегории и ввода ссылки на товар
subcategory_var = tk.StringVar()
subcategory_label = tk.Label(app, text="Выберите подкатегорию для парсинга:")
subcategory_label.pack(pady=5)

subcategory_dropdown = ttk.Combobox(app, textvariable=subcategory_var, width=50)
update_interface_with_subcategories()  # Обновляем выпадающий список сразу при запуске
subcategory_dropdown.pack(pady=5)

product_link_label = tk.Label(app, text="Или введите ссылку на товар для парсинга:")
product_link_label.pack(pady=5)

product_link_entry = tk.Entry(app, width=50)
product_link_entry.pack(pady=5)

# Кнопка для запуска парсинга данных по ссылке на товар
parse_product_button = tk.Button(app, text="Запустить парсинг по ссылке", command=start_parsing_product_link)
parse_product_button.pack(pady=10)

# Поле для вывода лога
output_text = scrolledtext.ScrolledText(app, width=80, height=20)
output_text.pack(padx=10, pady=10)

progress_bar = ttk.Progressbar(app, orient=tk.HORIZONTAL, length=400, mode='determinate', maximum=100)
progress_bar.pack(pady=10)

app.mainloop()
