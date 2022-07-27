import dataiku
import dataikuapi

def do(payload, config, plugin_config, inputs):
    """
    Create list of options of projects in instance.
    """
    remote_client = dataikuapi.DSSClient('https://se-global-demo-platform-ref.emea.dataiku-sandbox.io/', 'P0BRG0EVW8WXU3OELV53MG0QPDSV9S23')
    projects = remote_client.list_projects()
    
    choices = []
    for project in projects:
        if 'projectStatus' in project:
            if project['projectStatus'] == 'In Production' or project['projectStatus'] == 'In production':
                choices.append({"value": project.get('projectKey'), "label": project.get('name')})
    return {"choices": choices}
