# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     raquel.fabra@estudiante.uam.es
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


"""
Describe your python module here:
This module will provide the traditional Hello world example
"""
import os
import csv
from pyworkflow.utils import Message, makePath
from pwem.protocols import EMProtocol
from tomo.protocols.protocol_base import ProtTomoBase
from pyworkflow.protocol import params, Integer, PointerParam, BooleanParam, IntParam, FloatParam, StringParam, LEVEL_ADVANCED
from tomo.objects import SetOfTomograms, SetOfTomoMasks
from tardis import Plugin

OUTPUT_TOMOMASK_NAME = 'tomoMasks'

INSTANCE_SEGMENTATION = 0

class ProtMicro3d(EMProtocol, ProtTomoBase):
    _label = 'microtubule segmentation'
    _possibleOutputs = {OUTPUT_TOMOMASK_NAME: SetOfTomoMasks}

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

        form.addParam('additionalArgs', StringParam,
                      default="",
                      expertLevel=LEVEL_ADVANCED,
                      label='Additional options',
                      help='You can enter additional command line options to MemBrain here.')

        form.addParam('typeOfSegmentation', params.EnumParam,
                      choices=['instance segmentation',
                               'semantic segmentation'],
                      default=INSTANCE_SEGMENTATION,
                      label='Choose type of output segmentation',
                      display=params.EnumParam.DISPLAY_COMBO)

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        # Insert processing steps
        for i, tomo in enumerate(self.inTomograms.get()):
            self._insertFunctionStep(self.segmentMicrotubuleStep,
                        tomo.getTsId())

        self._insertFunctionStep(self.createOutputStep)





    def setupFolderStep(self, tomId):
        # Creating the tomogram folder
        tomoPath = self._getExtraPath(tomId)
        makePath(tomoPath)

        inputData = self.inTomograms.get()
        print(tomId)
        tomo = inputData[{'_tsId': tomId}]

        src = tomo.getFileName()
        dst = os.path.join(tomoPath, tomId + '.mrc')
        #os.symlink(src, dst)
        import shutil

        shutil.copy(src, dst)
        return tomoPath

    def segmentMicrotubuleStep(self, tomId):
        # say what the parameter says!!
        path =self.setupFolderStep(tomId)
        inputData = self.inTomograms.get()
        #absolute_path = os.path.abspath(path)
        print(tomId)
        tomo = inputData[{'_tsId': tomId}]
        #print(absolute_path)
        #TODO
        if self.typeOfSegmentation.get() == 0:
            outFileName = 'mrc_mrc'
        elif self.typeOfSegmentation.get() == 1:
            outFileName = 'mrc_None'
        else:
            if self.typeOfSegmentation.get() == 2:
                pass
        #path= tomo
        #tomoBaseName = removeBaseExt(tomofilename)
        inputFilename = tomId + '.mrc'
        tsIdFolder = self._getExtraPath(tomId)



        args =  ' -dir %s -out %s ' % (inputFilename, outFileName)
        args += ' -px %f ' %self.inputData.getSamplingRate()

        Plugin.runTardis(self, 'tardis_mt', args,  cwd=tsIdFolder)


    def createOutputStep(self):
        # register how many times the message has been printed
        # Now count will be an accumulated value
        labelledSet = self._genOutputSetOfTomoMasks(
            self.tomoMaskList, 'segmented')
        self._defineOutputs(**{OUTPUT_TOMOMASK_NAME: labelledSet})
        self._defineSourceRelation(self.inTomograms.get(), labelledSet)

    def _genOutputSetOfTomoMasks(self, tomoMaskList, suffix):
        tomoMaskSet = SetOfTomoMasks.create(
            self._getPath(), template='tomomasks%s.sqlite', suffix=suffix)
        inTomoSet = self.inTomograms.get()
        tomoMaskSet.copyInfo(inTomoSet)
        counter = 1
        
        if output_format == 'csv':
            csv_filename = os.path.join(self._getPath(), f'tomomasks_{suffix}.csv')
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['counter', 'file', 'volume_name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for file, inTomo in zip(tomoMaskList, inTomoSet):
                    tomoMask = TomoMask()
                    fn = inTomo.getFileName()
                    tomoMask.copyInfo(inTomo)
                    tomoMask.setLocation((counter, file))
                    vol_name = self._getExtraPath(replaceBaseExt(fn, 'csv'))
                    tomoMask.setVolName(vol_name)
                    tomoMaskSet.append(tomoMask)

                    writer.writerow({'counter': counter, 'file': file, 'volume_name': vol_name})
                    counter += 1
        else:
            for file, inTomo in zip(tomoMaskList, inTomoSet):
                tomoMask = TomoMask()
                fn = inTomo.getFileName()
                tomoMask.copyInfo(inTomo)
                tomoMask.setLocation((counter, file))
                tomoMask.setVolName(self._getExtraPath(replaceBaseExt(fn, 'mrc')))
                tomoMaskSet.append(tomoMask)
                counter += 1

        return tomoMaskSet

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
