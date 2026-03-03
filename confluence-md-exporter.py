import os
import sys
import re
import json
import getpass
import requests
import html2text
import urllib.parse
from bs4 import BeautifulSoup
from tqdm import tqdm

# --- Setup Markdown Converter ---
converter = html2text.HTML2Text()
converter.ignore_links = False
converter.ignore_images = False
converter.body_width = 0

def get_user_config():
    print("=== Confluence to Markdown Exporter ===")
    print(" (Press Ctrl+C at any time to cancel)\n")
    
    cred_file = "confluence_creds.json"
    domain, email, api_token = "", "", ""
    
    if os.path.exists(cred_file):
        try:
            with open(cred_file, "r") as f:
                creds = json.load(f)
                domain = creds.get("domain", "")
                email = creds.get("email", "")
                api_token = creds.get("api_token", "")
            print(f"✅ Loaded credentials for {email} from {cred_file}")
        except Exception as e:
            print(f"⚠️ Could not read {cred_file}: {e}")

    needs_saving = False
    
    if not domain:
        raw_domain = input("Enter Confluence domain prefix (e.g., 'your-company'): ").strip()
        domain = raw_domain.replace("https://", "").replace(".atlassian.net", "")
        needs_saving = True
        
    if not email:
        email = input("Enter your Atlassian email: ").strip()
        needs_saving = True
        
    if not api_token:
        api_token = getpass.getpass("Enter your API Token (keystrokes hidden): ").strip()
        needs_saving = True

    if needs_saving:
        save = input("\nWould you like to save these credentials for next time? (y/n): ").strip().lower()
        if save == 'y':
            with open(cred_file, "w") as f:
                json.dump({"domain": domain, "email": email, "api_token": api_token}, f, indent=4)
            print(f"🔒 Credentials saved to {cred_file}.")
    
    print("-" * 40)
    root_page_id = input("Enter the Root Page ID to export: ").strip()
    
    output_dir = input("Enter output folder name [default: confluence_export]: ").strip()
    if not output_dir:
        output_dir = "confluence_export"
        
    print("\nCalculating total pages to export (this might take a second)...\n")
    return domain, root_page_id, email, api_token, output_dir

def get_total_page_count(domain, email, api_token, root_page_id):
    url = f"https://{domain}.atlassian.net/wiki/rest/api/search"
    cql = f"ancestor={root_page_id} or id={root_page_id}"
    params = {"cql": cql, "limit": 1}
    
    response = requests.get(url, params=params, auth=(email, api_token), headers={"Accept": "application/json"})
    if response.status_code == 200:
        return response.json().get("totalSize", 1)
    return None

def sanitize_name(name):
    name = name.replace("/", "-").replace("\\", "-").replace(" ", "-")
    return re.sub(r'[*?:"<>|]', "", name).strip()

def process_images_in_html(domain, email, api_token, html_content, current_dir):
    soup = BeautifulSoup(html_content, 'html.parser')
    images_dir = os.path.join(current_dir, "images")
    created_img_dir = False
    
    for img in soup.find_all('img'):
        src = img.get('data-image-src') or img.get('src')
        if not src:
            continue
            
        if src.startswith('/'):
            full_url = f"https://{domain}.atlassian.net{src}"
        elif src.startswith(f"https://{domain}.atlassian.net"):
            full_url = src
        else:
            continue 
            
        filename = img.get('data-linked-resource-default-alias')
        
        if not filename:
            parsed_url = urllib.parse.urlparse(full_url)
            filename = os.path.basename(urllib.parse.unquote(parsed_url.path))
            
        if not filename or filename == "/" or "." not in filename:
            filename = f"image_{abs(hash(full_url))}.png"
            
        safe_filename = sanitize_name(filename)
        img_filepath = os.path.join(images_dir, safe_filename)
        
        if not created_img_dir:
            os.makedirs(images_dir, exist_ok=True)
            created_img_dir = True
            
        try:
            img_response = requests.get(full_url, auth=(email, api_token))
            if img_response.status_code == 200:
                with open(img_filepath, "wb") as f:
                    f.write(img_response.content)
                
                img['src'] = f"images/{safe_filename}"
                if img.get('data-image-src'):
                    img['data-image-src'] = f"images/{safe_filename}"
        except Exception:
            pass 

    return str(soup)

