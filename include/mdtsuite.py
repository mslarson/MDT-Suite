

#### IMPORTANT: check scoring parity for each task, especially MDTO. 
#### High likelyhood correct/incorrect scoring is ascertained correctly
#### but reported (logged) incorrectly, look into this!




"""Class MDTSuite runs an instance of whichever task is called, with whichever
parameters are passed to it. Additionally, creates a logfile and initializes 
it with all relevant task information, before actually running the task.

After the task is run, a list of scores is passed back to this class, and it will
append a list of scores/ratios to the logfile before closing it
"""

import os,sys,time, random
import mdto, mdts, mdtt
from psychopy.visual import Window, TextStim, Circle
from psychopy.event import clearEvents, getKeys, waitKeys


class MDTSuite(object):

    def __init__(self, expType, subID, subset, trialDur, ISI, expLenVar, 
                 selfPaced, curDir, logDir, expVariant='Normal',
                 screenType='Fullscreen', practiceTrials=True, buttonDiagnostic=True, inputButtons=['z','m'], pauseButton='p'):

        self.expType = expType
        self.expTypeNum = 0
        self.subset = subset
        self.screenType = screenType
        self.expVariant = expVariant
        self.subID = subID
        self.trialDur = trialDur
        self.ISI = ISI
        self.expLenVar = expLenVar
        self.selfPaced = selfPaced
        self.curDir = curDir
        self.logDir = logDir
        self.practiceTrials = practiceTrials
        self.buttonDiagnostic = buttonDiagnostic
        self.inputButtons = inputButtons
        self.pauseButton = pauseButton


        randomSeed = self.PairRandom(subID, subset)
        random.seed(randomSeed)

        #Set non-parametrized experiment variables
        #Use os.path.join to cover Unix/Windows use
        self.IMAGE_LOC = "images"
        self.MDTO_IMG_LOC = "mdto_images"
        self.MDTS_IMG_LOC = "mdts_images"
        self.MDTT_IMG_LOC = "mdtt_images"
        self.IMAGE_DIR = os.path.join(self.curDir, self.IMAGE_LOC)
        self.MDTO_IMG_DIR = os.path.join(self.IMAGE_DIR, self.MDTO_IMG_LOC, "Set_{}".format(subset))
        self.MDTS_IMG_DIR = os.path.join(self.IMAGE_DIR, self.MDTS_IMG_LOC, "Set_{}".format(subset))
        self.MDTT_IMG_DIR = os.path.join(self.IMAGE_DIR, self.MDTT_IMG_LOC, "Set_{}".format(subset))
        self.MDTT_NUM_STIM  = 32

    def MakeLog(self):
        """Creates and returns logfile based on exp type and the subject 
        number. If a logfile already exists with the same name, it will
        rename the old log file with a timestamp to differentiate them.
        Additionally, writes parametrized info to the log file.

        return: initialized log file, open for writing
        """
        sub = int(self.subID)
        subset = self.subset
        
        if (self.expType == "Object"):
            eType = "MDTO"
            self.expTypeNum = 0
        elif (self.expType == "Spatial"):
            eType = "MDTS"
            self.expTypeNum = 1
        elif (self.expType == "Temporal"):
            eType = "MDTT"
            self.expTypeNum = 2    

        #Create the logfile, and rename existing one if it exists
        logfileLoc = (self.logDir + "/%d_%s_log.txt" %(sub, eType))
        logfileDir = os.path.normpath(logfileLoc)
        if (os.path.isfile(logfileDir)):
            fileTime = time.strftime("%m%d%y_%H%M%S", time.localtime())
            rename = self.logDir + "/%d_%s_old_%s.txt" %(sub, eType, fileTime)
            logfileOld = os.path.normpath(rename)
            os.rename(logfileDir, logfileOld)
        log = open(logfileDir, 'w')

        logTime = time.strftime("%H:%M on %m/%d/%y", time.localtime())

        #Write experiment parameters to beginning of logfile
        log.write("MDT-%s Task: %s" %(self.expType, logTime))
        log.write("\nVersion: {}".format(self._version))
        log.write("\nSubject ID: %d" %(sub))
        log.write("\nStimulus Set: %d" %(subset))
        if self.selfPaced:
            log.write("\nTrial Duration: Self paced by subject")
        else:
            log.write("\nTrial Duration: %.2f" %(self.trialDur))
        log.write("\nISI: %.2f" %(self.ISI))
        lnT = "\nBlocks ran: %d" if eType == "MDTT" else "\nTrials/Condition: %d"
        log.write(lnT %(self.expLenVar))
        log.write("\nTask Variant: %s\n" %(self.expVariant))
        log.write("Input buttons: {}\n".format(self.inputButtons))

        return log

    def WriteScores(self, logfile, scoreList):
        """Writes scores to log file. This includes the correct, incorrect,
        and response scores for each of the four categories (easy, lure high,
        lure low, hard). For each of the tasks respectively, this is:

        Object: [Repeat, Lure Low, Lure High, Foil (Original)]
        Spatial: [Repeat, Small Move, Large Move, Corners]
        Temporal: [Adjacent, Eightish, Sixteenish, Primacy/Recency]

        Additionally, calculate the 8 score ratios, then close the logfile.
        """

        log = logfile
        scores = scoreList

        textList = (["Repeat","Lure High","Lure Low","Foil"],
                    ["Repeat","Small","Large","Corners"],
                    ["Adjacent","Eight","Sixteen","PR"])
        scoreText = ["Correct","Incorrect","Responses"]

        #Write to log each score type of each category
        log.write("\n\nScores:\n")
        for i in range(0,len(scores)):        #For each of 4 score types
            for j in range(0,3):            #For each of cor,inc,resp
                text = textList[self.expTypeNum][i] + " " + scoreText[j] + ":"
                score = scores[i][j]
                log.write("\n{:<20}{:>2}".format(text,score))

        log.write("\n")

        #Write to log each score ratio
        for i in range(0,len(scores)):        #For each of 4 score types
            for j in range(0,2):            #For both (correct,incorrect)
                if (scores[i][2] == 0):        #Prevent divide by 0 if no resp
                    ratioVar = 0.0
                else:
                    ratioVar = (float(scores[i][j]) / float(scores[i][2]))
                text = scoreText[j] + " | " + textList[self.expTypeNum][i]
                log.write("\n{:<25}{:>2.2f}".format(text,ratioVar))

        #Close the logfile
        log.close()

    def PairRandom(self, subjectNum, subsetNum):
        """Creates a unique seed for the random number generator based on the
        subject number, and the subset number. This function is simply an 
        implementation of the Cantor Pairing function
        Args:
            subjectNum: subject number
            subsetNum: subset number (choice from 1-10)
        Returns:
            seedNum: seed for the random number generator
        """
        numSum = int(subjectNum) + int(subsetNum)
        return ((numSum*(numSum+1))/2) + subsetNum

    def RunButtonDiagnostic(self):
        '''
        Run a test to make sure that the buttons are being recorded correctly
        Creates a temporary window and accepts keypresses
        Shows the buttonpresses with a highlighting circle
        '''
        if (self.screenType == 'Windowed'):
            screenSelect = False
        elif (self.screenType == 'Fullscreen'):
            screenSelect = True

        window = Window(fullscr=screenSelect,units='pix', 
                             color='White',allowGUI=False)
                            
        indRadius = 100
        tHeight = 2*indRadius/5
        posC1 = (-window.size[0]/4, 0)
        posC2 = (window.size[0]/4, 0 )
        #creating circle opjects
        circ1 = Circle(window, indRadius, lineColor = 'White', lineWidth = 6, pos = posC1) #training and p1 circles
        circ2 = Circle(window, indRadius, lineColor = 'White', lineWidth = 6, pos = posC2)     
        #creating text objects for cicles
        trtext1 = TextStim(window, " Button 1", color = 'White', height = tHeight, pos = posC1) #training text
        trtext2 = TextStim(window, " Button 2", color = 'White', height = tHeight, pos = posC2)
        
        #List of final circle and text objects
        trCircs = [circ1, circ2]
        trTexts = [trtext1, trtext2]

        trTxt = TextStim(window, "This is a test to ensure that the buttons are being recorded correctly.\n Press each button to make sure it is being recorded correctly.\n Press escape to move on", pos = (0,window.size[1]/4), color = "Black", height = 40, wrapWidth = 0.8*window.size[0])
                    
        for circ in trCircs:
            circ.fillColor = 'Gray'
        trTxt.draw(window)
        for circ in trCircs:
            circ.draw(window)
        for text in trTexts:
            text.draw(window)
        window.flip()
        
        while 1:
            key = waitKeys(keyList=self.inputButtons + [self.pauseButton,'escape'])[0]
            
            for circ in trCircs:
                circ.fillColor = 'Gray'
        
            if key =='escape' or key == self.pauseButton:
                #print "Press ecape one more time\n"
                break
            elif key == self.inputButtons[0]:
                trCircs[0].fillColor = 'Green'
            elif key == self.inputButtons[1]:
                trCircs[1].fillColor = 'Green'
                    
            trTxt.draw(window)
            for circ in trCircs:
                circ.draw(window)
            for text in trTexts:
                text.draw(window)
            window.flip()
                
        window.flip()
        window.close()


    def RunSuite(self, VERS):
        """Run through one of the three tasks. Each task will return a logfile,
        as well a scorelist. Following running a task, call the WriteScores()
        method within this class.
        """
        self._version = VERS
        logfile = self.MakeLog()
        log = -1
        scores = -1

        # Run button diagnostic tool if it is checked
        if self.buttonDiagnostic:
            self.RunButtonDiagnostic()
            clearEvents()
        
        # Make sure there are practice images 
        if self.practiceTrials:
            assert len([img for img in os.listdir(self.MDTO_IMG_DIR) if "PR_" in img]) != 0
            assert len([img for img in os.listdir(self.MDTS_IMG_DIR) if "PR_" in img]) != 0
            assert len([img for img in os.listdir(self.MDTT_IMG_DIR) if "PR_" in img]) != 0
           
        #Run Object Task
        if (self.expType == "Object"):
            expMDTO = mdto.MDTO(logfile, self.MDTO_IMG_DIR, self.screenType,
                                self.expVariant, self.trialDur, self.ISI, 
                                self.expLenVar, self.selfPaced, self.practiceTrials, self.inputButtons, self.pauseButton)
            (log, scores) = expMDTO.RunExp()

        #Run Spatial Task   
        elif(self.expType == "Spatial"):
            expMDTS = mdts.MDTS(logfile, self.MDTS_IMG_DIR, self.screenType,
                                self.trialDur, self.ISI, self.expLenVar, 
                                self.selfPaced, self.practiceTrials, self.inputButtons, self.pauseButton)
            #expMDTS.ImageDiagnostic()
            (log, scores) = expMDTS.RunExp()
            
        #Run Temporal Task
        elif(self.expType == "Temporal"):
            expMDTT = mdtt.MDTT(logfile, self.MDTT_IMG_DIR, self.subID,
                self.screenType, self.MDTT_NUM_STIM, self.expLenVar, 
                self.trialDur, self.ISI, self.selfPaced, self.practiceTrials, self.inputButtons, self.pauseButton)
            (log, scores) = expMDTT.RunExp()

        
        #Return value of -1 implies early exit condition, so dont write scores
        if ((log != -1) and (scores != -1)):
            self.WriteScores(log,scores)