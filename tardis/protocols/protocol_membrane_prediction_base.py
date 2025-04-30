# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
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
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************
from enum import Enum
from os.path import join
from typing import Union

from pwem.protocols import EMProtocol
from pyworkflow import BETA
from pyworkflow.object import Pointer
from pyworkflow.protocol import params, STEPS_PARALLEL, FloatParam, StringParam, LEVEL_ADVANCED, GE, \
    LE, GPU_LIST
from pyworkflow.utils import Message
from tomo.objects import SetOfTomoMasks

# Inputs
IN_TOMOS = 'inputSetOfTomograms'
SEG_MODE = 'segmentationType'

# Segmentation types
class TardisSegModes(Enum):
    instance = 0
    semantic = 1

class TardisOutputs(Enum):
    segmentations = SetOfTomoMasks


class ProtTardisBase(EMProtocol):
    _devStatus = BETA
    _possibleOutputs = TardisOutputs
    stepsExecutionMode = STEPS_PARALLEL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inTomosDict = None

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam(IN_TOMOS,
                      params.PointerParam,
                      pointerClass='SetOfTomograms',
                      important=True,
                      label='Tomograms',
                      help='Set of tomogram to be segmented.')

        form.addParam(SEG_MODE, params.EnumParam,
                      choices=[TardisSegModes.instance.name,
                               TardisSegModes.semantic.name],
                      default=TardisSegModes.instance.value,
                      label='Choose type of output segmentation',
                      display=params.EnumParam.DISPLAY_HLIST,
                      help=('- Semantic segmentation:\n'
                            'Classifies each pixel in an image into a category, grouping together all pixels '
                            'that belong to the same object class, e. g., detects the membranes or '
                            'microtubules.\n\n'
                            '- Instance segmentation:\n'
                            'Similar to semantic segmentation but goes a step further—it not only classifies '
                            'objects but also differentiates between individual instances of the same category, '
                            'e. g. the different membranes or microtubules.'))

        form.addParam('dt', FloatParam,
                      default=0.9,
                      condition=f'{SEG_MODE}=={TardisSegModes.instance.value}',
                      label='Threshold',
                      validators=[GE(0),LE(1)],
                      help='You can enter additional command line options here.')

        form.addParam('additionalArgs', StringParam,
                      default="",
                      expertLevel=LEVEL_ADVANCED,
                      label='Additional options',
                      help='You can enter additional command line options here.')

        form.addHidden(GPU_LIST, StringParam,
                       default='0',
                       label="Choose GPU IDs")
        form.addParallelSection(threads=2, mpi=0)

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        closeSetDeps = []
        self._initialize()
        for tsId in self.inTomosDict.keys():
            segId = self._insertFunctionStep(self.segmentStep, tsId,
                                             prerequisites=[],
                                             needsGPU=True)
            cOutId = self._insertFunctionStep(self.createOutputStep, tsId,
                                              prerequisites=segId,
                                              needsGPU=False)
            closeSetDeps.append(cOutId)
        self._insertFunctionStep(self._closeOutputSet)

    def _initialize(self):
        self.inTomosDict = {tomo.getTsId(): tomo.clone() for tomo in self.getInTomos()}

    def segmentStep(self, tsId: str):
        # It must be defined by the child classes
        pass

    def createOutputStep(self, tsId: str):
        # To be defined by the children classes
        pass

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("This protocol has printed *%s* %i times." % (self.message, self.times))
        return summary

    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("%s has been printed in this run %i times." % (self.message, self.times))
            if self.previousCount.hasPointer():
                methods.append("Accumulated count from previous runs were %i."
                               " In total, %s messages has been printed."
                               % (self.previousCount, self.count))
        return methods

    # --------------------------- UTILS functions -----------------------------------
    def getInTomos(self, returnPointer: bool = False) -> Union[SetOfTomoMasks, Pointer]:
        inTomosPointer = getattr(self, IN_TOMOS)
        return inTomosPointer if returnPointer else inTomosPointer.get()

    def _getCurrentTomoDir(self, tsId: str) -> str:
        return self._getExtraPath(tsId)

    def _getCurrentTomoFile(self, tsId: str) -> str:
        return join(self._getCurrentTomoDir(tsId), f'{tsId}.mrc')

    def _getSegMode(self) -> str:
        segMode = getattr(self, SEG_MODE).get()
        return TardisSegModes.instance.name if segMode == TardisSegModes.instance.value else (
            TardisOutputs.segmentations.name)

    def _getOutputFileNameArg(self):
        # To be defined by the children classes
        pass

    def _getCmdArgs(self, tsId: str) -> str:
        tomo = self.inTomosDict[tsId]

        args = [f'--path {self._getCurrentTomoFile(tsId)}',
                f'--output_format {self._getOutputFileNameArg()}',
                f'--correct_px {tomo.getSamplingRate():.3f}',
                f'--dist_threshold {self.dt.get():.2f}',
                f'--device gpu']
        return ' '.join(args)