def preprocess_confluence_macros(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for panel in soup.find_all('div', class_='confluence-information-macro'):
        body = panel.find('div', class_='confluence-information-macro-body')
        if body:
            panel_type = "Note"
            if 'confluence-information-macro-warning' in panel.get('class', []):
                panel_type = "Warning"
            elif 'confluence-information-macro-information' in panel.get('class', []):
                panel_type = "Info"
                
            blockquote = soup.new_tag('blockquote')
            blockquote.append(BeautifulSoup(f"<strong>{panel_type}:</strong><br/>", 'html.parser'))
            blockquote.extend(body.contents)
            panel.replace_with(blockquote)
    return str(soup)

def get_page_content(domain, email, api_token, page_id):
    url = f"https://{domain}.atlassian.net/wiki/rest/api/content/{page_id}?expand=body.view"
    response = requests.get(url, auth=(email, api_token), headers={"Accept": "application/json"})
    response.raise_for_status()
    data = response.json()
    return data["title"], data["body"]["view"]["value"]

def get_child_pages(domain, email, api_token, page_id):
    children = []
    start, limit = 0, 50
    while True:
        url = f"https://{domain}.atlassian.net/wiki/rest/api/content/{page_id}/child/page"
        params = {"start": start, "limit": limit}
        response = requests.get(url, params=params, auth=(email, api_token), headers={"Accept": "application/json"})
        response.raise_for_status()
        
        results = response.json().get("results", [])
        if not results:
            break
            
        children.extend(results)
        if len(results) < limit:
            break
        start += limit
        
    return children

def export_page_tree(domain, email, api_token, page_id, current_dir, pbar, prefix=""):
    title, html_content = get_page_content(domain, email, api_token, page_id)
    safe_title = sanitize_name(title)
    
    prefixed_title = f"{prefix}{safe_title}" if prefix else safe_title
    os.makedirs(current_dir, exist_ok=True)
    
    pbar.set_postfix_str(f"Processing: {prefixed_title[:30]}")
    
    html_with_local_images = process_images_in_html(domain, email, api_token, html_content, current_dir)
    clean_html = preprocess_confluence_macros(html_with_local_images)
    md_content = converter.handle(clean_html)
    
    # --- NEW: Inject the original page title at the very top of the Markdown file ---
    md_content = f"# {title}\n\n" + md_content
    
    filepath = os.path.join(current_dir, f"{prefixed_title}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    pbar.update(1)

    child_pages = get_child_pages(domain, email, api_token, page_id)
    if child_pages:
        sub_dir = os.path.join(current_dir, prefixed_title)
        for index, child in enumerate(child_pages, start=1):
            child_prefix = f"{index:02d} - "
            export_page_tree(domain, email, api_token, child["id"], sub_dir, pbar, child_prefix)

# --- Main Execution ---
if __name__ == "__main__":
    try:
        DOMAIN, ROOT_PAGE_ID, EMAIL, API_TOKEN, BASE_OUTPUT_DIR = get_user_config()
        total_pages = get_total_page_count(DOMAIN, EMAIL, API_TOKEN, ROOT_PAGE_ID)
        
        with tqdm(total=total_pages, desc="Exporting Pages", unit="page", colour="green") as pbar:
            export_page_tree(DOMAIN, EMAIL, API_TOKEN, ROOT_PAGE_ID, BASE_OUTPUT_DIR, pbar)
            
            if pbar.n < pbar.total:
                pbar.update(pbar.total - pbar.n)
                
        print("\n🎉 Tree export complete!")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Export aborted by user. Partial files may remain in the output folder.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")