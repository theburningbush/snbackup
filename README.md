## Tool to backup notes from Supernote device

I created this to backup notes from my Supernote Nomad (A6 X2). It will *probably* work on any of the Supernote devices running the most up-to-date software.

**Github Repo: [snbackup](https://github.com/theburningbush/snbackup)**

The purpose is to download notes from a Supernote device and save them locally for backup and safe keeping. This is different than exporting notes as it does not attempt to convert notes to a different format. It's only meant to download the note files (with a .note extension) exactly as they are found on the device. If you are interested in converting your notes to PDF or PNG after they've been downloaded, see another project called [supernote-tool](https://github.com/jya-dev/supernote-tool).

It works by using the builtin [**Browse & Access**](https://support.supernote.com/en_US/Tools-Features/wi-fi-transfer) feature available on the Supernote device. This feature creates a small http web server directly on the device and makes it possible to browse its files through a web browser. The Supernote device and your computer must be on the same network.

### Steps:

1. Install Python 3.10 or newer alongside pip

2. Setup your Python virtual environment and install with `pip install snbackup`

3. Create a folder on your computer to store your Supernote backups

4. **IMPORTANT**: Edit the provided example `config.json` file and place it into the same directory where you want your backups to be saved.

### Example config.json:
```
{
    "save_dir": "/Users/devin/Documents/Supernote",
    "device_url": "http://192.168.1.105:8089/"
}
```

All backups, configuration files, and logs for **snbackup** are located under this **save_dir** location.  

Works the same for Mac or PC. The example above on a Windows machine would automatically translate to `C:\Users\devin\Documents\Supernote`

The **device_url** needed will be displayed on the Supernote when Browse & Access is enabled. Use that URL from your device here.

5. Make sure the Supernote device is connected to WiFi with the Browse & Access feature turned on

6. Run `snbackup` from your command line or terminal to start the process. This could take a few minutes depending on how many notes you have and how big they are. The first run is a full backup, but subsequent runs only backup the notes that have been modified since the last backup; this greatly speeds up future backups. You can force a full backup of all notes by running `snbackup -f` or `snbackup --full`

The notes are stored "as is" under your local save directory.  
So if a note called `Ideas` lives inside a folder called `Stuff` on your Supernote device, it will be stored locally as `/Users/devin/Documents/Supernote/Note/Stuff/Ideas.note` or as `C:\Users\devin\Documents\Supernote\Stuff\Ideas.note` on Windows.
  

### Future plans:
- Add a proper first time setup option
- Add archive or cleanup feature to remove old backups
- Persist metadata info in sqlite instead of json file
- Add note validation option to ensure local and remote notes are identical
- A restore device feature to bulk move local backups back to device
- Probably should build some unit tests...
