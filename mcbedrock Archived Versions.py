import concurrent.futures
import requests
from bs4 import BeautifulSoup
import tqdm

url = "https://mcpedl.org/post-sitemap.xml"
res = requests.get(url)
soup = BeautifulSoup(res.content, 'xml')

versions = []
for url in soup.find_all('url'):
    loc = url.find('loc').text
    if loc.startswith("https://mcpedl.org/minecraft-pe-"):
        version = loc.split("https://mcpedl.org/minecraft-pe-")[1].split("/")[0]
        if "-apk" in version:
            version = version.split("-apk")[0]
        versions.append(version)
    
sorted_versions = sorted(versions, key=lambda x: [int(y) for y in x.split('-') if y.isdigit()])

downloadable_versions = []

def check_version(url):
    version = url.find('loc').text.split("https://mcpedl.org/minecraft-pe-")[1].split("/")[0]
    if "-apk" in version:
        version = version.split("-apk")[0]
    version_elegida = version.replace('-', '.')
    lastmod = url.find('lastmod').text.strip()[:10]
    fecha = '-'.join(reversed(lastmod.split('-')))
    url_final = f"https://mcpedl.org/uploads_files/{fecha}/minecraft-{version}.apk"
    response = requests.get(url_final, stream=True)
    if response.status_code == 200:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > 1000:
            response.close()
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup.title == "404 Not Found" in soup.title.string:
                response.close()
                return None
            else:
                version_parts = version_elegida.split('.')
                # pad version parts with leading zeros to ensure numerical sorting
                version_parts = [part.zfill(3) for part in version_parts]
                # join version parts back into a single string
                version_sort_key = ''.join(version_parts)
                return version_sort_key, version_elegida
        else:
            response.close()
            return None
    else:
        response.close()
        return None

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(check_version, url) for url in soup.find_all('url') if url.find('loc').text.startswith("https://mcpedl.org/minecraft-pe-")]
    for future in tqdm.tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
        result = future.result()
        if result:
            version_sort_key, version_elegida = result
            downloadable_versions.append(version_elegida)

    # sort the versions numerically
    downloadable_versions = sorted(downloadable_versions, key=lambda v: [int(part) for part in v.split('.')])
    
    print(downloadable_versions)


version_elegida = input("\nEscribe la versión que deseas descargar (en el formato 1.2.3): ")
if version_elegida == "":
    # select the latest version available
    downloadable_versions.sort(reverse=True)
    version_elegida = downloadable_versions[0].replace('-', '.')
else:
    # check if the version entered by the user is available
    if version_elegida not in downloadable_versions:
        print(f"La versión {version_elegida} no está disponible para descargar.")
        exit()
    version_elegida = version_elegida.replace('.', '-')

# find the URL for the selected version
for url in soup.find_all('url'):
    loc = url.find('loc').text
    if loc.startswith(f"https://mcpedl.org/minecraft-pe-{version_elegida}"):
        lastmod = url.find('lastmod').text.strip()[:10]
        fecha = '-'.join(reversed(lastmod.split('-')))
        url_final = f"https://mcpedl.org/uploads_files/{fecha}/minecraft-{version_elegida}.apk"
        print(f"\nLa URL final es: {url_final}")
        break