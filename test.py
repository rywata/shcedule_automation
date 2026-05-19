from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

options = Options()
options.add_argument("--user-data-dir=" + os.path.expanduser("~/chrome-prenotami-profile"))
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://prenotami.esteri.it/")
input("Chrome abriu? Pressione Enter para fechar...")
driver.quit()