import time
import os
import sys
import json
import os.path
import datetime
import dataiku
import dataikuapi

from datetime import datetime
from dataiku.runnables import Runnable
from dataikuapi.utils import DataikuException


class MyRunnable(Runnable):

    def __init__(self, project, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project = project
        self.config = config
        self.plugin_config = plugin_config
    
    def get_codenv(self, project, definition, client):
        code_envs = []
        for env_definition in definition:
            if "plugin_" not in env_definition["envName"]:
                local_code_env = client.get_code_env('PYTHON', env_definition["envName"])
                if project in (str(local_code_env.list_usages())):
                    code_envs.append(env_definition)
        return code_envs
    
    def create_codenv_instance(self, external_code_env, remote_client, local_client):
        # Delete codenv if exists
        try:
            code_env = local_client.get_code_env('PYTHON', external_code_env['envName'])
            code_env.delete()
        except:
            print("The codenv does not exist")

        code_env_to_create = remote_client.get_code_env('PYTHON', external_code_env['envName'])
        pythonInterpreter = code_env_to_create.get_definition()["desc"]["pythonInterpreter"]
        code_env = local_client.create_code_env('PYTHON', external_code_env['envName'], 'DESIGN_MANAGED', {"pythonInterpreter": pythonInterpreter})
        
        external_code_env_definition = remote_client.get_code_env('PYTHON', external_code_env['envName'])

        packages = external_code_env_definition.get_definition()['specPackageList'].split('\n')
        packages = '\n'.join(map(str, packages))

        
        # Setup packages to install
        definition = code_env.get_definition()
        definition["desc"]["installCorePackages"] = True
        definition["desc"]["installJupyterSupport"] = True
        # install package
        definition["specPackageList"] = packages
        #Save the new settings
        code_env.set_definition(definition)

        # Actually perform the installation
        code_env.update_packages()
        code_env.set_jupyter_support(True)  


    def run(self, progress_callback):        
        project_to_import = self.config.get("project_to_import", "")
        local_client = dataiku.api_client()
        
        if project_to_import == "":
            raise Exception("Project id is required")
        try:
            projects = local_client.list_project_keys()
            if project_to_import in projects:
                return '\n Project already exists on your instance'
        except:
            return '\n Could not established connection with your instance remote host or api key not correct'

        # use public python api to get access to remote host
        remote_client = dataikuapi.DSSClient('https://se-global-demo-platform-ref.emea.dataiku-sandbox.io/', 'P0BRG0EVW8WXU3OELV53MG0QPDSV9S23')

        # ignore SSL Certificates if selected
        if self.config.get("ignore_ssl_certs"):
            remote_client._session.verify = False

        html = '<div> Successfully connected to remote host: %s</div>' %(remote_client.host)
        now = datetime.now()
        today = now.strftime("%d-%m-%Y_%H-%M")
        
        # Get codenv
        definition = remote_client.list_code_envs()
        codenvs_to_create = self.get_codenv(project_to_import, definition, remote_client)
        
        # Create codenv
        for codenv in codenvs_to_create:
            self.create_codenv_instance(codenv, remote_client, local_client)
        version_bundle = "latest"
        #Export bundle
        project = remote_client.get_project(project_to_import)
        #project.export_bundle(version_bundle)
        remote_client.download_exported_bundle_archive_to_file(version_bundle, "temp_bundle.zip")

        #Import bundle
        bundle_file_stream = open("temp_bundle.zip", 'rb')
        local_client.create_project_from_bundle_archive(bundle_file_stream)
        test_project = local_client.get_project(project_to_import)
        test_project.preload_bundle(version_bundle) # for code envs
        test_project.activate_bundle(version_bundle)
        os.remove("temp_bundle.zip")
        return 'Successfully imported project'

        html += '</div>'
        return html

