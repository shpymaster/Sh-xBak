# Sh-xBak.py

## Description
This Python program performs flexible backup operations on Windows platform.

Backup procedure is realised as creation/update of RAR format archive, using WinRAR as a backup engine.
Each backup job should be preliminary configured in JSON configuration file.
Configuration file contains unlimited number of configurations necessary to perform the backup tasks:
definitions of jobs and job packages, paths to .EXE programs and work destinations, definitions of work-modes and program switches. Each backup job is a list of one or multiple individually defined packages (RAR archives).

All core events are registered in the LOG log-file. All execution errors are registered in ERR error-file. Day/time stamp of last execution of each job package is registered in the STAT statistics JSON file (for future automation).

Currently the following work-modes are avaialable:
- Backup archive located at the local drive (i.e. drive already mounted/connected to the system).
- Backup archive located at the encrypted VeraCrypt volume, which should be mounted/unmounted during the job execution.
- Backup archive located at the netowrk location, which should be mounted/dismounted during the job execution (like WebDAV accessible netowrk volume). This mode is heavily dependent on network capacity/availability and may work with serious issues.
- Special mode for checking (1) size of LOG file and (2) existence of ERR file. If LOG size exceeds a pre-defined volume or if ERR file exists, the appropriate erroe message will displayed.

## Usage
**Pythonw.exe Sh-xBak.py -j jobname -p archive_password [-opt_switch opt_value ....]**

*All optional switches are listed in the JSON settings file in the "JobSwitches" section.*

## Dependencies
This program uses library modules:
- sh_messagebox
- sh_sysutil