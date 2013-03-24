#!/usr/bin/env python
#    run python as determined from the environment.
#    For example, this could be under linux, macintosh or cygwin environments
#!/usr/bin/env win32python.sh
#    run a script that starts a Windows version of Python from cygwin
#
# For example, add the following to your path (in bash):
#    export PATH=/home/user/twoutline:$PATH
###

###############################################################################
# twoutline - description based outlines with TaskWarrior
#
# Copyright 2012,2013 Aikido Guy.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the
#
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA
# 02110-1301
# USA
#
###############################################################################
# default configuration
TASK_PROG   = "task"  # command to run TaskWarrior
OUTLINE_SEP = "."     # separator between numbers in the hierarchy e.g. 2.3.4
                      # change to "-" or whatever you'd like to use (untested)
LOCAL_TIMEZONE         = 'Canada/Eastern' # your location in the world
PRINT_DATE_TIME_FORMAT = "%Y/%m/%d %H:%M" 
#
# Do not change the following unless you are sure you know what to do
UTC_FORMAT = "%Y%m%dT%H%M%SZ"  # Zulu time zone used by TaskWarrior
### 

import json  # See http://json.org/
import os
import platform
import string
import sys
import time
import datetime
import pytz      # See http://pytz.sourceforge.net/
                 # Tested with: pytz-2012c-py2.7.egg

if(LOCAL_TIMEZONE not in pytz.all_timezones):
   raise RuntimeError("Did NOT find timezone '" + LOCAL_TIMEZONE + "'")
theLocalTimeZone = pytz.timezone(LOCAL_TIMEZONE) 

def getNowInUTCandLocalTime():
   nowInUTC = datetime.datetime.utcnow()
   # make the naive datetime into a UTC aware datetime
   nowInUTC = pytz.utc.localize(nowInUTC)
   # convert to local time zone
   nowInLocalTimeZone = nowInUTC.astimezone(theLocalTimeZone)
   return (nowInUTC, nowInLocalTimeZone) 

def convertUTCTimeStringToLocalTimeString(utcTimeAsString):
   # create naive datetime from string
   parsedUTC = datetime.datetime.strptime(utcTimeAsString, UTC_FORMAT)
   # make the naive datetime into a UTC aware datetime
   parsedUTC = pytz.utc.localize(parsedUTC)
   # convert UTC time into local time zone
   parsedUTC = parsedUTC.astimezone(theLocalTimeZone)
   # convert to string format
   localTimeAsString = parsedUTC.strftime(PRINT_DATE_TIME_FORMAT)
   return localTimeAsString 

def runTaskWarriorCommand(cmd):
   cmd = TASK_PROG + " rc.verbose=nothing " + cmd
   # Debugging
   # sys.stdout.write("running: '" + cmd + "'\n")
   ###
   os.system(cmd)

def runTaskWarriorCommandAndCollectJSON(cmd):
   cmd = TASK_PROG + " rc.verbose=nothing rc.json.array=yes " + cmd
   # Debugging
   # sys.stdout.write("running: '" + cmd + "'\n")
   ###
   fin,fout = os.popen4(cmd)
   result   = fout.read()
   if( (result==None) or (result=="") ):
      raise RuntimeError("No matching tasks for: " + cmd)
   jsonObj  = json.loads(result)
   return jsonObj

def findFirstKeyForValueInDictionary(val, dic):
   for k,v in dic.iteritems():
      if v==val:
         return k;
   return None

def extractStringBeforeFirstSpace(stringToExtractFrom):
   elementIdx = stringToExtractFrom.find(" ")
   if(elementIdx<0):
      # if no space, then return the whole input string
      return stringToExtractFrom
   return stringToExtractFrom[0:elementIdx]

def writeUndoMessage(numCmds):
   sys.stdout.write("twOutline issued " + str(numCmds) + " command(s) to TaskWarrior\n")
   if(numCmds>0):
      sys.stdout.write("   To undo all twOutline changes run the following:\n")
      sys.stdout.write("      twOutline undo " + str(numCmds) + "\n")

def issueTaskWarriorModifyCommandsForCompressedPaths(
   initialPaths, initialUUIDs, compressedPaths, compressedUUIDs):
   """ Compressing the outline does not change the inherent
       structure, so we can safely use the same indices to
       determine the modify commands to issue to TaskWarrior
   """
   numCmds = 0
   for ii,initialPath in initialPaths.iteritems():
      compressedPath = compressedPaths[ii]
      if(initialPath!=compressedPath):
         numCmds = numCmds + 1
         runTaskWarriorCommand(initialUUIDs[ii] + " modify /^" + initialPath + " /" + compressedPath + " /")
   writeUndoMessage(numCmds)

def issueTaskWarriorModifyCommandsForMovedPaths(
   initialPaths, initialUUIDs, movedPaths, movedUUIDs):
   """ Moving parts of the outline will cause a structural
       change. However, if there were k tasks in the original
       outline then there will be exactly k tasks in the new
       outline in a 1-1 manner. All that we need to do, is
       match the tasks based on the UUIDs and then issue the
       appropriate modification commands to TaskWarrior.
       This code assumes that UUIDs are unique... so no checking
       is performed that they truly are.
   """
   numCmds = 0
   for ii,initialPath in initialPaths.iteritems():
      initialUUID  = initialUUIDs[ii]
      movedUUIDIdx = findFirstKeyForValueInDictionary(initialUUID,movedUUIDs)
      if(movedUUIDIdx==None):
         raise RuntimeError("UUID '" + initialUUID + "' not found in new outline?")
      movedPath = movedPaths[movedUUIDIdx]
      if(initialPath!=movedPath):
         numCmds = numCmds + 1
         runTaskWarriorCommand(initialUUID + " modify /^" + initialPath + " /" + movedPath + " /")
   writeUndoMessage(numCmds)

