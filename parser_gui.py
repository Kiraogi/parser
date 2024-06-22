import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import pandas as pd
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

# Глобальная переменная для списка подкатегорий
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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "section-catalog-list-item-link")))
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

# Переменные для отслеживания прогресса и общего количества товаров
progress = tk.IntVar()
total_items = tk.IntVar()

# Остальной код парсера остаётся без изменений до функции start_parsing()

# Функция сохранения данных в Excel (без изменений)
def save_to_excel(products, filename):
    product_list = []
    for product in products:
        for price_label, price_value in product['prices'].items():
            product_list.append({
                'Тип товара': product['product_type'],
                'Название': product['name'],
                'Бренд': product['brand'],
                'Цена за': price_label,
                'Цена': price_value,
                'Ссылка на товар': product['link']
            })
    df = pd.DataFrame(product_list)
    df.to_excel(filename, index=False)
    messagebox.showinfo("Сохранение данных", f"Данные успешно сохранены в файл {filename}")

# Функция для запуска парсинга (без изменений)
def start_parsing():
    selected_subcategory = subcategory_var.get()
    if not selected_subcategory:
        messagebox.showwarning("Выбор подкатегории", "Пожалуйста, выберите подкатегорию для парсинга.")
        return

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Парсинг данных, пожалуйста подождите...\n")

    progress.set(0)
    total_items.set(0)
    products = []

    def run_parsing():
        result = parse_catalog_petrovich(selected_subcategory, progress, total_items)
        if result:
            products.extend(result)
            for product in result:
                output_text.insert(tk.END, f"{product}\n")
        else:
            output_text.insert(tk.END, "Ошибка при парсинге подкатегории.\n")

        if products:
            filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
            if filename:
                save_to_excel(products, filename)

    def update_progress():
        while progress.get() < total_items.get():
            progress_bar['value'] = progress.get()
            app.update_idletasks()
            time.sleep(0.1)
        progress_bar['value'] = total_items.get()
        app.update_idletasks()

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