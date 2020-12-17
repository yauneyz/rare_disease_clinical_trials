#!/usr/bin/env python
# coding: utf-8



import xml.etree.ElementTree as ET
from glob import glob
import os
import sys
import pickle
import pandas as pd
import csv
from progress.bar import Bar
from tqdm.notebook import tqdm, trange


# Trial class that represents all the relevant data from one trial
# The constructor takes all of the relevant data, defaulting empty fields to null
class Trial:
    def __init__(self,disease=None,number=None,sponsor=None,phase=None,study_type=None,url=None):
        self.disease=disease
        self.number=number
        self.sponsor=sponsor
        self.phase=phase
        self.study_type=study_type
        self.url = url
        self.fields = ["disease","number","sponsor","phase","study_type", "url"]
        
        # This is the list of cancers that 
    
    # Determines if this trial is one that we want to process
    def is_target(self, cancers):
        if self.disease is None:
            return False
        return (self.disease.lower() in cancers) 
    
    # Returns the data as a list to be written to a spreadsheet
    def get_data(self):
        return [str(self.__dict__[key]) for key in self.fields]


# Takes in the filename of an xml document (relative to the current path) and returns a Trial object
def parse_file(filename):
        try:
            tree = ET.parse(filename)
            sponsor = tree.find('sponsors').find('lead_sponsor').find('agency').text
            
            # Sponsor
            if (tree.find('sponsors') is not None 
                and tree.find('sponsors').find('lead_sponsor') is not None 
                and tree.find('sponsors').find('lead_sponsor').find('agency') is not None):
                sponsor = tree.find('sponsors').find('lead_sponsor').find('agency').text
            else:
                sponsor = None
            
            # Study Type
            if tree.find('study_type') is not None:
                study_type = tree.find('study_type').text
            else:
                study_type = None
                
            # Condition
            if tree.find('condition') is not None:
                disease = tree.find('condition').text
            else:
                disease = None
            
            # ID
            if tree.find('id_info') is not None and tree.find('id_info').find('nct_id') is not None:
                nct_id = tree.find('id_info').find('nct_id').text
            else:
                nct_id = None
              
            # Phase
            if tree.find('phase') is not None:
                phase = tree.find('phase').text
            else:
                phase = None
                
            # URL
            if tree.find('required_header') is not None and tree.find('required_header').find('url') is not None:
                url =tree.find('required_header').find('url').text
            else:
                url = None
                
        except Exception as e:
            print("Unable to parse file: ",filename, e)
            return
        return Trial(
            disease=disease,
            sponsor=sponsor,
            study_type=study_type,
            number=nct_id,
            phase=phase,
            url=url
        )
        
# Loops through all of the files in the directory and creates a spreadsheet with all of their data
def parse_directory(directory):
    
    if directory is None:
        directory = os.getcwd()
    
    # Get the list of rare cancers by reading the spreadsheet
    # The cancers are in the first column
    cancers = pd.read_csv('rare_cancers.csv').iloc[:,0].to_numpy()

    # Make them all lowercase
    cancers = [c.lower() for c in cancers]
    
    fields = ["disease","number","sponsor","phase","study_type"]
    
    # Change directory to set up glob
    old_dir = os.getcwd()
    os.chdir(directory)
    
    # Get a list of all the files in the directory
    file_list = glob("**/*.xml",recursive=True)   
    
    # Loop through all of the files and parse each one
    trials = []
    size = len(file_list)
    with Bar('Processing', max=size) as bar:
        bars = 0
        size = len(file_list)
        for i in range(size):
            trials.append(parse_file(file_list[i]))
            bar.next()
    
    # Change directory back for output
    os.chdir(old_dir)
    
    # Write the result to a spreadsheet
    # Include a progress bar so they can see how far along they are
    with open('output.csv', 'w') as output:
        writer = csv.writer(output)
        
        # Write the headers:
        headers = ["Disease","Number","Sponsor","Phase","Study Type", "URL"]
        writer.writerow(headers)
        
        # Write the data
        valid_trials = [trial for trial in trials if trial is not None and trial.is_target(cancers)]
        for trial in valid_trials:
            writer.writerow(trial.get_data())

if __name__=="__main__":
    
    # This is where the clinical trial folder was downloaded to
    # Replace it with your own
    default_directory = '/home/zac/Downloads/ClinicalTrials'
    
    # Try to get the command line argument
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    else:
        directory = default_directory
    
    parse_directory(directory)
