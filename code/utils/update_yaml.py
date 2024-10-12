from ruamel.yaml import YAML
from utils.get_root_directory import get_project_root
#from get_root_directory import get_project_root
import os
import sys
import re
from datetime import datetime, time

class UpdateYamlDefinition():
    def __init__(self,generated_root,git_project_root):
        #self.generated_yaml = generated_yaml
        self.root_dir       = str(get_project_root())
        self.yaml           = YAML()
        self.yaml.witdh     = 4096
        #self.template_name  = template_name
        self.files          = []
        self.original_root  = git_project_root
        #self.timestamp      = timestamp
        self.generated_root = generated_root

    # files é um dict 
    # file_path = {'source': 'xyz/blah.yaml', 'append': 'zzz/append.yaml'}
    def update_yaml_definition(self,original_file,update_file):
        # reads current config
        try:
            with open(original_file,'r') as fp:
                code = self.yaml.load(fp)

            with open(update_file,'r') as fp:
                append = self.yaml.load(fp)

            update_keys = [x for x in append.keys()]
            # update each key
            for key in update_keys:
                try:
                    code[key].update(append[key])
                except:
                    code[key] = append[key]

            with open(update_file,'w') as fp:
                self.yaml.dump(code, fp)

            # por algum motivo, o dump está cortando o task_path_mapper.yaml
            if os.path.split(update_file)[1] == 'task_path_mapper.yaml':
                with open(update_file,'r') as fp:
                    original_content = ''.join(fp.readlines())
                    
                # está cortando por algum motivo o campo quando tem {{ ou }}
                new_content = re.sub(r'({{)\n\s+',r'\1 ',re.sub(r'\n\s+(}})', r' \1', original_content))

                # escreve no mesmo arquivo que foi atualizado anteriormente
                with open(update_file,'w') as fp:
                    fp.write(new_content)
        except:
            pass

    # lists the yaml (or yml) files that need to be updated
    # relpath is used to get the same structure as the production airflow folders defined by the git repo
    def list_yaml_to_update(self):
        path = self.generated_root

        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for file in f:
                if any(['.yaml' in file,'.yml' in file]):
                    self.files.append({'relpath':os.path.relpath(os.path.join(r, file), path), 'generated_path':os.path.join(r, file), 'original_path': os.path.join(self.original_root,os.path.relpath(os.path.join(r, file), path))})