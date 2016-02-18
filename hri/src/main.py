#!/usr/bin/env python


#------- Massimiliano Patacchiola -------
#------- Plymouth University 2016 -------
#
# It is necessary to have pyQt4 installed
#
# To generate python code from the .ui file:
# pyuic4 mainwindow.ui -o design.py
#
#

# Libraries for Qt
from PyQt4 import QtGui  # Import the PyQt4 module we'll need
from PyQt4.QtCore import QElapsedTimer
from PyQt4.QtCore import QThread
from PyQt4.QtCore import SIGNAL

import sys  
import os
import time

#python -m pip install pyaudio
#sudo apt-get install python-pyaudio python3-pyaudio
import pyaudio

#Importing my custom libraries
sys.path.insert(1, '../include')
sys.path.insert(1, "../include/pynaoqi-python2.7-2.1.3.3-linux64") #import this module for the nao.py module

import design
import parser
import nao
import logbook


class WorkerThread(QThread):
  def __init__(self):
    QThread.__init__(self)

    #Signal variables
    self.disable_signal = SIGNAL("disable_signal")
    self.enable_signal = SIGNAL("enable_signal")
    self.no_robot_signal = SIGNAL("no_robot_signal")
    self.yes_robot_signal = SIGNAL("yes_robot_signal")
    self.bad_xml_signal = SIGNAL("bad_xml_signal")
    self.good_xml_signal = SIGNAL("good_xml_signal")

    #Misc variables
    self.myParser = parser.Parser()
    self.timer = QElapsedTimer()
    self.STATE_MACHINE = 0

    #Status variables
    self._robot_connected = False
    self._xml_uploaded = False
    self._start_pressed = False



  def run(self):
    #Init the State machine 
    self.emit(self.enable_signal) #GUI enabled
    self.timer.start()
    self.STATE_MACHINE = 0

    while True:

        if self.STATE_MACHINE == 0:
            current_time = time.strftime("%H:%M:%S", time.gmtime())
            status = "robot_coonnected = " + str(self._robot_connected) + "\n" + "xml_uploaded = " + str(self._xml_uploaded) + "\n" + "start_pressed = " + str(self._start_pressed) + "\n"
            print "[0] " + current_time + " Waiting... \n" + status
            time.sleep(3)
            if self._robot_connected==True and self._xml_uploaded==True and self._start_pressed==True:
                self.STATE_MACHINE = 1 #switching to next state
                self.emit(self.disable_signal) #GUI disabled
                self.logger = logbook.Logbook()

        if self.STATE_MACHINE == 1:
            print "[1] Robot Talking + Logbook Init"           
            time.sleep(5)
            self.STATE_MACHINE = 2
 
        if self.STATE_MACHINE == 2:
            print "[2] Robot Talking + Looking/Non-Looking"
            time.sleep(5)
            #TODO play mp3 file and look
            #when mp3 file finish          
            self.timer.elapsed() #sart timer for next state
            self.STATE_MACHINE = 3 #next state

        if self.STATE_MACHINE == 3:
            print "[3] Waiting for the subject answer..."           
            self.emit(self.enable_signal) #GUI enbled
            time.sleep(5)
            #TODO catch the subject answer
            #when subject give the answer
            time_elapsed = self.timer.elapsed() #record the time
            print "[3] TIME: " + str(time_elapsed)
            self.STATE_MACHINE = 4 #next state
     
        if self.STATE_MACHINE == 4:
            print "[4] Pointing/Non-Pointing"           
            self.emit(self.disable_signal) #GUI disabled
            #TODO Give the reward and move/not-move the robot
            time.sleep(5)             
            self.STATE_MACHINE = 5 #next state

        if self.STATE_MACHINE == 5:
            print "[5] Saving the trial in the logbook"
            time.sleep(5)
            self.logger.AddLine(1,2,3,4,5,6,7,8,9)
            self.STATE_MACHINE = 2 #cycling to state 2

  def start_experiment(self):
    self._start_pressed = True

  def confirm(self):
    print "CONFIRMED!"
    print "TIME: " + str(self.timer.elapsed())

  def ip(self, ip_string, port_string):
    print "IP: " + str(ip_string) 

    try:
        self.myPuppet = nao.Puppet(ip_string, port_string, True)
        self.emit(self.yes_robot_signal)
        self._robot_connected=True
    except Exception,e:
        print "\nERROR: Impossible to find the robot!\n"
        print "Error was: ", e
        self.emit(self.no_robot_signal)
        self._robot_connected=False

  def xml(self, path):
    print("Looking for external files... ")
    if not os.path.isfile(str(path)):
            print("\nERROR: I cannot find the XML file. The programm will be stopped!\n")
            self._xml_uploaded = False
            return
    print("Initializing XML Parser... ")
    try:
        self.myParser.LoadFile(str(path))
        self.myParser.parse_experiment_list()
        self.emit(self.good_xml_signal)
        self._xml_uploaded = True
    except:
        self.emit(self.bad_xml_signal)
        print("\nERROR: Impossible to read the XML file!\n")
        self._xml_uploaded = False


  def wake(self, state):
        if state == True:
             self.myPuppet.wake_up()
        else:     
             self.myPuppet.rest()

  def stop(self):
    self.stopped = 1

  def __del__(self):
    self.wait()


