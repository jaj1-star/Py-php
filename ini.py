import requests
import os

url = "https://example.com/index.php"
save_dir = "site"

os.makedirs(save_dir, exist_ok=True)

r = requests.get(url)

with open(f"{save_dir}/index.php", "wb") as f:
    f.write(r.content)

print("تم تحميل index.php بنجاح ✔")
