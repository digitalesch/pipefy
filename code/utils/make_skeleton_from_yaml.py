#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 22 16:36:31 2021

@author: picpay
"""
# std-lib imports
import os
import yaml
import re
from shutil import copyfile

# built imports
from utils.yaml_loader import YamlLoader
from utils.get_root_directory import get_project_root

class SkeletonCookiecutterTemplate():
    def __init__(self,template_name,root_dir):
        self.extensions = ['yaml','yml','py','json']                        # extensions used to create templates from yaml_file
        self.template_name = template_name                                  # gets template name, which is used to generate folders
        self.paths = {
            'root': root_dir,                                               # gets root folder for project, by finding .root file
            'templates' : os.path.join('templates',self.template_name),
            'generated' : os.path.join('generated',self.template_name),
        }
        self.yaml_files = []
        
        self.template_dict = self.read_yaml_file(
                                os.path.join(
                                    self.paths['root'],
                                    'templates',
                                    self.template_name,
                                    'definitions',
                                    'template_directory.yaml'
                                )
                            )

    # reads the stream path to get yaml dict with help of Loader: YamlLoader
    def read_yaml_file(self,stream):
        with open(stream,'r') as yaml_file:
            file_dict = yaml.load(yaml_file, YamlLoader)

        return file_dict

    def walk_yaml(self,folder_def,dir):
        if isinstance(folder_def,dict):
            for key,value in folder_def.items():
                if not any([re.findall('\.'+extension+'$',key) for extension in ['yaml','yml','py','json']]):
                    os.makedirs(os.path.join(dir,key))
                    self.walk_yaml(value,os.path.join(dir,key))
                else:
                    copyfile(
                        os.path.join(self.paths['root'],'templates',self.template_name,value),
                        os.path.join(dir,key)
                    )
        else:
            # list
            try:
                if isinstance(folder_def,list):
                    for item in folder_def:
                        for key,value in item.items():
                            copyfile(
                                os.path.join(self.paths['root'],'templates',self.template_name,value),
                                os.path.join(dir,key)
                            )
            # when metadata is defined, the origin doesn't have the same file    
            except:
                pass