import os
import urllib.parse
import pandas as pd
import requests

# Excel dosyasını oku
df = pd.read_excel('Kitap (9).xlsx')

# Klasörleri oluştur
os.makedirs('iller', exist_ok=True)
os.makedirs('tarihieserler', exist_ok=True)


def download_wikimedia_image(query, save_path):
  url = f'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&ns=6&prop=imageinfo&iiprop=url&format=json'
  headers = {'User-Agent': 'PieceOfPastApp/1.0'}
  try:
    res = requests.get(url, headers=headers, timeout=10).json()
    pages = res.get('query', {}).get('pages', {})
    for _, page_info in pages.items():
      img_url = page_info.get('imageinfo', [{}])[0].get('url')
      if img_url and (
          img_url.endswith('.jpg')
          or img_url.endswith('.png')
          or img_url.endswith('.jpeg')
      ):
        img_data = requests.get(img_url, headers=headers, timeout=10).content
        with open(save_path, 'wb') as f:
          f.write(img_data)
        print(f'İndirildi: {save_path}')
        return True
  except Exception as e:
    print(f'Hata ({query}): {e}')
  return False


# 1. İl Görselleri (77 Adet)
provinces = df['İl'].unique()
for prov in provinces:
  file_path = f'iller/{prov}.png'
  if not os.path.exists(file_path):
    download_wikimedia_image(f'{prov} Türkiye', file_path)

# 2. Tarihi Eser Görselleri (557 Adet)
for _, row in df.iterrows():
  site_name = str(row['Tarihî / Arkeolojik Alan']).strip()
  file_path = f'tarihieserler/{site_name}.png'
  if not os.path.exists(file_path):
    download_wikimedia_image(site_name, file_path)
