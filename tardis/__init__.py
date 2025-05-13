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


__version__ = '3.0.0'
_logo = "icon.png"
_references = ['Kiewisz2024.12.19.629196', '10.1093/micmic/ozad067.485']


class Plugin(pwem.Plugin):
    _homeVar = TARDIS_HOME
    _pathVars = [TARDIS_HOME]
    _url = 'https://smlc-nysbc.github.io/TARDIS'

    @classmethod
    def _defineVariables(cls):
        cls._defineEmVar(TARDIS_HOME, TARDIS_FOLDER + '-' + TARDIS_VERSION)
        cls._defineVar(TARDIS_ENV_ACTIVATION, DEFAULT_ACTIVATION_CMD)

    @classmethod
    def getEnviron(cls):
        """ Setup the environment variables needed to launch Tardis. """
        environ = Environ(os.environ)
        if 'PYTHONPATH' in environ:
            # this is required for python virtual env to work
            del environ['PYTHONPATH']
        # environ.update({'CUDA_VISIBLE_DEVICES': gpuId})
        return environ

    @classmethod
    def getTardisEnvActivation(cls):
        return cls.getVar(TARDIS_ENV_ACTIVATION)

    @classmethod
    def runTardis(cls, protocol, program, args, cwd=None):
        cudaStr = f" && CUDA_VISIBLE_DEVICES=%(GPU)s {program} "
        fullProgram = '%s %s %s' % (cls.getCondaActivationCmd(), cls.getTardisEnvActivation(), cudaStr)
        protocol.runJob(fullProgram, args, env=cls.getEnviron(), cwd=cwd)

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
        installationCmd += f'conda create -y -n {env_name} python=3.11 && '

        # Activate new the environment
        installationCmd += f'conda activate {env_name} && '

        # Install downloaded code
        installationCmd += f'pip install "tardis-em=={TARDIS_VERSION}" && '

        # Flag installation finished
        installationCmd += f'touch {TARDIS_INSTALLED}'

        tardis_commands = [(installationCmd, TARDIS_INSTALLED)]

        env.addPackage(TARDIS_FOLDER,
                       version=TARDIS_VERSION,
                       tar='void.tgz',
                       commands=tardis_commands,
                       neededProgs=cls.getDependencies(),
                       default=True)