class ExampleApp(QtGui.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.btnBrowse.clicked.connect(self.browse_folder)  # When the button is pressed execute browse_folder function
        #self.btnStartExperiment.clicked.connect(lambda: self.start_experiment(1))
        self.btnStartExperiment.clicked.connect(self.start_experiment)
        self.btnConfirm.clicked.connect(self.confirm_pressed)
        self.btnConnectToNao.clicked.connect(self.connect_pressed)
        self.btnWakeUp.clicked.connect(self.wake_up_pressed)
        self.btnRest.clicked.connect(self.rest_pressed)

        #Signal to be sent to Thread
        self.start_signal = SIGNAL("start_signal")
        self.confirm_signal = SIGNAL("confirm_signal")
        self.xml_path_signal = SIGNAL("xml_path_signal")
        self.ip_signal = SIGNAL("ip_signal")
        self.wake_up_signal = SIGNAL("wake_up_signal")

        self.showMaximized()

    def start_experiment(self):
        self.emit(self.start_signal)

    def confirm_pressed(self):
        self.emit(self.confirm_signal)

    def connect_pressed(self):
        ip_string = str(self.lineEditNaoIP.text())
        port_string = str(self.lineEditNaoPort.text())
        #print "IP: " + ip_string
        self.emit(self.ip_signal, ip_string, port_string)

    def wake_up_pressed(self):
        self.emit(self.wake_up_signal, True)

    def rest_pressed(self):
        self.emit(self.wake_up_signal, False)          

    def disable_gui(self):
        self.horizontalSlider.setEnabled(False)
        self.btnConfirm.setEnabled(False)
        self.btnStartExperiment.hide() #hiding the start button
        self.horizontalSlider.setValue(5)

    def enable_gui(self):
        self.horizontalSlider.setEnabled(True)
        self.btnConfirm.setEnabled(True)


    def browse_folder(self):
        selected_file = QtGui.QFileDialog.getOpenFileName(self, "Select a configuration file", "","XML files(*.xml)")

        if selected_file: # if user didn't pick a directory don't continue
            self.textEditXML.setText(selected_file) # self.listWidget.addItem(selected_file)  # add file to the listWidget
            self.emit(self.xml_path_signal, selected_file)
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setWindowTitle("No file selected")
            msgBox.setText("ATTENTION: You did not select any XML file.");
            msgBox.exec_();

    def no_robot_error(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setWindowTitle("Ops... Connection Error")
            msgBox.setText("ERROR: It was not possible to find the robot. \nFollow these tips and try to connect again. \n \n1- Check if the robot is running correctly. \n2- Check if the wifi router is running properly. \n3- Press the button on the robot chest to verify if the IP address is correct. \n4- Check if another software or GUI is connected to the robot. \n");
            msgBox.exec_();
            self.btnWakeUp.setEnabled(False)
            self.btnRest.setEnabled(False)

    def yes_robot_confirmation(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Information)
            msgBox.setWindowTitle("Well Done!")
            msgBox.setText("I found the robot, the connection was successfully established!")
            msgBox.exec_();
            self.btnWakeUp.setEnabled(True)
            self.btnRest.setEnabled(True)

    def bad_xml_error(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setWindowTitle("Ops... malformed XML file")
            msgBox.setText("ERROR: It was not possible to read the XML file. \nFollow these tips and try to select again. \n \n1- Verify if you can open correctly the file with a text editor (es. notepad). \n2- Once opened the file, check if for each open bracket <trial> there is a closed bracket </trial>. \n");
            msgBox.exec_();

    def good_xml_confirmation(self):
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Information)
            msgBox.setWindowTitle("Very Good!")
            msgBox.setText("I opened the XML file correctly. Be carefull, this does not mean that what you write inside the file is correct...")
            msgBox.exec_();

def main():

    #New instance of QApplication
    app = QtGui.QApplication(sys.argv)  
    form = ExampleApp()

    #Creating the main thread
    thread = WorkerThread()

    #Connecting: form > thread
    thread.connect(form, form.start_signal, thread.start_experiment)
    thread.connect(form, form.xml_path_signal, thread.xml) #sending XML path
    thread.connect(form, form.confirm_signal, thread.confirm)
    thread.connect(form, form.ip_signal, thread.ip)
    thread.connect(form, form.wake_up_signal, thread.wake)

    #Connecting: thread > form
    form.connect(thread, thread.disable_signal, form.disable_gui)
    form.connect(thread, thread.enable_signal, form.enable_gui)
    form.connect(thread, thread.no_robot_signal, form.no_robot_error)
    form.connect(thread, thread.yes_robot_signal, form.yes_robot_confirmation)
    form.connect(thread, thread.bad_xml_signal, form.bad_xml_error)
    form.connect(thread, thread.good_xml_signal, form.good_xml_confirmation)

    #Starting thread
    thread.start()

    #Show the form and execute the app
    form.show()  
    app.exec_()  



if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function




