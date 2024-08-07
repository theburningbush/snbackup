## Simple utility to backup notes from a Supernote device over WiFi

I created this cli tool to backup notes from my Supernote Nomad (A6 X2) over WiFi. No accounts or third party cloud service providers are necessary. It will *probably* work on any of the Supernote devices running the most up-to-date software.

**Github repo for [snbackup](https://github.com/theburningbush/snbackup)**

The purpose is to download notes from a Supernote device and save them locally for backup and safe keeping. This is different than exporting notes as it does not attempt to convert notes to a different format. It's only meant to download the note files (with a `.note` extension) exactly as they are found on the device. If you are interested in converting your notes to PDF or PNG after downloading, see another project called [supernote-tool](https://github.com/jya-dev/supernote-tool).

It works by using the builtin [**Browse & Access**](https://support.supernote.com/en_US/Tools-Features/wi-fi-transfer) feature available on the Supernote device. This feature creates a small web server directly on the device and makes it possible to browse its files through a web browser. The Supernote device and your computer must be on the same local network.

### Steps:

1. Install Python 3.10 or newer along with pip

2. Setup your Python virtual environment and install with `pip install snbackup`

3. Create a folder on your computer to store your Supernote note backups

4. **IMPORTANT:** Create a file called ``` or edit the one provided with this project. This file is *required* to determine where to save your backups and where to access the device on the network. For example I place my config file in the same directory as my backups.

### Example `:
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
}
```

> All note backups, metadata files, and logs for **snbackup** are located under the **save_dir** location.  

> Should work the same for Mac or PC. Use the forward slashes just like in the example above even on Windows.

> The **device_url** needed will be displayed on the Supernote when Browse & Access is enabled. Use that URL from your device here.

5. Make sure the Supernote device is connected to WiFi with the Browse & Access feature turned on

6. There are two ways to run the command from your terminal or command line:
    - `snbackup` 
        > *This will look for the ` in your current working directory*
    - `snbackup -c /the/path/to/``
        > *This optionally specifies the location of the `*  

The first run may take a few minutes depending on how big your notes are and how many you have on the device. The first backup is a full backup, but subsequent runs only backup the notes that have been modified since the last backup; this greatly speeds up future backups.

You can also force a full backup of all notes by running `snbackup -f` or `snbackup --full`

The notes are stored *as is* under your local save directory setup in the `config.json` file. 
If a note called `Ideas` lives inside a folder called `Stuff` on your Supernote device, it will be stored locally as `/Users/devin/Documents/Supernote/<YYYY-MM-DD>/Note/Stuff/Ideas.note` or translated to `C:\Users\devin\Documents\Supernote\<YYYY-MM-DD>\Note\Stuff\Ideas.note` on Windows.
  

### Future plans:
- Add a proper first time setup option
- Add archive or cleanup feature to remove old backups
- Persist note metadata in sqlite instead of json file
- Add note validation option to ensure local and remote notes are identical
- A restore device feature to bulk move local backups back to device
