import os
import sys
import re
import json
import getpass
import requests
import html2text
import urllib.parse
import time
import shutil  # Added for window autosizing
from bs4 import BeautifulSoup
from tqdm import tqdm
import subprocess
import platform

# --- Setup Markdown Converter ---
converter = html2text.HTML2Text()
converter.ignore_links = False
converter.ignore_images = False
converter.body_width = 0

def get_center_header(text, char="="):
    """Dynamically sizes headers to the terminal width."""
    columns, _ = shutil.get_terminal_size()
    return text.center(columns, char)

def draw_line(char="-"):
    """Draws a line across the full terminal width."""
    columns, _ = shutil.get_terminal_size()
    return char * columns

def sanitize_name(name):
    """Replaces spaces with hyphens and removes illegal characters."""
    name = name.replace("/", "-").replace("\\", "-").replace(" ", "-")
    return re.sub(r'[*?:"<>|]', "", name).strip()

def get_user_config(base_path):
    """Handles authentication and returns credentials with initial defaults."""
    print(get_center_header(" Confluence to Markdown Exporter ", "="))
    print("(Press Ctrl+C at any time to cancel)".center(shutil.get_terminal_size()[0]))
    print()
    
    cred_file = os.path.join(base_path, "confluence_creds.json")
    domain, email, api_token = "", "", ""
    
    # Initial defaults for the first run of the loop
    default_root_page_id = "2093252612" 
    default_output_dir = "confluence_export"
    
    if os.path.exists(cred_file):
        try:
            with open(cred_file, "r") as f:
                creds = json.load(f)
                domain = creds.get("domain", "")
                email = creds.get("email", "")
                api_token = creds.get("api_token", "")
            print(f" ✅ Loaded credentials for {email}")
        except Exception:
            pass

    needs_saving = False
    if not domain:
        raw_domain = input("Enter Confluence domain prefix: ").strip()
        domain = raw_domain.replace("https://", "").replace(".atlassian.net", "")
        needs_saving = True
    if not email:
        email = input("Enter your Atlassian email: ").strip()
        needs_saving = True
    if not api_token:
        api_token = getpass.getpass("Enter your API Token (hidden): ").strip()
        needs_saving = True

    if needs_saving:
        save = input("\nSave these credentials for next time? (y/n): ").strip().lower()
        if save == 'y':
            with open(cred_file, "w") as f:
                json.dump({"domain": domain, "email": email, "api_token": api_token}, f, indent=4)
            print(" 🔒 Credentials saved.")
    
    print(draw_line())
    
    # We now return the credentials and the default values for the UI loop
    return domain, default_root_page_id, email, api_token, default_output_dir

def preprocess_confluence_macros(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for panel in soup.find_all('div', class_='confluence-information-macro'):
        body = panel.find('div', class_='confluence-information-macro-body')
        if body:
            panel_type = "Note"
            classes = panel.get('class', [])
            if 'confluence-information-macro-warning' in classes:
                panel_type = "Warning"
            elif 'confluence-information-macro-information' in classes:
                panel_type = "Info"
            blockquote = soup.new_tag('blockquote')
            blockquote.append(BeautifulSoup(f"<strong>{panel_type}:</strong><br/>", 'html.parser'))
            blockquote.extend(body.contents)
            panel.replace_with(blockquote)
    return str(soup)

def process_images(domain, email, api_token, html_content, current_dir):
    soup = BeautifulSoup(html_content, 'html.parser')
    images_dir = os.path.join(current_dir, "images")
    created_img_dir = False
    for img in soup.find_all('img'):
        src = img.get('data-image-src') or img.get('src')
        if not src: continue
        full_url = f"https://{domain}.atlassian.net{src}" if src.startswith('/') else src
        fname = sanitize_name(img.get('data-linked-resource-default-alias') or 
                             os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(full_url).path)))
        if "." not in fname: fname += ".png"
        if not created_img_dir:
            os.makedirs(images_dir, exist_ok=True)
            created_img_dir = True
        try:
            res = requests.get(full_url, auth=(email, api_token), timeout=10)
            if res.status_code == 200:
                with open(os.path.join(images_dir, fname), "wb") as f:
                    f.write(res.content)
                img['src'] = f"images/{fname}"
        except: pass 
    return str(soup)

def get_page_content(domain, email, api_token, page_id):
    url = f"https://{domain}.atlassian.net/wiki/rest/api/content/{page_id}?expand=body.view"
    response = requests.get(url, auth=(email, api_token), timeout=15)
    response.raise_for_status()
    data = response.json()
    return data["title"], data["body"]["view"]["value"]

