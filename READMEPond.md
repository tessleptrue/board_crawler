# Pond5 Collection Parser Setup Guide for Mac

This guide will help you set up and run the Pond5 Collection Parser on a brand new Mac computer. Follow these steps in order, and don't skip any steps!

## What You'll Need Before Starting
- A Mac computer
- Internet connection
- About 15-20 minutes of time

## Step 1: Install Python
1. Open your web browser and go to: https://www.python.org/downloads/
2. Click the big yellow "Download Python" button (it will automatically show the latest version for Mac)
3. Once downloaded, click the downloaded file (it will be named something like "python-3.x.x-macos11.pkg")
4. Follow the installation wizard:
   - Click "Continue" through the introduction
   - Click "Agree" to the license
   - Click "Install" (you might need to enter your Mac password)
   - Wait for the installation to complete
   - Click "Close" when finished

## Step 2: Install Required Tools
1. Open "Terminal" on your Mac
   - Click the magnifying glass icon in the top-right corner of your screen
   - Type "Terminal" and press Enter
2. Install Homebrew (a tool that helps install other programs) by copying and pasting this command:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Press Enter and follow any prompts (you might need to enter your password)
4. After Homebrew is installed, install curl by typing:
   ```
   brew install curl
   ```

## Step 3: Set Up Your Work Folder
1. Create a new folder on your Desktop called "pond5_parser":
   - Open Finder
   - Click on "Desktop" on the left
   - Right-click in the window and select "New Folder"
   - Name it "pond5_parser"

## Step 4: Create the Script File
1. Open TextEdit:
   - Click the magnifying glass icon in the top-right corner
   - Type "TextEdit" and press Enter
2. In TextEdit:
   - Click "Format" in the menu bar
   - Click "Make Plain Text"
3. Copy the entire Python script (the code you received)
4. Paste it into TextEdit
5. Click "File" → "Save As"
   - Navigate to the "pond5_parser" folder you created on your Desktop
   - Name the file "pond5_parser.py"
   - Make sure "Plain Text" is selected
   - Click "Save"

## Step 5: Run the Script
1. In Terminal, navigate to your script folder by typing:
   ```
   cd ~/Desktop/pond5_parser
   ```
2. Run the script by typing:
   ```
   python3 pond5_parser.py
   ```

## What to Expect
- When the script runs successfully, it will create a new file called "pond5_collection_data.csv" in the same folder
- This CSV file will contain the data from the Pond5 collection
- You can open this file with Numbers (Mac's spreadsheet app) or Excel to view the results

## Customizing the Script
To analyze different Pond5 collections:
1. Open the script in TextEdit
2. Find the section that looks like this:
   ```python
   urls = [
       "https://www.pond5.com/collections/6421444-judds-appalachia",
   ]
   ```
3. Replace the URL with the Pond5 collection URL you want to analyze
4. Save the file
5. Run the script again using the steps above

## Troubleshooting
If you get any errors:
- Make sure you're connected to the internet
- Double-check that you copied the entire script correctly
- Verify that you're in the correct folder in Terminal
- Try closing Terminal and opening it again

Need more help? The script creates a backup file with ".error" extension if something goes wrong, which might help identify the problem.

## Important Notes
- This script only works with public Pond5 collections
- The script may take a few minutes to run depending on the collection size
- Make sure you have permission to access and download the collection data
