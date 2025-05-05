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
from collections import OrderedDict
from enum import Enum
from os.path import join
from typing import Union

from pwem.protocols import EMProtocol
from pyworkflow import BETA
from pyworkflow.object import Pointer
from pyworkflow.protocol import params, STEPS_PARALLEL, FloatParam, StringParam, LEVEL_ADVANCED, GE, \
    LE, GPU_LIST, PointerParam, EnumParam, IntParam
from pyworkflow.utils import Message, makePath, createLink
from tardis import Plugin
from tomo.objects import SetOfTomoMasks, SetOfMeshes, TomoMask

# Inputs
IN_TOMOS = 'inputSetOfTomograms'
SEG_TARGET = 'segmentationTarget'
SEG_MODE = 'segmentationType'


# Segmentation targets
class TardisSegTargets(Enum):
    membranes = 0
    microtubules = 1

# Segmentation modes
class TardisSegModes(Enum):
    instance = 0
    semantic = 1

# Protocol outputs
class TardisOutputs(Enum):
    segmentations = SetOfTomoMasks
    meshes = SetOfMeshes

# Patch size allowed values are 32, 64, 96, 128, 256, 512
patchSizeValDict = OrderedDict()
patchSizeValDict['32'] =  0
patchSizeValDict['64'] =  1
patchSizeValDict['96'] =  2
patchSizeValDict['128'] =  3
patchSizeValDict['256'] =  4
patchSizeValDict['512'] =  5


