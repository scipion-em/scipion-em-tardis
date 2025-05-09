# **************************************************************************
# *
# * Authors:     J.L. Vilas (jlvilas@cnb.csic.es)
# *
# * Centro Nacional de Biotecnologia CNB-CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
import os
import pwem
from pyworkflow.utils import Environ
from .constants import *


__version__ = '1.0.0'
_logo = "icon.png"
_references = ['Kiewiszz2023','Kiewisz2022']


class Plugin(pwem.Plugin):
    _homeVar = TARDIS_HOME
    _pathVars = [TARDIS_HOME]
    _url = 'https://smlc-nysbc.github.io/TARDIS'

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(TARDIS_HOME, TARDIS_FOLDER + '-' + TARDIS_VERSION)
        cls._defineVar(TARDIS_ENV_ACTIVATION, DEFAULT_ACTIVATION_CMD)

    @classmethod
    def getEnviron(cls, gpuId='0'):
        """ Setup the environment variables needed to launch Tardis. """
        environ = Environ(os.environ)
        if 'PYTHONPATH' in environ:
            # this is required for python virtual env to work
            del environ['PYTHONPATH']

        environ.update({'CUDA_VISIBLE_DEVICES': gpuId})
        return environ

    @classmethod
    def getTardisEnvActivation(cls):
        return cls.getVar(TARDIS_ENV_ACTIVATION)

    @classmethod
    def runTardis(cls, protocol, program, args, cwd=None, gpuId='0'):

        cudaStr = f" && CUDA_VISIBLE_DEVICES=%(GPU)s {program} "
        fullProgram = '%s %s %s' % (cls.getCondaActivationCmd(), cls.getTardisEnvActivation(), cudaStr)
        protocol.runJob(fullProgram, args, env=cls.getEnviron(gpuId=gpuId), cwd=cwd)

    @classmethod
    def getTardisProgram(cls, program):
        return os.path.join(cls.getHome(), 'bin', '%s' % program)

    @classmethod
    def getDependencies(cls):
        neededProgs = []
        condaActivationCmd = cls.getCondaActivationCmd()
        if not condaActivationCmd:
            neededProgs.append('conda')

        return neededProgs

    @classmethod
    def defineBinaries(cls, env):
        cls.addTardisPackage(env, TARDIS_VERSION)

    @classmethod
    def addTardisPackage(cls, env, version):

        TARDIS_INSTALLED = 'tardis_%s_installed' % version
        env_name = getTardisEnvName(version)
        # try to get CONDA activation command
        installationCmd = cls.getCondaActivationCmd()

        # Create the environment
        installationCmd += 'conda create -y -n %s python=3.11 && ' \
                           % env_name

        # Activate new the environment
        installationCmd += 'conda activate %s && ' % env_name

        # Install downloaded code
        installationCmd += 'git clone https://github.com/SMLC-NYSBC/TARDIS.git && '
        installationCmd += 'cd TARDIS && '
        installationCmd += 'pip install . && '
        installationCmd += 'cd .. && '

        # Flag installation finished
        installationCmd += 'touch %s' % TARDIS_INSTALLED

        tardis_commands = [(installationCmd, TARDIS_INSTALLED)]

        env.addPackage(TARDIS_FOLDER,
                       version=TARDIS_VERSION,
                       tar='void.tgz',
                       commands=tardis_commands,
                       neededProgs=cls.getDependencies(),
                       default=True)

    @classmethod
    def getTardisCmd(cls, program):
        """ Composes a Tardis command for a given program. """

        # Program to run
        program = cls.getTardisProgram(program)

        fullProgram = ' %s %s && %s' % (cls.getCondaActivationCmd(), cls.getTardisEnvActivation(), program)

        # Command to run
        cmd = fullProgram

        return cmd




