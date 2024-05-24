# pylint: skip-file
from __future__ import annotations
import copy
from dataclasses import asdict
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, apply_cmd_log, dict_to_envy, get_selector_val
from dcw.stdmods.deployments import DcwDeployment
from dcw.stdmods.services import DcwService
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, value_map_dataclass
from jenkinsapi.jenkins import Jenkins

# --------------------------------------
#   Jenkins
# --------------------------------------
# region
__doc__ = '''Jenkins - integration with Jenkins'''
NAME = name = 'jenkins'
SELECTOR = selector = ['jenkins']


@dcw_cmd()
def cmd_test(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')

    server = Jenkins(state['proj.cfg.jenkins.url'], username=state['proj.cfg.jenkins.username'],
                     password=state['proj.cfg.jenkins.password'])

    xml_str = '''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@1400.v7fd111b_ec82f">
  <actions>
    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobAction plugin="pipeline-model-definition@2.2198.v41dd8ef6dd56"/>
    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction plugin="pipeline-model-definition@2.2198.v41dd8ef6dd56">
      <jobProperties/>
      <triggers/>
      <parameters/>
      <options/>
    </org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction>
  </actions>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@3894.3896.vca_2c931e7935">
    <script>pipeline {
    agent any

    stages {
        stage(&apos;YoYo&apos;) {
            steps {
                sh &apos;whoami&apos;
                sh &apos;dcw --help&apos;
            }
        }
    }
}
</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
'''

    # server.delete_job('test-multi')
    # server.get
    # server.create_job('test-multi', xml_str)

    # server.build_job('test-multi')
    for jobname, job in server.get_jobs():
        if job.name == 'test-multi':
            print(job.get_last_build().get_console())
            # print(job.get_build(2).get_console())
    return []


@dcw_cmd({'name': ..., 'type': ...})
def cmd_export(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    pass

# endregion
