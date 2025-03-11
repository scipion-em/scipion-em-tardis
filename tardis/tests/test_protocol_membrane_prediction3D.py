#!/usr/bin/env python
import tempfile

# ***************************************************************************
# *
# * Authors:     Raquel Fabra López (raquel.fabra@estudiante.uam.es)
# *
# * Unidad de Bioinformatica of Centro Nacional de Biotecnologia, CSIC
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
from pyworkflow.tests import setupTestProject, DataSet
from pyworkflow.utils import magentaStr

from tomo.protocols import ProtImportTomograms
from tomo.tests.test_base_centralized_layer import TestBaseCentralizedLayer
from tardis.protocols.protocol_membrane_prediction3D import (ProtTardisMembrans3d, INSTANCE_SEGMENTATION,
                                                    SEMANTIC_SEGMENTATION, MEMBRANE_SEGMENTATION, MICROTUBULE_SEGMENTATION, OUTPUT_TOMOMASK_NAME)
from tomo3d.protocols.protocol_base import outputTomo3dObjects
from tomo.tests import EMD_10439, DataSetEmd10439


class TestMembrane3D(TestBaseCentralizedLayer):

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.ds = DataSet.getDataSet(EMD_10439)
        cls._runPreviousProtocols()

    @classmethod
    def _runPreviousProtocols(cls):

        cls.importedTomo = cls._importTomograms()

    @classmethod
    def _importTomograms(cls):
        print(magentaStr("\n==> Importing data - tomograms:"))
        protImportTomogram = cls.newProtocol(ProtImportTomograms,
                                             filesPath=cls.ds.getFile(DataSetEmd10439.tomoEmd10439.value),
                                             samplingRate=5.0)

        cls.launchProtocol(protImportTomogram)
        outputTomos = getattr(protImportTomogram, 'Tomograms', None)
        cls.assertIsNotNone(outputTomos, 'No tomograms were genetated.')

        return outputTomos

    @classmethod
    def _runTardis(cls, inTomograms=None, recMethod=None, segMethod=None, dt= None, objectLabel= None):
        whatSegment = 'MEMBRANE_SEGMENTATION' if recMethod is MEMBRANE_SEGMENTATION else 'MICROTUBULE_SEGMENTATION'

        print(magentaStr(f"\n==> Segmenting the tomograms using the method {whatSegment} :"))
        #TODO: if instance .... else ...
        #TODO: add to newProtocol dataset + height

        protSegTomo = cls.newProtocol(ProtTardisMembrans3d,
                                      inTomograms=inTomograms,
                                      whatSegment= recMethod,
                                      typeOfSegmentation= segMethod)

        protSegTomo.setObjLabel(f'Tomo seg {whatSegment}')
        cls.launchProtocol(protSegTomo)
        outTomos = getattr(protSegTomo, OUTPUT_TOMOMASK_NAME, None)
        return outTomos

    #TODO: add def checkTomoMasks, add vol
    def _checkTomos(self, inTomoSet):
        self.checkTomoMask(inTomoSet,
                            expectedSetSize=inTomoSet.getSize(),
                            expectedSRate=inTomoSet.getSamplingRate())#                   expectedDimensions=inTomoSet.getFirstItems().getDimensions())

    def testMembraneSegmentation(self):
         instanceOrSemantic = [INSTANCE_SEGMENTATION, SEMANTIC_SEGMENTATION]
         objectLabel =['INSTANCE_SEGMENTATION', 'SEMANTIC_SEGMENTATION']
         whatSegment = MEMBRANE_SEGMENTATION
         for segType in instanceOrSemantic:
             segTomo = self._runTardis(inTomograms=self.importedTomo, recMethod=whatSegment, segMethod=segType, objectLabel= None)
             print(segTomo)
             self._checkTomos(segTomo)

###############################################################################################

# class TestMicrotubule3D(TestBaseCentralizedLayer):
#
#     @classmethod
#     def setUpClass(cls):
#         setupTestProject(cls)
#         cls.ds = DataSet.getDataSet(EMD_10439)
#         cls._runPreviousProtocols()
#
#     @classmethod
#     def _runPreviousProtocols(cls):
#
#         cls.importedTomo = cls._importTomograms()
#
#     @classmethod
#     def _importTomograms(cls):
#         print(magentaStr("\n==> Importing data - tomograms:"))
#         protImportTomogram = cls.newProtocol(ProtImportTomograms,
#                                              filesPath=cls.ds.getFile(DataSetEmd10439.tomoEmd10439.value),
#                                              samplingRate=5.0)
#
#         cls.launchProtocol(protImportTomogram)
#         outputTomos = getattr(protImportTomogram, 'Tomograms', None)
#         cls.assertIsNotNone(outputTomos, 'No tomograms were genetated.')
#
#         return outputTomos
#
#     @classmethod
#     def _runTardis(cls, inTomograms=None, recMethod=None, segMethod=None, dt= None, objectLabel= None):
#         whatSegment = 'MEMBRANE_SEGMENTATION' if recMethod is MEMBRANE_SEGMENTATION else 'MICROTUBULE_SEGMENTATION'
#
#         print(magentaStr(f"\n==> Segmenting the tomograms using the method {whatSegment} :"))
#         #TODO: if instance .... else ...
#         #TODO: add to newProtocol dataset + height
#
#         protSegTomo = cls.newProtocol(ProtTardisMembrans3d,
#                                       inTomograms=inTomograms,
#                                       whatSegment= recMethod,
#                                       typeOfSegmentation= segMethod)
#
#         protSegTomo.setObjLabel(f'Tomo seg {whatSegment}')
#         cls.launchProtocol(protSegTomo)
#         outTomos = getattr(protSegTomo, OUTPUT_TOMOMASK_NAME, None)
#         return outTomos
#
#     #TODO: add def checkTomoMasks, add vol
#     def _checkTomos(self, inTomoSet):
#         self.checkTomograms(inTomoSet,
#                             expectedSetSize=inTomoSet.getSize(),
#                             expectedSRate=inTomoSet.getSamplingRate())#                   expectedDimensions=inTomoSet.getFirstItems().getDimensions())

    # def testMicrotubuleSegmentation(self):
    #
    #     instanceOrSemantic = [INSTANCE_SEGMENTATION, SEMANTIC_SEGMENTATION]
    #     objectLabel =['INSTANCE_SEGMENTATION', 'SEMANTIC_SEGMENTATION']
    #     whatSegment = MICROTUBULE_SEGMENTATION
    #     for segType in instanceOrSemantic:
    #         segTomo = self._runTardis(inTomograms=self.importedTomo, recMethod=whatSegment, segMethod=segType, objectLabel= None)
    #         print(segTomo)
    #         self._checkTomos(segTomo)