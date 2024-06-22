import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import pandas as pd
import time
import datetime
import requests
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

    # Обновляем дату последнего обновления
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


# Функция для сохранения данных в Excel
def save_to_excel(products, filename):
    df = pd.DataFrame(products)
    df.to_excel(filename, index=False)
    messagebox.showinfo("Сохранение данных", f"Данные успешно сохранены в файл {filename}")


# Функция для запуска парсинга с использованием Selenium
def start_parsing():
    selected_subcategory = subcategory_var.get()
    if not selected_subcategory:
        messagebox.showwarning("Выбор подкатегории", "Пожалуйста, выберите подкатегорию для парсинга.")
        return

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Парсинг данных, пожалуйста, подождите...\n")

    progress.set(0)
    total_items.set(0)
    products = []

    def update_progress():
        while progress.get() < total_items.get():
            progress_bar['value'] = progress.get()
            app.update_idletasks()
            time.sleep(0.1)
        progress_bar['value'] = total_items.get()
        app.update_idletasks()

    def run_parsing():
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(subcategories[selected_subcategory])

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "catalog-item")))

            product_cards = driver.find_elements(By.CLASS_NAME, "catalog-item")
            total_items.set(len(product_cards))

            for card in product_cards:
                try:
                    link = card.find_element(By.CLASS_NAME, "catalog-item-link").get_attribute("href")

                    driver.get(link)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "pdp-main-info__wrapper")))

                    try:
                        main_category = driver.find_element(By.CSS_SELECTOR, "a[data-test='bread-crumbs-item'] span").text.strip()
                    except:
                        main_category = ""

                    try:
                        product_type = driver.find_element(By.CSS_SELECTOR, "div.value a span").text.strip()
                    except:
                        product_type = ""

                    try:
                        name = driver.find_element(By.CSS_SELECTOR, "h1[data-test='product-title']").text.strip()
                    except:
                        name = ""

                    try:
                        product_code = driver.find_element(By.CSS_SELECTOR, "span[data-test='product-code']").text.strip()
                    except:
                        product_code = ""

                    try:
                        brand = driver.find_element(By.CSS_SELECTOR, "div.value a span").text.strip()
                    except:
                        brand = ""

                    prices = {}
                    try:
                        gold_price = driver.find_element(By.CSS_SELECTOR, "p[data-test='product-gold-price']").text.strip()
                        prices['По карте'] = gold_price
                    except:
                        pass

                    try:
                        retail_price = driver.find_element(By.CSS_SELECTOR, "p[data-test='product-retail-price']").text.strip()
                        prices['обычно'] = retail_price
                    except:
                        pass

                    products.append({
                        'Основанная категория': main_category,
                        'Тип товара': product_type,
                        'Название': name,
                        'Код товара': product_code,
                        'Бренд': brand,
                        'Цена за': prices,
                        'Ссылка на товар': link
                    })

                    progress.set(progress.get() + 1)
                    app.update_idletasks()

                except Exception as e:
                    print(f"Ошибка при обработке товара: {str(e)}")

            if products:
                output_text.insert(tk.END, f"Найдено товаров: {len(products)}\n")
                filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
                if filename:
                    save_to_excel(products, filename)
            else:
                output_text.insert(tk.END, "Товары не найдены.\n")

            driver.quit()

        except KeyError:
            messagebox.showerror("Ошибка выбора подкатегории", "Выбранная подкатегория не найдена.")
        except Exception as e:
            messagebox.showerror("Ошибка парсинга", f"Произошла ошибка при парсинге: {str(e)}")
        finally:
            update_progress()

    parsing_thread = threading.Thread(target=run_parsing)
    parsing_thread.start()

    progress_thread = threading.Thread(target=update_progress)
    progress_thread.start()


# Добавление виджетов для выбора подкатегории и вывода лога (без изменений)
parse_button = tk.Button(app, text="Запустить парсинг", command=start_parsing)
parse_button.pack(pady=10)

subcategory_var = tk.StringVar()
subcategory_label = tk.Label(app, text="Выберите подкатегорию для парсинга:")
subcategory_label.pack(pady=5)

subcategory_dropdown = ttk.Combobox(app, textvariable=subcategory_var, width=50)
update_interface_with_subcategories()  # Обновляем выпадающий список сразу при запуске
subcategory_dropdown.pack(pady=5)

output_text = scrolledtext.ScrolledText(app, width=80, height=20)
output_text.pack(padx=10, pady=10)

progress_bar = ttk.Progressbar(app, orient=tk.HORIZONTAL, length=400, mode='determinate', maximum=100)
progress_bar.pack(pady=10)

app.mainloop()