class CmdLineOptions(object):
   def printUsage(self, argv):
      sys.stdout.write("twOutline - description based outlines with TaskWarrior\n")
      sys.stdout.write("       ID Description\n")
      sys.stdout.write("      ---------------\n")
      sys.stdout.write("       1  1 Introduction\n")
      sys.stdout.write("       3  1.1 Beginning\n")
      sys.stdout.write("       2  1.2 Middle\n")
      sys.stdout.write("       6  1.2.1 Important\n")
      sys.stdout.write("       5  1.3 End\n")
      sys.stdout.write("       4  2 Conclusion\n")
      sys.stdout.write("Usage:\n")
      sys.stdout.write("\n")
      sys.stdout.write("twOutline <filter> tableofcontents all text|latex\n")
      sys.stdout.write("twOutline <filter> tableofcontents from <sectionA> to <sectionB> text\n")
      sys.stdout.write("  -collect the outline from TaskWarrior and print it\n")
      sys.stdout.write("\n")
      sys.stdout.write("twOutline <filter> move <sectionA> before|after|under <sectionB>\n")
      sys.stdout.write("  -move a section to another location\n")
      sys.stdout.write("  -<section> has the form X or X" + OUTLINE_SEP + "Y or X" + OUTLINE_SEP + "Y" + OUTLINE_SEP + "Z etc.\n")
      sys.stdout.write("  -neither <sectionA> nor <sectionB> need to be associated with actual tasks\n")
      sys.stdout.write("\n")
      sys.stdout.write("twOutline <filter> modify <sectionA> to <sectionB> <outlineCmd>\n")
      sys.stdout.write("  -modify tasks in the interval\n")
      sys.stdout.write("  -<section> has the form X or X" + OUTLINE_SEP + "Y or X" + OUTLINE_SEP + "Y" + OUTLINE_SEP + "Z etc.\n")
      sys.stdout.write("  -<outlineCmd> may be one of the following:\n")
      sys.stdout.write("      wait all <date>\n")
      sys.stdout.write("      wait distribute <number> <unit>\n")
      sys.stdout.write("         -<number> has format X or X.Y\n")
      sys.stdout.write("         -<unit> is one of the supported units e.g. hours, days, weeks, etc.\n")
      sys.stdout.write("\n")
      sys.stdout.write("twOutline <filter> compress\n")
      sys.stdout.write("  -removes all horizontal numbering gaps in the outline\n")
      sys.stdout.write("  -numbers start from 1\n")
      sys.stdout.write("\n")
      sys.stdout.write("twOutline undo <numberOfTimes>\n")
      sys.stdout.write("  -issue <numberOfTimes> undos to TaskWarrior\n")
      sys.stdout.write("  -this is a convenience wrapper for TaskWarrior\n")
      raise RuntimeError("") # break out of the program
   def __init__(self, argv):
      self.taskfilter = ""
      self.cmd         = ""
      self.cmdIdx      = -1
      self.tocSel      = ""
      self.tocType     = ""
      self.sectionAIdx = -1
      self.locationIdx = -1
      self.sectionBIdx = -1
      self.modifyCmd   = ""
      self.waitType    = "" # all|distribute
      self.waitDate    = ""
      self.waitNumber  = -1 # should be positive
      self.waitUnit    = "" # should be a valid TaskWarrior unit e.g. hours, days, weeks, etc.
      self.waitCounter = 1
      if 'compress' in argv:
         self.cmd    = "compress"
         self.cmdIdx = argv.index(self.cmd)
         # and get the filter for the command
         self.taskfilter = string.join(argv[0:self.cmdIdx])
      if 'tableofcontents' in argv:
         self.cmd    = "tableofcontents"
         self.cmdIdx = argv.index(self.cmd)
         if(len(argv)-1 < self.cmdIdx+1):
            self.printUsage(argv)
         self.tocSel = argv[self.cmdIdx+1]
         #
         # twOutline <filter> tableofcontents all text|latex
         if(self.tocSel=="all"):
            if(len(argv)-1 < self.cmdIdx+2):
               self.printUsage(argv)
            self.tocType = argv[self.cmdIdx+2]
         #
         # twOutline <filter> tableofcontents from <sectionA> to <sectionB> text
         if(self.tocSel=="from"):
            if(len(argv)-1 < self.cmdIdx+2):
               self.printUsage(argv)
            self.sectionAIdx = self.cmdIdx+2
            #
            if(len(argv)-1 < self.cmdIdx+3):
               self.printUsage(argv)
            if(argv[self.cmdIdx+3]!="to"):
               self.printUsage(argv)
            #
            if(len(argv)-1 < self.cmdIdx+4):
               self.printUsage(argv)
            self.sectionBIdx = self.cmdIdx+4
            #
            if(len(argv)-1 < self.cmdIdx+5):
               self.printUsage(argv)
            self.tocType = argv[self.cmdIdx+5]
         if(self.tocSel==""):
            self.printUsage(argv)
         # and get the filter for the command
         self.taskfilter = string.join(argv[0:self.cmdIdx])
      if 'move' in argv:
         self.cmd    = "move"
         self.cmdIdx = argv.index(self.cmd)
         if 'before' in argv:
            self.locationIdx = argv.index("before")
            if 'after' in argv:
               self.printUsage(argv)
            if 'under' in argv:
               self.printUsage(argv)
         if 'after' in argv:
            self.locationIdx  = argv.index("after")
            if 'before' in argv:
               self.printUsage(argv)
            if 'under' in argv:
               self.printUsage(argv)
         if 'under' in argv:
            self.locationIdx = argv.index("under")
            if 'before' in argv:
               self.printUsage(argv)
            if 'after' in argv:
               self.printUsage(argv)
         if(self.cmdIdx < 0):
            self.printUsage(argv)
         if(self.locationIdx < 0):
            self.printUsage(argv)
         if(self.cmdIdx + 2 != self.locationIdx):
            self.printUsage(argv)
         if(len(argv)-1 != self.locationIdx+1):
            self.printUsage(argv)
         self.sectionAIdx = self.cmdIdx+1
         self.sectionBIdx = self.locationIdx+1
         # and get the filter for the command
         self.taskfilter = string.join(argv[0:self.cmdIdx])
      if 'modify' in argv:
         # modify <sectionA> to <sectionB> <outlineCmd>
         self.cmd    = "modify"
         self.cmdIdx = argv.index(self.cmd)
         if(len(argv)-1 < self.cmdIdx+1):
            self.printUsage(argv)
         self.sectionAIdx = self.cmdIdx+1
         if(len(argv)-1 < self.sectionAIdx+1):
            self.printUsage(argv)
         if(argv[self.sectionAIdx+1]!="to"):
            self.printUsage(argv)
         if(len(argv)-1 < self.sectionAIdx+2):
            self.printUsage(argv)
         self.sectionBIdx = self.sectionAIdx+2
         #
         # process <outlineCmd>
         if(len(argv)-1 < self.sectionBIdx+1):
            self.printUsage(argv)
         self.modifyCmd  = argv[self.sectionBIdx+1]
         #
         if(self.modifyCmd=="wait"):
            if(len(argv)-1 < self.sectionBIdx+2):
               self.printUsage(argv)
            self.waitType = argv[self.sectionBIdx+2]
            if(self.waitType=="all"):
               # wait all <date>
               if(len(argv)-1 < self.sectionBIdx+3):
                  self.printUsage(argv)
               self.waitDate = argv[self.sectionBIdx+3]
            if(self.waitType=="distribute"):
               # wait distribute <number> <unit>
               if(len(argv)-1 < self.sectionBIdx+3):
                  self.printUsage(argv)
               self.waitNumber = float(argv[self.sectionBIdx+3]) # a positive number
               if(self.waitNumber < 0.0):
                  raise RuntimeError("<number> should be positive but it was '" + str(self.waitNumber) + "'")
               #
               if(len(argv)-1 < self.sectionBIdx+4):
                  self.printUsage(argv)
               self.waitUnit   = argv[self.sectionBIdx+4]        # a valid unit e.g. hours, days, weeks, etc.
         # and get the filter for the command
         self.taskfilter = string.join(argv[0:self.cmdIdx])
      if 'undo' in argv:
         self.cmd    = "undo"
         self.cmdIdx = argv.index(self.cmd)
      # if no cmd, then some kind of error
      if(self.cmd == ""):
         self.printUsage(argv)
   def getSectionLabelForSectionA(self, argv):
      return argv[self.sectionAIdx]
   def getSectionLabelForSectionB(self, argv):
      return argv[self.sectionBIdx]
   def getLocationCommand(self, argv):
      return argv[self.locationIdx]