class ProtTardisSeg(EMProtocol):
    """Semantic or instance segmentation of microtubules and membranes in tomograms"""

    _label = 'tomogram segmentation'
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
        form.addParam(IN_TOMOS, PointerParam,
                      pointerClass='SetOfTomograms',
                      important=True,
                      label='Tomograms',
                      help='Set of tomogram to be segmented.')

        form.addParam(SEG_TARGET, EnumParam,
                      choices=[TardisSegTargets.membranes.name,
                               TardisSegTargets.microtubules.name],
                      default=TardisSegTargets.membranes.value,
                      label='Select segmentation target',
                      display=EnumParam.DISPLAY_HLIST)

        form.addParam(SEG_MODE, EnumParam,
                      choices=[TardisSegModes.instance.name,
                               TardisSegModes.semantic.name],
                      default=TardisSegModes.instance.value,
                      label='Choose type of output segmentation',
                      display=EnumParam.DISPLAY_HLIST,
                      help=('- Semantic segmentation:\n'
                            'Classifies each pixel in an image into a category, grouping together all pixels '
                            'that belong to the same object class, e. g., detects the membranes or '
                            'microtubules.\n\n'
                            '- Instance segmentation:\n'
                            'Similar to semantic segmentation but goes a step further—it not only classifies '
                            'objects but also differentiates between individual instances of the same category, '
                            'e. g. the different membranes or microtubules.'))
        
        form.addParam('distThreshold', FloatParam,
                      default=0.9,
                      condition=f'{SEG_MODE}=={TardisSegModes.instance.value}',
                      label='Threshold used for instance prediction',
                      validators=[GE(0),LE(1)],
                      help='Float value between 0.0 and 1.0. Higher value then 0.9 will lower number '
                           'of the predicted instances, a lower value will increase the number of '
                           'predicted instances.')

        form.addParam('cnnThreshold', FloatParam,
                      default=0.5,
                      condition=f'{SEG_MODE}=={TardisSegModes.semantic.value}',
                      label='Threshold used for semantic prediction',
                      validators=[GE(0),LE(1)],
                      help='Float value between 0.0 and 1.0. Higher value than 0.5 will lead to a reduction '
                           'in noise and membrane prediction recall. A lower value will increase membrane '
                           'prediction recall but may lead to increased noise.')

        form.addParam('patchSize', EnumParam,
                      display=EnumParam.DISPLAY_COMBO,
                      choices=list(patchSizeValDict.keys()),
                      default=patchSizeValDict['128'],  # Patch of 128 px
                      label='Window size used for prediction (px)',
                      help='This will break tomograms into smaller patches with 25% overlap. Smaller '
                           'values than 128 consume less GPU, but also may lead to worse segmentation results.')

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
        self.program = 'tardis_mem' if self._segTargetIsMembrane() else 'tardis_mt'
        self.inTomosDict = {tomo.getTsId(): tomo.clone() for tomo in self.getInTomos()}

    def segmentStep(self, tsId: str):
        tomo = self.inTomosDict[tsId]
        tomoPath = self._getExtraPath(tsId)
        makePath(tomoPath)
        createLink(tomo.getFileName(), self._getCurrentTomoFile(tsId))
        args = self._getCmdArgs(tsId)
        Plugin.runTardis(self, self.program, args, cwd=self._getCurrentTomoDir(tsId))

    def createOutputStep(self, tsId: str):
        if self._segModeIsSemantic():
            self._createSemanticOutput(tsId)
        else:
            self._createInstanceOutput(tsId)

    # --------------------------- INFO functions -----------------------------------
    # def _summary(self):
    #     """ Summarize what the protocol has done"""
    #     summary = []
    #
    #     if self.isFinished():
    #         summary.append("This protocol has printed *%s* %i times." % (self.message, self.times))
    #     return summary
    #
    # def _methods(self):
    #     methods = []
    #
    #     if self.isFinished():
    #         methods.append("%s has been printed in this run %i times." % (self.message, self.times))
    #         if self.previousCount.hasPointer():
    #             methods.append("Accumulated count from previous runs were %i."
    #                            " In total, %s messages has been printed."
    #                            % (self.previousCount, self.count))
    #     return methods

    # --------------------------- UTILS functions -----------------------------------
    def getInTomos(self, returnPointer: bool = False) -> Union[SetOfTomoMasks, Pointer]:
        inTomosPointer = getattr(self, IN_TOMOS)
        return inTomosPointer if returnPointer else inTomosPointer.get()

    def _getCurrentTomoDir(self, tsId: str) -> str:
        return self._getExtraPath(tsId)

    def _getCurrentTomoFile(self, tsId: str) -> str:
        return join(self._getCurrentTomoDir(tsId), f'{tsId}.mrc')

    def _segTargetIsMembrane(self) -> bool:
        return True if getattr(self, SEG_TARGET).get() == TardisSegTargets.membranes.value else False

    def _segModeIsSemantic(self) -> bool:
        return True if getattr(self, SEG_MODE).get() == TardisSegModes.semantic.value else False

    # def _getSegMode(self) -> str:
    #     segMode = getattr(self, SEG_MODE).get()
    #     return TardisSegModes.instance.name if segMode == TardisSegModes.instance.value else (
    #         TardisOutputs.segmentations.name)

    def _getOutputFileNameArg(self) -> str:
        return 'mrc_mrc' if getattr(self, SEG_MODE).get() == TardisSegModes.instance.value else 'mrc_None'

    def _getCmdArgs(self, tsId: str) -> str:
        tomo = self.inTomosDict[tsId]

        args = [f'--path {tsId}.mrc',
                '--output_format mrc_npy',
                f'--correct_px {tomo.getSamplingRate():.3f}',
                f'--patch_size {self.patchSize.get()}',
                '--device gpu']
        if self._segModeIsSemantic():
            args.append(f'--cnn_threshold {self.cnnThreshold.get():.2f}')
        else:
            args.append(f'--dist_threshold {self.distThreshold.get():.2f}')
        return ' '.join(args)

    def _createSemanticOutput(self, tsId: str):
        pass

    def _createInstanceOutput(self, tsId: str):
        with self._lock:
            inTomo = self.inTomosDict[tsId]
            outputSet = self._getOutputSet()
            tomoMask = TomoMask()
            tomoMask.setFileName(self._getOutputFileName(tsId))
            tomoMask.setVolName(inTomo.getFileName())
            tomoMask.copyInfo(inTomo)
            outputSet.append(tomoMask)
            self._store(outputSet)
