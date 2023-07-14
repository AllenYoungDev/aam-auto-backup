#!/usr/bin/env python3

import platform

import sys
import os
import errno

import time

import datetime

from filelock import Timeout, FileLock

import pathlib

import shutil

import re

import boto3
import botocore.config
import botocore

"""
How to use this Python CLI program (command formats)
====================================================

Backup (to USB hard drive and AWS S3 Glacier Deep Archive)
----------------------------------------------------------
Because this program uses Windows Shadow Copy via ShadowSpawn.exe,
this program must be run with the administrator privilege when doing backup.

For backup, ShadowSpawn.exe must be in the same directory as this program file.

For backup, 7z.exe (the 7-Zip CLI program) must be in the same directory 
as this program file.


To execute a backup operation using AAM Auto Backup, use the command format
in the "command arguments and format" section of
"Regular-backup Operation Mode" or "Incremental-only Backup Operation Mode",
in "AAM Auto Backup document.doc".


Restore to local computer in one step
-------------------------------------
For restoring to the local computer,
7z.exe (the 7-Zip CLI program) must be in the same directory as this program 
file.

To execute a backup operation using AAM Auto Backup, use the command format
in the "command arguments and format" section of
"One-step AWS S3 Data Restoration Operation Mode",
in "AAM Auto Backup document.doc".



Restore to AWS S3 from AWS S3 Glacier Deep Archive
--------------------------------------------------
Refer to the "Restore to AWS S3 from AWS S3 Glacier Deep Archive" section
in "AAM Auto Backup document.doc".


Check AWS S3 restoration status
-------------------------------
Refer to the "Check AWS S3 restoration status" section
in "AAM Auto Backup document.doc".


Download to local computer from AWS S3
--------------------------------------
Refer to the "Download to local computer from AWS S3" section
in "AAM Auto Backup document.doc".


Decompress all the downloaded full and incremental backup files
on the local computer
---------------------------------------------------------------
For restoring to the local computer,
7z.exe (the 7-Zip CLI program) must be in the same directory as this program 
file.

Refer to the "Decompress all the downloaded full and incremental backup files
on the local computer" section in "AAM Auto Backup document.doc".

"""


#I think I need class Aam_Auto_Backup_Command_Arguments,
#with all the command arguments as public data variables, 
#strOperationType public data variable, and a function (likely __init__())
#for assigning the data variables.  in all likely chance, I'll get this.
#tag:  aam_abca
#[10/18/2020 8:50 AM CST]
#UPDATE [10/18/2020 9:09 AM CST] I'll use Aam_Auto_Backup_Launcher
class Aam_Auto_Backup_Launcher:  #tag:  aam_abl
    def __init__(self, str_listCommandArguments):
        
        self.str_listCommandArguments = str_listCommandArguments
        self.iNumberOfCommandArguments = len(str_listCommandArguments)
        
        self.strOperationType = str_listCommandArguments[1]
        

        if self.strOperationType == 'regular-backup':
            
            self.strExecutionAgentType = str_listCommandArguments[2]
            
            if self.strExecutionAgentType == 'user':
                self._GetUserBackupCommandArguments()
                self.aam_ab = Aam_Auto_Backup(self)
                self.aam_ab.ExecuteRegularBackup()
            else: #ShadowSpawn
                self._GetShadowSpawnBackupCommandArguments()
                self.aam_ab = Aam_Auto_Backup(self)
                self.aam_ab.PerformShadowSpawnExecutedBackUpOperation()
            
        elif self.strOperationType == 'incremental-only-backup':
            
            self.strExecutionAgentType = str_listCommandArguments[2]
            
            if self.strExecutionAgentType == 'user':
                self._GetUserBackupCommandArguments()
                self.bSendEmailReport = False
                self.aam_ab = Aam_Auto_Backup(self)
                self.aam_ab.ExecuteIncrementalOnlyBackup()
            else: #ShadowSpawn
                self._GetShadowSpawnBackupCommandArguments()
                self.aam_ab = Aam_Auto_Backup(self)
                self.aam_ab.PerformShadowSpawnExecutedBackUpOperation()
            
        elif self.strOperationType == 'one-step-aws-data-restoration':
            self._GetOneStepAwsDataRestorationCommandArguments()
            self.aam_ab = Aam_Auto_Backup(self)
            self.aam_ab.RestoreAwsS3DataToLocalComputerInOneStep()
            
        elif self.strOperationType == \
            'restore-to-aws-s3-from-aws-s3-glacier-deep-archive':
            self._GetOneStepAwsDataRestorationCommandArguments()
            self.aam_ab = Aam_Auto_Backup(self)
            self.aam_ab.RestoreToAwsS3FromAwsS3GlacierDeepArchive()
            
        elif self.strOperationType == 'check-aws-s3-restoration-status':
            self._GetOneStepAwsDataRestorationCommandArguments()
            self.aam_ab = Aam_Auto_Backup(self)
            self.aam_ab.CheckAwsS3RestorationStatus()
            
        elif self.strOperationType == 'download-to-local-computer-from-aws-s3':
            self._GetOneStepAwsDataRestorationCommandArguments()
            self.aam_ab = Aam_Auto_Backup(self)
            self.aam_ab.DownloadToLocalComputerFromAwsS3()
            
        elif self.strOperationType == 'decompress-all-downloaded-backup-files':
            self._GetOneStepAwsDataRestorationCommandArguments()
            self.aam_ab = Aam_Auto_Backup(self)
            self.aam_ab.DecompressAllDownloadedBackupFiles()
            
        else:
            sys.exit('Invalid command!')
            
            
    def _GetUserBackupCommandArguments(self):
        
        if self.iNumberOfCommandArguments < 23:
            sys.exit('Invalid number of command arguments!')
        
        self.strPythonExecutableFullPath = self.str_listCommandArguments[3]
        self.fOngoingBackupWaitingPeriodInSeconds = \
            float(self.str_listCommandArguments[4])
        self.fTotalOngoingBackupWaitTimeInSeconds = \
            float(self.str_listCommandArguments[5])
        self.strLogDirectoryFullPath = self.str_listCommandArguments[6]
        if self.str_listCommandArguments[7] == 'True':
            self.bSendEmailReport = True
        else:
            self.bSendEmailReport = False
        self.strEmailSenderName = self.str_listCommandArguments[8]
        self.strEmailSenderAddress = self.str_listCommandArguments[9]        
        self.strEmailRecipientAddress = self.str_listCommandArguments[10]
        self.strBackupInstructionPlainTextFileFullPath = \
            self.str_listCommandArguments[11]
        self.strShadowCopyDriveName = self.str_listCommandArguments[12]
        self.str_listBackupDestinationTypes = \
            self.str_listCommandArguments[13].split('|')
        for iBackupDestinationTypeIndex, strBackupDestinationType in \
            enumerate(self.str_listBackupDestinationTypes):
            self.str_listBackupDestinationTypes[iBackupDestinationTypeIndex] \
                = strBackupDestinationType.strip()
        self.strLocalBackupDestinationDirectoryFullPath = \
            self.str_listCommandArguments[14]
        if self.str_listCommandArguments[15] == 'True':
            self.bKeepMissingBackupSourcesFilesInBackupDestination = True
        else:
            self.bKeepMissingBackupSourcesFilesInBackupDestination = False
        self.strBackupEncryptionAes256Key = \
            self.str_listCommandArguments[16]
        self.strBackupAwsS3BucketName = self.str_listCommandArguments[17]
        self.strUniqueBackupSourceLocationName = \
            self.str_listCommandArguments[18]
        self.strBackupAwsIamUserAccessKeyId = \
            self.str_listCommandArguments[19]
        self.strBackupAwsIamUserSecretAccessKey = \
            self.str_listCommandArguments[20]
        self.strForceFullBackup = self.str_listCommandArguments[21]
        self.strAutomaticForceFullBackup = self.str_listCommandArguments[22]
        
        if '_' in self.strUniqueBackupSourceLocationName:
            sys.exit('Critical error.  One or more underscores in the unique \
backup-source location name.  Run the program again without an underscore \
in the unique backup-source location name.')
    
    
    def _GetShadowSpawnBackupCommandArguments(self):
        if self.iNumberOfCommandArguments < 16:
            sys.exit('Invalid number of command arguments!')        
        
        self.strLastAwsS3FullBackupDateAndTime = \
            self.str_listCommandArguments[3].strip()
        self.strLastAwsS3IncrementalBackupDateAndTime = \
            self.str_listCommandArguments[4].strip()
        self.strBackupExecutionStartDateTime = \
            self.str_listCommandArguments[5].strip()
        self.strLocalBackupSourceDirectoryFullPath = \
            self.str_listCommandArguments[6]
        self.strShadowCopyDriveName = self.str_listCommandArguments[7]
        self.str_listBackupDestinationTypes = \
            self.str_listCommandArguments[8].split('|')
        for iBackupDestinationTypeIndex, strBackupDestinationType in \
            enumerate(self.str_listBackupDestinationTypes):
            self.str_listBackupDestinationTypes[iBackupDestinationTypeIndex] \
                = strBackupDestinationType.strip()        
        self.strLocalBackupDestinationDirectoryFullPath = \
            self.str_listCommandArguments[9]
        if self.str_listCommandArguments[10] == 'True':
            self.bKeepMissingBackupSourcesFilesInBackupDestination = True
        else:
            self.bKeepMissingBackupSourcesFilesInBackupDestination = False
        self.strBackupEncryptionAes256Key = self.str_listCommandArguments[11]
        self.strUniqueBackupSourceLocationName = \
            self.str_listCommandArguments[12]
        self.strAwsS3BackupFilesDirectoryFullPath = \
            self.str_listCommandArguments[13]
        self.strForceFullBackup = self.str_listCommandArguments[14]
        self._strBackupScope = self.str_listCommandArguments[15]
            
        
    def _GetOneStepAwsDataRestorationCommandArguments(self):
        if self.iNumberOfCommandArguments < 14:
            sys.exit('Invalid number of command arguments!')          
        
        self.strLogDirectoryFullPath = self.str_listCommandArguments[2]
        if self.str_listCommandArguments[3] == 'True':
            self.bSendEmailReport = True
        else:
            self.bSendEmailReport = False
        self.strEmailSenderName = self.str_listCommandArguments[4]
        self.strEmailSenderAddress = self.str_listCommandArguments[5]
        self.strEmailRecipientAddress = self.str_listCommandArguments[6]
        self.iAwsS3ObjectRestorationPeriodInDays = \
            int(self.str_listCommandArguments[7])
        self.strBackupDecryptionAes256Key = self.str_listCommandArguments[8]
        self.strBackupAwsS3BucketName = self.str_listCommandArguments[9]
        self.strUniqueBackupSourceLocationName = \
            self.str_listCommandArguments[10]
        self.strBackupAwsIamUserAccessKeyId = self.str_listCommandArguments[11]
        self.strBackupAwsIamUserSecretAccessKey = \
            self.str_listCommandArguments[12]
        self.strAwsS3DataRestorationDestinationDirectoryFullPath = \
            self.str_listCommandArguments[13]  
            
        if '_' in self.strUniqueBackupSourceLocationName:
            sys.exit('Critical error.  One or more underscores in the unique \
backup-source location name.  Run the program again without an underscore \
in the unique backup-source location name.')


