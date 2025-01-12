# Getty Board Parser - Installation and Usage Guide

This guide will help you set up and run the Getty Board Parser on your Mac computer, even if you've never used command-line tools before.

## Prerequisites

Before you begin, make sure your Mac is running the latest version of macOS. You can check this by clicking on the Apple menu (🍎) in the top-left corner and selecting "About This Mac."

## Step 1: Install Required Software

1. **Install Homebrew**
   - Open "Terminal" (you can find it using Spotlight Search - press Command+Space and type "Terminal")
   - Copy and paste this command into Terminal:
     ```
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
   - Press Enter and follow any prompts
   - When asked for your password, type it (note: you won't see characters as you type)

2. **Install Python**
   - In Terminal, type:
     ```
     brew install python
     ```
   - Press Enter and wait for the installation to complete

3. **Install curl**
   - In Terminal, type:
     ```
     brew install curl
     ```
   - Press Enter and wait for the installation to complete

## Step 2: Set Up Your Project

1. **Create a new folder for your project**
   - Open Finder
   - Click on "Documents" in the sidebar
   - Right-click in the window and select "New Folder"
   - Name it "GettyParser"

2. **Save the script**
   - Create a new text file using TextEdit
   - Go to TextEdit > Preferences and select "Plain Text"
   - Copy the entire Python script
   - Paste it into TextEdit
   - Save the file as `getty_parser.py` in your GettyParser folder
   - Make sure to remove the `.txt` extension if it's automatically added

## Step 3: Configure the Script

1. **Open the script**
   - Right-click on `getty_parser.py`
   - Select "Open With" > TextEdit

2. **Modify the URLs**
   - Find the `urls` section near the bottom of the file
   - Replace the example URL with your Getty board URLs
   - For example:
     ```python
     urls = [
         "https://www.gettyimages.com/collaboration/boards/your-board-url-here",
         "https://www.gettyimages.com/collaboration/boards/another-board-url"
     ]
     ```

## Step 4: Run the Script

1. **Open Terminal**
   - Press Command+Space
   - Type "Terminal"
   - Press Enter

2. **Navigate to your project folder**
   - Type:
     ```
     cd Documents/GettyParser
     ```
   - Press Enter

3. **Run the script**
   - Type:
     ```
     python3 getty_parser.py
     ```
   - Press Enter

## Output and Results

- The script will create a file called `board_data.csv` in your GettyParser folder
- You can open this file with Numbers (Mac's spreadsheet app) or Microsoft Excel
- The file will contain information about all the assets from your Getty boards

## Troubleshooting

If you encounter any errors:

1. **Check your internet connection**
   - Make sure you're connected to the internet
   - Try opening the Getty board URLs in your web browser

2. **Verify the URLs**
   - Make sure the Getty board URLs are correct
   - Ensure you have access to these boards

3. **Common Error Messages**
   - "Permission denied": You might need to run the command with `sudo python3 getty_parser.py`
   - "No such file or directory": Make sure you're in the correct folder in Terminal

## Need Help?

If you're still having trouble:
- Double-check that you've followed all steps exactly
- Make sure all the URLs are correct and accessible
- Try restarting your computer and running the script again

## Notes

- The script will automatically skip any duplicate entries
- By default, it excludes certain private information like release info and user IDs
- The CSV file can be opened in any spreadsheet program