class Outline(object):
   def __init__(self):
      self.jsonObj  = None # initialized only for top level outline object
      self.mark     = None # boolean (indicated by presence of uuid)
      self.idx      = None # only for marked nodes
      self.sections = None # dictionary
   def importFromTaskWarrior(self,taskfilter):
      self.jsonObj = runTaskWarriorCommandAndCollectJSON(taskfilter + " export")
      self.__createOutlineFromJSON(self.jsonObj)
      # now we've finished constructing the outline, so label the idxs
      self.__assignIndicesToMarkedSections(0)
   def __createOutlineFromJSON(self,jsonObj):
      for task in jsonObj:
         uuid     = task["uuid"]
         fulldesc = task["description"]
         if((uuid!=None) and (fulldesc!=None)):
            sl = extractStringBeforeFirstSpace(fulldesc)
            if(self.__isValidStructuredLabels(sl,sl.split(OUTLINE_SEP))==True):
               self.insertStructuredLabel(uuid,sl)
   def __assignIndicesToMarkedSections(self,idx):
      """ Internal utility function; not meant to be invoked """
      if(self.mark!=None):
         self.idx = idx
         idx = idx + 1
      if(self.sections!=None):
         for key,val in self.sections.iteritems():
            idx = val.__assignIndicesToMarkedSections(idx)
      return idx
   def __areValidStructuredLabels(self,sl,labelsAsStrings):
      for ll in labelsAsStrings:
         if(ll.isdigit()==False):
            sys.stdout.write("<section> = " + sl + "\n")
            raise RuntimeError("<section> should be composed of digits")
         if(int(ll)<1):
            sys.stdout.write("<section> = " + sl + "\n")
            raise RuntimeError("<section> should be composed of digits that are >= 1")
   def __isValidStructuredLabels(self,sl,labelsAsStrings):
      for ll in labelsAsStrings:
         if(ll.isdigit()==False):
            return False
         # Don't check for constraints on value (do it later)
         #if(int(ll)<1):
         #   return False
      return True
   def insertStructuredLabel(self,uuid,sl):
      """ Input is a string like "1.2.3.4" """
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      self.__insertCheckedAndSplitLabels(uuid,sl,labelsAsStrings)
   def __insertCheckedAndSplitLabels(self,uuid,sl,labelsAsStrings):
      """ Internal utility function; not meant to be invoked """
      if((labelsAsStrings==None) or (len(labelsAsStrings)<1)):
         if(self.mark!=None):
            sys.stdout.write("<uuid>    = " + uuid + "\n")
            sys.stdout.write("<section> = " + sl + "\n")
            raise RuntimeError("Section already exists... trying to add a duplicate")
         self.mark = uuid
         return
      if(self.sections==None):
         self.sections = { int(labelsAsStrings[0]):Outline() }
      else:
         if((int(labelsAsStrings[0]) in self.sections) == False):
            self.sections[int(labelsAsStrings[0])] = Outline()
      child = self.sections[int(labelsAsStrings[0])]
      child.__insertCheckedAndSplitLabels(uuid,sl,labelsAsStrings[1:])
   def removeOutlineForStructuredLabel(self,sl):
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      return self.__removeOutlineForStructuredLabel(sl,labelsAsStrings)
   def __removeOutlineForStructuredLabel(self,sl,labelsAsStrings):
      if((labelsAsStrings==None) or (len(labelsAsStrings)<1)):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if(self.sections==None):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if((int(labelsAsStrings[0]) in self.sections) == False):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      key = int(labelsAsStrings[0])
      section = self.sections[key]
      if(len(labelsAsStrings)==1):
         del self.sections[key]
         return section
      return section.__removeOutlineForStructuredLabel(sl,labelsAsStrings[1:])
   def insertOutlineBeforeStructuredLabel(self,ol,sl):
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      return self.__insertOutlineBeforeStructuredLabel(ol,sl,labelsAsStrings)
   def __insertOutlineBeforeStructuredLabel(self,ol,sl,labelsAsStrings):
      if((labelsAsStrings==None) or (len(labelsAsStrings)<1)):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if(self.sections==None):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if((int(labelsAsStrings[0]) in self.sections) == False):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if(len(labelsAsStrings)==1):
         sortedSectionKeys = sorted(self.sections.keys())
         keyToInsertBefore = int(labelsAsStrings[0])
         if(((keyToInsertBefore-1)>=1) and (keyToInsertBefore-1 in sortedSectionKeys)):
            # if the previous section doesn't have any marked subsections
            # then it is safe to delete it
            prevOl = self.sections[keyToInsertBefore-1]
            if(prevOl.__hasAtLeastOneMarkedSection()==False):
               del self.sections[keyToInsertBefore-1]
               sortedSectionKeys = sorted(self.sections.keys()) # update deletion
         if(((keyToInsertBefore-1)<1) or (keyToInsertBefore-1 in sortedSectionKeys)):
            # insert at the current location since we couldn't put before
            # and then MAY need to shift down
            startIdx = sortedSectionKeys.index(keyToInsertBefore)
            endIdx = self.__findLastConsecutiveSectionIndexAfter(sortedSectionKeys,startIdx)
            endIdx = endIdx + 1 # to make correct slice add 1
            shiftKeysReversed = sortedSectionKeys[startIdx:endIdx]
            shiftKeysReversed.reverse() # inplace reverse
            for shiftKey in shiftKeysReversed: # consider last one first
               tmp = self.sections[shiftKey]
               del self.sections[shiftKey]
               self.sections[shiftKey+1] = tmp
            self.sections[keyToInsertBefore] = ol
         else:
            # can insert before
            self.sections[keyToInsertBefore-1] = ol
      else:
         recursionKey = int(labelsAsStrings[0])
         section = self.sections[recursionKey]
         section.__insertOutlineBeforeStructuredLabel(ol,sl,labelsAsStrings[1:])
   def insertOutlineAfterStructuredLabel(self,ol,sl):
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      return self.__insertOutlineAfterStructuredLabel(ol,sl,labelsAsStrings)
   def __insertOutlineAfterStructuredLabel(self,ol,sl,labelsAsStrings):
      if((labelsAsStrings==None) or (len(labelsAsStrings)<1)):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if(self.sections==None):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if((int(labelsAsStrings[0]) in self.sections) == False):
         raise RuntimeError("Couldn't find section '" + sl + "' in outline")
      if(len(labelsAsStrings)==1):
         sortedSectionKeys = sorted(self.sections.keys())
         keyToInsertAfter = int(labelsAsStrings[0])
         if(keyToInsertAfter+1 in sortedSectionKeys):
            # if the next section doesn't have any marked subsections
            # then it is safe to delete it
            nextOl = self.sections[keyToInsertAfter+1]
            if(nextOl.__hasAtLeastOneMarkedSection()==False):
               del self.sections[keyToInsertAfter+1]
               sortedSectionKeys = sorted(self.sections.keys()) # update deletion
         if(keyToInsertAfter+1 in sortedSectionKeys):
            # insert at the current location since we couldn't put before
            # and then MAY need to shift down
            startIdx = sortedSectionKeys.index(keyToInsertAfter+1)
            endIdx = self.__findLastConsecutiveSectionIndexAfter(sortedSectionKeys,startIdx)
            endIdx = endIdx + 1 # to make correct slice add 1
            shiftKeysReversed = sortedSectionKeys[startIdx:endIdx]
            shiftKeysReversed.reverse() # inplace reverse
            for shiftKey in shiftKeysReversed: # consider last one first
               tmp = self.sections[shiftKey]
               del self.sections[shiftKey]
               self.sections[shiftKey+1] = tmp
            self.sections[keyToInsertAfter+1] = ol
         else:
            # can insert after
            self.sections[keyToInsertAfter+1] = ol
      else:
         recursionKey = int(labelsAsStrings[0])
         section = self.sections[recursionKey]
         section.__insertOutlineAfterStructuredLabel(ol,sl,labelsAsStrings[1:])
   def insertOutlineUnderStructuredLabel(self,ol,sl):
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      return self.__insertOutlineUnderStructuredLabel(ol,sl,labelsAsStrings)
   def __insertOutlineUnderStructuredLabel(self,ol,sl,labelsAsStrings):
      if((labelsAsStrings==None) or (len(labelsAsStrings)==0)):
         if(self.sections==None):
            self.sections = { 1:ol }
         else:
            if((1 in self.sections) == False):
               self.sections[1] = ol
            else:
               sortedSectionKeys = sorted(self.sections.keys())
               keyToInsertBefore = 1
               # insert at the current location since we couldn't put before
               # and then MAY need to shift down
               startIdx = sortedSectionKeys.index(keyToInsertBefore)
               endIdx = self.__findLastConsecutiveSectionIndexAfter(sortedSectionKeys,startIdx)
               endIdx = endIdx + 1 # to make correct slice
               shiftKeysReversed = sortedSectionKeys[startIdx:endIdx]
               shiftKeysReversed.reverse() # inplace reverse
               for shiftKey in shiftKeysReversed: # consider last one first
                  tmp = self.sections[shiftKey]
                  del self.sections[shiftKey]
                  self.sections[shiftKey+1] = tmp
               self.sections[keyToInsertBefore] = ol
      else:
         recursionKey = int(labelsAsStrings[0])
         section = self.sections[recursionKey]
         section.__insertOutlineUnderStructuredLabel(ol,sl,labelsAsStrings[1:])
   def __findLastConsecutiveSectionIndexAfter(self,sortedKeys,startIdx):
      """ Given 2,3,4,6 as keys and 1 as startIdx then return 2 as endIdx """
      sortedKeys2 = sortedKeys[startIdx:]
      endIdx = startIdx
      for ii,vv in enumerate(sortedKeys2):
         if(ii+1 < len(sortedKeys2)):
            if(sortedKeys2[ii+1] == (sortedKeys2[ii]+1)):
               endIdx = endIdx + 1
            else:
               break
      return endIdx
   def isStructuredLabelInOutline(self,sl):
      """ Input is a string like "1.2.3.4" """
      labelsAsStrings = sl.split(OUTLINE_SEP)
      self.__areValidStructuredLabels(sl,labelsAsStrings)
      return self.__isStructuredLabelInOutline(sl,labelsAsStrings)
   def __isStructuredLabelInOutline(self,sl,labelsAsStrings):
      """ Internal utility function; not meant to be invoked """
      if((labelsAsStrings==None) or (len(labelsAsStrings)<1)):
         return True
      if(self.sections==None):
         return False
      if((int(labelsAsStrings[0]) in self.sections) == False):
         return False
      child = self.sections[int(labelsAsStrings[0])]
      return child.__isStructuredLabelInOutline(sl,labelsAsStrings[1:])
   def printOutlineAsText(self):
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         subsection = self.sections[key]
         subsection.__printOutlineAsText(self.jsonObj)
   def __printOutlineAsText(self,jsonObj):
      # jsonObj is only kept inside Outline object at top-level
      if(self.mark!=None):
         fullDesc  = self.__getFullDescriptionForUUID(self.mark,jsonObj)
         theID     = self.__getIDForUUID(self.mark,jsonObj)
         theStatus = self.__getStatusForUUID(self.mark,jsonObj)
         sys.stdout.write(str(theID) + "\t" + theStatus + "\t" + fullDesc + "\n")
      if(self.sections!=None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            subsection = self.sections[key]
            subsection.__printOutlineAsText(jsonObj)
   def printOutlineAsLatex(self):
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         subsection = self.sections[key]
         subsection.__printOutlineAsLatex(self.jsonObj)
   def __printOutlineAsLatex(self,jsonObj):
      # jsonObj is only kept inside Outline object at top-level
      if(self.mark!=None):
         fullDesc = self.__getFullDescriptionForUUID(self.mark,jsonObj)
         sys.stdout.write("% " + fullDesc + "\n")
         sl = extractStringBeforeFirstSpace(fullDesc)
         labelsAsStrings = sl.split(OUTLINE_SEP)
         sys.stdout.write("\\")
         for sec in labelsAsStrings[0:(len(labelsAsStrings)-1)]: # not last section
            sys.stdout.write("sub")
         sys.stdout.write("section{")
         sys.stdout.write(fullDesc[(len(sl)+1):]) # everything except structured label
         sys.stdout.write("}\n\n\n")
      if(self.sections!=None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            subsection = self.sections[key]
            subsection.__printOutlineAsLatex(jsonObj)
   def __getFullDescriptionForUUID(self,uuid,jsonObj):
      for task in jsonObj:
         taskUUID = task["uuid"]
         if(taskUUID==uuid):
            return task["description"]
      raise RuntimeError("Implementation problem!\nuuid " + uuid + " not found in TaskWarrior")
   def __getIDForUUID(self,uuid,jsonObj):
      for task in jsonObj:
         taskUUID = task["uuid"]
         if(taskUUID==uuid):
            return task["id"]
      raise RuntimeError("Implementation problem!\nuuid " + uuid + " not found in TaskWarrior")
   def __getStatusForUUID(self,uuid,jsonObj):
      for task in jsonObj:
         taskUUID = task["uuid"]
         if(taskUUID==uuid):
            status = task["status"]
            if(status=="completed"):
               status = status + "\t" # add an extra tab so things line up
            if(status=="pending"):
               status = "\t\t"        # add an extra tab so things line up
            if(status=="waiting"):
               status = convertUTCTimeStringToLocalTimeString(task["wait"])
            return status
      raise RuntimeError("Implementation problem!\nuuid " + uuid + " not found in TaskWarrior")
   def printOutlineForDebugging(self):
      sys.stdout.write("Outline:\n")
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         val = self.sections[key]
         val.__printOutline(3,str(key))
   def __printOutline(self,indent,path):
      """ Internal utility function; not meant to be invoked
          indent is a number specifying how many chars to indent
      """
      if(self.mark!=None):
         sys.stdout.write(" "*indent + path + " uuid:" + self.mark + " idx:" + str(self.idx) + "\n")
      if(self.sections != None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            val = self.sections[key]
            val.__printOutline(indent, path+OUTLINE_SEP+str(key))
   def collectOutlinePaths(self):
      allPaths = { } # idx:path
      if(self.sections==None or self.sections.keys()==None):
         raise RuntimeError("No tasks seem to have a hierarchy associated to them (e.g. X or X.Y or X.Y.Z etc.)")
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         val = self.sections[key]
         allPaths = val.__collectOutlinePaths(str(key),allPaths)
      return allPaths
   def __collectOutlinePaths(self,currPath,allPaths):
      """ Internal utility function; not meant to be invoked """
      if(self.mark!=None):
         allPaths[self.idx] = currPath
      if(self.sections != None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            val = self.sections[key]
            allPaths = val.__collectOutlinePaths(currPath+OUTLINE_SEP+str(key),allPaths)
      return allPaths
   def collectOutlineUUIDs(self):
      allUUIDs = { } # idx:uuid
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         val = self.sections[key]
         allUUIDs = val.__collectOutlineUUIDs(allUUIDs)
      return allUUIDs
   def __collectOutlineUUIDs(self,allUUIDs):
      """ Internal utility function; not meant to be invoked """
      if(self.mark!=None):
         allUUIDs[self.idx] = self.mark
      if(self.sections != None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            val = self.sections[key]
            allUUIDs = val.__collectOutlineUUIDs(allUUIDs)
      return allUUIDs
   def compressOutline(self):
      if(self.sections==None):
         return
      self.__createCompressedLabelsForSubsections()
      for key,val in self.sections.iteritems():
         val.compressOutline()
   def __createCompressedLabelsForSubsections(self):
      """ Internal utility function; not meant to be invoked
          replace original keys with new key values
      """
      subsectionKeys = sorted(self.sections.keys())
      for ii,oldkey in enumerate(subsectionKeys):
         oldval = self.sections[oldkey]
         del self.sections[oldkey]
         self.sections[ii+1] = oldval # python is 0-based and I want 1-based labels
   def __hasAtLeastOneMarkedSection(self):
      if(self.mark!=None):
         return True
      if(self.sections!=None):
         for key,val in self.sections.iteritems():
            hasMarked = val.__hasAtLeastOneMarkedSection()
            if(hasMarked==True):
               return True
      return False
   # The passed function will be invoked like this:
   #    fcn(taskUUID, taskID, taskDesc, taskStatus, userData)
   # whenever the task should be visited.
   def visitFromSectionToSection(self,aa,bb,fcn,userData):
      numberOfVisits = 0
      aaLabelsAsStrings = aa.split(OUTLINE_SEP)
      bbLabelsAsStrings = bb.split(OUTLINE_SEP)
      #print aaLabelsAsStrings
      #print bbLabelsAsStrings
      aaStart = int(aaLabelsAsStrings[0])
      bbStart = int(bbLabelsAsStrings[0])
      #print "interval [" + str(aaStart) + ".." + str(bbStart) + "]"
      #
      subsectionKeys = sorted(self.sections.keys())
      for key in subsectionKeys:
         if((key>=aaStart) and (key<=bbStart)):
            #print "Visiting " + str(key)
            subsection = self.sections[key]
            numberOfVisits += subsection.__visitFromSectionToSection(self.jsonObj,aaLabelsAsStrings,bbLabelsAsStrings,1,fcn,userData)
      return numberOfVisits
   def __visitFromSectionToSection(self,jsonObj,aaLabelsAsStrings,bbLabelsAsStrings,depth,fcn,userData):
      # jsonObj is only kept inside Outline object at top-level
      # Debugging
      #print "depth = " + str(depth)
      ###
      numberOfVisits = 0
      if(self.mark!=None):
         # is it ok to output this one? i.e. are we after the start and before the end?
         fullDesc  = self.__getFullDescriptionForUUID(self.mark,jsonObj)
         if(self.__isTaskAfterStartInHierarchy(fullDesc,aaLabelsAsStrings,depth)==True):
            if(self.__isTaskBeforeEndInHierarchy(fullDesc,bbLabelsAsStrings,depth)==True):
               theID     = self.__getIDForUUID(self.mark,jsonObj)
               theStatus = self.__getStatusForUUID(self.mark,jsonObj)
               fcn(self.mark, theID, fullDesc, theStatus, userData)
               numberOfVisits += 1
      if(self.sections!=None):
         subsectionKeys = sorted(self.sections.keys())
         for key in subsectionKeys:
            # TODO: probably could optimize a little bit here... i.e. if key is out of interval...
            subsection = self.sections[key]
            numberOfVisits += subsection.__visitFromSectionToSection(jsonObj,aaLabelsAsStrings,bbLabelsAsStrings,depth+1,fcn,userData)
      return numberOfVisits
   def __isTaskAfterStartInHierarchy(self,taskFullDesc,start,depth):
         sl              = extractStringBeforeFirstSpace(taskFullDesc)
         labelsAsStrings = sl.split(OUTLINE_SEP)
         # Debugging
         #print "sl = " + sl
         #print labelsAsStrings
         #print "len(start)           = " + str(len(start))
         #print "len(labelsAsStrings) = " + str(len(labelsAsStrings))
         ###
         if(depth > len(start)):
            #print "depth > len(start)"
            #print "Return True"
            return True
         if(depth > len(labelsAsStrings)):
            #print "depth > len(labelsAsStrings)"
            #print "Return True"
            return True
         equalCnt = 0
         for ii in range(depth):
            if(int(labelsAsStrings[ii]) > int(start[ii])):
               #print "int(labelsAsStrings[" + str(ii) + "]) > int(start[" + str(ii) + "])"
               #print "   i.e. " + labelsAsStrings[ii] + " > " + start[ii]
               #print "Return True"
               return True
            if(int(labelsAsStrings[ii]) == int(start[ii])):
               equalCnt = equalCnt + 1
         if(equalCnt==depth):
            #print "equalCnt==depth"
            #print "Return True"
            return True
         #print "Return False"
         return False
   def __isTaskBeforeEndInHierarchy(self,taskFullDesc,end,depth):
         sl              = extractStringBeforeFirstSpace(taskFullDesc)
         labelsAsStrings = sl.split(OUTLINE_SEP)
         # Debugging
         #print "sl = " + sl
         #print labelsAsStrings
         #print "len(end)             = " + str(len(end))
         #print "len(labelsAsStrings) = " + str(len(labelsAsStrings))
         ###
         if(depth > len(end)):
            #print "depth > len(end)"
            #print "Return True"
            return True
         if(depth > len(labelsAsStrings)):
            #print "depth > len(labelsAsStrings)"
            #print "Return True"
            return True
         equalCnt = 0
         for ii in range(depth):
            if(int(labelsAsStrings[ii]) < int(end[ii])):
               #print "int(labelsAsStrings[" + str(ii) + "]) < int(end[" + str(ii) + "])"
               #print "   i.e. " + labelsAsStrings[ii] + " < " + end[ii]
               #print "Return True"
               return True
            if(int(labelsAsStrings[ii]) == int(end[ii])):
               equalCnt = equalCnt + 1
         if(equalCnt==depth):
            #print "equalCnt==depth"
            #print "Return True"
            return True
         #print "Return False"
         return False

# This function will be invoked by the 'visitFromSectionToSection()' function
def visitorPrinter(taskUUID, taskID, taskDesc, taskStatus, userData):
   sys.stdout.write(str(taskID) + "\t" + taskStatus + "\t" + taskDesc + "\n")
   return

# This function will be invoked by the 'visitFromSectionToSection()' function
# userData is expected to be 'CmdLineOptions'
def visitorWaiterForAllSameWaitDate(taskUUID, taskID, taskDesc, taskStatus, userData):
   runTaskWarriorCommand(taskUUID + " modify wait:" + userData.waitDate)
   return

# This function will be invoked by the 'visitFromSectionToSection()' function
# userData is expected to be 'CmdLineOptions'
def visitorWaiterForDistributeWaitDate(taskUUID, taskID, taskDesc, taskStatus, userData):
   waitDate = str(userData.waitCounter * userData.waitNumber) + userData.waitUnit
   # Debugging
   # print taskUUID + " modify wait:" + waitDate
   runTaskWarriorCommand(taskUUID + " modify wait:" + waitDate)
   userData.waitCounter += 1
   return

def main(argv):
   try:
      opts = CmdLineOptions(argv)
      if(opts.cmd=="undo"):
         for ii in range(int(argv[opts.cmdIdx+1])):
            runTaskWarriorCommand("undo")
         return
      ol = Outline()
      ol.importFromTaskWarrior(opts.taskfilter)
      initialPaths = ol.collectOutlinePaths()
      initialUUIDs = ol.collectOutlineUUIDs()
      if(opts.cmd=="tableofcontents"):
         # twOutline <filter> tableofcontents all text|latex
         if(opts.tocSel=="all"):
            if(opts.tocType=="text"):
               ol.printOutlineAsText()
            if(opts.tocType=="latex"):
               ol.printOutlineAsLatex()
         # twOutline <filter> tableofcontents from <sectionA> to <sectionB> text
         if(opts.tocSel=="from"):
            aa = opts.getSectionLabelForSectionA(argv)
            bb = opts.getSectionLabelForSectionB(argv)
            numberOfVisits = ol.visitFromSectionToSection(aa,bb,visitorPrinter,None)
            sys.stdout.write("\n" + str(numberOfVisits) + " tasks\n")

      if(opts.cmd=="compress"):
         ol.compressOutline()
         compressedPaths = ol.collectOutlinePaths()
         compressedUUIDs = ol.collectOutlineUUIDs()
         issueTaskWarriorModifyCommandsForCompressedPaths(
            initialPaths, initialUUIDs, compressedPaths, compressedUUIDs)
      if(opts.cmd=="move"):
         locationCmd = opts.getLocationCommand(argv)
         aa = opts.getSectionLabelForSectionA(argv)
         bb = opts.getSectionLabelForSectionB(argv)
         if(aa==bb):
            sys.stdout.write("Source " + aa + " and destination " + bb + " of move are the same\n")
            sys.stdout.write("You could either:\n")
            sys.stdout.write("   1) edit the task to modifiy the section, or\n")
            sys.stdout.write("   2) change the move command in order to make it\n")
            sys.stdout.write("      relative to an already existing section\n")
            raise RuntimeError("Can't move " + aa + " " + locationCmd + " " + bb)
         if(bb.startswith(aa)):
            sys.stdout.write("Section " + aa + " is a super section of " + bb + "\n")
            sys.stdout.write("You could either:\n")
            sys.stdout.write("   1) manually edit the outline or\n")
            sys.stdout.write("   2) move " + bb + " to another location and try again\n")
            raise RuntimeError("Cannot move '" + aa + "' under '" + bb + "'")
         if(ol.isStructuredLabelInOutline(aa)==False):
            raise RuntimeError("Section '" + aa + "' is not in the outline (typo?)")
         if(ol.isStructuredLabelInOutline(bb)==False):
            raise RuntimeError("Section '" + bb + "' is not in the outline (typo?)")
         A = ol.removeOutlineForStructuredLabel(aa)
         if(locationCmd=="before"):
            ol.insertOutlineBeforeStructuredLabel(A,bb)
         if(locationCmd=="after"):
            ol.insertOutlineAfterStructuredLabel(A,bb)
         if(locationCmd=="under"):
            ol.insertOutlineUnderStructuredLabel(A,bb)
         movedPaths = ol.collectOutlinePaths()
         movedUUIDs = ol.collectOutlineUUIDs()
         issueTaskWarriorModifyCommandsForMovedPaths(
            initialPaths, initialUUIDs, movedPaths, movedUUIDs)
      if(opts.cmd=="modify"):
         #print "cmdIdx      = " + str(opts.cmdIdx)
         #print "sectionAIdx = " + str(opts.sectionAIdx)
         #print "sectionBIdx = " + str(opts.sectionBIdx)
         #if(opts.modifyCmd=="wait"):
         #   print "waitType    = " + opts.waitType
         #   if(opts.waitType=="all"):
         #      print "waitDate    = " + opts.waitDate
         #   if(opts.waitType=="distribute"):
         #      print "waitNumber  = " + str(opts.waitNumber) # a positive number
         #      print "waitUnit    = " + opts.waitUnit        # a valid unit e.g. hours, days, weeks, etc.

         aa = opts.getSectionLabelForSectionA(argv)
         bb = opts.getSectionLabelForSectionB(argv)
         if(ol.isStructuredLabelInOutline(aa)==False):
            raise RuntimeError("Section '" + aa + "' is not in the outline (typo?)")
         if(ol.isStructuredLabelInOutline(bb)==False):
            raise RuntimeError("Section '" + bb + "' is not in the outline (typo?)")

         if(opts.modifyCmd=="wait"):
            if(opts.waitType=="all"):
               #print "modify " + argv[opts.sectionAIdx] + " to " + argv[opts.sectionBIdx] + " wait all " + opts.waitDate
               #ol.printOutlineForDebugging()
               #ol.visitFromSectionToSection(aa,bb,visitorPrinter,None)
               numberOfVisits = ol.visitFromSectionToSection(aa,bb,visitorWaiterForAllSameWaitDate,opts)
               sys.stdout.write("\n" + str(numberOfVisits) + " tasks modified\n")
            if(opts.waitType=="distribute"):
               # wait distribute <number> <unit>
               # print "modify " + argv[opts.sectionAIdx] + " to " + argv[opts.sectionBIdx] + " wait distribute " + str(opts.waitNumber) + " " + opts.waitUnit
               numberOfVisits = ol.visitFromSectionToSection(aa,bb,visitorWaiterForDistributeWaitDate,opts)
               sys.stdout.write("\n" + str(numberOfVisits) + " tasks modified\n")

      sys.stdout.flush()
   except RuntimeError as e:
      print e
      sys.stdout.flush()

main(sys.argv[1:])
 
