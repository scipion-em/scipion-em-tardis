# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:    Scipion Team (scipion@cnb.csic.es)
# *
# *  BCU, Centro Nacional de Biotecnologia, CSIC
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
import logging
from enum import Enum
from os.path import join
from typing import Union
import numpy as np
from pwem.protocols import EMProtocol
from pyworkflow import BETA
from pyworkflow.object import Pointer, Set
from pyworkflow.protocol import STEPS_PARALLEL, FloatParam, StringParam, LEVEL_ADVANCED, GE, \
    LE, GPU_LIST, PointerParam, EnumParam, IntParam
from pyworkflow.utils import Message, makePath, createLink, cyanStr
from tardis import Plugin
from tomo.constants import BOTTOM_LEFT_CORNER
from tomo.objects import SetOfTomoMasks, SetOfMeshes, TomoMask, MeshPoint


logger = logging.getLogger(__name__)

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
    instances = 0
    semantic = 1
    both = 2

# Protocol outputs
class TardisOutputs(Enum):
    segmentations = SetOfTomoMasks
    meshes = SetOfMeshes


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
                      choices=[TardisSegModes.instances.name,
                               TardisSegModes.semantic.name,
                               TardisSegModes.both.name],
                      default=TardisSegModes.both.value,
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
                      condition=f'{SEG_MODE} in [{TardisSegModes.instances.value}, {TardisSegModes.both.value}]',
                      label='Threshold for instance prediction',
                      validators=[GE(0),LE(1)],
                      help='Float value between 0.0 and 1.0. Higher value then 0.9 will lower number '
                           'of the predicted instances, a lower value will increase the number of '
                           'predicted instances.')

        form.addParam('cnnThreshold', FloatParam,
                      default=0.5,
                      condition=f'{SEG_MODE} in [{TardisSegModes.semantic.value}, {TardisSegModes.both.value}]',
                      label='Threshold for semantic prediction',
                      validators=[GE(0),LE(1)],
                      help='Float value between 0.0 and 1.0. Higher value than 0.5 will lead to a reduction '
                           'in noise and membrane prediction recall. A lower value will increase membrane '
                           'prediction recall but may lead to increased noise.')

        form.addParam('boxSize', IntParam,
                      label='Meshes box size (px)',
                      expertLevel=LEVEL_ADVANCED,
                      default=20,
                      help='The box size is required at coordinates or meshes level by some visualization tools, '
                           'such as Napari or Eman.')

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
        logger.info(cyanStr(f'===> tsId = {tsId}: segmenting...'))
        tomo = self.inTomosDict[tsId]
        tomoPath = self._getExtraPath(tsId)
        makePath(tomoPath)
        createLink(tomo.getFileName(), self._getCurrentTomoFile(tsId))
        args = self._getCmdArgs(tsId)
        Plugin.runTardis(self, self.program, args, cwd=self._getCurrentTomoDir(tsId))

    def createOutputStep(self, tsId: str):
        logger.info(cyanStr(f'===> tsId = {tsId}: Creating the results...'))
        with self._lock:
            segMode = getattr(self, SEG_MODE).get()
            if segMode == TardisSegModes.both.value:
                self._createSemanticOutput(tsId)
                self._createInstanceOutput(tsId)
            elif segMode == TardisSegModes.semantic.value:
                self._createSemanticOutput(tsId)
            else:  # instance
                self._createInstanceOutput(tsId)

    # --------------------------- INFO functions ------------------------------------

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

    def _getOutputFormatArg(self) -> str:
        """Tardis output format argument is composed of two elements -out <format>_<format>.
        The first output format is the semantic mask.  The second output is predicted instances
        of the detected objects."""
        segMode = getattr(self, SEG_MODE).get()
        if segMode == TardisSegModes.both.value:
            return 'mrc_csv'
        elif segMode == TardisSegModes.semantic.value:
            return 'mrc_None'
        else:  # instance
            return 'None_csv'

    def _getCmdArgs(self, tsId: str) -> str:
        tomo = self.inTomosDict[tsId]
        args = [f'--path {tsId}.mrc',
                f'--output_format {self._getOutputFormatArg()}',
                f'--correct_px {tomo.getSamplingRate():.3f}',
                '--device gpu']
        segMode = getattr(self, SEG_MODE).get()
        if segMode == TardisSegModes.both.value:
            args.extend([f'--cnn_threshold {self.cnnThreshold.get():.2f}',
                         f'--dist_threshold {self.distThreshold.get():.2f}'])
        elif segMode == TardisSegModes.semantic.value:
            args.append(f'--cnn_threshold {self.cnnThreshold.get():.2f}')
        else:  # instance
            args.append(f'--dist_threshold {self.distThreshold.get():.2f}')
        return ' '.join(args)

    def _createSemanticOutput(self, tsId: str):
        inTomo = self.inTomosDict[tsId]
        outputSet = self._getOutputMaskSet()
        tomoMask = TomoMask()
        tomoMask.setFileName(self._getOutputFileName(tsId, TardisSegModes.semantic.name, 'mrc'))
        tomoMask.setVolName(inTomo.getFileName())
        tomoMask.copyInfo(inTomo)
        outputSet.append(tomoMask)
        self._store(outputSet)

    def _createInstanceOutput(self, tsId: str):
        outMeshes = self._getOutputMeshes()
        self._addMeshPoints(tsId, outMeshes)
        self._store(outMeshes)

    def _getOutputFileName(self, tsId: str, suffix: str, ext: str) -> str:
        return join(self._getExtraPath(tsId, 'Predictions'), f'{tsId}_{suffix}.{ext}')

    def _getOutputMaskSet(self) -> SetOfTomoMasks:
        outSetSetAttrib = self._possibleOutputs.segmentations.name
        outputSet = getattr(self, outSetSetAttrib, None)
        if outputSet:
            outputSet.enableAppend()
        else:
            outputSet = SetOfTomoMasks.create(self._getPath(), template='tomomasks%s.sqlite')
            outputSet.copyInfo(self.getInTomos())
            outputSet.setStreamState(Set.STREAM_OPEN)
            self._defineOutputs(**{outSetSetAttrib: outputSet})
            self._defineSourceRelation(self.getInTomos(returnPointer=True), outputSet)
        return outputSet

    def _getOutputMeshes(self) -> SetOfMeshes:
        outSetSetAttrib = self._possibleOutputs.meshes.name
        outputSet = getattr(self, outSetSetAttrib, None)
        if outputSet:
            outputSet.enableAppend()
        else:
            outputSet = SetOfMeshes.create(self._getPath(), template='meshes%s.sqlite')
            inTomosPointer = self.getInTomos(returnPointer=True)
            outputSet.setPrecedents(inTomosPointer)
            outputSet.setBoxSize(self.boxSize.get())
            outputSet.setSamplingRate(inTomosPointer.get().getSamplingRate())
            outputSet.setStreamState(Set.STREAM_OPEN)
            self._defineOutputs(**{outSetSetAttrib: outputSet})
            self._defineSourceRelation(self.getInTomos(returnPointer=True), outputSet)
        return outputSet

    def _addMeshPoints(self, tsId: str, mesh: SetOfMeshes):
        tomo = self.inTomosDict[tsId]
        sr = tomo.getSamplingRate()
        fnCsv = self._getOutputFileName(tsId, TardisSegModes.instances.name, 'csv')
        data = np.loadtxt(fnCsv, delimiter=',', skiprows=1)  # Skip the header row
        for row in data:
            point = MeshPoint()
            # Lines are [groupId, x, y, z] with coords in angstroms
            groupId = int(row[0])
            x = row[1]
            y = row[2]
            z = row[3]
            point.setVolume(tomo)
            point.setGroupId(groupId)
            point.setPosition(x / sr,
                              y / sr,
                              z / sr,
                              BOTTOM_LEFT_CORNER)
            mesh.append(point)


