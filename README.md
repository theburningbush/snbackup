## Command line utility to wirelessly backup files from a Supernote device

The primary goal of this project is to create a CLI tool to wirelessly backup files (in particular notes) from a Supernote device to a local computer. It doesn't require a user account, mobile app, or storing notes with third-party cloud providers. Its purpose is to archive device files for storage and safekeeping and doesn't attempt to export or convert notes to another format. 

This tool will *probably* work on any of the Supernote devices running the most up-to-date software. It works by using the builtin [Browse & Access](https://support.supernote.com/en_US/Tools-Features/wi-fi-transfer) feature available on the Supernote device. If Ratta changes how the Browse & Access feature works in future software updates, it is possible this application will break.  

Versioned releases are on [PyPi](https://pypi.org/) but the most up-to-date info is found on Github: [snbackup](https://github.com/theburningbush/snbackup)  

### Setup Process:

1. Install Python 3.10 or newer along with pip

2. Setup your Python virtual environment and install with `pip install snbackup`. You could also use `pipx` or `uv` to make it globally available on your system.

3. Create a folder somewhere on your computer to store your Supernote backups.

4. **IMPORTANT:** Create a file called `config.json` or edit and use the one provided with this project. This file is **_required_** to determine where to save your backups and where to access the device on the network. For example, I place my config file in the same directory as my backups.  

#### Example config.json (must contain _save_dir_ and _device_url_):  
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
}
```

5. Make sure the Supernote device is connected to WiFi with the Browse & Access feature turned on  

6. There are three main ways to run the `snbackup` tool from your terminal or command line:
    - This will look for the required **_config.json_** from step **4** in your current working directory:  
    `snbackup` 

    - This optionally specifies the location of the required **_config.json_** file:  
    `snbackup -c /the/path/to/config.json`  

    - You can also set the environment variable `SNBACKUP_CONF` which points to the location of the **_config.json_** and then run `snbackup` from any directory without needing to specify the config location.  
    `export SNBACKUP_CONF="/path/to/config.json"`

---

The `snbackup` tool will attempt to connect to your device and download _all files_ it finds to the `save_dir` directory specified in your **_config.json_**. The first run may take a few minutes or more as it will attempt to download everything; subsequent runs only download new or modified files.  

The tool will make a new directory within your `save_dir` folder for today and save all files as they are found on the device. For example, if a note titled `Ideas` is stored within your `Stuff` folder, it will be backed up locally as `/your/chosen/directory/<YYYY-MM-DD>/Note/Stuff/Ideas.note`. This example would translate to `C:\your\chosen\directory\<YYYY-MM-DD>\Note\Stuff\Ideas.note` on a Windows computer.

Everything `snbackup` does will be printed out to your terminal as well as logged to the `snbackup.log` file also stored in your `save_dir` directory.  

## Helpful Information:
By default, the tool will attempt to backup _everything_ on device. This includes files found in the Document folder, EXPORT folder, SCREENSHOT folder, etc. If you prefer to only download your notes which are found within the device's Note folder, use the command `snbackup --notes`.  

It does not currently attempt to download files from a micro sd card if one has been installed on the Supernote device.  

## Uploading:
You can also _upload_ files from your local computer with the `-u` flag to any of the following folders found on the Supernote device: **Note, Document, EXPORT, MyStyle, SCREENSHOT, INBOX**.  

For example, `snbackup -u Report.pdf` will upload the _Report.pdf_ file to the _Document_ folder by default. The command `snbackup -u /path/to/picture.jpg -d MyStyle` will upload the _picture.jpg_ file to the destination folder _MyStyle_.  

Additionally, you can specify multiple files at once separated by a space:  
`snbackup -u file1 file2 file3`  

If no destination is specified after the `-d` flag the device Document folder is used.  

The accepted file formats for the upload are **.note, .pdf, .epub, .docx, .doc, .txt, .png, .jpg, .jpeg, .bmp, .webp, .cbz, .fb2, .xps, .mobi**  

## Additional Options:
- Show all available command line options:  
`snbackup -h`  

- Inspect new files to be downloaded from device and but do not download:  
`snbackup -i`  

- The full backup flag will ignore previously saved backups and force the tool to redownload everything from device:  
`snbackup -f`

- Remove all but the specified number of backups from your local backup directory. This example will keep only the 5 most recent backups and delete any older ones:  
`snbackup --cleanup 5`

- Print program version:  
`snbackup -v`  

---  
There are additional configuration options that can be set in the config.json file.  
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
    "num_backups": 7,
    "cleanup": true,
    "truncate_log": 500
}
```
In addition to the two required `save_dir` and `device_url` keys, this example config keeps only the 7 most recent backups and also prevents the program's log file from exceeding 500 lines. With `num_backups` and `cleanup` both set, the cleanup process will run automatically, and the `--cleanup` flag no longer needs to be specified.  

By default the _snbackup.log_ file only keeps the last 1000 lines. This number can be adjusted in the config.json file.

### Tips:
- If your Supernote device's IP address changes often on your local network, consider assigning it a static IP address. This can typically be done by logging into your router and configuring it there.  

- Windows systems use the backslash character `\` as a separator for file paths. This is tricky for JSON files. Luckily, you can still use forward slashes `/` as shown in the example config.json even on Windows. However, you can also escape the backslashes if you prefer. For example your `save_dir` might look something like this `"C:\\Users\\devin\\My Documents\\Supernote"` on a Windows computer.  
