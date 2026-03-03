# Confluence to Markdown Exporter

This tool automatically downloads a Confluence page and all of its nested subpages, converting them into cleanly formatted Markdown (`.md`) files. It also downloads all attached images, fixes the image links, and preserves your Confluence tree structure with numbered folders.

## 📋 Prerequisites

Before running the exporter, you need to gather three pieces of information:

**1. Your Atlassian API Token**
You must generate a personal API token to allow the tool to read your Confluence pages.
* Go to: [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
* Click **Create API token**.
* Give it a memorable label (e.g., "Markdown Exporter") and click **Create**.
* **Copy the token immediately** and save it somewhere safe. You will not be able to see it again!

**2. Your Confluence Domain Prefix**
This is the first part of your company's Confluence URL. 
* If your Confluence URL is `https://acme-corp.atlassian.net/...`, your domain prefix is **`acme-corp`**.

**3. The Root Page ID**
This is the unique ID of the top-level page you want to export. The tool will export this page and *everything* nested underneath it.
* Go to the Confluence page in your web browser.
* Look at the URL. The Page ID is the long string of numbers at the end.
* Example: In `.../wiki/spaces/ENG/pages/123456789/API+Docs`, the Page ID is **`123456789`**.

---

## 🚀 Downloading and Installing

This tool is a standalone portable executable. There is no installation process required!

1. Download the `Confluence_Exporter.exe` file provided by your team.
2. Place the `.exe` file into an empty folder on your computer where you want your exported documentation to be saved.

---

## 💻 Running the Exporter

1. **Double-click** the `Confluence_Exporter.exe` file to run it. (Alternatively, you can run it via Command Prompt or PowerShell).
2. The terminal window will open and prompt you for the following:
   * **Domain prefix** (e.g., `acme-corp`)
   * **Atlassian Email** (the email you use to log into Confluence)
   * **API Token** (*Note: Your keystrokes will be hidden for security when you paste your token. Just right-click to paste and hit Enter.*)
3. You will be asked if you want to save these credentials. If you type `y`, it will create a small `confluence_creds.json` file in the same folder. Next time you run the tool, you won't have to type your email or token again!
4. Finally, enter the **Root Page ID** you want to export, and choose a name for the output folder.

### Stopping the Export
If you ever need to cancel the download midway through, click inside the terminal window and press **`Ctrl + C`**. The tool will safely abort the process.