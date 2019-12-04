''' -----------------------
program: Sh-xBak
version: 1.1.20191022

usage: Sh-xBak -j jobname -p archive_password [-opt_switch opt_value ....]
optional swithes are listed in the JSON settings file
------------------------'''

import json
import os
import os.path
import sys
import time
import subprocess
import sh_messagebox as shmb
import sh_sysutil as shsu

jobExitEvent = {
    0: "Sh-xBak Job Completed",
    1: "Error opening Settings File",
    2: "Error opening Job: ",
    3: "Mode not realised yet",
    4: "Check Log & Error files",
    5: "Program file not found",
    6: "Job option not defined",
    7: "Error running program",
    8: "Error mounting VCrypt volume",
    9: "Error mounting network drive",
    10: "Error dismounting network drive"
}

KEY_JOB_NAME = "-j"
KEY_ARCHIVE_PSW = "-p"
KEY_DRIVE_LETTER = "-d"
KEY_NET_SERVER_NAME = "-sn"
KEY_NET_SERVER_ACCOUNT = "-sa"
KEY_NET_ACCOUNT_PSW = "-sp"
KEY_NET_DISCONNECT_DELAY_MINUTES = "-sd"
KEY_VOLUME_NAME = "-vn"
KEY_VOLUME_PSW = "-vp"

PROGRAM_NAME = "Sh-xBak"
PROGRAM_VER = "1.1"
EXIT_DELAY = 10000 #msec
PROGRAM_ICON = (__file__[:-3] + ".ico")
FILE_SETTINGS = (__file__[:-3] + ".json")
FILE_STATISTICS = (__file__[:-3] + "-stat.json")
FILE_LOG = (__file__[:-3] +  ".log")
FILE_ERROR = (__file__[:-3] +  ".err")
DIR_INCLUDE = os.path.dirname(__file__) + "\\Include\\"
MAX_LOG_SIZE = 30000 #bytes
VCRYPT_WAIT_SECONDS = 90 #sec
vcSwitchesMount = "/a /h n /m ts /m rm /q /s"
vcSwitchesDismount = "/q /s /d /f"
rarCommand = "U -r -ep2 -ri1 -rr -ibck -dh -as -m5 -md32m -msrar -mszip "

def script_exit(seErrorCode, seExitCode, seString=None):
    msgTitle = PROGRAM_NAME
    msgText = jobExitEvent[seExitCode] + (": " + seString if seString else "")
    eventText = msgText
    if seErrorCode:
        msgTitle += " ERROR" if seErrorCode else ""
        eventText = "ERROR: " + eventText + ". Exit code: " + str(seExitCode)
        msgText = "ERROR:\n" + msgText + "\nExit coode: " + str(seExitCode)
    log_event(eventText, seErrorCode if seErrorCode else None)
    shmb.shShowMessage(0, msgTitle, msgText, 
        shmb.SH_MESSAGE_ERROR if seErrorCode else shmb.SH_MESSAGE_INFO, EXIT_DELAY, PROGRAM_ICON)
    sys.exit(seExitCode)

def log_event(leEvent, leErrorCode=None):
    s = get_time_stamp() + " : " + leEvent + "\n"  
    with open(FILE_LOG, "a") as logFile:
        logFile.write(s)    
    if leErrorCode:
        with open(FILE_ERROR, "a") as errorFile:
            errorFile.write(s)
    return None

def check_log_error_files():
    strMessage = ""
    errCount = 0
    log_event("Routine started: Check Log and Error files")
    logSize = os.stat(FILE_LOG).st_size
    if logSize > MAX_LOG_SIZE:
        strMessage += "Log File too long (" + str(logSize) +"). "
        errCount += 1
    try:
        os.stat(FILE_ERROR)
        strMessage += "ERROR File Detected"
        errCount += 1
    except:
        pass  
    if errCount:
        script_exit(1, 4, strMessage)
    script_exit(0, 0)

def get_job_option(optName):
    optVal = argDict.get_option(optName)
    if not optVal:
        try:
            optVal = jobRecord[settingsData["JobSwitches"][optName]]
        except:
            script_exit(1, 6, optName)
    return optVal

def get_time_stamp():   
    return (time.strftime("%Y.%m.%d_%H:%M:%S", time.localtime()))

def update_statistics(packageName):
        with open(FILE_STATISTICS, "r") as statistics_file:
            statisticsData = json.load(statistics_file)
        statRecord = None
        for rec in statisticsData["PackageStatistics"]:
            if rec["Package"] == packageName: 
                statRecord = rec
                rec["LastBackup"] = get_time_stamp()
                break
        else:
            statRecord = {}
            statRecord["Package"] = packageName
            statRecord["LastBackup"] = get_time_stamp()
            statisticsData["PackageStatistics"].append(statRecord)
        with open(FILE_STATISTICS, "w") as statistics_file:
            json.dump(statisticsData, statistics_file, indent=4)

