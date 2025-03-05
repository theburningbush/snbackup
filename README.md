[![GitHub Release](https://img.shields.io/github/v/release/theburningbush/snbackup)](https://pypi.org/project/snbackup/)
[![PyPI - Version](https://img.shields.io/pypi/v/snbackup)](https://pypi.org/project/snbackup/)
![Supported Python Versions](https://img.shields.io/pypi/pyversions/snbackup)
![OS support](https://img.shields.io/badge/OS-macOS%20Linux%20Windows-red) 

## CLI tool for wireless Supernote backups  
The primary goal of this project is to create a Python command line interface tool to wirelessly backup files (in particular Notes) from a Supernote device to a local computer. It doesn't require a user account, mobile app, or storing notes with third-party cloud providers. Its purpose is to archive device files for storage and safekeeping and doesn't attempt to export or convert notes to another format.  

This tool will *probably* work on any of the Supernote devices running the most up-to-date software. It works by using the builtin [Browse & Access](https://support.supernote.com/en_US/Tools-Features/wi-fi-transfer) feature available on the Supernote device. If Ratta changes how the Browse & Access feature works in future software updates, it is possible this tool will break.  

## Table of Contents
- [Setup](#setup-process)
- [Helpful Info](#helpful-information)
- [Uploading](#uploading)
- [Additional Options](#additional-options)
- [Tips](#tips)

### Setup Process:  

1. Install with `pip install snbackup` into your Python virtual environment. I prefer to use [pipx](https://pipx.pypa.io/stable/) to make it globally available on my system.  

2. Create a folder somewhere on your computer to store your Supernote backups.  

3. **IMPORTANT:** Create a file called `config.json`. This file is **_required_** to determine where to save your backups and where to access the device on the network. There are a couple options.  
    - Run `snbackup --setup` to run a prompted setup and supply your backup directory path, device IP address, and device port number. This will save your _config.json_ to a _.config_ folder within your home directory. The tool will look for this config file automatically when it runs.  
    - Manually create the _config.json_ file. Copy and paste from the example below and adjust as needed. Place this file in your chosen backup directory from step **2**.  

#### Example config.json (It must contain _save_dir_ and _device_url_):  
```json
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
}
```

4. Make sure the Supernote device is connected to WiFi with the Browse & Access feature turned on.  

5. There are three main ways to run the `snbackup` tool from your terminal or command line:  
    - This will first look for the required **_config.json_** from step **3** in the _.config_ folder (if you ran --setup) and then fallback to looking for the file in your current working directory:  
    `snbackup`  

    - Use the `-c` or `--config` flag to optionally specify the location of your **_config.json_** file:  
    `snbackup -c /the/path/to/config.json`  

    - You can also set the environment variable `SNBACKUP_CONF` which points to the location of the **_config.json_**. This allows you to run `snbackup` from anywhere without needing to specify the config file location. The exact command to set environment variables will depend on your operating system and terminal shell.  
    `export SNBACKUP_CONF="/path/to/config.json"`  

---

The `snbackup` tool will attempt to connect to your device and download _all files_ it finds to the `save_dir` directory specified in your **_config.json_**. The first run may take a few minutes or more as it will attempt to download everything; subsequent runs only download new or modified files.  

The tool will make a new directory within your chosen `save_dir` folder for today and save all files as they are found on the device:   

| **Supernote Path**    | **Local Save Directory**                                      |
|:------------------------|:--------------------------------------------------------------|
| `Note/Stuff/Ideas`      | `/save/directory/<YYYY-MM-DD>/Note/Stuff/Ideas.note`          |
| `Note/note with spaces` | `/save/directory/<YYYY-MM-DD>/Note/note+with+spaces.note`     |
| `Document/Random.pdf`   | `/save/directory/<YYYY-MM-DD>/Document/Random.pdf`            |

> Forward slashes `/` will be automatically converted to backslashes `\` on Windows systems.  

In addition to printing out information to the terminal, a `snbackup.log` file will be created alongside the backups in your `save_dir` directory.  

## Helpful Information:
By default, the tool will attempt to backup _everything_ on device. This includes files found in the Document folder, EXPORT folder, SCREENSHOT folder, etc. If you prefer to only download your notes which are found within the device's Note folder, use the command `snbackup --notes`.  

It does not currently attempt to download files from a micro sd card if one has been installed on the Supernote device.  

## Uploading:
You can also _upload_ files from your local computer with the `-u` flag to any of the following folders found on the Supernote device: **Note, Document, EXPORT, MyStyle, SCREENSHOT, INBOX**.  

For example, `snbackup -u Report.pdf` will upload the _Report.pdf_ file to the _Document_ folder by default.  

The command `snbackup -u /path/to/picture.jpg -d MyStyle` will upload the _picture.jpg_ file to the destination folder _MyStyle_.  

Additionally, you can specify multiple files at once separated by a space:  
`snbackup -u file1 file2 file3`  

If no destination is specified after the `-d` flag the device Document folder is used.   

#### Accepted file extensions for uploads:
| Category       | File Extensions                          |
|----------------|------------------------------------------|
| **Note/Text**  | `.note`, `.txt`                          |
| **Documents**  | `.pdf`, `.docx`, `.doc`, `.xps`          |
| **eBooks**     | `.epub`, `.mobi`, `.fb2`, `.cbz`         |
| **Images**     | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp` |


## Additional Options:
- Show all available command line options:  
`snbackup -h`  

- Inspect new files to be downloaded from device but do not download:  
`snbackup -i`  

- List out date and size information for backups found locally:  
`snbackup -ls`  

- The full backup flag will ignore previously saved backups and force the tool to redownload everything from device:  
`snbackup -f`  

- Remove all but the specified number of backups from your local backup directory. This example will keep only the 5 most recent backups and delete any older ones:  
`snbackup --cleanup 5`  

---  
### Additional configuration options can be set in the config.json file.  
```json
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
    "num_backups": 7,
    "cleanup": true,
    "truncate_log": 500
}
```  
In addition to the two required `save_dir` and `device_url` keys, this example config keeps only the 7 most recent backups and also prevents the log file from exceeding 500 lines. With `num_backups` and `cleanup` both set, the cleanup process will run automatically, and the `--cleanup` flag no longer needs to be specified.  

By default the _snbackup.log_ file only keeps the last 1000 lines. This number can be adjusted in the config.json file.  

### Tips:
- If your Supernote device's IP address changes often on your local network, consider assigning it a static IP address. This can typically be done by logging into your router and configuring it there.  

- Windows systems use the backslash character `\` as a separator for file paths. This is tricky for JSON files. Luckily, you can still use forward slashes `/` as shown in the example config.json even on Windows. However, you can also escape the backslashes if you prefer. For example your `save_dir` might look something like this `"C:\\Users\\devin\\My Documents\\Supernote"` on a Windows computer.  

- I made this tool for me because I'm slightly paranoid about losing my written notes, thoughts, plans, brain dumps, etc... I'm open to feedback if you experience bugs or have any ideas for improvements.  
