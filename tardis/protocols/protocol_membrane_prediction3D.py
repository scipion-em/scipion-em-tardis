# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Raquel Fabra López (raquel.fabra@estudiante.uam.es)
# *
# * Escuela Politécnica Superior (EPS)
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

from pyworkflow.object import Set
from pyworkflow.utils import Message, makePath
from pyworkflow.protocol import  PointerParam, EnumParam, FloatParam, StringParam, LEVEL_ADVANCED, GPU_LIST
from pyworkflow.utils import replaceBaseExt
from pwem.protocols import EMProtocol

from tomo.protocols.protocol_base import ProtTomoBase
import tomo.constants as const
from tomo.objects import SetOfTomoMasks, TomoMask, SetOfMeshes, MeshPoint

from tardis import Plugin
import os

OUTPUT_TOMOMASK_NAME = 'tomoMasks'
OUTPUT_MESHES_NAME = 'meshes'

# Variables globales 
INSTANCE_SEGMENTATION = 0
SEMANTIC_SEGMENTATION = 1

MEMBRANE_SEGMENTATION = 0
MICROTUBULE_SEGMENTATION = 1

class ProtTardisMembrans3d(EMProtocol, ProtTomoBase):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'tomogram segmentation'
    _possibleOutputs = {OUTPUT_TOMOMASK_NAME: SetOfTomoMasks, OUTPUT_MESHES_NAME: SetOfMeshes}

    tomoMaskList = []

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """

        # The most basic segmentation command is as follows:
        # tardis_mem -dir <path-to-your-tomograms> -out mrc_None

        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inTomograms', PointerParam,
                      pointerClass='SetOfTomograms',
                      allowsNull=False,
                      label='Input tomograms')

        form.addParam('whatSegment', EnumParam,
                      choices=['Membrane segmentation',
                               'Microtubule segmentation'],
                      default=MEMBRANE_SEGMENTATION,
                      label='Select segmentation type',
                      display=EnumParam.DISPLAY_COMBO)

        form.addParam('typeOfSegmentation', EnumParam,
                      choices=['instance segmentation',
                               'semantic segmentation'],
                      default=INSTANCE_SEGMENTATION,
                      label='Choose type of output segmentation',
                      display=EnumParam.DISPLAY_COMBO)

        form.addParam('dt', FloatParam,
                      default=0.9,
                      condition='typeOfSegmentation==%i' % INSTANCE_SEGMENTATION,
                      label='Threshold',
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
        # Insert processing steps
        for i, tomo in enumerate(self.inTomograms.get()):
            tomId = tomo.getTsId()
            self._insertFunctionStep(self.segmentStep, tomId)

        self._insertFunctionStep(self.createOutputStep)

    def setupFolderStep(self, tomId):
        # Creating the tomogram folder
        tomoPath = self._getExtraPath(tomId)
        makePath(tomoPath)

        inputData = self.inTomograms.get()
        tomo = inputData[{'_tsId': tomId}]

        src = tomo.getFileName()
        dst = os.path.join(tomoPath, tomId + '.mrc')

        import shutil

        shutil.copy(src, dst)
        return tomoPath

    def segmentStep(self, tomId):

        _ = self.setupFolderStep(tomId)
        inputData = self.inTomograms.get()

        tomo = inputData[{'_tsId': tomId}]

        if self.typeOfSegmentation.get() == INSTANCE_SEGMENTATION:
            outFileName = 'mrc_csv'
        elif self.typeOfSegmentation.get() == SEMANTIC_SEGMENTATION:
            outFileName = 'mrc_csv'

        _= tomo

        inputFilename = tomId + '.mrc'
        tsIdFolder = self._getExtraPath(tomId)

        args = ' -dir %s -out %s ' % (inputFilename, outFileName)
        args += ' -px %f ' % inputData.getSamplingRate()
        args += ' -dt %f ' % self.dt.get()
        args += ' -dv gpu '

        if self.whatSegment.get() == MEMBRANE_SEGMENTATION:
            Plugin.runTardis(self, 'tardis_mem', args, cwd=tsIdFolder)
        elif self.whatSegment.get() == MICROTUBULE_SEGMENTATION:
            Plugin.runTardis(self, 'tardis_mt', args, cwd=tsIdFolder)

    def createOutputStep(self):

        inTomoSet = self.inTomograms.get()
        sampling = inTomoSet.getSamplingRate()
        if self.typeOfSegmentation.get() == SEMANTIC_SEGMENTATION:
            output = SetOfTomoMasks.create(self._getPath(), template='tomomasks%s.sqlite', suffix='segmented')
            output.copyInfo(inTomoSet)
            counter = 1
            for inTomo in inTomoSet:
                tomoMask = TomoMask()
                tomId = inTomo.getTsId()
                fn = os.path.join(self._getExtraPath(tomId, 'Predictions'), tomId + segType + '.mrc')

                tomoMask.setLocation((counter, fn))
                tomoMask.setVolName(self._getExtraPath(replaceBaseExt(fn, 'mrc')))
                tomoMask.copyInfo(inTomo)

                tomoMask.setVolName(fn)
                tomoMaskSet.append(tomoMask)
                counter += 1

            self._defineOutputs(**{OUTPUT_TOMOMASK_NAME: output})

            return tomoMaskSet
        else:
            output = self._createSetOfMeshes(inTomoSet)
            output.setBoxSize(10)
            for inTomo in inTomoSet:
                tsId = inTomo.getTsId()
                fnCsv = self._getExtraPath(tsId, 'Predictions', tsId+'_instances.csv')
                coordinates = self.readCSVinstances(fnCsv)
                self.addMeshPoints(inTomo, coordinates, output, sampling)
            self._defineOutputs(**{OUTPUT_MESHES_NAME: output})

        output.setSamplingRate(sampling)
        output.setStreamState(Set.STREAM_OPEN)
        output.enableAppend()

        self._defineSourceRelation(self.inTomograms.get(), output)


    def readCSVinstances(self, fnCsv):
        import csv
        coords = []
        with open(fnCsv, mode='r') as file:
            csvFile = csv.reader(file)
            next(csvFile)
            for lines in csvFile:
                coords.append(lines)
        return coords

    def addMeshPoints(self, tomogram, coordinates, mesh, sampling):
        for m, z, y, x in coordinates:
            point = MeshPoint()
            point.setVolume(tomogram)
            point.setGroupId(int(float(m)))
            point.setPosition(float(z)/sampling, float(y)/sampling, float(x)/sampling, const.BOTTOM_LEFT_CORNER)
            mesh.append(point)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        return summary

    def _methods(self):
        methods = []

        return methods