def get_child_pages(domain, email, api_token, page_id):
    children = []
    start, limit = 0, 50
    while True:
        url = f"https://{domain}.atlassian.net/wiki/rest/api/content/{page_id}/child/page"
        params = {"start": start, "limit": limit}
        response = requests.get(url, params=params, auth=(email, api_token))
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results: break
        children.extend(results)
        if len(results) < limit: break
        start += limit
    return children

def export_page_tree(domain, email, api_token, page_id, current_dir, pbar, prefix=""):
    try:
        title, html = get_page_content(domain, email, api_token, page_id)
        safe_title = sanitize_name(title)
        prefixed_title = f"{prefix}{safe_title}" if prefix else safe_title
        os.makedirs(current_dir, exist_ok=True)
        
        pbar.set_description(f"Exporting: {prefixed_title[:25]}")
        
        html_with_images = process_images(domain, email, api_token, html, current_dir)
        clean_html = preprocess_confluence_macros(html_with_images)
        md_content = f"# {title}\n\n" + converter.handle(clean_html)
        
        with open(os.path.join(current_dir, f"{prefixed_title}.md"), "w", encoding="utf-8") as f:
            f.write(md_content)
        pbar.update(1)

        child_pages = get_child_pages(domain, email, api_token, page_id)
        if child_pages:
            sub_dir = os.path.join(current_dir, prefixed_title)
            for index, child in enumerate(child_pages, start=1):
                export_page_tree(domain, email, api_token, child["id"], sub_dir, pbar, f"{index:02d}-")
    except: pbar.update(1)

def run_main():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    session_history = []
    print(get_center_header(" Confluence Markdown Exporter ", "="))

    try:
        dom, default_rid, eml, tok, default_out = get_user_config(base_path)
        
        while True:
            print("\n" + "-"*40)
            rid = input(f"Enter Confluence Page ID: ").strip() or default_rid
            out = input(f"Enter Output Folder Name: ").strip() or default_out
            
            full_out_path = os.path.join(base_path, out)
            
            # Re-insert the "Calculating" message here for better feedback
            print("\n" + "Calculating total pages...".center(shutil.get_terminal_size()[0]))

            try:
                search_url = f"https://{dom}.atlassian.net/wiki/rest/api/search"
                params = {"cql": f"ancestor={rid} or id={rid}", "limit": 1}
                response = requests.get(search_url, params=params, auth=(eml, tok))
                response.raise_for_status()
                total = response.json().get("totalSize", 1)
                
                cols, _ = shutil.get_terminal_size()
                with tqdm(total=total, unit="page", colour="green", ncols=min(cols, 100)) as pbar:
                    export_page_tree(dom, eml, tok, rid, full_out_path, pbar)
                    if pbar.n < pbar.total: 
                        pbar.update(pbar.total - pbar.n)
                
                print(f"\n🎉 SUCCESS! Saved to: {full_out_path}")
                session_history.append(full_out_path)
                
                # Update defaults for next loop iteration
                default_rid = rid
            
            except Exception as e:
                print(f"\n❌ Export Error: {e}")

            print("\n" + "-"*40)
            choice = input("Would you like to export another page? (y/n): ").lower().strip()
            if choice != 'y':
                break

    except KeyboardInterrupt:
        print("\n🛑 Operation aborted by user.")
    except Exception as e:
        print(f"\n❌ System Error: {e}")

    # FINAL SUMMARY AND FINDER PROMPT
    if session_history:
        print("\n" + get_center_header(" SESSION SUMMARY ", "="))
        print(f"Successfully exported {len(session_history)} page tree(s):")
        for path in session_history:
            print(f" 📁 {path}")
        
        # Ask to open the last exported folder at the very end
        print("\n" + "-"*40)
        open_choice = input("Would you like to open the last export folder in Finder? (y/n): ").lower().strip()
        if open_choice == 'y':
            subprocess.run(["open", session_history[-1]])

    print("\n" + get_center_header(" Thank you for using the tool ", "="))
    print("Process finished. You may now close this window.".center(shutil.get_terminal_size()[0]))
    print()
    
    # Standard graceful exit sequence
    sys.stdout.flush()
    sys.stderr.flush()
    
    # This specific exit code signals to macOS that the process is finished
    # and prevents the terminal from reporting a crash/error.
    sys.exit(0)

if __name__ == "__main__":
    run_main()   




    