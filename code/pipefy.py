#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 17:50:05 2021

@author: picpay
"""

# std-lib imports
import os
import argparse
from datetime import datetime
import json
import shutil

# 3rd party imports
from cookiecutter import main as cc
import pandas
import yaml

# self-developed utils imports
from utils.yaml_loader import YamlLoader, LoaderIgnoreTags
from utils.get_root_directory import get_project_root
from utils.make_skeleton_from_yaml import SkeletonCookiecutterTemplate
from utils.update_yaml import UpdateYamlDefinition

class Pipefy():
    def __init__(self,arguments,definition_file=None,sheet_name=None):
        self.excel_file            = pandas.ExcelFile(definition_file)
        self.dataframes            = {}
        self.sheet                 = sheet_name
        self.root_dir              = str(get_project_root())
        self.create_dataframes()
        self.metadata_definition   = self.create_files_definitions()
        self.args                  = arguments
        
    def create_dataframes(self):
        if self.sheet is not None:
            sheets = ['metadata',self.sheet]
            for sheet in self.excel_file.sheet_names:
                if sheet in sheets:
                    self.dataframes[sheet] = self.excel_file.parse(sheet)

    def create_files_definitions(self) -> dict:
        table_dicts = {}


        # metadata for each table        
        for index, row in self.dataframes['metadata'][(self.dataframes['metadata']['CURATED_TABLE'] == self.sheet)].iterrows():
            table_name = row['CURATED_TABLE']
            
            table_dicts[table_name] = {
                'table_name':          '',
                'description':         '',
                'business_owner':      [],
                'data_steward':        [],
                'review_dg':           '',
                'update_frequency':    '',
                'source':              '',
                'tags':                [],
                'columns_description': []
            }   
            table_dicts[table_name]['table_name']=row['CURATED_TABLE']
            table_dicts[table_name]['description']=row['DESCRIPTION']
            table_dicts[table_name]['business_owner']=[item.strip() for item in row['BUSSINESS_OWNER'].split(',')]
            table_dicts[table_name]['data_steward']=[item.strip() for item in row['DATA_STEWARD'].split(',')]
            table_dicts[table_name]['review_dg']=row['REVIEW_DG']
            table_dicts[table_name]['update_frequency']=row['UPDATE_FREQUENCY']
            table_dicts[table_name]['source']=row['SOURCE']
            table_dicts[table_name]['tags']=[item.strip() for item in row['TAGS'].split(',')]
            
            for index, table_row in self.dataframes[table_name].iterrows():
                _tmp = {
                    'column':                '',
                    'description':           '',
                    'classification':        '',
                    'treatment':             '',
                    'review_dg_column':      '',
                    'confidentiality_level': ''
                }
                if not pandas.isna(table_row['ATTRIBUTE_CURATED']):
                    _tmp['column']=table_row['ATTRIBUTE_CURATED']
                    _tmp['description']=table_row['METADATA']
                    _tmp['classification']=table_row['LGPD']
                    _tmp['treatment']=str(table_row['TREATMENT'])
                    _tmp['review_dg_column']=(table_dicts[table_name]['review_dg'])
                    _tmp['confidentiality_level']=table_row['CONF_LEVEL']
                    # creates reference field metadata
                    if not pandas.isna(table_row['REFERENCE_FIELD']):
                        _tmp['ref']=[
                            {value:key} for key,value in json.loads(table_row['REFERENCE_FIELD']).items()
                        ]
                    table_dicts[table_name]['columns_description'].append(_tmp)
        
        return table_dicts

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    arguments_list = [
        {'name':'template_name','type':str,'help':'specify template name to construct folders/files'},
        {'name':'path_to_git_airflow','type':str,'help':'specify path for yaml / yml update'},
        {'name':'--metadata-file','type':str,'help':'specify file to build metadata file'},
        {'name':'--sheet','type':str,'help':'specify sheet to build metadata file'},
        {'name':'--skeleton','type':int,'help':'specify if skeleton is to be rebuild or not (integer, 0 -> false, 1 -> true)'},
    ]
    
    for arg in arguments_list:
        parser.add_argument(
            arg['name'],type=arg['type'],help=arg['help']
        )

    args = parser.parse_args()
    
    root_dir = str(get_project_root())

    # generates folder paths
    generated_template = SkeletonCookiecutterTemplate(args.template_name,root_dir)
   
    template_generated_folder = os.path.join(root_dir,generated_template.paths['generated'])

    # removes skeleton, so latest template is generated again
    if all([os.path.exists(os.path.join(template_generated_folder,'skeleton')),args.skeleton==1]):
        shutil.rmtree(os.path.join(template_generated_folder,'skeleton'))    
        
    if any([not os.path.exists(os.path.join(template_generated_folder,'skeleton')),args.skeleton==0]):
        generated_template.walk_yaml(generated_template.template_dict['__folders__'],os.path.join(root_dir,generated_template.paths['generated']))

    # creates timestamped folder
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path_to_generate = os.path.join(root_dir,generated_template.paths['generated'],'templated',ts)
    os.makedirs(path_to_generate)

    with open(os.path.join(root_dir,'templates',args.template_name,'definitions','cookiecutter.json'),'r') as cookiecuter_fp:
        cookiecutter_config = json.load(cookiecuter_fp)

    if 'curation' in cookiecutter_config['process_name']:
        # generates metadata from files
        file_name = 'pipefy.xlsx' if args.metadata_file is None else (args.metadata_file + '.xlsx')
        sheet_name = None if args.sheet is None else args.sheet
        pipes = Pipefy(args,os.path.join(root_dir,'templates',args.template_name,'definitions',file_name),sheet_name)
        metadata_definition = yaml.dump(pipes.metadata_definition[args.sheet],allow_unicode=True,sort_keys=False,width=400,line_break=False)
    else:
        # pipe without metadata
        pipes = Pipefy(args)
        metadata_definition = ""
    
    # creates templated folders / files
    cc.cookiecutter(
        template=os.path.join(root_dir,'generated',args.template_name,'skeleton'), 
        no_input=True,
        extra_context={
            'metadata_definition':   metadata_definition
        },
        output_dir=path_to_generate,
        overwrite_if_exists=True
    )
    
    # lib to update the yaml definition
    update_yaml = UpdateYamlDefinition(path_to_generate,args.path_to_git_airflow)
    update_yaml.list_yaml_to_update()
    
    # updates yaml with the origin files
    for file_to_update in update_yaml.files: 
        update_yaml.update_yaml_definition(file_to_update['original_path'],file_to_update['generated_path'])