class Aam_Auto_Backup:  #tag:  aam_ab
    def __init__(self, aam_abl):
        self._aam_abl = aam_abl
        
        self._PathSeparator = '\\'
        
        
        self._strProgramFileDirectoryFullPath = \
            os.path.dirname(os.path.abspath( __file__ ))
        
        self._strLockFileFullPath = \
            os.path.join(self._strProgramFileDirectoryFullPath,
            "AAM_Auto_Backup_lock_file")
        self._filelock = None
            
            
        self.boto3_session = None
        self.s3_resource = None
        self.backup_s3_bucket = None
        
        self.ses_client = None
        
        self.strAwsRegion = 'us-east-2'
                    
        self._iBackupAwsS3BucketObjectLifetimeInNumberOfMonths = 6
        
        self._strLocalBackupLogFileFullPath = ''
        self._fileLocalBackupLog = None
        
        if self._aam_abl.strOperationType == 'incremental-only-backup':
            self._bWaitForUserInputBeforeClosing = True
        elif self._aam_abl.strOperationType == 'one-step-aws-data-restoration':
            self._bWaitForUserInputBeforeClosing = True
        elif self._aam_abl.strOperationType == 'regular-backup' and \
            self._aam_abl.strForceFullBackup == 'yes':
            self._bWaitForUserInputBeforeClosing = True
        else:
            self._bWaitForUserInputBeforeClosing = False
        
        
        #######################################################################
        #Backup-source data variables
        #######################################################################
        self._str_listUserSpecifiedBackupSourceDirectoryFullPaths = []
            #absolute directory paths only.
        self._str_listUserSpecifiedDirectoriesToExclude = []
            #absolute directory paths and directory names only.
            #no relative directory paths.
        self._str_listUserSpecifiedFilesToExclude = []
            #absolute file paths and file names only.
            #no relative file paths.
        
        self._str_listShadowMountDirectoryFullPaths = []
            #the backup-source folder absolute paths.
        
        #shadow-copy mounted directory info plain text file contents
        #the following three data variables are built before
        #the shadowspawn.exe execution, for creating the shadow-copy mounted
        #directory info plain text file content above.
        #None of the following three data variables will contain a full path 
        #that doesn't exist in the shadow-mounted drive.        
        self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists = {}
            #str_listIncludedDirectories contains the following.
            #the shadow-mounted drive folder absolute paths,
            #not the backup-source folder absolute paths.
            #no relative folder paths.  no wild cards.
            #must not end in path separator.
            #for use by 7z.exe.
        self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists = {}
            #str_listUserExcludedDirectories contains the following.
            #the shadow-mounted drive folder absolute paths, and folder names.
            #no backup-source folder absolute paths;
            #no relative folder paths of any kind,
            #in the shadow-mounted drive or in the backup source directory.
            #wild cards allowed only in directory names, not in folder paths.
            #each entry must not end with path separator.
            #if no entry in the list, this should be an empty line.
            #for use by Robocopy and 7z.exe.
        self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists = {}
            #str_listUserExcludedFiles contains the following.
            #the shadow-mounted drive file absolute paths, and file names.
            #no backup-source file absolute paths;
            #no relative file paths of any kind, in the shadow-mounted drive
            #or in the backup source directory.
            #wild cards allowed only in file names, not in file paths.
            #each entry must not end with path separator.
            #if no entry in the list, this should be an empty line or
            #no entry in the file.
            #for use by Robocopy and 7z.exe
                        
        
        #######################################################################
        #Backup AWS S3 bucket query data variables
        #######################################################################
        self._str_listBackupSourceAwsS3UniqueNames = []
        
        self.regexp_objBackupAwsS3ObjectNameParser = re.compile( \
            r"^(.+?)_(\d+?)_(\d+?)\.(\d+?)_(\d+?)_(\d+?)\.(\d+?)_(.+?)_(.+?)(\.zip\.\d+?)?$", 
            re.IGNORECASE)
        
        self._strLatestCompleteUploadAwsS3FullBackupDate = ''
        self._strLatestCompleteUploadAwsS3FullBackupTime = ''
        self._strLatestCompleteUploadAwsS3IncrementalBackupDate = ''
        self._strLatestCompleteUploadAwsS3IncrementalBackupTime = ''
        
        #self._dictBackupSourceUniqueNamesToLatestCompleteUploadFullBackupAwsS3ObjectNameLists
        #self._dictBackupSourceUniqueNamesToLatestCompleteUploadIncrementalBackupAwsS3ObjectNameLists
        self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists = {}
            #Unique backup source names.
            #latest, complete-upload backup.
        self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists = {}
            #Unique backup source names.
            #latest, complete-upload, backup in ascending order.
        #self._str_listLatestCompleteUploadFullBackupAwsS3ObjectNames = None
        #self._str_listLatestCompleteUploadIncrementalBackupAwsS3ObjectNames = None
        self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists = {}
        
        #the following are built by an applicable Aam_Auto_Backup
        #class function(s?).
        #(TO ANSWER [11/8/2020 12:54 PM CST] why do I need these?)
        #([11/21/2020 1:11 PM CST] no need for the following.  not using them.)
        #self._dictBackupSourceLocationsToNamesToFullBackupAwsS3ObjectNameLists = {}
        #self._dictBackupSourceLocationsToNamesToIncrementalBackupAwsS3ObjectNameLists = {}
        #self._dictBackupSourceLocationsToNamesToIncrementalBackupArchiveFileNameLists = {}
        
        self._bAwsS3QueryFailure = False
        
        
        #######################################################################
        #AWS S3 backup files data variables
        #######################################################################
        self._strAwsS3BackupFilesDirectoryParentDirectoryFullPath = 'c:\\temp'
        self._strAwsS3BackupFilesDirectoryFullPath = ''
        
        
        #######################################################################
        #ShadowSpawn.exe execution data variables
        #######################################################################
        self._str_listShadowCopyInclusionFolderFullPaths = []
        self._str_listShadowCopyExclusionFolders = []
        self._str_listShadowCopyExclusionFiles = []
        #The above three data variables are initialized using
        #the shadow-copy mounted directory info plain text file content.

        self._str_listShadowCopyNonIncludedFolderFullPaths = []
            #the shadowspawn execution function generates the above
            #data variable, by scanning the shadow-mounted drive contents,
            #to use in building the Robocopy command.
            #the shadow-mounted drive folder absolute paths,
            #not the backup-source folder absolute paths.
            #no relative folder paths.  no wild cards.
            #must not end in path separator.
            #for use in the Robocopy command.
            
        self._str_listShadowCopyExclusionFolderFullPaths = []
        self._str_listShadowCopyExclusionFileFullPaths = []            

        self._str_listShadowCopyExclusionFolderRegularExpressions = []
        self._regexp_obj_listShadowCopyExclusionFolders = []

        self._str_listShadowCopyExclusionFileRegularExpressions = []
        self._regexp_obj_listShadowCopyExclusionFiles = []
        
        
        self._strBackupBatchFileExecutionSuccessMessage = \
            'AAM Auto Backup batch file execution success!'
        self._strRobocopySuccessMessage = \
            'Total    Copied   Skipped  Mismatch    FAILED    Extras'
        self._str7zExeSuccessMessage = 'Everything is Ok'
        self._strFilesToIncrementallyBackupStatusMessage = \
            'Number of files incrementally backed up:  '
        self._strLocalBackupDestinationValidationFailureMessage = \
            'Robocopy failure.'        
        
        
        #######################################################################
        #Email-content data variables
        #######################################################################
        self._bBackupSuccess = True
        self._bRestorationSuccess = True
        
        self._datetimeBackupExecutionStart = None
        self._strBackupExecutionStartDateTime = ''
        self._strCommandArgumentBackupExecutionStartDateTime = ''
        
        self._strBackupScope = '' #full or incremental
        
        self._bFileLockAcquisitionFailure = False
        self._bBackupInstructionPlainTextFileReadError = False
        
        self._str_listNoIncrementalBackupFilesShadowMountDirectoryFullPaths = []
        self._str_listLocalBackupValidationFailureShadowMountDirectoryFullPaths = []
        
        self._datetimeBackupExecutionEnd = None
        self._strBackupExecutionEndDateTime = ''
        
        
    def _ExecuteBackup(self, strBackupOperationType):
        #strBackupOperationType must be 'regular-backup' or 
        #'incremental-only-backup'.
    
        self.boto3_session = boto3.Session( \
            aws_access_key_id=self._aam_abl.strBackupAwsIamUserAccessKeyId,
            aws_secret_access_key=self._aam_abl.strBackupAwsIamUserSecretAccessKey,
            region_name=self.strAwsRegion)
        self.s3_resource = self.boto3_session.resource('s3')
        self.backup_s3_bucket = self.s3_resource.Bucket( \
            self._aam_abl.strBackupAwsS3BucketName)
        
        self.ses_client = boto3.client('ses', 
            aws_access_key_id=self._aam_abl.strBackupAwsIamUserAccessKeyId,
            aws_secret_access_key=self._aam_abl.strBackupAwsIamUserSecretAccessKey,
            region_name=self.strAwsRegion)
        #https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
        #TO DO [12/21/2020 1:14 PM CST] code update for Robocentric Producer v1.0.
        #when creating the AWS SES client object in the Python code, make sure 
        #to select the AWS region with the verified email address.
        #better yet, if possible, automate the email address verification via Python code.
        #[12/21/2020 1:24 PM CST] the above method requires verifying 
        #the recipient email address too.  maybe try to find a way to not do
        #that.
    
        #######################################################################
        #Stage 1
        #-------
        #Program execution preparation (initialization)
        #######################################################################
        
        #----------------------------------------------------------------------
        #Stage 1-1
        #Local backup log file creation, opening, and initialization
        #----------------------------------------------------------------------
        datetimeNow = datetime.datetime.now()
        strDateTimeNow = str(datetimeNow)
        strFileNameSafeDateTimeNow = strDateTimeNow.replace(':', '_')
        
        strLocalBackupLogFileBaseName = strFileNameSafeDateTimeNow + \
            ' ' + strBackupOperationType
        strLocalBackupLogFileFullName = strLocalBackupLogFileBaseName + '.txt'
        
        self._strLocalBackupLogFileFullPath = os.path.join( \
            self._aam_abl.strLogDirectoryFullPath, strLocalBackupLogFileFullName)        
        
        iCounter = 1
        
        while os.path.isfile(self._strLocalBackupLogFileFullPath):
            iCounter += 1
            strLocalBackupLogFileFullName = strLocalBackupLogFileBaseName + \
                ' ' + str(iCounter) + '.txt'
            self._strLocalBackupLogFileFullPath = os.path.join( \
                self._aam_abl.strLogDirectoryFullPath,
                strLocalBackupLogFileFullName)                  

        #https://docs.python.org/3/tutorial/inputoutput.html
        #https://docs.python.org/3/library/functions.html#open
        #https://docs.python.org/3/library/codecs.html#module-codecs
        try:
            self._fileLocalBackupLog = open( \
                self._strLocalBackupLogFileFullPath, 'w', encoding='utf-8')
        except Exception as exc:
            print('Failure to open the local backup log file.  "' + \
                self._strLocalBackupLogFileFullPath + '"\n' + str(exc))
            if self._bWaitForUserInputBeforeClosing:
                input("Press Enter to close the program...")
            sys.exit()
        
        #add the user-executed AAM Auto Backup command parameters 
        #to the local backup log file.
        self._fileLocalBackupLog.write( \
            '------------------------------------------------\n')        
        self._fileLocalBackupLog.write( \
            'User-executed AAM Auto Backup command parameters\n')
        self._fileLocalBackupLog.write( \
            '------------------------------------------------\n')            
        
        self._fileLocalBackupLog.write('strOperationType:  ' + \
            self._aam_abl.strOperationType + '\n')
        #self._fileLocalBackupLog.write('strExecutionAgentType:  ' + \
        #    self._aam_abl.strExecutionAgentType + '\n')
        self._fileLocalBackupLog.write('strPythonExecutableFullPath:  ' + \
            self._aam_abl.strPythonExecutableFullPath + '\n')
        self._fileLocalBackupLog.write('fOngoingBackupWaitingPeriodInSeconds:  ' + \
            str(self._aam_abl.fOngoingBackupWaitingPeriodInSeconds) + '\n')
        self._fileLocalBackupLog.write('fTotalOngoingBackupWaitTimeInSeconds:  ' + \
            str(self._aam_abl.fTotalOngoingBackupWaitTimeInSeconds) + '\n')
        self._fileLocalBackupLog.write('strLogDirectoryFullPath:  ' + \
            self._aam_abl.strLogDirectoryFullPath + '\n')
        self._fileLocalBackupLog.write('bSendEmailReport:  ' + \
            str(self._aam_abl.bSendEmailReport) + '\n')
        self._fileLocalBackupLog.write('strEmailSenderName:  ' + \
            self._aam_abl.strEmailSenderName + '\n')
        self._fileLocalBackupLog.write('strEmailSenderAddress:  ' + \
            self._aam_abl.strEmailSenderAddress + '\n')
        self._fileLocalBackupLog.write('strEmailRecipientAddress:  ' + \
            self._aam_abl.strEmailRecipientAddress + '\n')
        self._fileLocalBackupLog.write('strBackupInstructionPlainTextFileFullPath:  ' + \
            self._aam_abl.strBackupInstructionPlainTextFileFullPath + '\n')
        self._fileLocalBackupLog.write('strShadowCopyDriveName:  ' + \
            self._aam_abl.strShadowCopyDriveName + '\n')
        self._fileLocalBackupLog.write('str_listBackupDestinationTypes:  ' + \
            str(self._aam_abl.str_listBackupDestinationTypes) + '\n')
        self._fileLocalBackupLog.write('strLocalBackupDestinationDirectoryFullPath:  ' + \
            self._aam_abl.strLocalBackupDestinationDirectoryFullPath + '\n')
        self._fileLocalBackupLog.write('bKeepMissingBackupSourcesFilesInBackupDestination:  ' + \
            str(self._aam_abl.bKeepMissingBackupSourcesFilesInBackupDestination) + '\n')
        self._fileLocalBackupLog.write('strUniqueBackupSourceLocationName:  ' + \
            self._aam_abl.strUniqueBackupSourceLocationName + '\n')
        self._fileLocalBackupLog.write('strForceFullBackup:  ' + \
            self._aam_abl.strForceFullBackup + '\n')  
        self._fileLocalBackupLog.write('strAutomaticForceFullBackup:  ' + \
            self._aam_abl.strAutomaticForceFullBackup + '\n\n')        
        
        
        #----------------------------------------------------------------------
        #Stage 1-2
        #File lock acquisition
        #----------------------------------------------------------------------        
        
        fAmountOfTimeWaitedForFileLockInSeconds = 0.0
        
        self._filelock = FileLock(self._strLockFileFullPath)
        bFileLockAcquired = False
                
        while fAmountOfTimeWaitedForFileLockInSeconds < \
            self._aam_abl.fTotalOngoingBackupWaitTimeInSeconds:
        
            try:
                self._filelock.acquire(timeout=10)
            except Timeout:
                time.sleep(self._aam_abl.fOngoingBackupWaitingPeriodInSeconds)
                fAmountOfTimeWaitedForFileLockInSeconds += \
                    self._aam_abl.fOngoingBackupWaitingPeriodInSeconds
            else:
                bFileLockAcquired = True
                break
        
        self._datetimeBackupExecutionStart = datetimeNow
        self._strBackupExecutionStartDateTime = \
            str(self._datetimeBackupExecutionStart)
        self._strCommandArgumentBackupExecutionStartDateTime = \
            self._strBackupExecutionStartDateTime.replace('-', '')
        self._strCommandArgumentBackupExecutionStartDateTime = \
            self._strCommandArgumentBackupExecutionStartDateTime.replace(':', '')         
        
        if bFileLockAcquired:            
            strBackupExecutionStartingDateAndTimeMessage = \
                '\n\nBackup execution starting date and time:  ' + \
                self._strBackupExecutionStartDateTime
            print(strBackupExecutionStartingDateAndTimeMessage)
            self._fileLocalBackupLog.write( \
                strBackupExecutionStartingDateAndTimeMessage + '\n')
        else:
            self._bBackupSuccess = False
            self._bFileLockAcquisitionFailure = True
            self._fileLocalBackupLog.write( \
                'Unable to acquire the file lock.  Exiting program.\n\n')
            self._SendEmailReport()
            self._fileLocalBackupLog.close()
            print('Unable to acquire the file lock.  Exiting program.')
            if self._bWaitForUserInputBeforeClosing:
                input("Press Enter to close the program...")            
            sys.exit()
                    
                   
        #######################################################################
        #Stage 2
        #-------
        #AAM Auto Backup instruction plain text file processing
        ####################################################################### 
        self._str_listUserSpecifiedBackupSourceDirectoryFullPaths = []
            #all lower case when the OS is Windows
            #search "python how to detect os type" online.
            #https://stackoverflow.com/questions/1854/python-what-os-am-i-running-on/45679447
        self._str_listUserSpecifiedDirectoriesToExclude = []
        self._str_listUserSpecifiedFilesToExclude = []
        
        self._str_listShadowMountDirectoryFullPaths = []
        self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists = {}
        self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists = {}
        self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists = {}
        
        
        #----------------------------------------------------------------------
        #Stage 2-1
        #Read the content of the AAM Auto Backup instruction plain text file,
        #and create self._str_listUserSpecifiedBackupSourceDirectoryFullPaths,
        #self._str_listUserSpecifiedDirectoriesToExclude, and
        #self._str_listUserSpecifiedFilesToExclude.
        #----------------------------------------------------------------------
        #IMPLEMENTATION ALGORITHM [10/23/2020 5:05 PM CST]
        #Two while loops only.
        #First for folders to include.
        #Second for folders and files to exclude.
        #In while-loop condition, check for '' in file line text for loop termination or not starting.
        #In the first while loop, terminate the loop, if new line or blank line.
        #In the first while loop, check the existence of every path.
        #In the second while loop, continue the loop, if \n line.
        #In the second while loop, terminate the loop, if blank or empty line.
        #In the second while loop, if the line ends in /, and have colon in it,
        #perform path existence test--if the path doesn't exist, do not add to 
        #the list, and add to log file as a nonexistent folder full path.
        #In the second while loop, if the line does not end in /, add to 
        #the exclusion file list.  if it is a full path, check the file
        #full path existence; if it doesn't exist, do not add to 
        #the list, and add to log file as a nonexistent file full path.
        #UPDATE [11/27/2020 7:21 PM CST] actually, for the wild card support
        #in both directory and file names, in the second while loop,
        #wild card characters (existence)? must be tested.
        
        try:
            fileAamAutoBackupInstruction = open( \
                self._aam_abl.strBackupInstructionPlainTextFileFullPath, 
                'r', encoding='utf-8')
            
            while True:
                strAamAutoBackupInstructionLine = \
                    fileAamAutoBackupInstruction.readline()
                if strAamAutoBackupInstructionLine == '\n' or \
                    strAamAutoBackupInstructionLine == '': break
                
                strAamAutoBackupInstructionLine = \
                    strAamAutoBackupInstructionLine.strip()

                if strAamAutoBackupInstructionLine[-1] != \
                    self._PathSeparator:
                    strAamAutoBackupInstructionLine = \
                        strAamAutoBackupInstructionLine + self._PathSeparator

                if os.path.isdir(strAamAutoBackupInstructionLine):
                    if platform.system() == 'Windows':
                        strAamAutoBackupInstructionLine = \
                            strAamAutoBackupInstructionLine.lower()
                            
                    if strAamAutoBackupInstructionLine not in \
                        self._str_listUserSpecifiedBackupSourceDirectoryFullPaths:
                        self._str_listUserSpecifiedBackupSourceDirectoryFullPaths.append( \
                            strAamAutoBackupInstructionLine)
                else:
                    self._fileLocalBackupLog.write( \
                        'Invalid user-specified directory to backup:  ' + \
                        strAamAutoBackupInstructionLine + '\n')
            
            while strAamAutoBackupInstructionLine != '':
                strAamAutoBackupInstructionLine = \
                    fileAamAutoBackupInstruction.readline()
                if strAamAutoBackupInstructionLine == '\n':
                    continue
                elif strAamAutoBackupInstructionLine == '':
                    break
            
                strAamAutoBackupInstructionLine = \
                    strAamAutoBackupInstructionLine.strip()

                if platform.system() == 'Windows':
                    strAamAutoBackupInstructionLine = \
                        strAamAutoBackupInstructionLine.lower()  
                        
                    if ':' in strAamAutoBackupInstructionLine and \
                        ('*' in strAamAutoBackupInstructionLine or \
                        '?' in strAamAutoBackupInstructionLine):
                            
                        strErrorMessage = '\n\nAAM Auto Backup instruction \
plain text file contains a full path with a wild card.  Exiting program.'
                        raise Exception(strErrorMessage)

                    elif ':' not in strAamAutoBackupInstructionLine and \
                        self._PathSeparator in \
                        strAamAutoBackupInstructionLine[0:-1]:
                        #[12/4/2020 2:53 PM CST]
                        #the last character would be the path separator.
                        #so strAamAutoBackupInstructionLine[0:-1] is checked,
                        #not strAamAutoBackupInstructionLine.
                            
                        strErrorMessage = '\n\nAAM Auto Backup instruction \
plain text file contains a relative path.  Exiting program.'
                        raise Exception(strErrorMessage)                         
            
                if strAamAutoBackupInstructionLine[-1] == self._PathSeparator: #directory
                    if ':' in strAamAutoBackupInstructionLine:
                        if os.path.isdir(strAamAutoBackupInstructionLine):
                            if strAamAutoBackupInstructionLine not in \
                                self._str_listUserSpecifiedDirectoriesToExclude:
                                self._str_listUserSpecifiedDirectoriesToExclude.append( \
                                    strAamAutoBackupInstructionLine[0:-1])
                        else:
                            self._fileLocalBackupLog.write( \
                                'Invalid user-specified directory to exclude:  ' + \
                                strAamAutoBackupInstructionLine + '\n')
                    else:
                        if strAamAutoBackupInstructionLine not in \
                            self._str_listUserSpecifiedDirectoriesToExclude:
                            self._str_listUserSpecifiedDirectoriesToExclude.append( \
                                strAamAutoBackupInstructionLine[0:-1])
                else: #file
                    if ':' in strAamAutoBackupInstructionLine:
                        if os.path.isfile(strAamAutoBackupInstructionLine):
                            if strAamAutoBackupInstructionLine not in \
                                self._str_listUserSpecifiedFilesToExclude:
                                self._str_listUserSpecifiedFilesToExclude.append( \
                                    strAamAutoBackupInstructionLine)
                        else:
                            self._fileLocalBackupLog.write( \
                                'Invalid user-specified file to exclude:  ' + \
                                strAamAutoBackupInstructionLine + '\n')
                    else:
                        if strAamAutoBackupInstructionLine not in \
                            self._str_listUserSpecifiedFilesToExclude:
                            self._str_listUserSpecifiedFilesToExclude.append( \
                                strAamAutoBackupInstructionLine)              

            fileAamAutoBackupInstruction.close()
            
        except Exception as exc:
            try:
                fileAamAutoBackupInstruction.close()
            except:
                pass
            self._bBackupSuccess = False
            self._bBackupInstructionPlainTextFileReadError = True
            strErrorMessage = '\n\nAAM Auto Backup instruction plain text file \
processing error.  Exiting program.\n' + str(exc)
            self._fileLocalBackupLog.write(strErrorMessage)
            self._SendEmailReport()
            self._fileLocalBackupLog.close()
            self._filelock.release()
            print(strErrorMessage)
            if self._bWaitForUserInputBeforeClosing:
                input("Press Enter to close the program...")               
            sys.exit()
            
        #TO DO [11/30/2020 4:29 PM CST] for Robocentric Auto Backup v1.0 update
        #additional backup instruction validation.  quit when there's no input,
        #Mac path support, etc.
        

        #self._str_listUserSpecifiedBackupSourceDirectoryFullPaths
        #should have no child directory of a parent directory in
        #self._str_listUserSpecifiedBackupSourceDirectoryFullPaths,
        #because the child directory will be backed up when the parent directory
        #is backed up--the files of the child directory should not be
        #copied or included twice, especially in the AWS S3 backup zip files.
        #
        #process each element in
        #self._str_listUserSpecifiedBackupSourceDirectoryFullPaths,
        #and eliminate every child directory.
        #
        #use a while loop to handle the 
        #self._str_listUserSpecifiedBackupSourceDirectoryFullPaths length change.
        
        self._str_listUserSpecifiedBackupSourceDirectoryFullPaths.sort()
        
        #NOTE [12/4/2020 3:27 PM CST]
        #the following code doesn't need to handle the case when a previous 
        #directory full path is a child directory of a later directory full path.
        #because self._str_listUserSpecifiedBackupSourceDirectoryFullPaths
        #is sorted in ascending order, 
        #it only needs to handle when a later directory full path
        #is a child directory of a previous directory full path.
        iZeroBasedOuterListIndex = 0
        iNumberOfListElements = \
            len(self._str_listUserSpecifiedBackupSourceDirectoryFullPaths)
        while iZeroBasedOuterListIndex < iNumberOfListElements - 1:
            
            strOuterListElement = \
                self._str_listUserSpecifiedBackupSourceDirectoryFullPaths[ \
                    iZeroBasedOuterListIndex]
            
            for iZeroBasedInnerListIndex in range(iNumberOfListElements - 1,
                iZeroBasedOuterListIndex, -1):

                strInnerListElement = \
                    self._str_listUserSpecifiedBackupSourceDirectoryFullPaths[ \
                        iZeroBasedInnerListIndex]
                    
                if strOuterListElement in strInnerListElement:
                    self._str_listUserSpecifiedBackupSourceDirectoryFullPaths.pop( \
                        iZeroBasedInnerListIndex)   
                    
            iNumberOfListElements = \
                len(self._str_listUserSpecifiedBackupSourceDirectoryFullPaths)                    
                    
            iZeroBasedOuterListIndex += 1
            

        #----------------------------------------------------------------------
        #Stage 2-2
        #Create self._str_listShadowMountDirectoryFullPaths.
        #---------------------------------------------------------------------- 

        #-----------
        #Stage 2-2-1
        #Create str_list_listUserSpecifiedBackupSourceDirectoryFullPaths
        #using self._str_listUserSpecifiedBackupSourceDirectoryFullPaths.
        #-----------
        str_list_listUserSpecifiedBackupSourceDirectoryFullPaths = []
        
        for strUserSpecifiedBackupSourceDirectoryFullPath in \
            self._str_listUserSpecifiedBackupSourceDirectoryFullPaths:
            
            str_listUserSpecifiedBackupSourceDirectoryFullPath = \
                strUserSpecifiedBackupSourceDirectoryFullPath.split( \
                    self._PathSeparator)
                
            if str_listUserSpecifiedBackupSourceDirectoryFullPath[-1] == '':
                del str_listUserSpecifiedBackupSourceDirectoryFullPath[-1]
                
            #if ':' in str_listUserSpecifiedBackupSourceDirectoryFullPath[0]:
            #    str_listUserSpecifiedBackupSourceDirectoryFullPath[0] = \
            #        str_listUserSpecifiedBackupSourceDirectoryFullPath[0].replace( \
            #        ':', '')
                    
            str_list_listUserSpecifiedBackupSourceDirectoryFullPaths.append( \
                str_listUserSpecifiedBackupSourceDirectoryFullPath)
        
        #-----------
        #Stage 2-2-2
        #Create str_list_listShadowMountDirectoryFullPaths.
        #-----------
        #str_list_listUserSpecifiedBackupSourceDirectoryFullPaths must be
        #already sorted in ascending order.
        #That is, self._str_listUserSpecifiedBackupSourceDirectoryFullPaths
        #should've been already sorted before being used to create
        #str_list_listShadowMountDirectoryFullPaths.
        #also, no redundant items in
        #str_list_listUserSpecifiedBackupSourceDirectoryFullPaths.
        #
        #for the explanation of the algorithm used below, refer to the
        #"update [11/28/2020 6:28 AM CST] new shortest or earliest 
        #shared or common parent directories finding algorithm" section
        #in the AAM Auto Backup document.  the following is a highly-optmized
        #constant operation algorithm.
        str_list_listShadowMountDirectoryFullPaths = []
        
        for str_listUserSpecifiedBackupSourceDirectoryFullPath in \
            str_list_listUserSpecifiedBackupSourceDirectoryFullPaths:
     
            iNumberOfShadowMountDirectoryFullPaths = \
                len(str_list_listShadowMountDirectoryFullPaths)
                
            if iNumberOfShadowMountDirectoryFullPaths == 0:
                str_list_listShadowMountDirectoryFullPaths.append( \
                    str_listUserSpecifiedBackupSourceDirectoryFullPath)
                continue
        
            str_listLastShadowMountDirectoryFullPath = \
                str_list_listShadowMountDirectoryFullPaths[ \
                    iNumberOfShadowMountDirectoryFullPaths - 1]
                
            #find the earliest or shortest common or shared parent directory
            #for str_listUserSpecifiedBackupSourceDirectoryFullPath and
            #str_listLastShadowMountDirectoryFullPath.
            iNumberOfUserSpecifiedBackupSourceDirectoryFullPathElements = \
                len(str_listUserSpecifiedBackupSourceDirectoryFullPath)
            iNumberOfLastShadowMountDirectoryFullPathElements = \
                len(str_listLastShadowMountDirectoryFullPath)
            
            if iNumberOfUserSpecifiedBackupSourceDirectoryFullPathElements \
                < iNumberOfLastShadowMountDirectoryFullPathElements:                    
                iSmallerNumberOfBackupSourceDirectoryFullPathElements \
                    = iNumberOfUserSpecifiedBackupSourceDirectoryFullPathElements
            else:
                iSmallerNumberOfBackupSourceDirectoryFullPathElements \
                    = iNumberOfLastShadowMountDirectoryFullPathElements
    
            iNumberOfElementsInShortestCommonParentDirectoryPath = 0
    
            for iZeroBasedDirectoryPathElementIndex in range( \
                0, iSmallerNumberOfBackupSourceDirectoryFullPathElements):
                if str_listUserSpecifiedBackupSourceDirectoryFullPath[ \
                    iZeroBasedDirectoryPathElementIndex] == \
                    str_listLastShadowMountDirectoryFullPath[ \
                    iZeroBasedDirectoryPathElementIndex]:
                    iNumberOfElementsInShortestCommonParentDirectoryPath += 1
                else:
                    break    
                
            if iNumberOfElementsInShortestCommonParentDirectoryPath <= 1:
                str_list_listShadowMountDirectoryFullPaths.append( \
                    str_listUserSpecifiedBackupSourceDirectoryFullPath)
            elif iNumberOfElementsInShortestCommonParentDirectoryPath < \
                iNumberOfLastShadowMountDirectoryFullPathElements:
                    
                str_list_listShadowMountDirectoryFullPaths[ \
                    iNumberOfShadowMountDirectoryFullPaths - 1] = \
                    str_listLastShadowMountDirectoryFullPath[ \
                    0:iNumberOfElementsInShortestCommonParentDirectoryPath]

        
        #-----------
        #Stage 2-2-3
        #Create self._str_listShadowMountDirectoryFullPaths.
        #-----------
        self._str_listShadowMountDirectoryFullPaths = []
        
        for str_listShadowMountDirectoryFullPath in \
            str_list_listShadowMountDirectoryFullPaths:
            strShadowMountDirectoryFullPath = \
                self._PathSeparator.join(str_listShadowMountDirectoryFullPath)
            self._str_listShadowMountDirectoryFullPaths.append( \
                strShadowMountDirectoryFullPath)


        #----------------------------------------------------------------------
        #Stage 2-3
        #Create self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists,
        #self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists
        #self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists.
        #----------------------------------------------------------------------
        
        str_listUserSpecifiedBackupSourceDirectoryFullPaths = \
            self._str_listUserSpecifiedBackupSourceDirectoryFullPaths.copy()
        str_listUserSpecifiedDirectoriesToExclude = \
            self._str_listUserSpecifiedDirectoriesToExclude.copy()
        str_listUserSpecifiedFilesToExclude = \
            self._str_listUserSpecifiedFilesToExclude.copy()
            
                
        for strShadowMountDirectoryFullPath in \
            self._str_listShadowMountDirectoryFullPaths:
            
            iShadowMountDirectoryFullPathLength = \
                len(strShadowMountDirectoryFullPath)                    

            #Update
            #self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists.
            for iUserSpecifiedBackupSourceDirectoryFullPathIndex in range( \
                len(str_listUserSpecifiedBackupSourceDirectoryFullPaths) - 1,
                -1, -1):                
                
                strUserSpecifiedBackupSourceDirectoryFullPath = \
                    str_listUserSpecifiedBackupSourceDirectoryFullPaths[ \
                    iUserSpecifiedBackupSourceDirectoryFullPathIndex]
                    
                if strUserSpecifiedBackupSourceDirectoryFullPath[ \
                    0:iShadowMountDirectoryFullPathLength] != \
                    strShadowMountDirectoryFullPath:
                    continue
                
                iUserSpecifiedBackupSourceDirectoryFullPathLength = \
                    len(strUserSpecifiedBackupSourceDirectoryFullPath)
                    
                strIncludedShadowMountFolderFullPath = \
                    os.path.join(self._aam_abl.strShadowCopyDriveName + ':',
                    strUserSpecifiedBackupSourceDirectoryFullPath[ \
                    iShadowMountDirectoryFullPathLength: \
                    iUserSpecifiedBackupSourceDirectoryFullPathLength])
                
                if strShadowMountDirectoryFullPath in \
                    self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists:
                    self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists[ \
                    strShadowMountDirectoryFullPath].append( \
                    strIncludedShadowMountFolderFullPath)
                else:
                    self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists[ \
                    strShadowMountDirectoryFullPath] = \
                    [strIncludedShadowMountFolderFullPath]
                
                del str_listUserSpecifiedBackupSourceDirectoryFullPaths[ \
                    iUserSpecifiedBackupSourceDirectoryFullPathIndex]
                
                
            #Update
            #self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists.
            str_listDirectoriesToExcludeInThisShadowMountDirectory = []
            
            for iUserSpecifiedDirectoryToExcludeIndex in range( \
                len(str_listUserSpecifiedDirectoriesToExclude) - 1, -1, -1):
                                    
                strUserSpecifiedDirectoryToExclude = \
                    str_listUserSpecifiedDirectoriesToExclude[ \
                    iUserSpecifiedDirectoryToExcludeIndex]
                    
                if self._PathSeparator in strUserSpecifiedDirectoryToExclude:  
                    if strShadowMountDirectoryFullPath != \
                        strUserSpecifiedDirectoryToExclude[ \
                        0:iShadowMountDirectoryFullPathLength]:
                        continue

                    str_listDirectoriesToExcludeInThisShadowMountDirectory.append( \
                        strUserSpecifiedDirectoryToExclude.replace( \
                        strShadowMountDirectoryFullPath, 
                        self._aam_abl.strShadowCopyDriveName + ':'))
                    
                    del str_listUserSpecifiedDirectoriesToExclude[ \
                        iUserSpecifiedDirectoryToExcludeIndex]                    
                else:
                    str_listDirectoriesToExcludeInThisShadowMountDirectory.append( \
                        strUserSpecifiedDirectoryToExclude)
                    
            self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists[ \
                strShadowMountDirectoryFullPath] = \
                str_listDirectoriesToExcludeInThisShadowMountDirectory  


            #Update
            #self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists.                
            str_listFilesToExcludeInThisShadowMountDirectory = []
            
            for iUserSpecifiedFileToExcludeIndex in range( \
                len(str_listUserSpecifiedFilesToExclude) - 1, -1, -1):
                                    
                strUserSpecifiedFileToExclude = \
                    str_listUserSpecifiedFilesToExclude[ \
                    iUserSpecifiedFileToExcludeIndex]
                    
                if self._PathSeparator in strUserSpecifiedFileToExclude:
                    if strShadowMountDirectoryFullPath != \
                        strUserSpecifiedFileToExclude[ \
                        0:iShadowMountDirectoryFullPathLength]:
                        continue

                    str_listFilesToExcludeInThisShadowMountDirectory.append( \
                        strUserSpecifiedFileToExclude.replace( \
                        strShadowMountDirectoryFullPath, 
                        self._aam_abl.strShadowCopyDriveName + ':'))
                    
                    del str_listUserSpecifiedFilesToExclude[ \
                        iUserSpecifiedFileToExcludeIndex]                    
                else:
                    str_listFilesToExcludeInThisShadowMountDirectory.append( \
                        strUserSpecifiedFileToExclude)
                    
            self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists[ \
                strShadowMountDirectoryFullPath] = \
                str_listFilesToExcludeInThisShadowMountDirectory                
       
                
        #----------------------------------------------------------------------
        #Stage 2-4
        #Save in the local backup log the directories to backup, 
        #the directories to shadow mount, and folders and files to exclude.
        #----------------------------------------------------------------------  

        #Log the directories to backup.
        self._fileLocalBackupLog.write('\n\n')
        self._fileLocalBackupLog.write('---------------------\n')
        self._fileLocalBackupLog.write('Directories to backup\n')
        self._fileLocalBackupLog.write('---------------------\n')
        
        for strUserSpecifiedBackupSourceDirectoryFullPaths in \
            self._str_listUserSpecifiedBackupSourceDirectoryFullPaths:
            self._fileLocalBackupLog.write( \
                strUserSpecifiedBackupSourceDirectoryFullPaths + '\n')
        
        #Log the directories to shadow mount.
        self._fileLocalBackupLog.write('\n\n')
        self._fileLocalBackupLog.write('---------------------------\n')
        self._fileLocalBackupLog.write('Directories to shadow mount\n')
        self._fileLocalBackupLog.write('---------------------------\n')

        for strShadowMountDirectoryFullPath in \
            self._str_listShadowMountDirectoryFullPaths:
            self._fileLocalBackupLog.write( \
                strShadowMountDirectoryFullPath + '\n')

        #Log the folders to exclude.
        self._fileLocalBackupLog.write('\n\n')
        self._fileLocalBackupLog.write('------------------\n')
        self._fileLocalBackupLog.write('Folders to exclude\n')
        self._fileLocalBackupLog.write('------------------\n')        
        
        for strUserSpecifiedDirectoryToExclude in \
            self._str_listUserSpecifiedDirectoriesToExclude:
            self._fileLocalBackupLog.write( \
                strUserSpecifiedDirectoryToExclude + '\n')        
        
        #Log the files to exclude.
        self._fileLocalBackupLog.write('\n\n')
        self._fileLocalBackupLog.write('----------------\n')
        self._fileLocalBackupLog.write('Files to exclude\n')
        self._fileLocalBackupLog.write('----------------\n')  
        
        for strUserSpecifiedFileToExclude in \
            self._str_listUserSpecifiedFilesToExclude:
            self._fileLocalBackupLog.write( \
                strUserSpecifiedFileToExclude + '\n')        
        
        
        #######################################################################
        #Stage 3
        #-------
        #AWS S3 connection testing and
        #latest AWS S3 backup dates and times acquisition
        #######################################################################
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            self._BuildBackupSourceAwsS3UniqueNames()
            
            #---------------------------
            #backup AWS S3 bucket query
            #---------------------------   
            if strBackupOperationType == 'regular-backup':
                self._QueryBackupAwsS3Bucket( \
                    self._datetimeBackupExecutionStart.year,
                    self._datetimeBackupExecutionStart.month,
                    self._aam_abl.strUniqueBackupSourceLocationName)
                
            else:  #strBackupOperationType == 'incremental-only-backup'

                iYear = self._datetimeBackupExecutionStart.year
                iMonth = self._datetimeBackupExecutionStart.month
                
                iNumberOfBacktracedMonths = 1
                
                while True:
                    self._QueryBackupAwsS3Bucket(iYear, iMonth, 
                        self._aam_abl.strUniqueBackupSourceLocationName)
                    
                    if self._bAwsS3QueryFailure == False and \
                        self._strLatestCompleteUploadAwsS3FullBackupDate != '':
                        break
                                    
                    if iNumberOfBacktracedMonths >= \
                        self._iBackupAwsS3BucketObjectLifetimeInNumberOfMonths:
                        break
                    
                    iNumberOfBacktracedMonths += 1
                    
                    if iMonth == 1:
                        iMonth = 12
                        iYear -= 1
                    else:
                        iMonth -= 1
              
                
            strReportMessage = '\n\n' + strBackupOperationType + \
                ' AWS S3 query result:\n' + \
                '==========================================\n' + \
                'Full-backup date time: ' + \
                self._strLatestCompleteUploadAwsS3FullBackupDate + ' ' + \
                self._strLatestCompleteUploadAwsS3FullBackupTime + '\n' + \
                'Incremental-backup date time: ' + \
                self._strLatestCompleteUploadAwsS3IncrementalBackupDate + ' ' + \
                self._strLatestCompleteUploadAwsS3IncrementalBackupTime
            print(strReportMessage)
            self._fileLocalBackupLog.write(strReportMessage)
            
            
            if self._bAwsS3QueryFailure:
                self._aam_abl.str_listBackupDestinationTypes.remove('AWS')
                self._bBackupSuccess = False
                
                if 'local' not in self._aam_abl.str_listBackupDestinationTypes:
                    strErrorMessage = 'No local backup.  AWS S3 query failure.  \
Aborting backup operation.'
                    self._SendEmailReport()
                    self._fileLocalBackupLog.write(strErrorMessage)
                    self._fileLocalBackupLog.close()
                    self._filelock.release()
                    print(strErrorMessage)
                    if self._bWaitForUserInputBeforeClosing:
                        input("Press Enter to close the program...")                 
                    sys.exit()                         

            if strBackupOperationType == 'incremental-only-backup' and \
                self._strLatestCompleteUploadAwsS3FullBackupDate == '':
                strErrorMessage = '\n\nNo AWS S3 full backup for \
incremental-only backup.  Exiting program.'
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                print(strErrorMessage)
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                 
                sys.exit()
                
                
            #---------------------------------
            #Automatic force backup processing
            #---------------------------------
            if self._strLatestCompleteUploadAwsS3FullBackupDate != '' and \
                self._aam_abl.strAutomaticForceFullBackup == 'yes' and \
                'AWS' in self._aam_abl.str_listBackupDestinationTypes:
                #[12/4/2020 6:11 PM CST]
                #if AWS S3 query failed, 'AWS' is no longer in
                #self._aam_abl.str_listBackupDestinationTypes.
                #in that case, automatic force backup processing does not
                #need to be done, since it is for AWS S3 backup only,
                #and AWS S3 backup is skipped when the AWS S3 query fails.

                datetimeLastAwsS3FullBackup = datetime.datetime.strptime( \
                    self._strLatestCompleteUploadAwsS3FullBackupDate + ' ' + \
                    self._strLatestCompleteUploadAwsS3FullBackupTime,
                    "%Y%m%d %H%M%S.%f")
                
                fFileModification = os.path.getmtime( \
                    self._aam_abl.strBackupInstructionPlainTextFileFullPath)
                datetimeFileModification = datetime.datetime.fromtimestamp( \
                    fFileModification)
                    
                fFileCreation = os.path.getctime( \
                    self._aam_abl.strBackupInstructionPlainTextFileFullPath)
                datetimeFileCreation = datetime.datetime.fromtimestamp( \
                    fFileCreation)
            
                if datetimeFileModification > datetimeLastAwsS3FullBackup or \
                    datetimeFileCreation > datetimeLastAwsS3FullBackup:
                                        
                    if strBackupOperationType == 'incremental-only-backup':
                        strErrorMessage = '\n\nOutdated AWS S3 full backup for \
incremental-only backup.  Full backup must be performed first.  Exiting program.'
                        self._fileLocalBackupLog.write(strErrorMessage)
                        #self._bBackupSuccess = False
                        #self._SendEmailReport()
                        self._fileLocalBackupLog.close()
                        self._filelock.release()
                        print(strErrorMessage)
                        if self._bWaitForUserInputBeforeClosing:
                            input("Press Enter to close the program...")                         
                        sys.exit()   
                        
                    self._aam_abl.strForceFullBackup = 'yes'
            
            
        #######################################################################
        #Stage 4
        #-------
        #AWS S3 backup files directory creation
        #######################################################################
        #https://stackoverflow.com/questions/273192/how-can-i-safely-create-a-nested-directory
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            strDateTime = self._strBackupExecutionStartDateTime.replace('-', '')
            strDateTime = strDateTime.replace(':', '')
            strDateTime = strDateTime.replace(' ', '_')
            
            self._strAwsS3BackupFilesDirectoryFullPath = os.path.join( \
                self._strAwsS3BackupFilesDirectoryParentDirectoryFullPath,
                self._aam_abl.strUniqueBackupSourceLocationName.replace( \
                    ' ', '_') + strDateTime)
            
            try:
                pathlib.Path(self._strAwsS3BackupFilesDirectoryFullPath).mkdir( \
                    parents=True, exist_ok=True)
            except Exception as exc:
                strErrorMessage = 'AWS S3 backup files directory creation \
error.\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                print('Critical error.  AWS S3 backup files directory \
creation failure.  Aborting regular backup operation.')
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                
                sys.exit()
                
        
        #######################################################################
        #Stage 5
        #-------
        #Shadow-mount directories processing
        #######################################################################

        #Compute whether to perform full or incremental backup.
        strLastAwsS3FullBackupDateAndTime = \
            self._strLatestCompleteUploadAwsS3FullBackupDate + ' ' + \
            self._strLatestCompleteUploadAwsS3FullBackupTime
        strLastAwsS3FullBackupDateAndTime = \
            strLastAwsS3FullBackupDateAndTime.strip()
                        
        if strLastAwsS3FullBackupDateAndTime == '':
            self._strBackupScope = 'full-backup'
        elif self._aam_abl.strOperationType == 'regular-backup':
            if self._aam_abl.strForceFullBackup == 'yes':
                self._strBackupScope = 'full-backup'
            else: #self._aam_abl.strForceFullBackup == 'no'
                datetimeLastAwsS3FullBackup = datetime.datetime.strptime( \
                    strLastAwsS3FullBackupDateAndTime, "%Y%m%d %H%M%S.%f")
                
                datetimeBackupExecutionStart = datetime.datetime.strptime( \
                    self._strCommandArgumentBackupExecutionStartDateTime,
                    "%Y%m%d %H%M%S.%f")                    
                
                if datetimeLastAwsS3FullBackup.month == \
                    datetimeBackupExecutionStart.month:
                    self._strBackupScope = 'incremental-backup'                  
                else:
                    self._strBackupScope = 'full-backup'                
        else: #'incremental-only-backup'
            self._strBackupScope = 'incremental-backup' 



        strShadowCopyInstructionFileFullPath = os.path.join( \
            self._strProgramFileDirectoryFullPath,
            'shadow_copy_instruction.txt')
        
        for strShadowMountDirectoryFullPath in \
            self._str_listShadowMountDirectoryFullPaths:

            #------------------------------------------------------------------
            #Stage 5-1
            #Create a temporary plain text file that includes the lists of 
            #the folders and files to include and exclude, 
            #for this shadow-copy mounted directory.
            #------------------------------------------------------------------            
            try:
                fileShadowCopyInstruction = open( \
                    strShadowCopyInstructionFileFullPath, 'w', encoding='utf-8')
                
                #Write the list of folders to include (for use by 7z.exe).
                str_listIncludedDirectories = \
                    self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists[ \
                    strShadowMountDirectoryFullPath]
                for strIncludedDirectory in str_listIncludedDirectories:
                    fileShadowCopyInstruction.write( \
                        strIncludedDirectory + '\n')
                    #The ending path separator in strIncludedDirectory is used
                    #in PerformShadowSpawnExecutedBackUpOperation(), hence
                    #it must be present in shadow_copy_instruction.txt that
                    #will be generated later on using
                    #self._str_dictShadowMountDirectoryFullPathsToIncludedDirectoryLists.
                    #strUserExcludedDirectory is guaranteed to end in
                    #the path separator due to the code in
                    #the "AAM Auto Backup instruction plain text file processing"
                    #code block in _ExecuteBackup() earlier, which was required 
                    #for the proper shadow-mounted directory factoring.
                    #note that in Robocopy command, called later
                    #in PerformShadowSpawnExecutedBackUpOperation(),
                    #no path should end with a path separator; otherwise,
                    #Robocopy would generator error.
                    #[12/17/2020 6:31 PM CST]
                
                #Write the list of the user-excluded folders to exclude
                #(for use by Robocopy and 7z.exe).
                fileShadowCopyInstruction.write('\n')
                str_listUserExcludedDirectories = \
                    self._str_dictShadowMountDirectoryFullPathsToUserExcludedDirectoryLists[ \
                    strShadowMountDirectoryFullPath]
                for strUserExcludedDirectory in str_listUserExcludedDirectories:
                    fileShadowCopyInstruction.write( \
                        strUserExcludedDirectory + '\n')
                
                #Write the list of the user-excluded files to exclude
                #(for use by Robocopy and 7z.exe).
                fileShadowCopyInstruction.write('\n')
                str_listUserExcludedFiles = \
                    self._str_dictShadowMountDirectoryFullPathsToUserExcludedFileLists[ \
                    strShadowMountDirectoryFullPath]
                for strUserExcludedFile in str_listUserExcludedFiles:
                    fileShadowCopyInstruction.write( \
                        strUserExcludedFile + '\n')                  
                
                
                fileShadowCopyInstruction.close()
            except Exception as exc:
                try:
                    fileShadowCopyInstruction.close()
                except:
                    pass
                strErrorMessage = \
                    'Failure to create the shadow copy instruction file.  ' + \
                    strShadowCopyInstructionFileFullPath + '\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                 
                sys.exit()                
                               
                
            #------------------------------------------------------------------
            #Stage 5-2
            #Delete the shadow copy command output file.
            #------------------------------------------------------------------
            strShadowSpawnCommandOutputTextFile = \
                'shadow_copy_command_output.txt'
            strShadowSpawnCommandOutputTextFileFullPath = os.path.join( \
                self._strProgramFileDirectoryFullPath,
                strShadowSpawnCommandOutputTextFile)
            
            try:
                os.remove(strShadowSpawnCommandOutputTextFileFullPath)
            except OSError as e: # this would be "except OSError, e:" before Python 2.6
                if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                    strErrorMessage = 'Shadow copy command output file \
deletion error.\n' + str(e)
                    print(strErrorMessage)
                    self._fileLocalBackupLog.write(strErrorMessage)
                    self._bBackupSuccess = False
                    self._SendEmailReport()
                    self._fileLocalBackupLog.close()
                    self._filelock.release()
                    print('Critical error.  Shadow copy command output file \
deletion failure.  Aborting backup operation.')
                    if self._bWaitForUserInputBeforeClosing:
                        input("Press Enter to close the program...")                      
                    sys.exit()         
            
            #------------------------------------------------------------------
            #Stage 5-3
            #Execute the ShadowSpawn command.
            #------------------------------------------------------------------
            
            #TO DO [1/6/2021 1:34 PM CST]
            #for Robocentric Producer v1.0, try executing shadowspawn.exe
            #via a batch file, which executes chcp first for setting Unicode-8
            #before executing shadowspawn.exe.
            
            strShadowSpawnCommand = 'ShadowSpawn.exe "' + \
                strShadowMountDirectoryFullPath + '" ' + \
                self._aam_abl.strShadowCopyDriveName + ': "' + \
                self._aam_abl.strPythonExecutableFullPath + \
                '" AAM_auto_backup.py ' + strBackupOperationType + \
                ' ShadowSpawn "' + \
                self._strLatestCompleteUploadAwsS3FullBackupDate + ' ' + \
                self._strLatestCompleteUploadAwsS3FullBackupTime + '" "' + \
                self._strLatestCompleteUploadAwsS3IncrementalBackupDate + ' ' + \
                self._strLatestCompleteUploadAwsS3IncrementalBackupTime + '" "' + \
                self._strCommandArgumentBackupExecutionStartDateTime + '" "' + \
                strShadowMountDirectoryFullPath + '" "' + \
                self._aam_abl.strShadowCopyDriveName + '" "' + \
                ' | '.join(self._aam_abl.str_listBackupDestinationTypes) + '" "' + \
                self._aam_abl.strLocalBackupDestinationDirectoryFullPath + '" "' + \
                str(self._aam_abl.bKeepMissingBackupSourcesFilesInBackupDestination) + '" "' + \
                self._aam_abl.strBackupEncryptionAes256Key + '" "' + \
                self._aam_abl.strUniqueBackupSourceLocationName + '" "' + \
                self._strAwsS3BackupFilesDirectoryFullPath + '" "' + \
                self._aam_abl.strForceFullBackup + '" "' + \
                self._strBackupScope + '"' + \
                ' > "' + strShadowSpawnCommandOutputTextFile + '"'
            
            try:
                os.chdir(self._strProgramFileDirectoryFullPath)
                os.system(strShadowSpawnCommand)
            except Exception as exc:
                strErrorMessage = 'ShadowSpawn.exe execution error.\n' + \
                    strShadowSpawnCommand + '\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                print('Critical error.  ShadowSpawn.exe execution failure.  \
