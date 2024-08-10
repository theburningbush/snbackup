## Simple utility to backup notes from a Supernote device over WiFi

I created this cli tool to backup notes from my Supernote Nomad (A6 X2) over WiFi. No user accounts, mobile apps, or third party cloud service providers are necessary. It will *probably* work on any of the Supernote devices running the most up-to-date software.

Versioned releases are on [PyPi](https://pypi.org/) but the most up-to-date info is found on Github: [snbackup](https://github.com/theburningbush/snbackup)

The purpose is to download notes from a Supernote device and save them locally for backup and safe keeping. This is different than exporting notes as it does not attempt to convert notes to a different format. It's only meant to download the note files (with a `.note` extension) exactly as found on the device. If you are interested in converting your notes to PDF or PNG after downloading, see another project called [supernote-tool](https://github.com/jya-dev/supernote-tool).

It works by using the builtin [Browse & Access](https://support.supernote.com/en_US/Tools-Features/wi-fi-transfer) feature available on the Supernote device. This feature creates a small web server directly on the device and makes it possible to browse its files through a web browser. The Supernote device and your computer must be on the same local network.

### Steps:

1. Install Python 3.10 or newer along with pip

2. Setup your Python virtual environment and install with `pip install snbackup`

3. Create a folder on your computer to store your Supernote note backups

4. **IMPORTANT:** Create a file called `config.json` or edit the one provided with this project. This file is *required* to determine where to save your backups and where to access the device on the network. For example, I place my config file in the same directory as my backups.

### Example config.json:
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
}
```

> All note backups, metadata files, and logs are located under the **save_dir** directory.  

> It should work the same for Mac, Linux, or Windows machines. _Use forward slashes just like in the example config above even on Windows._

> The **device_url** needed will be displayed on the Supernote when Browse & Access is enabled. Use that URL from your device here.

5. Make sure the Supernote device is connected to WiFi with the Browse & Access feature turned on

6. There are two main ways to run the command from your terminal or command line:
    - This will look for config.json in your current working directory  
    `snbackup` 

    - This optionally specifies the location of the config.json file  
    `snbackup -c /the/path/to/config.json`  

The first run may take a few minutes or more as it will attempt to download all notes. Subsequent runs only download new or modified notes; this greatly speeds up future backups.

You can always force a full backup of all notes by running `snbackup -f` or `snbackup --full`

The notes are stored *as is* under your local save directory setup in the `config.json` file.  

> If a note called `Ideas` is found under a folder called `Stuff` on your Supernote device, it will be backed up locally as `/Users/devin/Documents/Supernote/<YYYY-MM-DD>/Note/Stuff/Ideas.note`  

> On a Windows machine this would translate to `C:\Users\devin\Documents\Supernote\<YYYY-MM-DD>\Note\Stuff\Ideas.note`

> Downloaded notes are separated by days in the format `YYYY-MM-DD` within your **save_dir** directory
  
## Some additionl options:
- Show all available command line options  
`snbackup -h`

- Inspect new notes to be downloaded from device and quit without downloading  
`snbackup -i`

- **EXPERIMENTAL:** Purge old backups from your local **save_dir** directory and keeps only the number requested here. In this example, all but the 5 most recent backups are removed.   
`snbackup -p 5`

- **EXPERIMENTAL:** You can optionally add **num_backups** to your `config.json` file to have it automatically remove old backups from your backup directory without needing to specify using the `-p` flag. **Be advised, this deletes your old backups! Handle with care.**  
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/",
    "num_backups": 3
}
```

### Future plans:
- Add a first time setup option to build config.json file
- Persist note metadata in sqlite instead of json file
- Add note validation option to ensure local and remote notes are identical
- A restore device feature to bulk move local backups back to device
