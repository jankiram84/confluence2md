# Confluence to Markdown Exporter

A professional CLI tool designed to export entire Confluence page trees into structured Markdown. It preserves parent-child hierarchies, handles image localization, and converts complex Confluence macros into clean Markdown formatting.

## 🚀 Description
This tool automates the tedious process of migrating documentation out of Confluence. It recursively downloads a parent page and all its nested children, organizing them into a hierarchical folder structure. 

**Key Features:**
* **Hierarchical Numbering**: Files are prefixed (e.g., `01-`, `02-`) to maintain the original Confluence order.
* **Macro Processing**: Automatically transforms Confluence "Info", "Note", and "Warning" panels into bolded blockquotes.
* **Image Localization**: Downloads embedded images to a local `images/` directory and updates Markdown links to point to those local files.
* **Clean UI**: Features a dynamic progress bar and a terminal interface that auto-sizes to your window.

## 📋 Prerequisites

Before running the exporter, you need to gather the following information:

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

1. Download the `Confluence_Exporter` file available in the `confluence2md_v1.0.0' release from the **Releases** section.
2. If macOS prevents it from opening because it is from an "unidentified developer":
   * **Right-click** the file and select **Open**.
3. Alternatively, open your Terminal, type `chmod +x `, drag the file into the terminal window, and hit **Enter**. Then you can double-click it to run.

---

## 💻 Running the Exporter

1. **Double-click** the `Confluence Exporter` file to run it.
2. The terminal window will open and prompt you for the following:
   * **Domain prefix** (e.g., `acme-corp`)
   * **Atlassian Email** (the email you use to log into Confluence)
   * **API Token** (*Note: Your keystrokes will be hidden for security when you paste your token. Just right-click to paste and hit Enter.*)
3. You will be asked if you want to save these credentials. If you type `y`, it will create a small `confluence_creds.json` file in the same folder. Next time you run the tool, you won't have to type your email or token again!
**Note**: For security, never share your confluence_creds.json file, as it contains your API token.
4. Finally, enter the **Root Page ID** you want to export, and choose a name for the output folder.

**Note on Closing**: Once the export reaches 100%, the terminal will display [Process completed]. You can safely close the window by pressing Cmd + W or clicking the red "X" in the corner.

### Stopping the Export
If you ever need to cancel the download midway through, click inside the terminal window and press **`Ctrl + C`**. The tool will safely abort the process.

## 🤖 GitHub Automation

This repository is configured with GitHub Actions to ensure the executable is always up-to-date with the latest code improvements.

* **Automatic Updates**: Every time the source code is updated and a new version tag (e.g., v1.0.1) is pushed, a new executable is automatically built and attached to the Releases page.

* **User Benefit**: Users can always find the most stable, pre-compiled version of the tool under the "Releases" sidebar on the right side of the GitHub repository page without ever needing to touch the source code.

## ⚠️ Common Errors & Troubleshooting

* 401 Unauthorized: This usually means your Email or API Token is incorrect. Double-check your Atlassian credentials.

* 403 Forbidden: Your account may not have "Export" or "View" permissions for the specific Page ID you provided.

* EOFError: This occurs if the terminal window is closed or disconnected while the tool is waiting for your input.

* Missing Images: Ensure you have permission to view attachments on the Confluence pages.

* Process Finished/Looping: On macOS, if the terminal window stays open but the script restarts, the tool is designed to exit gracefully after a short delay to prevent logic loops.