Aborting backup operation.')
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                
                sys.exit()

            
            #------------------------------------------------------------------
            #Stage 5-4
            #Process ShadowSpawn command output text file.
            #------------------------------------------------------------------        
            if not os.path.isfile(strShadowSpawnCommandOutputTextFileFullPath):
                strErrorMessage = 'Critical error.  No ShadowSpawn.exe command \
output file.'
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage + '\n')
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                  
                sys.exit()

            bBackupBatchFileExecutionSuccessMessage = False
            bRobocopySuccessMessage = False
            b7zExeSuccessMessage = False
            bFilesToIncrementallyBackupStatusMessage = False
            bLocalBackupDestinationValidationFailureMessage = False
            

            try:
                self._fileLocalBackupLog.write("\n\n\n")
                
                with open(strShadowSpawnCommandOutputTextFileFullPath, 'r', 
                    encoding='cp437') as fileShadowSpawnCommandOutput:
                    for strShadowSpawnCommandOutputLine in \
                        fileShadowSpawnCommandOutput:

                        self._fileLocalBackupLog.write( \
                            strShadowSpawnCommandOutputLine)
                        
                        #check for regular-backup batch file execution success message.
                        if self._strBackupBatchFileExecutionSuccessMessage \
                            in strShadowSpawnCommandOutputLine:
                            bBackupBatchFileExecutionSuccessMessage = True
                                
                        #check for Robocopy success message.
                        if self._strRobocopySuccessMessage \
                            in strShadowSpawnCommandOutputLine:
                            bRobocopySuccessMessage = True
                            
                        #check for 7z.exe success message.
                        if self._str7zExeSuccessMessage \
                            in strShadowSpawnCommandOutputLine:
                            b7zExeSuccessMessage = True
                            
                        #check for files to incrementally backup status.
                        if self._strFilesToIncrementallyBackupStatusMessage \
                            in strShadowSpawnCommandOutputLine:
                            bFilesToIncrementallyBackupStatusMessage = True
                            
                        #check for a local backup-destination validation failure.
                        if self._strLocalBackupDestinationValidationFailureMessage \
                            in strShadowSpawnCommandOutputLine:
                            bLocalBackupDestinationValidationFailureMessage = True                        
                        
                self._fileLocalBackupLog.write("\n\n\n")
                        
            except Exception as exc:
                strErrorMessage = 'File I/O error.  ShadowSpawn.exe command \
output file reading error.\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                  
                sys.exit()
            
            
            strErrorMessage = ''
                
            if not bBackupBatchFileExecutionSuccessMessage:
                strErrorMessage = 'No backup batch file execution \
success message.  Aborting backup.'
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                
            if 'local' in self._aam_abl.str_listBackupDestinationTypes and \
                not bRobocopySuccessMessage:
                strErrorMessage = 'No Robocopy execution \
success message.  Aborting backup.'
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                
            if 'AWS' in self._aam_abl.str_listBackupDestinationTypes and \
                not b7zExeSuccessMessage:
                strErrorMessage = 'No 7z.exe execution \
success message.  Aborting backup.'
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
            
            if strErrorMessage != '':
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                print('Critical error.  ShadowSpawn.exe execution failure \
Aborting regular backup operation.')
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")                  
                sys.exit()            
            
            if not bFilesToIncrementallyBackupStatusMessage:
                self._str_listNoIncrementalBackupFilesShadowMountDirectoryFullPaths.append( \
                    strShadowMountDirectoryFullPath)
            
            if bLocalBackupDestinationValidationFailureMessage:
                self._str_listLocalBackupValidationFailureShadowMountDirectoryFullPaths.append( \
                  strShadowMountDirectoryFullPath)
            
        
        #######################################################################
        #Stage 6
        #-------
        #AWS S3 backup files upload and deletion
        #######################################################################
        
        #TO DO [11/2/2020 7:09 PM CST]
        #I need to decide how to do this.
        #in all likely chance, I'll scan the entire local archive files
        #directory, build a list of backup-source file set lists,
        #then auto-generate and upload the upload-completion indicator file
        #after uploading each backup-source file set.
        #
        #I need to resolve how to handle the backup-sources with no files to
        #incrementally backup.
        #in all likely chance, if no archive file, I'll consider the backup 
        #source having no files to incrementally back up in this run.
        
        #----------------------------------------------------------------------
        #Stage 6-1
        #Build the list of archive files to upload.
        #----------------------------------------------------------------------
        #str_listArchiveFileFullPaths = []
        dictBackupSourceNamesToArchiveFileFullPathLists = {}
        
        strUniqueBackupSourceLocationName = ''
        strFullBackupDate = ''
        strFullBackupTime = ''
        strIncrementalBackupDate = ''
        strIncrementalBackupTime = ''
                        
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            try:
                for vDirectoryItem in \
                    os.listdir(self._strAwsS3BackupFilesDirectoryFullPath):
                        
                    strArchiveFileFullName = vDirectoryItem
                    strArchiveFileFullPath = os.path.join( \
                        self._strAwsS3BackupFilesDirectoryFullPath, vDirectoryItem)                    
                        
                    if not os.path.isfile(strArchiveFileFullPath):
                        continue
    #                    strErrorMessage = 'File I/O error.  Wrong type of item in \
    #the local archive file directory.\n' + \
    #                        self._strAwsS3BackupFilesDirectoryFullPath + '\n' + \
    #                        vDirectoryItem
    #                    print(strErrorMessage)
    #                    self._fileLocalBackupLog.write(strErrorMessage)
    #                    self._bBackupSuccess = False
    #                    self._SendEmailReport()
    #                    self._fileLocalBackupLog.close()
    #                    self._filelock.release()
    #                    if self._bWaitForUserInputBeforeClosing:
    #                        input("Press Enter to close the program...")                     
    #                    sys.exit()   
                                    
                    regexp_match_objLocalArchiveFileName = \
                        self.regexp_objBackupAwsS3ObjectNameParser.search( \
                        strArchiveFileFullName)
                        
                    if regexp_match_objLocalArchiveFileName == None:
                        continue
    #                    strErrorMessage = 'File I/O error.  Wrong type of item in \
    #the local archive file directory.\n' + \
    #                        self._strAwsS3BackupFilesDirectoryFullPath + '\n' + \
    #                        vDirectoryItem
    #                    print(strErrorMessage)
    #                    self._fileLocalBackupLog.write(strErrorMessage)
    #                    self._bBackupSuccess = False
    #                    self._SendEmailReport()
    #                    self._fileLocalBackupLog.close()
    #                    self._filelock.release()
    #                    if self._bWaitForUserInputBeforeClosing:
    #                        input("Press Enter to close the program...")                     
    #                    sys.exit()   
                        
                    strBackupSourceUniqueName = \
                        regexp_match_objLocalArchiveFileName.group(9) 
                        
                    if strBackupSourceUniqueName in \
                        dictBackupSourceNamesToArchiveFileFullPathLists:
                        dictBackupSourceNamesToArchiveFileFullPathLists[ \
                            strBackupSourceUniqueName].append(  \
                            strArchiveFileFullPath)
                    else:
                        dictBackupSourceNamesToArchiveFileFullPathLists[ \
                            strBackupSourceUniqueName] = \
                            [strArchiveFileFullPath]
                          
                            
                    if strUniqueBackupSourceLocationName == '':
                        strUniqueBackupSourceLocationName = \
                            regexp_match_objLocalArchiveFileName.group(1)
                        strFullBackupDate = \
                            regexp_match_objLocalArchiveFileName.group(2)
                        strFullBackupTime = \
                            regexp_match_objLocalArchiveFileName.group(3) + '.' + \
                            regexp_match_objLocalArchiveFileName.group(4)
                        strIncrementalBackupDate = \
                            regexp_match_objLocalArchiveFileName.group(5)
                        strIncrementalBackupTime = \
                            regexp_match_objLocalArchiveFileName.group(6) + '.' + \
                            regexp_match_objLocalArchiveFileName.group(7)                        
                        
            except Exception as exc:
                strErrorMessage = 'File I/O error.  File read error in \
the local archive file directory.\n' + \
                    self._strAwsS3BackupFilesDirectoryFullPath + '\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")             
                sys.exit()   
            

        #----------------------------------------------------------------------
        #Stage 6-2
        #Upload the archive files.
        #----------------------------------------------------------------------
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            try:
                for strBackupSourceAwsS3UniqueName in \
                    self._str_listBackupSourceAwsS3UniqueNames:
                        
                    #Upload the backup-source archive files, if applicable.
                    if strBackupSourceAwsS3UniqueName in \
                        dictBackupSourceNamesToArchiveFileFullPathLists:
                            
                        for strArchiveFileFullPath in \
                            dictBackupSourceNamesToArchiveFileFullPathLists[ \
                            strBackupSourceAwsS3UniqueName]:
                                
                            strArchiveFileFullName = os.path.basename( \
                                strArchiveFileFullPath)
                                
                            strMessage = 'Uploading ' + strArchiveFileFullName
                            self._fileLocalBackupLog.write(strMessage + '\n')
                            print(strMessage)                        
                            
                            self.backup_s3_bucket.upload_file( \
                                strArchiveFileFullPath, strArchiveFileFullName,
                                ExtraArgs={'StorageClass': 'DEEP_ARCHIVE'}) 
                            
                    #Create the backup-source archive files upload-completion 
                    #indicator file.
                    strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullName \
                        = strUniqueBackupSourceLocationName + '_' + \
                        strFullBackupDate + '_' + strFullBackupTime + '_' + \
                        strIncrementalBackupDate + '_' + \
                        strIncrementalBackupTime + '_yes_' + \
                        strBackupSourceAwsS3UniqueName
                    strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullPath \
                        = os.path.join(self._strAwsS3BackupFilesDirectoryFullPath,
                        strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullName)  
                    
                    with open( \
                        strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullPath, 
                        'w', encoding='utf-8') as \
                        fileBackupSourceArchiveFilesUploadCompletionIndicator:                
                        fileBackupSourceArchiveFilesUploadCompletionIndicator.write( \
                            'done')
                    
                    #Upload the backup-source archive files upload-completion 
                    #indicator file.
                    self.backup_s3_bucket.upload_file( \
                        strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullPath,
                        strBackupSourceArchiveFilesUploadCompletionIndicatorFileFullName,
                        ExtraArgs={'StorageClass': 'DEEP_ARCHIVE'})                
                                                    
            except Exception as exc:
                strErrorMessage = 'AWS S3 upload error.\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")             
                sys.exit()
        
                
        #----------------------------------------------------------------------
        #Stage 6-3
        #Remove the local archive files.
        #----------------------------------------------------------------------        
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            #https://stackoverflow.com/questions/43756284/how-to-remove-a-directory-including-all-its-files-in-python
            try:
                shutil.rmtree(self._strAwsS3BackupFilesDirectoryFullPath)
            except Exception as exc:
                strErrorMessage = 'File I/O error.  The local archive file \
    directory deletion error.\n' + self._strAwsS3BackupFilesDirectoryFullPath + \
                '\n' + str(exc)
                print(strErrorMessage)
                self._fileLocalBackupLog.write(strErrorMessage)
                self._bBackupSuccess = False
                self._SendEmailReport()
                self._fileLocalBackupLog.close()
                self._filelock.release()
                if self._bWaitForUserInputBeforeClosing:
                    input("Press Enter to close the program...")             
                sys.exit()              
        
        
        #######################################################################
        #Stage 7
        #-------
        #Temporary output files deletion
        #######################################################################
        try:
            strBackupBatchFileFullPath = os.path.join( \
                self._strProgramFileDirectoryFullPath,
                'AAM_Auto_Backup_shadow_copy.bat')
            
            os.remove(strShadowCopyInstructionFileFullPath)
            os.remove(strBackupBatchFileFullPath)
            os.remove(strShadowSpawnCommandOutputTextFileFullPath)
        except Exception as exc:
            strErrorMessage = 'File I/O error.  A temporary file deletion \
error.\n' + str(exc)
            print(strErrorMessage)
            self._fileLocalBackupLog.write(strErrorMessage + '\n')
            self._bBackupSuccess = False
            self._SendEmailReport()
            self._fileLocalBackupLog.close()
            self._filelock.release()
            if self._bWaitForUserInputBeforeClosing:
                input("Press Enter to close the program...")             
            sys.exit()          
        
        
        #######################################################################
        #Stage 8
        #-------
        #Record the backup ending time
        #######################################################################
        self._datetimeBackupExecutionEnd = datetime.datetime.now()
        self._strBackupExecutionEndDateTime = \
            str(self._datetimeBackupExecutionEnd)
        
        strBackupExecutionEndingDateAndTimeMessage = \
            '\n\nBackup execution ending date and time:  ' + \
            self._strBackupExecutionEndDateTime
        
        self._fileLocalBackupLog.write( \
            strBackupExecutionEndingDateAndTimeMessage)
        print(strBackupExecutionEndingDateAndTimeMessage + '\n')
        
        
        #######################################################################
        #Stage 9
        #-------
        #Email report sending
        #######################################################################
        self._SendEmailReport()
            
               
        #######################################################################
        #Stage 10
        #--------
        #Program execution cleanup
        #######################################################################
        
        #----------------------------------------------------------------------
        #Stage 10-1
        #Local backup log file closing
        #----------------------------------------------------------------------
        try:
            self._fileLocalBackupLog.close()
        except:
            print('Local backup log close failure.')
        
        #----------------------------------------------------------------------
        #Stage 10-2
        #File lock release
        #----------------------------------------------------------------------
        try:
            self._filelock.release()
        except:
            print('File lock release failure.')        
                
            
        if self._bWaitForUserInputBeforeClosing:
            input("Press Enter to close the program...")            
            
        
    def ExecuteRegularBackup(self):
        self._ExecuteBackup('regular-backup')
    
    
    def ExecuteIncrementalOnlyBackup(self):
        self._ExecuteBackup('incremental-only-backup')
                
        
    def _ConvertWildCardExpressionToRegularExpression(self,
        strWildCardExpression):
        strRegularExpression = ''
        
        for strWildCardExpressionCharacter in strWildCardExpression:
            
            if strWildCardExpressionCharacter == '?':
                strRegularExpression += '.'
            elif strWildCardExpressionCharacter == '*':
                strRegularExpression += '.*?'
            elif strWildCardExpressionCharacter == '+':
                strRegularExpression += '\\+'                    
            elif strWildCardExpressionCharacter == '^':
                strRegularExpression += '\\^'
            elif strWildCardExpressionCharacter == '$':
                strRegularExpression += '\\$'
            elif strWildCardExpressionCharacter == '[':
                strRegularExpression += '\\['                    
            elif strWildCardExpressionCharacter == ']':
                strRegularExpression += '\\]'
            elif strWildCardExpressionCharacter == '.':
                strRegularExpression += '\\.'   
            elif strWildCardExpressionCharacter == '|':
                strRegularExpression += '\\|'  
            elif strWildCardExpressionCharacter == '(':
                strRegularExpression += '\\('  
            elif strWildCardExpressionCharacter == ')':
                strRegularExpression += '\\)'                       
            else:
                strRegularExpression += \
                    strWildCardExpressionCharacter 
                    
        return strRegularExpression
        
        
    def PerformShadowSpawnExecutedBackUpOperation(self):
        #INPUTS
        #------
        #command arguments.
        #shadow_copy_instruction.txt
        #
        #OUTPUTS
        #-------
        #shadow_copy_command_output.txt in the AAM Auto Backup program directory.
        #if local backup is on, backup to the local backup destination directory.
        #if AWS backup is on, archive files in the AWS backup destination directory.


        #######################################################################
        #Stage 1
        #-------
        #Process shadow_copy_instruction.txt to build a set of needed data
        #variables.
        #######################################################################        
        self._str_listShadowCopyInclusionFolderFullPaths = []
        self._str_listShadowCopyExclusionFolders = []
        self._str_listShadowCopyExclusionFiles = []
        
        self._str_listShadowCopyNonIncludedFolderFullPaths = []
        
        self._str_listShadowCopyExclusionFolderFullPaths = []
        self._str_listShadowCopyExclusionFileFullPaths = []        
        
        self._str_listShadowCopyExclusionFolderRegularExpressions = []
        self._regexp_obj_listShadowCopyExclusionFolders = []        
        
        self._str_listShadowCopyExclusionFileRegularExpressions = []
        self._regexp_obj_listShadowCopyExclusionFiles = []
        
        
        strShadowCopyInstructionFileFullPath = os.path.join( \
            self._strProgramFileDirectoryFullPath,
            'shadow_copy_instruction.txt')
        
        try:
            fileShadowCopyInstruction = open( \
                strShadowCopyInstructionFileFullPath, 'r', encoding='utf-8')
            
            while True:
                strShadowCopyInstructionLine = \
                    fileShadowCopyInstruction.readline()
                if strShadowCopyInstructionLine == '\n' or \
                    strShadowCopyInstructionLine == '': break  
                
                strShadowCopyInstructionLine = \
                    strShadowCopyInstructionLine.strip()

                self._str_listShadowCopyInclusionFolderFullPaths.append( \
                    strShadowCopyInstructionLine)
            
            while True:
                strShadowCopyInstructionLine = \
                    fileShadowCopyInstruction.readline()
                if strShadowCopyInstructionLine == '\n' or \
                    strShadowCopyInstructionLine == '': break  
                
                strShadowCopyInstructionLine = \
                    strShadowCopyInstructionLine.strip()

                self._str_listShadowCopyExclusionFolders.append( \
                    strShadowCopyInstructionLine)
                
            while True:
                strShadowCopyInstructionLine = \
                    fileShadowCopyInstruction.readline()
                if strShadowCopyInstructionLine == '\n' or \
                    strShadowCopyInstructionLine == '': break  
                
                strShadowCopyInstructionLine = \
                    strShadowCopyInstructionLine.strip()

                self._str_listShadowCopyExclusionFiles.append( \
                    strShadowCopyInstructionLine)                
            
            fileShadowCopyInstruction.close()
        except Exception as exc:
            try:
                fileShadowCopyInstruction.close()
            except:
                pass
            sys.exit('File I/O error on shadow_copy_instruction.txt.\n' + \
                     str(exc))
        
        
        ##########################################################
        #Build self._str_listShadowCopyNonIncludedFolderFullPaths.
        ##########################################################
        str_listParentDirectoryFullPathsToProcessToFindExclusion = \
            [self._aam_abl.strShadowCopyDriveName + ':' \
             + self._PathSeparator]
        str_listNextLevelDirectoryFullPathsToProcessToFindExclusion = []

        try:
            #[12/2/2020 2:04 PM CST]
            #The following code builds 
            #self._str_listShadowCopyNonIncludedFolderFullPaths by scanning
            #every relevant directory in the shadow-mounted drive,
            #using os.listdir() and os.path.isdir().
            #
            #this code builds
            #str_listNextLevelDirectoryFullPathsToProcessToFindExclusion
            #for each set of 
            #str_listParentDirectoryFullPathsToProcessToFindExclusion,
            #then sets
            #str_listParentDirectoryFullPathsToProcessToFindExclusion to
            #str_listNextLevelDirectoryFullPathsToProcessToFindExclusion, and
            #repeats the process, until there is no more directory 
            #in the shadow-mounted drive to process for building
            #self._str_listShadowCopyNonIncludedFolderFullPaths.
            
            while str_listParentDirectoryFullPathsToProcessToFindExclusion != []:
                for strParentDirectoryFullPath in \
                    str_listParentDirectoryFullPathsToProcessToFindExclusion:
                    for strDirectoryItem in os.listdir(strParentDirectoryFullPath):
                        strDirectoryItemFullPath = os.path.join( \
                            strParentDirectoryFullPath, strDirectoryItem)
                        if not os.path.isdir(strDirectoryItemFullPath): continue
                    
                        if platform.system() == 'Windows':
                            strDirectoryItemFullPath = strDirectoryItemFullPath.lower()
                    
                    
                        #[12/2/2020 2:25 PM CST]
                        #Check strDirectoryItemFullPath against
                        #self._str_listShadowCopyInclusionFolderFullPaths
                        #to determine whether strDirectoryItemFullPath should be excluded
                        #or not.
                        #
                        #A more complex/evolved(use this) method than the below
                        #is required.
                        #if strDirectoryItemFullPath not in \
                        #    self._str_listShadowCopyInclusionFolderFullPaths:
                        #    xx
                        #
                        #The following updates
                        #self._str_listShadowCopyNonIncludedFolderFullPaths and
                        #str_listNextLevelDirectoryFullPathsToProcessToFindExclusion.
                        iDirectoryItemFullPathLength = len(strDirectoryItemFullPath)
                        
                        bExcludedDirectory = True
                        bShadowCopyInclusionFolder = False
                        for strShadowCopyInclusionFolderFullPath in \
                            self._str_listShadowCopyInclusionFolderFullPaths:
                                
                            if strDirectoryItemFullPath + self._PathSeparator == \
                                strShadowCopyInclusionFolderFullPath:
                                bExcludedDirectory = False
                                bShadowCopyInclusionFolder = True
                                break
                                
                            try:
                                if strDirectoryItemFullPath == \
                                    strShadowCopyInclusionFolderFullPath[ \
                                    0:iDirectoryItemFullPathLength] and \
                                    strShadowCopyInclusionFolderFullPath[ \
                                    iDirectoryItemFullPathLength] == \
                                    self._PathSeparator:
                                    bExcludedDirectory = False
                                    #[12/2/2020 2:31 PM CST]
                                    #For the explanation on the reason on why
                                    #break is used below, refer to
                                    #the "update [12/2/2020 1:58 PM CST]" section
                                    #in the AAM Auto Backup document.
                                    break
                            except:
                                pass
                            #[12/7/2020 8:45 AM CST]
                            #the above properly handles the following case.
                            #c:\temp\1 (backed up)
                            #c:\temp\12345 (backed up)
                            #c:\temp\123 (not backed up).
                            #the above code excludes c:\temp\123.
                            #only the parent directories of included directories
                            #and the included directories themselves
                            #are not excluded.                            
                                 
                        if bExcludedDirectory:
                            self._str_listShadowCopyNonIncludedFolderFullPaths.append( \
                                strDirectoryItemFullPath)
                        elif not bShadowCopyInclusionFolder: #bExcludedDirectory == False
                            str_listNextLevelDirectoryFullPathsToProcessToFindExclusion.append( \
                                strDirectoryItemFullPath)

                str_listParentDirectoryFullPathsToProcessToFindExclusion = \
                    str_listNextLevelDirectoryFullPathsToProcessToFindExclusion
                    
                str_listNextLevelDirectoryFullPathsToProcessToFindExclusion = []
     
        except Exception as exc:
            sys.exit('File I/O error while computing \
str_listShadowCopyNonIncludedFolderFullPaths.\n' + str(exc))        
        
        
        
        #Build self._str_listShadowCopyExclusionFolderFullPaths,
        #self._str_listShadowCopyExclusionFolderRegularExpressions and
        #self._regexp_obj_listShadowCopyExclusionFolders.
        for strShadowCopyExclusionFolder in \
            self._str_listShadowCopyExclusionFolders:
                
            if self._PathSeparator in strShadowCopyExclusionFolder:
                self._str_listShadowCopyExclusionFolderFullPaths.append( \
                    strShadowCopyExclusionFolder)
                continue
                
            strShadowCopyExclusionFolderRegularExpression = \
                self._ConvertWildCardExpressionToRegularExpression( \
                strShadowCopyExclusionFolder)
            
            regexp_objShadowCopyExclusionFolder = re.compile( \
                strShadowCopyExclusionFolderRegularExpression, re.IGNORECASE)
                
            self._str_listShadowCopyExclusionFolderRegularExpressions.append( \
                strShadowCopyExclusionFolderRegularExpression)
            self._regexp_obj_listShadowCopyExclusionFolders.append( \
                regexp_objShadowCopyExclusionFolder)
        
        
        #Build self._str_listShadowCopyExclusionFileFullPaths,
        #self._str_listShadowCopyExclusionFileRegularExpressions and
        #self._regexp_obj_listShadowCopyExclusionFiles.
        #([12/2/2020 2:50 PM CST] for the reasons on computing the above two
        #data variables, refer to the "file exclusion computation" section 
        #in the AAM Auto Backup document.)
        for strShadowCopyExclusionFile in \
            self._str_listShadowCopyExclusionFiles:
                
            if self._PathSeparator in strShadowCopyExclusionFile:
                self._str_listShadowCopyExclusionFileFullPaths.append( \
                    strShadowCopyExclusionFile)
                continue
                
            strShadowCopyExclusionFileRegularExpression = \
                self._ConvertWildCardExpressionToRegularExpression( \
                strShadowCopyExclusionFile)
            
            regexp_objShadowCopyExclusionFile = re.compile( \
                strShadowCopyExclusionFileRegularExpression, re.IGNORECASE)
                
            self._str_listShadowCopyExclusionFileRegularExpressions.append( \
                strShadowCopyExclusionFileRegularExpression)
            self._regexp_obj_listShadowCopyExclusionFiles.append( \
                regexp_objShadowCopyExclusionFile)        
        
        
        #######################################################################
        #Stage 2
        #-------
        #if applicable, generate the Robocopy command in memory.
        #######################################################################
        if 'local' in self._aam_abl.str_listBackupDestinationTypes:
            strRobocopyDestinationDirectoryFullPath = os.path.join( \
                self._aam_abl.strLocalBackupDestinationDirectoryFullPath,
                self._aam_abl.strLocalBackupSourceDirectoryFullPath.replace( \
                ':', ''))
            
            try:
                pathlib.Path(strRobocopyDestinationDirectoryFullPath).mkdir( \
                    parents=True, exist_ok=True)
            except Exception as exc:
                sys.exit('Robocopy destination directory creation error.\n' + \
                         str(exc))
            
            strRobocopyCommand = 'robocopy.exe ' + \
                self._aam_abl.strShadowCopyDriveName + ': "' + \
                strRobocopyDestinationDirectoryFullPath + '" /e'
                
            if not self._aam_abl.bKeepMissingBackupSourcesFilesInBackupDestination:
                strRobocopyCommand += ' /purge'
        
            if len(self._str_listShadowCopyExclusionFolders) > 0 or \
                len(self._str_listShadowCopyNonIncludedFolderFullPaths) > 0:
                strRobocopyCommand += ' /xd'
                for strShadowCopyExclusionFolder in \
                    self._str_listShadowCopyExclusionFolders:
                    strRobocopyCommand += \
                        ' "' + strShadowCopyExclusionFolder + '"'
                        
                for strShadowCopyNonIncludedFolderFullPath in \
                    self._str_listShadowCopyNonIncludedFolderFullPaths:
                    strRobocopyCommand += \
                        ' "' + strShadowCopyNonIncludedFolderFullPath + '"'
                    
            if len(self._str_listShadowCopyExclusionFiles) > 0:
                strRobocopyCommand += ' /xf'
                for strShadowCopyExclusionFile in \
                    self._str_listShadowCopyExclusionFiles:
                    strRobocopyCommand += \
                        ' "' + strShadowCopyExclusionFile + '"'

    
        #######################################################################
        #Stage 3
        #-------
        #if applicable, scan the shadow copy mount to build
        #the 7z.exe list file(s), and the 7z.exe command.
        #######################################################################
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
                        
            self._strBackupScope = self._aam_abl._strBackupScope
            
            if self._aam_abl.strLastAwsS3IncrementalBackupDateAndTime != '':
                datetimeLastIncrementalAwsS3Backup = \
                    datetime.datetime.strptime( \
                    self._aam_abl.strLastAwsS3IncrementalBackupDateAndTime,
                    "%Y%m%d %H%M%S.%f")

                        
            #Generate the 7z.exe list file(s), and build the 7z.exe command.
            if self._strBackupScope == 'full-backup':
                
                #Generate the inclusion 7z.exe list file.
                str7zInclusionListFileFullName = \
                    self._aam_abl.strBackupExecutionStartDateTime + \
                    '_inclusion_7z_list_file.txt'
                str7zInclusionListFileFullPath = os.path.join( \
                    self._strProgramFileDirectoryFullPath,
                    str7zInclusionListFileFullName)
                
                try:
                    file7zList = open(str7zInclusionListFileFullPath, 'w', 
                                      encoding='utf-8')                
                    
                    for strShadowCopyInclusionFolderFullPaths in \
                        self._str_listShadowCopyInclusionFolderFullPaths:
                    
                        file7zList.write( \
                            strShadowCopyInclusionFolderFullPaths + '\n')
                    
                    file7zList.close()
                    
                except Exception as exc:
                    try:
                        file7zList.close()
                    except:
                        pass
                    sys.exit('7z list file writing error.\n' + \
                             str7zInclusionListFileFullPath + '\n' + str(exc))                
                
                
                #Generate the exclusion 7z.exe list files.
                str7zNonRecursiveExclusionListFileFullName = \
                    self._aam_abl.strBackupExecutionStartDateTime + \
                    '_non-recursive_exclusion_7z_list_file.txt'
                str7zNonRecursiveExclusionListFileFullPath = os.path.join( \
                    self._strProgramFileDirectoryFullPath,
                    str7zNonRecursiveExclusionListFileFullName)

                str7zRecursiveExclusionListFileFullName = \
                    self._aam_abl.strBackupExecutionStartDateTime + \
                    '_recursive_exclusion_7z_list_file.txt'
                str7zRecursiveExclusionListFileFullPath = os.path.join( \
                    self._strProgramFileDirectoryFullPath,
                    str7zRecursiveExclusionListFileFullName)             
                
                try:
                    file7zNonRecursiveExclusionList = \
                        open(str7zNonRecursiveExclusionListFileFullPath, 'w', 
                        encoding='utf-8') 
                    file7zRecursiveExclusionList = \
                        open(str7zRecursiveExclusionListFileFullPath, 'w', 
                        encoding='utf-8')                         
                    
                    for strShadowCopyExclusionFolder in \
                        self._str_listShadowCopyExclusionFolders:
                    
                        if self._PathSeparator in strShadowCopyExclusionFolder:
                            file7zNonRecursiveExclusionList.write( \
                                strShadowCopyExclusionFolder + \
                                self._PathSeparator + '\n')
                        else:
                            file7zRecursiveExclusionList.write( \
                                strShadowCopyExclusionFolder + \
                                self._PathSeparator + '\n')
                    
                    for strShadowCopyExclusionFile in \
                        self._str_listShadowCopyExclusionFiles:
                    
                        if self._PathSeparator in strShadowCopyExclusionFile:
                            file7zNonRecursiveExclusionList.write( \
                                strShadowCopyExclusionFile + '\n')
                        else:
                            file7zRecursiveExclusionList.write( \
                                strShadowCopyExclusionFile + '\n')                 
                    
                    file7zNonRecursiveExclusionList.close()
                    file7zRecursiveExclusionList.close()
                    
                except Exception as exc:
                    try:
                        file7zNonRecursiveExclusionList.close()
                        file7zRecursiveExclusionList.close()
                    except:
                        pass
                    sys.exit('7z list file writing error.\n' + \
                        str7zNonRecursiveExclusionListFileFullPath + '\n' + \
                        str7zRecursiveExclusionListFileFullPath + '\n' + \
                        str(exc))         
                
                
                #Generate the 7z.exe command.
                strBackupSourceUniqueName = \
                    self._aam_abl.strLocalBackupSourceDirectoryFullPath.replace( \
                    ':', '')
                strBackupSourceUniqueName = \
                    strBackupSourceUniqueName.replace(self._PathSeparator, '_')                                                             
                strArchiveFileFullName = \
                    self._aam_abl.strUniqueBackupSourceLocationName + '_' + \
                    self._aam_abl.strBackupExecutionStartDateTime.replace( \
                    ' ', '_') + '_0_0.0_no_' + strBackupSourceUniqueName + '.zip'
                    
                str7zExeCommand = '"' + os.path.join( \
                    self._strProgramFileDirectoryFullPath, '7z.exe"') + \
                    ' a "' + os.path.join( \
                    self._aam_abl.strAwsS3BackupFilesDirectoryFullPath,
                    strArchiveFileFullName) + \
                    '" -spf2 -v4000000000b -mcu=on -mem=AES256 -p' + \
                    self._aam_abl.strBackupEncryptionAes256Key + \
                    ' @"' + str7zInclusionListFileFullPath + '" -xr-@"' + \
                    str7zNonRecursiveExclusionListFileFullPath + '" -xr@"' + \
                    str7zRecursiveExclusionListFileFullPath + '"'
            else: #incremental backup
                
                #Generate the inclusion 7z.exe list file.
                str7zInclusionListFileFullName = \
                    self._aam_abl.strBackupExecutionStartDateTime + \
                    '_inclusion_7z_list_file.txt'
                str7zInclusionListFileFullPath = os.path.join( \
                    self._strProgramFileDirectoryFullPath,
                    str7zInclusionListFileFullName)

                iNumberOfFilesIncrementallyBackedUp = 0

                try:
                    file7zList = open(str7zInclusionListFileFullPath, 'w', 
                                      encoding='utf-8')        
                
                    for strShadowCopyInclusionFolderFullPath in \
                        self._str_listShadowCopyInclusionFolderFullPaths:                
    
                        iShadowCopyInclusionFolderFullPathLength = \
                            len(strShadowCopyInclusionFolderFullPath)
                            
                        for strParentDirectoryFullPath, \
                            str_listChildDirectoryNames, \
                            str_listFileNames in \
                            os.walk(strShadowCopyInclusionFolderFullPath):
                            
                            #--------------------------------------------------
                            #Check if the user-specified folder exclusion(s)
                            #apply to this folder.
                            #--------------------------------------------------
                            bExclude = False
                            
                            #Check for the folder full-path match.                            
                            for strShadowCopyExclusionFolderFullPath in \
                                self._str_listShadowCopyExclusionFolderFullPaths:
                                    
                                iShadowCopyExclusionFolderFullPathLength = \
                                    len(strShadowCopyExclusionFolderFullPath)                                    
                                    
                                try:
                                    if strShadowCopyExclusionFolderFullPath == \
                                        strParentDirectoryFullPath[0: \
                                        iShadowCopyExclusionFolderFullPathLength] and \
                                        strParentDirectoryFullPath[ \
                                        iShadowCopyExclusionFolderFullPathLength] == \
                                        self._PathSeparator:
                                        bExclude = True
                                        break
                                except:
                                    pass
                            
                            if bExclude:
                                continue                            
                            
                            #Check for the folder name match.
                            strParentDirectoryNames = \
                                strParentDirectoryFullPath[ \
                                iShadowCopyInclusionFolderFullPathLength: \
                                len(strParentDirectoryFullPath)]
                            str_listParentDirectoryNames = \
                                strParentDirectoryNames.split( \
                                self._PathSeparator)

                            if str_listParentDirectoryNames != ['']:
                                for regexp_objShadowCopyExclusionFolder in \
                                    self._regexp_obj_listShadowCopyExclusionFolders:
                                                                            
                                    for strParentDirectoryName in \
                                        str_listParentDirectoryNames:
                                        
                                        regexp_match_objExclusionFolder = \
                                            regexp_objShadowCopyExclusionFolder.search( \
                                            strParentDirectoryName)                                         
                                            
                                        if regexp_match_objExclusionFolder != None:
                                            bExclude = True
                                            break
                                    
                                    if bExclude:
                                        break                                  
                                    
                                if bExclude:
                                    continue                                 

                                
                            #--------------------------------------------------
                            #Check if the user-specified file exclusion(s)
                            #apply to the files in this folder.
                            #Record the files that are not excluded.
                            #--------------------------------------------------                            
                            for strFileName in str_listFileNames:
                                                 
                                bExclude = False
                                
                                #Check for the file full-path match. 
                                strFileFullPath = os.path.join( \
                                    strParentDirectoryFullPath,
                                    strFileName)                                  
                                
                                for strShadowCopyExclusionFileFullPath in \
                                    self._str_listShadowCopyExclusionFileFullPaths:                     
                                        
                                    if strFileFullPath == \
                                        strShadowCopyExclusionFileFullPath:
                                        bExclude = True
                                        break                            
                                
                                if bExclude:
                                    continue                                
                                
                               
                                #Check for the file name match.
                                for regexp_objShadowCopyExclusionFile in \
                                    self._regexp_obj_listShadowCopyExclusionFiles:
                                        
                                    regexp_match_objExclusionFile = \
                                        regexp_objShadowCopyExclusionFile.search( \
                                        strFileName) 
                                        
                                    if regexp_match_objExclusionFile != None:
                                        bExclude = True
                                        break                                         
                                       
                                if bExclude:
                                    continue
                                
                                #Check file modification date time.
                                fFileModification = \
                                    os.path.getmtime("\\\\?\\" + strFileFullPath)
                                datetimeFileModification = \
                                    datetime.datetime.fromtimestamp( \
                                    fFileModification)
                                    
                                fFileCreation = \
                                    os.path.getctime("\\\\?\\" + strFileFullPath)
                                datetimeFileCreation = \
                                    datetime.datetime.fromtimestamp( \
                                    fFileCreation)
                                    
                                if datetimeFileModification <= \
                                    datetimeLastIncrementalAwsS3Backup and \
                                    datetimeFileCreation <= \
                                    datetimeLastIncrementalAwsS3Backup:
                                    continue
                                                                   
                            
                                file7zList.write(strFileFullPath + '\n')
                                
                                iNumberOfFilesIncrementallyBackedUp += 1
                            
                    file7zList.close()
                    
                except Exception as exc:
                    try:
                        file7zList.close()
                    except:
                        pass
                    sys.exit('7z list file writing error.\n' + \
                             str7zInclusionListFileFullPath + '\n' + str(exc))
                    
                if iNumberOfFilesIncrementallyBackedUp == 0:
                    print('\nNo files to incrementally back up.')
                else:
                    print('\n' \
                          + self._strFilesToIncrementallyBackupStatusMessage + \
                          str(iNumberOfFilesIncrementallyBackedUp) + '\n')
                    
                    
                #Generate the 7z.exe command.
                strBackupSourceUniqueName = \
                    self._aam_abl.strLocalBackupSourceDirectoryFullPath.replace( \
                    ':', '')
                strBackupSourceUniqueName = \
                    strBackupSourceUniqueName.replace(self._PathSeparator, '_')                                                             
                strArchiveFileFullName = \
                    self._aam_abl.strUniqueBackupSourceLocationName + '_' + \
                    self._aam_abl.strLastAwsS3FullBackupDateAndTime.replace( \
                    ' ', '_') + '_' + \
                    self._aam_abl.strBackupExecutionStartDateTime.replace( \
                    ' ', '_') + '_no_' + strBackupSourceUniqueName + '.zip'
                    
                str7zExeCommand = '"' + os.path.join( \
                    self._strProgramFileDirectoryFullPath, '7z.exe"') + \
                    ' a "' + os.path.join( \
                    self._aam_abl.strAwsS3BackupFilesDirectoryFullPath,
                    strArchiveFileFullName) + \
                    '" -spf2 -v4000000000b -mcu=on -mem=AES256 -p' + \
                    self._aam_abl.strBackupEncryptionAes256Key + \
                    ' @"' + str7zInclusionListFileFullPath + '"'                  
                        
        
        #######################################################################
        #Stage 4
        #-------
        #auto-generate (overwrite or create) the backup batch file.
        ####################################################################### 
        strBackupBatchFileBaseName = 'AAM_Auto_Backup_shadow_copy'
        strBackupBatchFileFullName = strBackupBatchFileBaseName + '.bat'
        strBackupBatchFileFullPath = os.path.join( \
            self._strProgramFileDirectoryFullPath, strBackupBatchFileFullName)   
        
        try:
            fileBackupBatch = open( \
                strBackupBatchFileFullPath, 'w', encoding='utf-8')
            
            fileBackupBatch.write( \
                'cd /D ' + self._aam_abl.strShadowCopyDriveName + ':\n')
            
            if 'local' in self._aam_abl.str_listBackupDestinationTypes:
                fileBackupBatch.write(strRobocopyCommand + '\n')
            
            if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
                fileBackupBatch.write(str7zExeCommand + '\n')
                    
            fileBackupBatch.close() 
            
        except Exception as exc:
            try:
                fileBackupBatch.close()
            except:
                pass
            sys.exit('AAM Auto Backup batch file writing error.\n' + \
                strBackupBatchFileFullPath + '\n' + str(exc))        
        
        #######################################################################
        #Stage 5
        #-------
        #execute the backup batch file.
        #######################################################################
        try:
            os.system('"' + strBackupBatchFileFullPath + '"')
        except Exception as exc:
            sys.exit('AAM Auto Backup batch file execution error.\n' + \
                strBackupBatchFileFullPath + '\n' + str(exc))
        
        
        #######################################################################
        #Stage 6
        #-------
        #perform the local backup-destination validation check.
        #######################################################################
        if 'local' in self._aam_abl.str_listBackupDestinationTypes:
            
            #[12/7/2020 3:00 PM CST]
            #Verify that all the applicable files in the shadow-mounted
            #directory are present and up-to-date in the backup destination.
            
            datetimeBackupExecutionStart = datetime.datetime.strptime( \
                self._aam_abl.strBackupExecutionStartDateTime,
                "%Y%m%d %H%M%S.%f")
            
            print('\n')
            
            try:
                for strShadowCopyInclusionFolderFullPath in \
                    self._str_listShadowCopyInclusionFolderFullPaths:
    
                    iShadowCopyInclusionFolderFullPathLength = \
                        len(strShadowCopyInclusionFolderFullPath)
                        
                    for strParentDirectoryFullPath, \
                        str_listChildDirectoryNames, \
                        str_listFileNames in \
                        os.walk(strShadowCopyInclusionFolderFullPath):
                            
                        #--------------------------------------------------
                        #Check if the user-specified folder exclusion(s)
                        #apply to this folder.
                        #--------------------------------------------------
                        bExclude = False
                        
                        #Check for the folder full-path match.                            
                        for strShadowCopyExclusionFolderFullPath in \
                            self._str_listShadowCopyExclusionFolderFullPaths:
                                
                            iShadowCopyExclusionFolderFullPathLength = \
                                len(strShadowCopyExclusionFolderFullPath)                                    
                                
                            try:
                                if strShadowCopyExclusionFolderFullPath == \
                                    strParentDirectoryFullPath[0: \
                                    iShadowCopyExclusionFolderFullPathLength] \
                                    and \
                                    strParentDirectoryFullPath[ \
                                    iShadowCopyExclusionFolderFullPathLength] \
                                    == self._PathSeparator:
                                    bExclude = True
                                    break    
                            except:
                                break
                        
                        if bExclude:
                            continue                            
                        
                        #Check for the folder name match.
                        strParentDirectoryNames = \
                            strParentDirectoryFullPath[ \
                            iShadowCopyInclusionFolderFullPathLength: \
                            len(strParentDirectoryFullPath)]
                        if strParentDirectoryNames != '':
                            str_listParentDirectoryNames = \
                                strParentDirectoryNames.split( \
                                self._PathSeparator)
                                                            
                            for regexp_objShadowCopyExclusionFolder in \
                                self._regexp_obj_listShadowCopyExclusionFolders:
                                                                        
                                for strParentDirectoryName in \
                                    str_listParentDirectoryNames:
                                    
                                    regexp_match_objExclusionFolder = \
                                        regexp_objShadowCopyExclusionFolder.search( \
                                        strParentDirectoryName)                                         
                                        
                                    if regexp_match_objExclusionFolder != None:
                                        bExclude = True
                                        break
                                
                                if bExclude:
                                    break                                  
                                
                            if bExclude:
                                continue                             
                                                       
                        
                        #--------------------------------------------------
                        #Check if the user-specified file exclusion(s)
                        #apply to the files in this folder.
                        #Check the files that are not excluded.
                        #--------------------------------------------------                            
                        for strFileName in str_listFileNames:
                                             
                            bExclude = False
                            
                            #Check for the file full-path match. 
                            strFileFullPath = os.path.join( \
                                strParentDirectoryFullPath,
                                strFileName)                                  
                            
                            for strShadowCopyExclusionFileFullPath in \
                                self._str_listShadowCopyExclusionFileFullPaths:                     
                                    
                                if strFileFullPath == \
                                    strShadowCopyExclusionFileFullPath:
                                    bExclude = True
                                    break                            
                            
                            if bExclude:
                                continue                                
                            
                           
                            #Check for the file name match.
                            for regexp_objShadowCopyExclusionFile in \
                                self._regexp_obj_listShadowCopyExclusionFiles:
                                    
                                regexp_match_objExclusionFile = \
                                    regexp_objShadowCopyExclusionFile.search( \
                                    strFileName) 
                                    
                                if regexp_match_objExclusionFile != None:
                                    bExclude = True
                                    break                                         
                                   
                            if bExclude:
                                continue
                            
                            #Check file modification date time.
                            fFileModification = \
                                os.path.getmtime("\\\\?\\" + strFileFullPath)
                            datetimeFileModification = \
                                datetime.datetime.fromtimestamp( \
                                fFileModification)
                                
                            fFileCreation = \
                                os.path.getctime("\\\\?\\" + strFileFullPath)
                            datetimeFileCreation = \
                                datetime.datetime.fromtimestamp( \
                                fFileCreation)
                                
                            if self._strBackupScope == 'incremental-backup':
                                if datetimeFileModification <= \
                                    datetimeLastIncrementalAwsS3Backup and \
                                    datetimeFileCreation <= \
                                    datetimeLastIncrementalAwsS3Backup:
                                    continue
                                    #[12/7/2020 4:46 PM CST]
                                    #the above code is for skipping the backup-
                                    #destination file check, only for 
                                    #incremental backup, based on
                                    #the shadow-mounted drive file modification
                                    #and creation times.
                                    #in full backup, every file is checked below.
                            
                            #Check that the file exists at the backup destination.
                            #TO DO [1/7/2021 4:40 AM CST] using "\\\\?\\" is
                            #for Windows only.  Support Mac OS and Linux.
                            strFileFullPathWithoutDrive = \
                                os.path.splitdrive(strFileFullPath)[1]
                            strDestinationFileFullPath = "\\\\?\\" + \
                                os.path.join( \
                                strRobocopyDestinationDirectoryFullPath,
                                strFileFullPathWithoutDrive[1:])
                            if not os.path.isfile(strDestinationFileFullPath):
                                print('Robocopy failure.  A missing file in the \
backup destination.  ' + strDestinationFileFullPath)
                                continue
                                                       
                            
                            #Compare the file modification date times.                                
                            fDestinationFileModificationTime = \
                                os.path.getmtime(strDestinationFileFullPath)
                            datetimeDestinationFileModification = \
                                datetime.datetime.fromtimestamp( \
                                fDestinationFileModificationTime)                            
                                
                            #[1/19/2021 2:14 PM CST]
                            #refer to the "Robocopy validation failure" section
                            #in the AAM Auto Backup design document for
                            #why the following comparison is used.
                            if datetimeDestinationFileModification != \
                                datetimeFileModification and \
                                datetimeFileModification < \
                                datetimeBackupExecutionStart:
                                print('Robocopy failure.  Mismatching file \
modification date times.')
                                print('strFileFullPath: ' + strFileFullPath)
                                print('datetimeFileModification: ' + \
                                      str(datetimeFileModification))
                                print('strDestinationFileFullPath: ' + \
                                      strDestinationFileFullPath)
                                print('datetimeDestinationFileModification: ' + \
                                      str(datetimeDestinationFileModification))
                            else:
                                #Compare the file sizes.
                                if datetimeFileModification <= \
                                    datetimeBackupExecutionStart:
                                    if os.path.getsize(strDestinationFileFullPath) != \
                                        os.path.getsize("\\\\?\\" + strFileFullPath):
                                        print('Robocopy failure.  Mismatching file sizes.')  
                                        
                                        print('strFileFullPath: ' + strFileFullPath)
                                        print('datetimeFileModification: ' + \
                                              str(datetimeFileModification))
                                        print('strDestinationFileFullPath: ' + \
                                              strDestinationFileFullPath)
                                        print('datetimeDestinationFileModification: ' + \
                                              str(datetimeDestinationFileModification))                                        
                        
            except Exception as exc:
                sys.exit('File I/O error during local backup-destination \
validation check.\n' + str(exc))
                        
            print('\n')
            
            
        #######################################################################
        #Stage 7
        #-------
        #remove the 7z.exe list file.
        #######################################################################
        if 'AWS' in self._aam_abl.str_listBackupDestinationTypes:
            if self._strBackupScope == 'full-backup':
                try:
                    os.remove(str7zInclusionListFileFullPath)
                    os.remove(str7zNonRecursiveExclusionListFileFullPath)
                    os.remove(str7zRecursiveExclusionListFileFullPath)
                except OSError as e: # this would be "except OSError, e:" before Python 2.6
                    if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                        print('7z.exe list file deletion error.\n' + \
                              str7zInclusionListFileFullPath + '\n' + \
                              str7zNonRecursiveExclusionListFileFullPath + '\n' + \
                              str7zRecursiveExclusionListFileFullPath + '\n' + \
                              str(e)) 
            else:
                try:
                    os.remove(str7zInclusionListFileFullPath)
                except OSError as e: # this would be "except OSError, e:" before Python 2.6
                    if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                        print('7z.exe list file deletion error.\n' + \
                              str7zInclusionListFileFullPath + '\n' + str(e))
            
        
        #######################################################################
        #Stage 8
        #-------
        #print() backup batch file execution success message
        #(to use later for execution success validation).
        #######################################################################        
        print(self._strBackupBatchFileExecutionSuccessMessage)
        
        
    def RestoreAwsS3DataToLocalComputerInOneStep(self):
                
        datetimeNow = datetime.datetime.now()
        self._datetimeBackupExecutionStart = datetimeNow
        self._strBackupExecutionStartDateTime = \
            str(self._datetimeBackupExecutionStart)
        strDateTimeNow = str(datetimeNow)
        strFileNameSafeDateTimeNow = strDateTimeNow.replace(':', '_')
        
        strLocalBackupLogFileBaseName = strFileNameSafeDateTimeNow + \
            ' one-step data restoration'        
        strLocalBackupLogFileFullName = strLocalBackupLogFileBaseName + '.txt'
        
        self._strLocalBackupLogFileFullPath = os.path.join( \
            self._aam_abl.strLogDirectoryFullPath, strLocalBackupLogFileFullName)        
        
        try:
            #TO DO [11/7/2020 7:33 AM CST]
            #if writing to the local backup log file, it must be opened first.
            #if using the local backup log file in this function,
            #handle the issue of opening it here.            
                
            self._fileLocalBackupLog = open( \
                self._strLocalBackupLogFileFullPath, 'w', encoding='utf-8') 
        except Exception as exc:
            print('Fatal error.  Cannot open the local log file.\n' + str(exc))
            if self._bWaitForUserInputBeforeClosing:
                input("Press Enter to close the program...")             
            sys.exit()             
            
            
        strBackupDataRestorationInitiationTimeMessage = \
            "The AWS S3 backup restoration initiation time: " + strDateTimeNow
            
        print(strBackupDataRestorationInitiationTimeMessage)
            
        
        try:                      
            #Save the local log intro.
            self._fileLocalBackupLog.write( \
                strBackupDataRestorationInitiationTimeMessage + '\n\n')
            self._fileLocalBackupLog.write( \
                'Log Directory Full Path:  ' + \
                self._aam_abl.strLogDirectoryFullPath + '\n')
            self._fileLocalBackupLog.write( \
                'AWS S3 Object Restoration Period in Days:  ' + \
                str(self._aam_abl.iAwsS3ObjectRestorationPeriodInDays) + '\n')
            self._fileLocalBackupLog.write( \
                'Unique Backup-Source Location Name:  ' + \
                self._aam_abl.strUniqueBackupSourceLocationName + '\n')
            self._fileLocalBackupLog.write( \
                'AWS S3 Data Restoration Destination Directory Full Path:  ' + \
                self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath + '\n')        
            
            
            #Commence the archive restoration on AWS S3.
            strMessage = 'Commencing archive restoration on AWS S3 on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n\n\n')
            print(strMessage)
            self.RestoreToAwsS3FromAwsS3GlacierDeepArchive()
            
            #Log the AWS S3 objects used in restoration.
            for strBackupSourceName in \
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                
                self._fileLocalBackupLog.write(strBackupSourceName + '\n')
                self._fileLocalBackupLog.write('----------------------\n')
                    
                str_listFullBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                for strFullBackupAwsS3ObjectName in \
                    str_listFullBackupAwsS3ObjectNames:
                    self._fileLocalBackupLog.write( \
                        strFullBackupAwsS3ObjectName + '\n')
                self._fileLocalBackupLog.write('\n')
                
                
                if strBackupSourceName not in \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                    continue
                
                str_listIncrementalBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                for strIncrementalBackupAwsS3ObjectName in \
                    str_listIncrementalBackupAwsS3ObjectNames:
                    self._fileLocalBackupLog.write( \
                        strIncrementalBackupAwsS3ObjectName + '\n')
                self._fileLocalBackupLog.write('\n\n')
                
                #str_listIncrementalBackupArchiveFileNames = \
                #    self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                #    strBackupSourceName]
                #for strIncrementalBackupArchiveFileName in \
                #    str_listIncrementalBackupArchiveFileNames:
                #    self._fileLocalBackupLog.write( \
                #        strIncrementalBackupArchiveFileName + '\n')
                #self._fileLocalBackupLog.write('\n')            
            
            
            #Check the archive restoration on AWS S3.
            #loop to check every six hours up to 55 hours.
            fTotalTimeWaitedInSeconds = 0.0
            while not self.CheckAwsS3RestorationStatus():
                time.sleep(3600 * 6)
                fTotalTimeWaitedInSeconds += 3600.0 * 6
                if fTotalTimeWaitedInSeconds >= 198000.0:
                    strMessage = 'Data restoration failure.  No AWS S3 objects \
restoration after waiting for 55 hours.'
                    self._fileLocalBackupLog.write(strMessage + '\n')
                    print(strMessage)
                    if self._bWaitForUserInputBeforeClosing:
                        input("Press Enter to close the program...")                        
                    sys.exit()
            
            strMessage = 'Archive restoration completed on AWS S3 on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n')
            print(strMessage)            
            
            
            #Download the archives from AWS S3.
            strMessage = 'Commencing archive download from AWS S3 on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n')
            print(strMessage)
            
            self.DownloadToLocalComputerFromAwsS3()
            
            strMessage = 'Archive download from AWS S3 completed on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n')
            print(strMessage)             
            
            
            #Decompress the downloaded archives from AWS S3.
            strMessage = 'Commencing downloaded archive decompression on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n')
            print(strMessage)
            
            self.DecompressAllDownloadedBackupFiles()
            
            strMessage = 'Downloaded archive decompression completed on ' + \
                str(datetime.datetime.now()) + '.'
            self._fileLocalBackupLog.write(strMessage + '\n')
            print(strMessage)              
                           
        
            print('All the backup files have been restored successfully.  \
Check the local log file.\n' + self._strLocalBackupLogFileFullPath)
            
            print('Congratulations!  AWS S3 data restoration success!')
        
        except Exception as exc:
            print('Fatal error while executing \
RestoreAwsS3DataToLocalComputerInOneStep().\n' + str(exc)) 
            self._bAwsS3QueryFailure = True
            self._bRestorationSuccess = False
        finally:
            self._datetimeBackupExecutionEnd = datetime.datetime.now()
            self._strBackupExecutionEndDateTime = \
                str(self._datetimeBackupExecutionEnd)            
            
            strBackupExecutionEndingDateAndTimeMessage = \
                '\n\nBackup execution ending date and time:  ' + \
                self._strBackupExecutionEndDateTime            
            
            self._fileLocalBackupLog.write( \
                strBackupExecutionEndingDateAndTimeMessage)
            print(strBackupExecutionEndingDateAndTimeMessage + '\n')
            
            self._SendEmailReport()
            self._fileLocalBackupLog.close()
    
    
        if self._bWaitForUserInputBeforeClosing:
            input("Press Enter to close the program...")        
    
    
    def RestoreToAwsS3FromAwsS3GlacierDeepArchive(self):
        
        #TO DO [11/6/2020 9:41 PM CST]
        #if needed,
        #use _QueryBackupAwsS3BucketForDataRestoration()
        #to get the list of the AWS S3 objects to restore.
        self._InitializeDataRestoration()
        
        try:
            for strBackupSourceName in \
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                
                str_listFullBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strFullBackupAwsS3ObjectName in \
                    str_listFullBackupAwsS3ObjectNames:
                        
                    s3_objectToRestore = self.s3_resource.Object( \
                        self._aam_abl.strBackupAwsS3BucketName,
                        strFullBackupAwsS3ObjectName)
                    try:
                        s3_objectToRestore.restore_object( \
                            RestoreRequest={'Days': \
                            self._aam_abl.iAwsS3ObjectRestorationPeriodInDays,
                            'GlacierJobParameters': {'Tier': 'Bulk'}})
                        #search "aws s3 boto3 restore_object reference" online.
                        #https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/s3.html#S3.Client.restore_object                     
                        #search "aws s3 boto3 glacier deep archive restore_object example"
                        #online.
                        #https://docs.aws.amazon.com/AmazonS3/latest/dev/restoring-objects.html
                        #https://forums.aws.amazon.com/thread.jspa?threadID=249282
                        #https://stackoverflow.com/questions/64535043/how-to-download-archive-from-glacier-deep-archive-locally-using-boto3   
                        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#restore-glacier-objects-in-an-amazon-s3-bucket
                    except botocore.exceptions.ClientError as exc:
                        if exc.response['Error']['Code'] == 'RestoreAlreadyInProgress':
                            pass
                        else:
                            raise Exception('Error in AWS S3 object restore request.\n' + \
                                str(exc))


                if strBackupSourceName not in \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                    continue

                str_listIncrementalBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strIncrementalBackupAwsS3ObjectName in \
                    str_listIncrementalBackupAwsS3ObjectNames:
                        
                    s3_objectToRestore = self.s3_resource.Object( \
                        self._aam_abl.strBackupAwsS3BucketName,
                        strIncrementalBackupAwsS3ObjectName)
                    try:
                        s3_objectToRestore.restore_object( \
                            RestoreRequest={'Days': \
                            self._aam_abl.iAwsS3ObjectRestorationPeriodInDays,
                            'GlacierJobParameters': {'Tier': 'Bulk'}})
                    except botocore.exceptions.ClientError as exc:
                        if exc.response['Error']['Code'] == 'RestoreAlreadyInProgress':
                            pass
                        else:
                            raise Exception('Error in AWS S3 object restore request.\n' + \
                                str(exc))    

        except Exception as exc:
            raise Exception('Error in AWS S3 object restore request.\n' + \
                str(exc))

    def CheckAwsS3RestorationStatus(self):
        #Returns True if all the applicable AWS S3 objects are restored.
        #Returns False otherwise.
        
        
        #TO DO [11/6/2020 9:41 PM CST]
        #if needed,
        #use _QueryBackupAwsS3BucketForDataRestoration()
        #to get the list of the AWS S3 objects to restore.        
        self._InitializeDataRestoration()
        
        
        try:
            for strBackupSourceName in \
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                
                str_listFullBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strFullBackupAwsS3ObjectName in \
                    str_listFullBackupAwsS3ObjectNames:
                        
                    s3_objectToRestore = self.s3_resource.Object( \
                        self._aam_abl.strBackupAwsS3BucketName,
                        strFullBackupAwsS3ObjectName)

                    #no need to check that
                    #s3_objectToRestore.storage_class == 'DEEP_ARCHIVE'
                    
                    if s3_objectToRestore.restore is None:
                        raise Exception('An applicable AWS S3 object is not in \
the restoration mode.  ' + strFullBackupAwsS3ObjectName)
                    elif 'ongoing-request="true"' in s3_objectToRestore.restore:
                        print("AWS S3 objects restoration ongoing.")
                        return False
                    elif 'ongoing-request="false"' not in \
                        s3_objectToRestore.restore:
                        raise Exception('An AWS S3 object without \
ongoing-request="true" doesn\'t have ongoing-request="false".  ' \
                        + strFullBackupAwsS3ObjectName)                       
                        
                    
                str_listIncrementalBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strIncrementalBackupAwsS3ObjectName in \
                    str_listIncrementalBackupAwsS3ObjectNames:
                        
                    s3_objectToRestore = self.s3_resource.Object( \
                        self._aam_abl.strBackupAwsS3BucketName,
                        strIncrementalBackupAwsS3ObjectName)
                    
                    #no need to check that
                    #s3_objectToRestore.storage_class == 'DEEP_ARCHIVE'
                    
                    if s3_objectToRestore.restore is None:
                        raise Exception('An applicable AWS S3 object is not in \
the restoration mode.  ' + strIncrementalBackupAwsS3ObjectName)
                    elif 'ongoing-request="true"' in s3_objectToRestore.restore:
                        print("AWS S3 objects restoration ongoing.")
                        return False
                    elif 'ongoing-request="false"' not in \
                        s3_objectToRestore.restore:
                        raise Exception('An AWS S3 object without \
ongoing-request="true" doesn\'t have ongoing-request="false".  ' \
                        + strIncrementalBackupAwsS3ObjectName)
                    
        except Exception as exc:
            raise Exception('Error while checking AWS S3 object restoration \
status.\n' + str(exc))


        print("AWS S3 objects restoration complete!")
        return True

    def DownloadToLocalComputerFromAwsS3(self):
        
        #TO DO [11/6/2020 9:41 PM CST]
        #if needed,
        #use _QueryBackupAwsS3BucketForDataRestoration()
        #to get the list of the AWS S3 objects to download.  
        self._InitializeDataRestoration()
        
        
        try:
            for strBackupSourceName in \
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                
                str_listFullBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strFullBackupAwsS3ObjectName in \
                    str_listFullBackupAwsS3ObjectNames:
                    
                    strDownloadedArchiveFileFullPath = os.path.join( \
                        self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath,
                        strFullBackupAwsS3ObjectName)
                        
                    self.backup_s3_bucket.download_file( \
                        strFullBackupAwsS3ObjectName,
                        strDownloadedArchiveFileFullPath)                    
                        
                    
                str_listIncrementalBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName]
                    
                for strIncrementalBackupAwsS3ObjectName in \
                    str_listIncrementalBackupAwsS3ObjectNames:
                        
                    strDownloadedArchiveFileFullPath = os.path.join( \
                        self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath,
                        strIncrementalBackupAwsS3ObjectName)
                        
                    self.backup_s3_bucket.download_file( \
                        strIncrementalBackupAwsS3ObjectName,
                        strDownloadedArchiveFileFullPath) 
            
        except Exception as exc:
            raise Exception('Error while downloading AWS S3 object.\n' + \
                str(exc))

        print('AWS S3 objects download completed!')


    def DecompressAllDownloadedBackupFiles(self):
        #TO DO [11/6/2020 9:41 PM CST]
        #if needed,
        #use _QueryBackupAwsS3BucketForDataRestoration()
        #to get the list of the AWS S3 objects to download.  
        self._InitializeDataRestoration()
        
        
        try:
            iBackupSourceNameCounter = 0
            
            for strBackupSourceName in \
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                
                iBackupSourceNameCounter += 1
                
                strDestinationBackupSourceDirectoryFullPath = os.path.join( \
                    self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath,
                    str(iBackupSourceNameCounter))
                
                os.mkdir(strDestinationBackupSourceDirectoryFullPath)
                    
                
                #Decompress the full-backup archive.
                strFullBackupArchiveFullFileName = \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                    strBackupSourceName][0] #this should be the first zip file.

                strFullBackupArchiveFileFullPath = os.path.join( \
                    self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath,
                    strFullBackupArchiveFullFileName)
                    
                
                str7zCommand = '7z x "' + strFullBackupArchiveFileFullPath + \
                    '" -o"' + strDestinationBackupSourceDirectoryFullPath + \
                    '" -y -p' + self._aam_abl.strBackupDecryptionAes256Key
                os.chdir(self._strProgramFileDirectoryFullPath)
                os.system(str7zCommand)
                      
                        
                #Decompress the incremental-backup archive(s).
                str_listIncrementalBackupAwsS3ObjectNames = \
                    self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                    strBackupSourceName]
                #str_listIncrementalBackupAwsS3ObjectNames must be in
                #ascending order.  [11/23/2020 9:42 AM CST]
                    
                for strIncrementalBackupAwsS3ObjectName in \
                    str_listIncrementalBackupAwsS3ObjectNames:
                        
                    strDownloadedArchiveFileFullPath = os.path.join( \
                        self._aam_abl.strAwsS3DataRestorationDestinationDirectoryFullPath,
                        strIncrementalBackupAwsS3ObjectName)
                        
                    str7zCommand = '7z x "' + strDownloadedArchiveFileFullPath + \
                        '" -o"' + strDestinationBackupSourceDirectoryFullPath + \
                        '" -y -p' + self._aam_abl.strBackupDecryptionAes256Key
                    os.chdir(self._strProgramFileDirectoryFullPath)
                    os.system(str7zCommand)           
            
        except Exception as exc:
            raise Exception('Error while decompressing downloaded backup files.\n' + \
                str(exc)) 
            
        #delete all the downloaded backup files here? [11/10/2020 4:57 PM CST]
        #NOPE.  not now.  maybe later.
        

        print('Downloaded backup archives decompression completed!')
        
    
    def _BuildBackupSourceAwsS3UniqueNames(self):
        #[12/4/2020 5:00 PM CST]
        #Each shadow-mount directory is a backup source.
        
        self._str_listBackupSourceAwsS3UniqueNames = []
        
        for strShadowMountDirectoryFullPath in \
            self._str_listShadowMountDirectoryFullPaths:
            strShadowMountDirectoryFullPath = \
                strShadowMountDirectoryFullPath.replace(':', '')
            strShadowMountDirectoryFullPath = \
                strShadowMountDirectoryFullPath.replace( \
                self._PathSeparator, '_')
                
            if strShadowMountDirectoryFullPath in \
                self._str_listBackupSourceAwsS3UniqueNames:
                #[11/3/2020 9:20 AM CST]
                #this needs to be handled properly.
                #[11/22/2020 7:36 AM CST] what to do here exactly?
                #raise an error?  silently ignore it?  do what here?
                continue
                
            self._str_listBackupSourceAwsS3UniqueNames.append( \
                strShadowMountDirectoryFullPath)
    
    
    def _InitializeAwsS3Query(self, iYear, iMonth,
        strUniqueBackupSourceLocationName):
        
        str_listBackupAwsS3ObjectNames = []
                
        strBackupAwsS3BucketObjectPrefix = \
            strUniqueBackupSourceLocationName + '_' + \
            str(iYear) + str(iMonth).zfill(2)
                      
        iteratorAwsS3Objects = self.backup_s3_bucket.objects.filter( \
            Prefix=strBackupAwsS3BucketObjectPrefix)
        
        for s3_object in iteratorAwsS3Objects:
            
            strBackupAwsS3BucketObjectKey = s3_object.key
            
            if strBackupAwsS3BucketObjectKey[-1] == '/' and \
                s3_object.size == 0:
                continue
                                
            str_listBackupAwsS3ObjectNames.append( \
                strBackupAwsS3BucketObjectKey)

        
        str_listBackupAwsS3ObjectNames.sort(reverse=True)
                
        self._strLatestCompleteUploadAwsS3FullBackupDate = ''
        self._strLatestCompleteUploadAwsS3FullBackupTime = ''
        
        self._strLatestCompleteUploadAwsS3IncrementalBackupDate = ''
        self._strLatestCompleteUploadAwsS3IncrementalBackupTime = ''
        
        self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists = {}
        self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists = {}
        self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists = {}
        
        return str_listBackupAwsS3ObjectNames
    
    
    def _QueryBackupAwsS3Bucket(self, iYear, iMonth, 
                                strUniqueBackupSourceLocationName):
        #[12/9/2020 5:51 AM CST]
        #This function is for performing AWS S3 querying for data backup,
        #not restoration.
        #
        #This function does not return any value.
        #
        #Function behavior when AWS S3 querying succeeds
        #-----------------------------------------------
        #When the AWS S3 query is successful, this function returns with
        #self._bAwsS3QueryFailure set to False, and
        #the following data variables set to the latest completed-upload full
        #and incremental backup dates and times that are retrieved from AWS S3.
        #
        #self._strLatestCompleteUploadAwsS3FullBackupDate
        #self._strLatestCompleteUploadAwsS3FullBackupTime
        #self._strLatestCompleteUploadAwsS3IncrementalBackupDate
        #self._strLatestCompleteUploadAwsS3IncrementalBackupTime
        #        
        #If there is no incremental backup in AWS S3 for the given year and
        #month, the latest incremental date and time is set to the full-backup
        #date and time.        
        #
        #If there is no complete-upload full-backup AWS S3 objects in the month
        #given, with all the backup sources, this function
        #sets all of the above data variables to the empty string, and returns
        #with self._bAwsS3QueryFailure set to False.
        #
        #Because this function is for data backup, not restoration, this
        #function does not retrieve the AWS S3 backup object lists.         
        #
        #
        #Function behavior when AWS S3 querying fails
        #--------------------------------------------       
        #When there is an AWS S3 bucket query error, this function sets
        #self._bAwsS3QueryFailure to True, sets every data variable above
        #to an empty string, then returns.
        #
        #
        #Implementation techniques
        #-------------------------
        #NOTE [10/26/2020 10:06 AM CST]
        #This function, _QueryBackupAwsS3Bucket(), retrieves the dates and times
        #of the AWS S3 full and incremental backups with all of the backup sources  
        #or shadow-mounted directories fully uploaded.  AAM Auto Backup does not 
        #consider a full or incremental backup with an incomplete-upload backup 
        #source as a complete-upload full or incremental backup.
        #        
        #[12/9/2020 6:24 AM CST]
        #In order to properly handle
        #multiple backup sources or shadow-copy mounted directories,
        #this function checks for the upload-completeness of
        #full and incremental backups for every backup source or 
        #shadow-copy mounted directory.
        #
        #In order for this function to know what backup sources to look for
        #in AWS S3, before calling this function, AAM Auto Backup
        #(this program) must
        #process the AAM Auto Backup instruction plain text file first,
        #and provide the list of the backup sources in
        #self._str_listBackupSourceAwsS3UniqueNames.        
        #
        #This function uses str_listRemainingBackupSourceAwsS3UniqueNames
        #to check for the backup-source completeness
        #in an AWS S3 backup object set.
              
        
        try:
            str_listBackupAwsS3ObjectNames = self._InitializeAwsS3Query( \
                iYear, iMonth, strUniqueBackupSourceLocationName)
        except Exception as exc:
            strErrorMessage = 'AWS S3 query error in \
_QueryBackupAwsS3Bucket.' + '\n' + str(exc)
            print(strErrorMessage)
            self._fileLocalBackupLog.write('\n' + strErrorMessage)
            self._bAwsS3QueryFailure = True
            return
                     
        
        #######################################################################
        #Build the following data variables.
        #self._strLatestCompleteUploadAwsS3FullBackupDate
        #self._strLatestCompleteUploadAwsS3FullBackupTime
        #self._strLatestCompleteUploadAwsS3IncrementalBackupDate
        #self._strLatestCompleteUploadAwsS3IncrementalBackupTime
        #######################################################################   
        self._bAwsS3QueryFailure = False
        
        str_listRemainingBackupSourceAwsS3UniqueNames = []
        bInvalidAwsS3FullBackup = False
                       
        strLastIncrementalBackupFullBackupDate = ''
        strLastIncrementalBackupFullBackupTime = ''
        
        iZeroBasedIncrementalBackupStartIndex = -1
        iZeroBasedIncrementalBackupEndIndex = -1

        #Get the latest completed-upload full-backup date and time
        #in the current month, with all the backup sources.
        #(str_listRemainingBackupSourceAwsS3UniqueNames is used to check for
        #backup-source completeness or exact-matchness.)                
        for iZeroBasedBackupAwsS3ObjectNameIndex in \
            range(0, len(str_listBackupAwsS3ObjectNames)):

            strBackupAwsS3ObjectName = str_listBackupAwsS3ObjectNames[ \
                iZeroBasedBackupAwsS3ObjectNameIndex]            
            
            regexp_match_objBackupAwsS3ObjectName = \
                self.regexp_objBackupAwsS3ObjectNameParser.search( \
                strBackupAwsS3ObjectName)
                
            if regexp_match_objBackupAwsS3ObjectName == None:
                strErrorMessage = 'Invalid AWS S3 object name in \
_QueryBackupAwsS3Bucket(). ' + strBackupAwsS3ObjectName
                print(strErrorMessage)
                self._fileLocalBackupLog.write('\n' + strErrorMessage + '\n')
                continue            

            strFullBackupDate = regexp_match_objBackupAwsS3ObjectName.group(2)
            strFullBackupTime = \
                regexp_match_objBackupAwsS3ObjectName.group(3) + '.' + \
                regexp_match_objBackupAwsS3ObjectName.group(4)
                
            strIncrementalBackupDate = \
                regexp_match_objBackupAwsS3ObjectName.group(5)  
                
            if strIncrementalBackupDate != '0': #not a full backup
                if not bInvalidAwsS3FullBackup and \
                    str_listRemainingBackupSourceAwsS3UniqueNames == [] and \
                    self._strLatestCompleteUploadAwsS3FullBackupDate != '':
                    break                 
                
                if strLastIncrementalBackupFullBackupDate == strFullBackupDate \
                    and \
                    strLastIncrementalBackupFullBackupTime == strFullBackupTime:
                    iZeroBasedIncrementalBackupEndIndex += 1
                else:
                    strLastIncrementalBackupFullBackupDate = strFullBackupDate
                    strLastIncrementalBackupFullBackupTime = strFullBackupTime
                    
                    iZeroBasedIncrementalBackupStartIndex = \
                        iZeroBasedBackupAwsS3ObjectNameIndex
                    iZeroBasedIncrementalBackupEndIndex = \
                        iZeroBasedBackupAwsS3ObjectNameIndex                        
                
                continue

            strBackupSourceUniqueName = \
                regexp_match_objBackupAwsS3ObjectName.group(9)


            if strFullBackupDate == \
                self._strLatestCompleteUploadAwsS3FullBackupDate and \
                strFullBackupTime == \
                self._strLatestCompleteUploadAwsS3FullBackupTime:
                    
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True           
                            
                    if strBackupSourceUniqueName in \
                        str_listRemainingBackupSourceAwsS3UniqueNames:
                        str_listRemainingBackupSourceAwsS3UniqueNames.remove( \
                            strBackupSourceUniqueName)
                    else:
                        bInvalidAwsS3FullBackup = True
                    
                else: #regexp_match_objBackupAwsS3ObjectName.group(8) == 'no':
                    #bUploadCompletionIndicator = False
                    if strBackupSourceUniqueName not in \
                        self._str_listBackupSourceAwsS3UniqueNames: 
                        bInvalidAwsS3FullBackup = True

            else: #latest full-backup upload date and time change handling
                
                if not bInvalidAwsS3FullBackup and \
                    str_listRemainingBackupSourceAwsS3UniqueNames == [] and \
                    self._strLatestCompleteUploadAwsS3FullBackupDate != '':
                    break                 
                
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True           
                                                
                    bInvalidAwsS3FullBackup = False
                    
                    str_listRemainingBackupSourceAwsS3UniqueNames = \
                        self._str_listBackupSourceAwsS3UniqueNames.copy()
                    if strBackupSourceUniqueName in \
                        str_listRemainingBackupSourceAwsS3UniqueNames:
                        str_listRemainingBackupSourceAwsS3UniqueNames.remove( \
                            strBackupSourceUniqueName)
                    else:
                        bInvalidAwsS3FullBackup = True                        
                        
                    self._strLatestCompleteUploadAwsS3FullBackupDate = \
                        strFullBackupDate
                    self._strLatestCompleteUploadAwsS3FullBackupTime = \
                        strFullBackupTime      
                    
                else: #regexp_match_objBackupAwsS3ObjectName.group(8) == 'no':
                    #bUploadCompletionIndicator = False
                    
                    #If the code execution reaches here, there was an upload
                    #failure, since there is a missing upload-completeness
                    #indicator AWS S3 object.
                    
                    bInvalidAwsS3FullBackup = True
                    
                    str_listRemainingBackupSourceAwsS3UniqueNames = \
                        self._str_listBackupSourceAwsS3UniqueNames.copy() 
                        
                    self._strLatestCompleteUploadAwsS3FullBackupDate = \
                        strFullBackupDate
                    self._strLatestCompleteUploadAwsS3FullBackupTime = \
                        strFullBackupTime

            
        if self._strLatestCompleteUploadAwsS3FullBackupDate == '':
            return
        elif bInvalidAwsS3FullBackup or \
            str_listRemainingBackupSourceAwsS3UniqueNames != []:
            self._strLatestCompleteUploadAwsS3FullBackupDate = ''
            self._strLatestCompleteUploadAwsS3FullBackupTime = ''
            self._strLatestCompleteUploadAwsS3IncrementalBackupDate = ''
            self._strLatestCompleteUploadAwsS3IncrementalBackupTime = ''
            return 
                    
        
        #Get the latest completed-upload incremental-backup date and time
        #in the current month, with all the backup sources.                    
        if strLastIncrementalBackupFullBackupDate != \
            self._strLatestCompleteUploadAwsS3FullBackupDate or \
            strLastIncrementalBackupFullBackupTime != \
            self._strLatestCompleteUploadAwsS3FullBackupTime:
                
            self._strLatestCompleteUploadAwsS3IncrementalBackupDate = \
                self._strLatestCompleteUploadAwsS3FullBackupDate
            self._strLatestCompleteUploadAwsS3IncrementalBackupTime = \
                self._strLatestCompleteUploadAwsS3FullBackupTime 
            
            return
        
        str_listRemainingBackupSourceAwsS3UniqueNames = []
        bInvalidAwsS3IncrementalBackup = False        
        
        strLastIncrementalBackupDate = ''
        strLastIncrementalBackupTime = ''
                
        for iZeroBasedBackupAwsS3ObjectNameIndex in \
            range(iZeroBasedIncrementalBackupStartIndex, 
                  iZeroBasedIncrementalBackupEndIndex + 1):

            strBackupAwsS3ObjectName = str_listBackupAwsS3ObjectNames[ \
                iZeroBasedBackupAwsS3ObjectNameIndex]
                
            regexp_match_objBackupAwsS3ObjectName = \
                self.regexp_objBackupAwsS3ObjectNameParser.search( \
                strBackupAwsS3ObjectName)
                
            if regexp_match_objBackupAwsS3ObjectName == None:
                continue
                           
            
            strIncrementalBackupDate = \
                regexp_match_objBackupAwsS3ObjectName.group(5)
            strIncrementalBackupTime = \
                regexp_match_objBackupAwsS3ObjectName.group(6) + '.' + \
                regexp_match_objBackupAwsS3ObjectName.group(7)            
            
            strBackupSourceUniqueName = \
                regexp_match_objBackupAwsS3ObjectName.group(9)            
            
            
            if strIncrementalBackupDate == strLastIncrementalBackupDate and \
                strIncrementalBackupTime == strLastIncrementalBackupTime:
                    
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True           
                            
                    if strBackupSourceUniqueName in \
                        str_listRemainingBackupSourceAwsS3UniqueNames:
                        str_listRemainingBackupSourceAwsS3UniqueNames.remove( \
                            strBackupSourceUniqueName)
                    else:
                        bInvalidAwsS3IncrementalBackup = True
                    
                else: #regexp_match_objBackupAwsS3ObjectName.group(8) == 'no':
                    #bUploadCompletionIndicator = False
                    if strBackupSourceUniqueName not in \
                        self._str_listBackupSourceAwsS3UniqueNames: 
                        bInvalidAwsS3IncrementalBackup = True

            else: #latest incremental-backup upload date and time change handling
                
                if not bInvalidAwsS3IncrementalBackup and \
                    str_listRemainingBackupSourceAwsS3UniqueNames == [] and \
                    strLastIncrementalBackupDate != '':
                    self._strLatestCompleteUploadAwsS3IncrementalBackupDate = \
                        strLastIncrementalBackupDate
                    self._strLatestCompleteUploadAwsS3IncrementalBackupTime = \
                        strLastIncrementalBackupTime
                    break
                
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True           
              
                    bInvalidAwsS3IncrementalBackup = False
                    
                    str_listRemainingBackupSourceAwsS3UniqueNames = \
                        self._str_listBackupSourceAwsS3UniqueNames.copy()
                    if strBackupSourceUniqueName in \
                        str_listRemainingBackupSourceAwsS3UniqueNames:
                        str_listRemainingBackupSourceAwsS3UniqueNames.remove( \
                            strBackupSourceUniqueName)
                    else:
                        bInvalidAwsS3IncrementalBackup = True                        
                        
                    strLastIncrementalBackupDate = strIncrementalBackupDate
                    strLastIncrementalBackupTime = strIncrementalBackupTime      
                    
                else: #regexp_match_objBackupAwsS3ObjectName.group(8) == 'no':
                    #bUploadCompletionIndicator = False
                    
                    #If the code execution reaches here, there was an upload
                    #failure, since there is a missing upload-completeness
                    #indicator AWS S3 object.
                    
                    bInvalidAwsS3IncrementalBackup = True
                    
                    str_listRemainingBackupSourceAwsS3UniqueNames = \
                        self._str_listBackupSourceAwsS3UniqueNames.copy() 
                        
                    strLastIncrementalBackupDate = strIncrementalBackupDate
                    strLastIncrementalBackupTime = strIncrementalBackupTime 
            

        if self._strLatestCompleteUploadAwsS3IncrementalBackupDate == '':
            if not bInvalidAwsS3IncrementalBackup and \
                str_listRemainingBackupSourceAwsS3UniqueNames == [] and \
                strLastIncrementalBackupDate != '':
                 
                self._strLatestCompleteUploadAwsS3IncrementalBackupDate = \
                    strLastIncrementalBackupDate
                self._strLatestCompleteUploadAwsS3IncrementalBackupTime = \
                    strLastIncrementalBackupTime
            else:
                self._strLatestCompleteUploadAwsS3IncrementalBackupDate = \
                    self._strLatestCompleteUploadAwsS3FullBackupDate
                self._strLatestCompleteUploadAwsS3IncrementalBackupTime = \
                    self._strLatestCompleteUploadAwsS3FullBackupTime


    def _InitializeDataRestoration(self):
        
        if self.boto3_session != None: return
        
        
        self.boto3_session = boto3.Session( \
            aws_access_key_id=self._aam_abl.strBackupAwsIamUserAccessKeyId,
            aws_secret_access_key=self._aam_abl.strBackupAwsIamUserSecretAccessKey,
            region_name=self.strAwsRegion)
        self.s3_resource = self.boto3_session.resource('s3')
        self.backup_s3_bucket = self.s3_resource.Bucket( \
            self._aam_abl.strBackupAwsS3BucketName)
        
        self.ses_client = boto3.client('ses', 
            aws_access_key_id=self._aam_abl.strBackupAwsIamUserAccessKeyId,
            aws_secret_access_key=self._aam_abl.strBackupAwsIamUserSecretAccessKey,
            region_name=self.strAwsRegion)
        #https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
                    

        datetimeNow = datetime.datetime.now()
        iYear = datetimeNow.year
        iMonth = datetimeNow.month
        
        iNumberOfBacktracedMonths = 1
        
        while not self._QueryBackupAwsS3BucketForDataRestoration(iYear, iMonth, 
            self._aam_abl.strUniqueBackupSourceLocationName):
                                       
            if iNumberOfBacktracedMonths >= \
                self._iBackupAwsS3BucketObjectLifetimeInNumberOfMonths:
                raise Exception('Error.  No archive AWS S3 to restore.')
            
            iNumberOfBacktracedMonths += 1
            
            if iMonth == 1:
                iMonth = 12
                iYear -= 1
            else:
                iMonth -= 1
    

    def _QueryBackupAwsS3BucketForDataRestoration(self, iYear, iMonth, 
        strUniqueBackupSourceLocationName):
        #Function return values
        #----------------------
        #This function returns True if AWS S3 query success.
        #This function returns False if AWS S3 query failure.
        #
        #
        #Function behavior when AWS S3 querying succeeds
        #-----------------------------------------------        
        #When the AWS S3 query is successful, this function sets the following 
        #data variables to the latest completed-upload full and incremental
        #backup dates, times, and AWS S3 object lists, and returns True.
        #
        #self._strLatestCompleteUploadAwsS3FullBackupDate
        #self._strLatestCompleteUploadAwsS3FullBackupTime
        #self._strLatestCompleteUploadAwsS3IncrementalBackupDate
        #self._strLatestCompleteUploadAwsS3IncrementalBackupTime
        #
        #self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists
        #self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists
        #self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists        
        #
        #
        #Function behavior when AWS S3 querying fails
        #--------------------------------------------
        #When the AWS S3 query is unsuccessful, this function returns False
        #with all of the above data variables set to the empty value.
        #
        #
        #Implementation techniques
        #-------------------------
        #NOTE [10/26/2020 10:06 AM CST]
        #This function, like _QueryBackupAwsS3Bucket(), retrieves 
        #the latest AWS S3 full and incremental backups with all of the backup   
        #sources or shadow-mounted directories fully uploaded.  AAM Auto Backup  
        #does not consider a full or incremental backup with an incomplete-upload  
        #backup source as a complete-upload full or incremental backup.
        #
        #
        #Unlike _QueryBackupAwsS3Bucket(), this function does not expect
        #any particular backup sources to be present in AWS S3, so
        #this function does not use self._str_listBackupSourceAwsS3UniqueNames
        #produced by processing the AAM Auto Backup instruction plain text file.
        #
        #Performing data restoration from AWS S3 means that the backed-up data
        #on the local computer has been damaged, lost, or stolen, so in
        #all likely chance, the AAM Auto Backup instruction plain text file
        #is not present when an AWS S3 data restoration is performed.
        #
        #As such, this function looks only at the latest complete-upload AWS S3 
        #full and incremental backup objects for deciding the backup sources to
        #restore from AWS S3.
        #
        #This function gets the latest AWS S3 full backup with completed upload
        #for all backup sources, then gets all the completed-upload AWS S3 
        #incremental backups of the latest completed-upload AWS S3 full backup
        #for all backup sources.
        #
        #This function builds
        #self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists,
        #self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists,
        #and self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists
        #while processing the names of the retrieved AWS S3 objects with the
        #given iYear, iMonth, and strUniqueBackupSourceLocationName.
        #        
        #
        #[12/9/2020 7:57 AM CST]
        #This separate AWS S3 query function is used, instead of using 
        #a single _QueryBackupAwsS3Bucket() function for AWS S3 querying for
        #both data backup and restoration, because this function implementation
        #is significantly different from the backup AWS S3 query implementation
        #code.
        #        
        #Although this function has some code blocks that are the same as
        #the ones in _QueryBackupAwsS3Bucket(), still, this function's
        #implementation code is significantly different from the
        #_QueryBackupAwsS3Bucket() implementation code, due to building
        #the lists of the backup AWS S3 objects.
        #
        #
        #ALGORITHM UPDATE IDEA [12/9/2020 4:46 PM CST]
        #Because str_listBackupAwsS3ObjectNames is sorted in the reverse 
        #or descending order,
        #incremental backup AWS S3 objects are present before the full backup
        #AWS S3 objects, on the same full-backup date and time.
        #That property can be used to more efficiently process
        #the incremental backup AWS S3 objects of the latest completed-upload
        #AWS S3 full backup.
        #store the incremental backup AWS S3 object names while processing
        #each AWS S3 full backup set in a separate list, and process that
        #separate list after processing the latest completed-upload
        #AWS S3 full backup.
        #(TO DECIDE [12/9/2020 5:00 PM CST] implement the above now, in both
        #_QueryBackupAwsS3Bucket() and 
        #_QueryBackupAwsS3BucketForDataRestoration()?  think and decide on it,
        #and then implement the decision!!!!!)
        #(NOTE [12/9/2020 5:20 PM CST] whether I implement the above or not,
        #the below code must be updated.  the incremental backup for-loop
        #code is wrong; it doesn't work.)
        #(UPDATE [12/9/2020 5:24 PM CST] I just realized that a better way is
        #to keep the incremental backup AWS S3 object starting index 
        #[and perhaps even ending index] for
        #each full-backup AWS S3 object set being processed.  that index
        #or those starting and ending indexes can be used to process
        #the applicable incremental backup AWS S3 objects after getting the
        #completed-upload AWS S3 full backup info.  in all likely chance,
        #I'll use this.) ([12/9/2020 5:36 PM CST] yeah, in all likely chance,
        #I'll implement this.  I'll make the decision tomorrow, not today.)
        #
        #(FINAL DECISION [12/10/2020 5:52 AM CST] I've no objection to 
        #the above so I'll implement the above [i.e. the incremental-backup
        #AWS S3 objects starting and ending indexes use].  
        #initialize iZeroBasedIncrementalBackupEndIndex to -1.
        #set iZeroBasedIncrementalBackupStartIndex to
        #iZeroBasedIncrementalBackupEndIndex + 1,
        #if iZeroBasedIncrementalBackupStartIndex is -1,
        #in "if strIncrementalBackupDate != '0':" if 
        #self._strLatestCompleteUploadAwsS3FullBackupDate and
        #self._strLatestCompleteUploadAwsS3FullBackupTime are different from
        #the incremental-backup AWS S3 object date and time.
        #set iZeroBasedIncrementalBackupEndIndex in 
        #"else: #latest full-backup upload date and time change handling",
        #and set iZeroBasedIncrementalBackupStartIndex to -1.
        #ok, I think the above code implementation method will work perfectly!)
        #
        #(UPDATE [12/10/2020 7:46 AM CST] wait, the above algorithm might not be
        #correct.
        #iZeroBasedIncrementalBackupEndIndex should be set immediately after
        #"if strIncrementalBackupDate != '0': #not a full backup",
        #to iZeroBasedBackupAwsS3ObjectNameIndex - 1, at the start of the next
        #full-backup AWS S3 object set. ... )
        #
        #(UPDATE [12/10/2020 8:00 AM CST] wait, the above algorithm is not
        #correct.
        #iZeroBasedIncrementalBackupEndIndex should be initialized to -1
        #before the full-backup processing for-loop.
        #iZeroBasedIncrementalBackupEndIndex should be incremented by one
        #in "if strIncrementalBackupDate != '0': #not a full backup". ...)
        #
        #(UPDATE [12/10/2020 8:08 AM CST] wait, the above algorithm is not
        #correct.
        #strLastIncrementalBackupFullBackupDate and 
        #strLastIncrementalBackupFullBackupTime should be used, initialized
        #to the empty string before the full-backup AWS S3 objects processing
        #for-loop.
        #in "if strIncrementalBackupDate != '0': #not a full backup",
        #if strFullBackupDate and strFullBackupTime are different from
        #strLastIncrementalBackupFullBackupDate and 
        #strLastIncrementalBackupFullBackupTime,
        #set iZeroBasedIncrementalBackupStartIndex and
        #iZeroBasedIncrementalBackupEndIndex to
        #iZeroBasedBackupAwsS3ObjectNameIndex, and set 
        #strLastIncrementalBackupFullBackupDate and 
        #strLastIncrementalBackupFullBackupTime to
        #strFullBackupDate and strFullBackupTime.
        #if strFullBackupDate and strFullBackupTime are the same with
        #strLastIncrementalBackupFullBackupDate and
        #strLastIncrementalBackupFullBackupTime,
        #increment iZeroBasedIncrementalBackupEndIndex by one.
        #perform the incremental-backup AWS S3 objects processing,
        #only if strLastIncrementalBackupFullBackupDate and 
        #strLastIncrementalBackupFullBackupTime, are the same as
        #self._strLatestCompleteUploadAwsS3FullBackupDate and
        #self._strLatestCompleteUploadAwsS3FullBackupTime.)
        #([12/10/2020 8:20 AM CST] ok, I think the above algorithm is 
        #absolutely right.
        #after a break, I'll assess the above algorithm, and if I find no
        #problem in it, I'll implement it!)
        #(FINAL DECISION [12/10/2020 11:20 AM CST] I'm implementing the above.)
        #(UPDATE [12/10/2020 12:44 PM CST]
        #make sure to prevent updating the incremental backup info (date, time, 
        #and index range), after getting the completed-upload AWS S3 full backup.
        #DONE!  full-backup AWS S3 objects processing for-loop exit code
        #in "if strIncrementalBackupDate != '0': #not a full backup"!
        #[12/10/2020 12:45 PM CST])

        
        try:
            str_listBackupAwsS3ObjectNames = self._InitializeAwsS3Query( \
                iYear, iMonth, strUniqueBackupSourceLocationName)
        except Exception as exc:
            strErrorMessage = 'AWS S3 query error in \
_QueryBackupAwsS3BucketForDataRestoration().' + '\n' + str(exc)
            print(strErrorMessage)
            if self._aam_abl.strOperationType == 'one-step-aws-data-restoration':
                self._fileLocalBackupLog.write('\n' + strErrorMessage)
            self._bAwsS3QueryFailure = True
            return False
             
        self._bAwsS3QueryFailure = False
        
        #######################################################################
        #Build the following data variables.
        #self._strLatestCompleteUploadAwsS3FullBackupDate
        #self._strLatestCompleteUploadAwsS3FullBackupTime
        #self._strLatestCompleteUploadAwsS3IncrementalBackupDate
        #self._strLatestCompleteUploadAwsS3IncrementalBackupTime
        #
        #self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists
        #self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists
        #self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists        
        #######################################################################
        
        #Get the latest completed-upload full-backup date and time
        #in the current month, with every backup source completely uploaded.
        #(backup-source completeness can be detected using the upload-
        #completion indicator AWS S3 object.)
        #(UPDATE, FINAL DECISION [11/22/2020 11:14 AM CST] when restoring
        #AWS S3 backup data, the backup sources in AWS S3 are used as they are,
        #without comparing them to anything.  the AWS S3 data restoration
        #is all about restoring what's in AWS S3--the AWS S3 data does not
        #need to be compared to anything else.)
        bLastFullBackupChecked = False
        
        str_listCompleteUploadBackupSourceAwsS3Names = []
        
        strLastIncrementalBackupFullBackupDate = ''
        strLastIncrementalBackupFullBackupTime = ''
        
        iZeroBasedIncrementalBackupStartIndex = -1
        iZeroBasedIncrementalBackupEndIndex = -1        
        
        for iZeroBasedBackupAwsS3ObjectNameIndex in \
            range(0, len(str_listBackupAwsS3ObjectNames)):

            strBackupAwsS3ObjectName = str_listBackupAwsS3ObjectNames[ \
                iZeroBasedBackupAwsS3ObjectNameIndex]
                
            regexp_match_objBackupAwsS3ObjectName = \
                self.regexp_objBackupAwsS3ObjectNameParser.search( \
                strBackupAwsS3ObjectName)
                
            if regexp_match_objBackupAwsS3ObjectName == None:
                strErrorMessage = 'Invalid AWS S3 object name in \
_QueryBackupAwsS3BucketForRegularBackup(). ' + strBackupAwsS3ObjectName
                print(strErrorMessage)
                if self._aam_abl.strOperationType == \
                    'one-step-aws-data-restoration':
                    self._fileLocalBackupLog.write('\n' + strErrorMessage + '\n')                 
                continue
                
            strFullBackupDate = regexp_match_objBackupAwsS3ObjectName.group(2)
            strFullBackupTime = \
                regexp_match_objBackupAwsS3ObjectName.group(3) + '.' + \
                regexp_match_objBackupAwsS3ObjectName.group(4)            
            
            strIncrementalBackupDate = \
                regexp_match_objBackupAwsS3ObjectName.group(5)  
                
            if strIncrementalBackupDate != '0': #not a full backup
                if len(self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists) \
                    > 0:
                        
                    bAllBackupSourcesCompletelyUploaded = True
                    for strBackupSourceName in \
                        self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                        if strBackupSourceName not in \
                            str_listCompleteUploadBackupSourceAwsS3Names:
                            bAllBackupSourcesCompletelyUploaded = False
                            break
    
                    if bAllBackupSourcesCompletelyUploaded == True:
                        bLastFullBackupChecked = True
                        break                
                
                if strLastIncrementalBackupFullBackupDate == strFullBackupDate \
                    and \
                    strLastIncrementalBackupFullBackupTime == strFullBackupTime:
                    iZeroBasedIncrementalBackupEndIndex += 1
                else:
                    strLastIncrementalBackupFullBackupDate = strFullBackupDate
                    strLastIncrementalBackupFullBackupTime = strFullBackupTime
                    
                    iZeroBasedIncrementalBackupStartIndex = \
                        iZeroBasedBackupAwsS3ObjectNameIndex
                    iZeroBasedIncrementalBackupEndIndex = \
                        iZeroBasedBackupAwsS3ObjectNameIndex                        
                
                continue
            
            strBackupSourceUniqueName = \
                regexp_match_objBackupAwsS3ObjectName.group(9)          
                                  
            
            if strFullBackupDate == \
                self._strLatestCompleteUploadAwsS3FullBackupDate and \
                strFullBackupTime == \
                self._strLatestCompleteUploadAwsS3FullBackupTime:
                    
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True
                    str_listCompleteUploadBackupSourceAwsS3Names.append( \
                        strBackupSourceUniqueName)                    
                    continue                    
                    
                if strBackupSourceUniqueName in \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                        strBackupSourceUniqueName].append(strBackupAwsS3ObjectName)
                else:
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                        strBackupSourceUniqueName] = [strBackupAwsS3ObjectName]     
            else:
                if len(self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists) \
                    > 0:
                        
                    bAllBackupSourcesCompletelyUploaded = True
                    for strBackupSourceName in \
                        self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                        if strBackupSourceName not in \
                            str_listCompleteUploadBackupSourceAwsS3Names:
                            bAllBackupSourcesCompletelyUploaded = False
                            break
    
                    if bAllBackupSourcesCompletelyUploaded == True:
                        bLastFullBackupChecked = True
                        break                   
                
                self._strLatestCompleteUploadAwsS3FullBackupDate = \
                    strFullBackupDate
                self._strLatestCompleteUploadAwsS3FullBackupTime = \
                    strFullBackupTime
                    
                str_listCompleteUploadBackupSourceAwsS3Names = []
                
                self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists = {}
                
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True
                    str_listCompleteUploadBackupSourceAwsS3Names.append( \
                        strBackupSourceUniqueName)
                else:
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                        strBackupSourceUniqueName] = [strBackupAwsS3ObjectName] 
                
            
        if self._strLatestCompleteUploadAwsS3FullBackupDate == '':
            return False
            
        if not bLastFullBackupChecked:
            if len(self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists) \
                > 0:
                    
                bAllBackupSourcesCompletelyUploaded = True
                for strBackupSourceName in \
                    self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
                    if strBackupSourceName not in \
                        str_listCompleteUploadBackupSourceAwsS3Names:
                        bAllBackupSourcesCompletelyUploaded = False
                        break

                if not bAllBackupSourcesCompletelyUploaded:
                    self._strLatestCompleteUploadAwsS3FullBackupDate = ''
                    self._strLatestCompleteUploadAwsS3FullBackupTime = ''                    
                    return False    
            
        
        #Get the latest completed-upload incremental-backup date and time
        #in the completed-upload full-backup date and time,
        #with all the backup sources.
        if strLastIncrementalBackupFullBackupDate != \
            self._strLatestCompleteUploadAwsS3FullBackupDate or \
            strLastIncrementalBackupFullBackupTime != \
            self._strLatestCompleteUploadAwsS3FullBackupTime:
                
            self._strLatestCompleteUploadAwsS3IncrementalBackupDate = \
                self._strLatestCompleteUploadAwsS3FullBackupDate
            self._strLatestCompleteUploadAwsS3IncrementalBackupTime = \
                self._strLatestCompleteUploadAwsS3FullBackupTime 
            
            return True
        
        
        str_listCompleteUploadBackupSourceAwsS3Names = []
        dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists = {}
        dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists = {}
        #dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists and
        #dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists are used
        #to avoid deleting the complete-upload incremental backups already
        #recorded in 
        #self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists and
        #self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists.
        
        strLastIncrementalBackupDate = ''
        strLastIncrementalBackupTime = ''
        
        for iZeroBasedBackupAwsS3ObjectNameIndex in \
            range(iZeroBasedIncrementalBackupStartIndex, 
                  iZeroBasedIncrementalBackupEndIndex + 1):

            strBackupAwsS3ObjectName = str_listBackupAwsS3ObjectNames[ \
                iZeroBasedBackupAwsS3ObjectNameIndex]
                
            regexp_match_objBackupAwsS3ObjectName = \
                self.regexp_objBackupAwsS3ObjectNameParser.search( \
                strBackupAwsS3ObjectName)
                
            if regexp_match_objBackupAwsS3ObjectName == None:        
                continue
                
            
            strIncrementalBackupDate = \
                regexp_match_objBackupAwsS3ObjectName.group(5)
            strIncrementalBackupTime = \
                regexp_match_objBackupAwsS3ObjectName.group(6) + '.' + \
                regexp_match_objBackupAwsS3ObjectName.group(7)            
            
            strBackupSourceUniqueName = \
                regexp_match_objBackupAwsS3ObjectName.group(9)          

            
            if strIncrementalBackupDate == strLastIncrementalBackupDate and \
                strIncrementalBackupTime == strLastIncrementalBackupTime:
                    
                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True
                    str_listCompleteUploadBackupSourceAwsS3Names.append( \
                        strBackupSourceUniqueName)
                    continue                    
                    
                if strBackupSourceUniqueName in \
                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                        strBackupSourceUniqueName].append(strBackupAwsS3ObjectName)
                else:
                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                        strBackupSourceUniqueName] = [strBackupAwsS3ObjectName]
                
                iLastPeriodPosition = strBackupAwsS3ObjectName.rfind('.')
                if int(strBackupAwsS3ObjectName[iLastPeriodPosition + 1: \
                    len(strBackupAwsS3ObjectName)]) == 1:
                    #dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                    #    strBackupSourceUniqueName] = \
                    #    strBackupAwsS3ObjectName[0:iLastPeriodPosition]   
                    dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                        strBackupSourceUniqueName] = [strBackupAwsS3ObjectName]
            else:
                if len(dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists) \
                    > 0:
                        
                    bAllBackupSourcesCompletelyUploaded = True
                    for strBackupSourceName in \
                        dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                        if strBackupSourceName not in \
                            str_listCompleteUploadBackupSourceAwsS3Names:
                            bAllBackupSourcesCompletelyUploaded = False
                            break
    
                    if bAllBackupSourcesCompletelyUploaded == True:
                        if self._strLatestCompleteUploadAwsS3IncrementalBackupDate \
                            == '':
                            self._strLatestCompleteUploadAwsS3IncrementalBackupDate \
                                = strLastIncrementalBackupDate
                            self._strLatestCompleteUploadAwsS3IncrementalBackupTime \
                                = strLastIncrementalBackupTime                        
                        
                        for strBackupSourceName in \
                            dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                            if strBackupSourceName in \
                                self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                                self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                                    strBackupSourceName].extend( \
                                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                                    strBackupSourceName])
                    
                                self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                                    strBackupSourceName].extend( \
                                    dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                                    strBackupSourceName])
                            else:
                                self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                                    strBackupSourceName] = \
                                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                                    strBackupSourceName]
                                    
                                self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                                    strBackupSourceName] = \
                                    dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                                    strBackupSourceName]                                  
                
                strLastIncrementalBackupDate = strIncrementalBackupDate
                strLastIncrementalBackupTime = strIncrementalBackupTime
                    
                str_listCompleteUploadBackupSourceAwsS3Names = []
                
                dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists = {}
                dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists = {}

                if regexp_match_objBackupAwsS3ObjectName.group(8) == 'yes':
                    #bUploadCompletionIndicator = True
                    str_listCompleteUploadBackupSourceAwsS3Names.append( \
                        strBackupSourceUniqueName)
                    continue

                dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                    strBackupSourceUniqueName] = [strBackupAwsS3ObjectName]
                                                                                 
                iLastPeriodPosition = strBackupAwsS3ObjectName.rfind('.')
                if int(strBackupAwsS3ObjectName[iLastPeriodPosition + 1: \
                    len(strBackupAwsS3ObjectName)]) == 1:
                    #dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                    #    strBackupSourceUniqueName] = \
                    #    strBackupAwsS3ObjectName[0:iLastPeriodPosition]   
                    dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                        strBackupSourceUniqueName] = [strBackupAwsS3ObjectName]                                                                                 

                
        if len(dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists) \
            > 0:
  
            bAllBackupSourcesCompletelyUploaded = True
            for strBackupSourceName in \
                dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                if strBackupSourceName not in \
                    str_listCompleteUploadBackupSourceAwsS3Names:
                    bAllBackupSourcesCompletelyUploaded = False
                    break

            if bAllBackupSourcesCompletelyUploaded == True:
                if self._strLatestCompleteUploadAwsS3IncrementalBackupDate \
                    == '':
                    self._strLatestCompleteUploadAwsS3IncrementalBackupDate \
                        = strLastIncrementalBackupDate
                    self._strLatestCompleteUploadAwsS3IncrementalBackupTime \
                        = strLastIncrementalBackupTime                  
                
                for strBackupSourceName in \
                    dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                    if strBackupSourceName in \
                        self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists:
                        self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                            strBackupSourceName].extend( \
                            dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                            strBackupSourceName])
            
                        self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                            strBackupSourceName].extend( \
                            dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                            strBackupSourceName])
                    else:
                        self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                            strBackupSourceName] = \
                            dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                            strBackupSourceName]
                            
                        self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                            strBackupSourceName] = \
                            dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                            strBackupSourceName]                

        for strBackupSourceName in \
            self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists:
            
            self._dictBackupSourceNamesToFullBackupAwsS3ObjectNameLists[ \
                strBackupSourceName].sort()
            self._dictBackupSourceNamesToIncrementalBackupAwsS3ObjectNameLists[ \
                strBackupSourceName].sort()
            self._dictBackupSourceNamesToIncrementalBackupArchiveFileNameLists[ \
                strBackupSourceName].sort()

        return True

        
    def _SendEmailReport(self):
        """
        INPUTS
        ------
        self._aam_abl.bSendEmailReport
        self._aam_abl.strOperationType
        
        self._bBackupSuccess
        self._datetimeBackupExecutionStart
        self._aam_abl.strUniqueBackupSourceLocationName
        self._aam_abl.str_listBackupDestinationTypes
        self._strBackupScope
        self._bFileLockAcquisitionFailure
        self._bBackupInstructionPlainTextFileReadError
        self._bAwsS3QueryFailure
        self._str_listLocalBackupValidationFailureShadowMountDirectoryFullPaths
        self._str_listNoIncrementalBackupFilesShadowMountDirectoryFullPaths
        
        self._bRestorationSuccess
        
        self._aam_abl.strEmailSenderName
        self._aam_abl.strEmailSenderAddress
        self._aam_abl.strEmailRecipientAddress
                
        
        OUTPUTS
        -------
        The sent email
        """    
        
        #######################################################################
        #If send email report is disabled, return without attempting
        #to send the email.
        #######################################################################
        if not self._aam_abl.bSendEmailReport: return


        #######################################################################
        #If incremental-only backup, return without attempting
        #to send the email.
        #######################################################################
        if self._aam_abl.strOperationType == 'incremental-only-backup':
            return
        
        
        #######################################################################
        #Check the email-content data variables,
        #and generate the email content and title.
        #######################################################################
        if self._aam_abl.strOperationType == 'regular-backup':
        
            if self._bBackupSuccess:
                strEmailTitle = 'SUCCESS, '
            else:
                strEmailTitle = 'FAILURE, '
                
            if self._strBackupScope == 'full-backup':
                strEmailTitle += self._strBackupExecutionStartDateTime + \
                    ' ' + 'full regular backup!'
            else:
                strEmailTitle += self._strBackupExecutionStartDateTime + \
                    ' ' + 'incremental regular backup!'
            
            strEmailReportContent = \
                'Data Backup Execution Start Date-Time:  ' + \
                self._strBackupExecutionStartDateTime + '\n\n'             
            strEmailReportContent += \
                'Data Backup Execution End Date-Time:  ' + \
                self._strBackupExecutionEndDateTime + '\n\n\n'             
            
            
            strEmailReportContent += \
                'Unique Backup-Source Location Name:  ' + \
                self._aam_abl.strUniqueBackupSourceLocationName + '\n\n'            
            
            strEmailReportContent += 'Backup destination type(s):  ' + \
                str(self._aam_abl.str_listBackupDestinationTypes) + '\n\n'
            
            strEmailReportContent += 'Backup scope:  ' + self._strBackupScope \
                + '\n\n'
            
            if self._bFileLockAcquisitionFailure:
                strEmailReportContent += 'Unable to acquire the file lock.\n\n'
    
            if self._bBackupInstructionPlainTextFileReadError:
                strEmailReportContent += \
                    'Unable to read the backup instruction plain text file.\n\n'  
                    
            if self._bAwsS3QueryFailure:
                strEmailReportContent += 'AWS S3 query failure.\n\n'   
    
            if len(self._str_listLocalBackupValidationFailureShadowMountDirectoryFullPaths) \
                != 0:
                strEmailReportContent += \
                    'Local Backup Validation Failure Shadow Mount Directory Full Paths.\n'
                for strLocalBackupValidationFailureShadowMountDirectoryFullPath in \
                    self._str_listLocalBackupValidationFailureShadowMountDirectoryFullPaths:
                    strEmailReportContent += \
                        strLocalBackupValidationFailureShadowMountDirectoryFullPath \
                        + '\n'
                strEmailReportContent += '\n'
                
            if len(self._str_listNoIncrementalBackupFilesShadowMountDirectoryFullPaths) \
                != 0:
                strEmailReportContent += \
                    'No Incremental Backup Files Shadow Mount Directory Full Paths.\n'
                for strNoIncrementalBackupFilesShadowMountDirectoryFullPath in \
                    self._str_listNoIncrementalBackupFilesShadowMountDirectoryFullPaths:
                    strEmailReportContent += \
                        strNoIncrementalBackupFilesShadowMountDirectoryFullPath \
                        + '\n'
                strEmailReportContent += '\n'                
                        
            strEmailReportContent += \
                'For more info, refer to the local backup log.\n' + \
                self._strLocalBackupLogFileFullPath
        else: #data restoration
            if self._bRestorationSuccess:
                strEmailTitle = 'SUCCESS, '
            else:
                strEmailTitle = 'FAILURE, '
                
            strEmailTitle += self._strBackupExecutionStartDateTime + \
                ' data restoration!'
                
            strEmailReportContent = \
                'Data Restoration Execution Start Date-Time:  ' + \
                self._strBackupExecutionStartDateTime + '\n\n'             
            strEmailReportContent += \
                'Data Restoration Execution End Date-Time:  ' + \
                self._strBackupExecutionEndDateTime + '\n\n\n'                
                
            strEmailReportContent += \
                'Unique Backup-Source Location Name:  ' + \
                self._aam_abl.strUniqueBackupSourceLocationName + '\n\n'   
                
            if self._bAwsS3QueryFailure:
                strEmailReportContent += 'AWS S3 query failure.\n\n'                
                            
            strEmailReportContent += \
                'For more info, refer to the local data restoration log.\n' + \
                self._strLocalBackupLogFileFullPath
        

        #######################################################################
        #Try sending the email.
        #######################################################################  
        try:
            dictSesSendEmailResponse = self.ses_client.send_email(
              Source          = self._aam_abl.strEmailSenderName + ' <' + \
                  self._aam_abl.strEmailSenderAddress + '>',
              Destination     = {
                'ToAddresses' : [
                  self._aam_abl.strEmailRecipientAddress,
                ]
              },
            
              Message = {
                'Subject'    : {
                  'Data'     : strEmailTitle,
                  'Charset'  : 'UTF-8'
                },
                'Body'       : {
                  'Text'     : {
                    'Data'   : strEmailReportContent,
                    'Charset': 'UTF-8'
                  #},
                  #'Html'     : {
                  #  'Data'   : strEmailReportContent,
                  #  'Charset': 'UTF-8'
                  }
                }
              },
            
              ReplyToAddresses = [
                self._aam_abl.strEmailSenderAddress,
              ],
                      
              ReturnPath = self._aam_abl.strEmailSenderAddress,   
            )
        except Exception as exc:
            self._fileLocalBackupLog.write('\n\n--------------------\n')
            self._fileLocalBackupLog.write('Email sending error!\n' + \
                str(exc) + '\n')
            self._fileLocalBackupLog.write('--------------------\n')
            print('Email sending error!\n' + str(exc))
         

if __name__ == '__main__':
    aam_abl = Aam_Auto_Backup_Launcher(sys.argv)