def run_task_winrar(driveLetter=None):
    log_event("Performing WinRAR task")
    try:
        exeWinRar = shsu.shExeFile(programPathsRecord["WinRAR"])
    except FileNotFoundError:
        script_exit(1, 5, programPathsRecord["WinRAR"])
    psw = get_job_option(KEY_ARCHIVE_PSW)
    psw = (" -p" + psw) if psw != "none" else ""
    packageList = jobRecord["PackageList"]
    while packageList:
        packageRecord = settingsData["Packages"][packageList[0]]
        exeWinRar.set_arguments (rarCommand + psw + " -x@" + DIR_INCLUDE + 
            packageRecord["ExcludeFile"] + " \"" + ((driveLetter + ":") if driveLetter else "") +
            os.path.expandvars(settingsData["BakDestination"][jobRecord["BakDestination"]]) +
            settingsData["BakDirectory"][jobRecord["BakDirectory"]] + packageRecord["BakFile"] + 
            "\" @" + DIR_INCLUDE + packageRecord["IncludeFile"])
        log_event("Processing: " + packageRecord["BakFile"])
        prgExitCode = exeWinRar.run()
        log_event("WinRAR exit code: " + str(prgExitCode))
        if prgExitCode not in (0, 10):
            script_exit(prgExitCode, 7, "WinRAR exit code: " + str(prgExitCode))
        update_statistics(packageList[0])
        packageList = packageList[1:]
    log_event ("WinRAR task completed.")
    return 0

if __name__ == "__main__":

    log_event("-"*25 + " " + PROGRAM_NAME + " " + PROGRAM_VER)
    log_event(PROGRAM_NAME + " started.")
    argDict = shsu.shOptionDictionary(sys.argv)
    jobName = argDict.get_option(KEY_JOB_NAME)
    try:
        with open(FILE_SETTINGS, "r") as settings_file:
            settingsData = json.load(settings_file)
    except:
        script_exit(1, 1, FILE_SETTINGS)
    try:
        jobRecord = settingsData["Jobs"][jobName]
    except:
        script_exit(1, 2, jobName)   
    log_event("Job name: " + jobName)
    shmb.shShowMessage(0, PROGRAM_NAME, PROGRAM_NAME + " started\n Job name: " + jobName, 
        shmb.SH_MESSAGE_INFO, EXIT_DELAY, PROGRAM_ICON)

    programPathsRecord = settingsData["ProgramPaths"][jobRecord["ProgramPaths"]]   
    workMode = jobRecord["WorkMode"]

    if workMode == "Check_Logs":
        check_log_error_files()

    elif workMode == "VC_Volume":
        log_event("Mounting VCrypt volume: " + get_job_option(KEY_DRIVE_LETTER))
        try:
            exeVCrypt = shsu.shExeFile(programPathsRecord["VeraCrypt"])
        except FileNotFoundError:
            script_exit(1, 5, programPathsRecord["VeraCrypt"])
        exeVCrypt.set_arguments (vcSwitchesMount + " /l " + get_job_option(KEY_DRIVE_LETTER) +
            " /v " + get_job_option(KEY_VOLUME_NAME) + " /p " + get_job_option(KEY_VOLUME_PSW))
        prgExitCode = exeVCrypt.run()
        if prgExitCode: script_exit(prgExitCode, 7, "VCrypt exit code: " + str(prgExitCode) )
        try:
            shsu.sh_wait_path_availability(get_job_option(KEY_DRIVE_LETTER) + ":\\", VCRYPT_WAIT_SECONDS)
        except FileNotFoundError:
            script_exit(1, 8, get_job_option(KEY_DRIVE_LETTER))
        run_task_winrar(get_job_option(KEY_DRIVE_LETTER))
        log_event("Dismounting VCrypt volume")
        exeVCrypt.set_arguments (vcSwitchesDismount)
        prgExitCode = exeVCrypt.run()
        if prgExitCode: script_exit(prgExitCode, 7, "VCrypt exit code: " + str(prgExitCode) )

    elif workMode == "Local_Drive":
        run_task_winrar()

    elif workMode == "Network_Drive":
        delayMinutes = int(get_job_option(KEY_NET_DISCONNECT_DELAY_MINUTES)) * 60
        log_event("Mounting network drive")
        prgExitCode = subprocess.run (["net", "use", get_job_option(KEY_DRIVE_LETTER)+":", get_job_option(KEY_NET_SERVER_NAME),
            "/user:" + get_job_option(KEY_NET_SERVER_ACCOUNT),  get_job_option(KEY_NET_ACCOUNT_PSW)], shell=True).returncode
        if prgExitCode: script_exit(1, 9, "Error code: " + str(prgExitCode))
        run_task_winrar(get_job_option(KEY_DRIVE_LETTER))
        log_event("Delaying dismount for " + str(delayMinutes) + " minutes")
        time.sleep(delayMinutes)
        log_event("Dismounting network drive")
        prgExitCode = subprocess.run(["net", "use", get_job_option(KEY_DRIVE_LETTER)+":", "/delete"], shell=True).returncode
        if prgExitCode: script_exit(1, 10, "Error code: " + str(prgExitCode))

    else:
        script_exit(0, 3, workMode)
       
    log_event(PROGRAM_NAME + " completed.")
    shmb.shShowMessage(0, PROGRAM_NAME, PROGRAM_NAME + " completed\n Job name: " + jobName, 
        shmb.SH_MESSAGE_INFO, EXIT_DELAY, PROGRAM_ICON)
