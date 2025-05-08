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
from typing import Tuple, Union

from imod.constants import OUTPUT_TOMOGRAMS_NAME
from imod.protocols import ProtImodTomoNormalization
from imod.protocols.protocol_base import IN_TOMO_SET, BINNING_FACTOR
from pyworkflow.tests import setupTestProject, DataSet
from pyworkflow.utils import magentaStr, cyanStr
from tardis.protocols.protocol_tardis_seg import TardisSegModes, TardisSegTargets, ProtTardisSeg, IN_TOMOS, SEG_TARGET, \
    SEG_MODE
from tomo.objects import SetOfTomoMasks, SetOfMeshes
from tomo.protocols import ProtImportTomograms
from tomo.tests.test_base_centralized_layer import TestBaseCentralizedLayer
from tomo.tests import EMD_10439, DataSetEmd10439
from abc import ABC, abstractmethod


class TestTardisBase(TestBaseCentralizedLayer, ABC):
    ds = None
    importedTomos = None
    binFactor = None
    binnedTomos = None
    unbinnedSRate = None
    segTarget = None

    @classmethod
    def setUpClass(cls):
        setupTestProject(cls)
        cls.setupChildTest()
        cls.runPrevProtocols()

    @classmethod
    @abstractmethod
    def setupChildTest(cls):
        pass

    @classmethod
    def runPrevProtocols(cls):
        try:
            print(cyanStr('--------------------------------- RUNNING PREVIOUS PROTOCOLS ---------------------------------'))
            cls._runPreviousProtocols()
            print(
                cyanStr('\n-------------------------------- PREVIOUS PROTOCOLS FINISHED ---------------------------------'))
        except Exception as e:
            raise  Exception(f'Something Failed when executing the previous protocols -> {e}')

    @classmethod
    @abstractmethod
    def _runPreviousProtocols(cls):
        pass

    @classmethod
    def _runBinTomograms(cls):
        print(magentaStr('\n==> Binning the tomograms with IMOD'))
        protArgsDict = {
            IN_TOMO_SET: cls.importedTomos,
            BINNING_FACTOR: cls.binFactor
        }
        protBinTomos = cls.newProtocol(ProtImodTomoNormalization, **protArgsDict)
        cls.launchProtocol(protBinTomos)
        binnedTomos = getattr(protBinTomos, OUTPUT_TOMOGRAMS_NAME, None)
        cls.binnedTomos = binnedTomos

    def _runTardis(self,
                   segTarget: int,
                   segMode: int,
                   cnnThreshold: float = 0.5,
                   distThreshold: float = 0.9)\
            -> Tuple[Union[SetOfTomoMasks, None], Union[SetOfMeshes, None]]:

        infoStr, objLabel = self._getInfoStrs(segTarget, segMode)
        print(magentaStr(infoStr))
        tardisInputDict = {
            IN_TOMOS: self.importedTomos,
            SEG_TARGET: segTarget,
            SEG_MODE: segMode,
            'cnnThreshold': cnnThreshold,
            'distThreshold': distThreshold
        }
        protTardis = self.newProtocol(ProtTardisSeg, **tardisInputDict)
        self.launchProtocol(protTardis)
        protTardis.setObjLabel(objLabel)
        segmentations = getattr(protTardis, protTardis._possibleOutputs.segmentations.name, None)
        meshes = getattr(protTardis, protTardis._possibleOutputs.meshes.name, None)
        return segmentations, meshes

    @staticmethod
    def _getInfoStrs(segTarget: int, segMode: int) -> Tuple[str, str]:
        if segTarget == TardisSegTargets.actin.value:
            segTargetStr = TardisSegTargets.actin.name
        elif segTarget == TardisSegTargets.membranes.value:
            segTargetStr = TardisSegTargets.membranes.name
        else:
            segTargetStr = TardisSegTargets.microtubules.name

        if segMode == TardisSegModes.instances.value:
            segModeStr = TardisSegModes.instances.name
        elif segMode == TardisSegModes.semantic.value:
            segModeStr = TardisSegModes.semantic.name
        else:
            segModeStr = TardisSegModes.both.name
        infoStr = (f'\n==> Running Tardis:'
                   f'\n\t - Seg Target = {segTargetStr}'
                   f'\n\t - Seg Mode = {segModeStr}')
        objLabel = f'tardis {segTargetStr} {segModeStr}'
        return infoStr, objLabel


class TestTardisMembraneSeg(TestTardisBase):

    @classmethod
    def setupChildTest(cls):
        cls.ds = DataSet.getDataSet(EMD_10439)
        cls.unbinnedSRate = DataSetEmd10439.unbinnedSRate.value
        cls.segTarget = TardisSegTargets.membranes.value
        cls.binFactor = 2

    @classmethod
    def _runPreviousProtocols(cls):
        cls._importTomograms()
        cls._runBinTomograms()

    @classmethod
    def _importTomograms(cls):
        print(magentaStr("\n==> Importing data - tomograms:"))
        protImportTomogram = cls.newProtocol(ProtImportTomograms,
                                             filesPath=cls.ds.getFile(DataSetEmd10439.tomoEmd10439.value),
                                             samplingRate=cls.unbinnedSRate)
        cls.launchProtocol(protImportTomogram)
        outputTomos = getattr(protImportTomogram, 'Tomograms', None)
        cls.importedTomos = outputTomos

    def testMembraneSeg_01(self):
        segMode = TardisSegModes.both.value
        self._runTardis(self.segTarget, segMode)

#     @classmethod
#     def _runTardis(cls, inTomograms=None, recMethod=None, segMethod=None):
#         whatSegment = 'MEMBRANE_SEGMENTATION' if recMethod is MEMBRANE_SEGMENTATION else 'MICROTUBULE_SEGMENTATION'
#
#         if segMethod == INSTANCE_SEGMENTATION:
#             method = '-> Instance'
#         elif segMethod == SEMANTIC_SEGMENTATION:
#             method = '-> Semantic'
#
#         print(magentaStr(f"\n==> Segmenting the tomograms using the method {whatSegment} {method}:"))
#
#         protSegTomo = cls.newProtocol(ProtTardisMembransSeg,
#                                       inTomograms=inTomograms,
#                                       whatSegment=recMethod,
#                                       typeOfSegmentation=segMethod)
#
#         protSegTomo.setObjLabel(f'Tomo seg {whatSegment}')
#         cls.launchProtocol(protSegTomo)
#         outTomos = getattr(protSegTomo, OUTPUT_TOMOMASK_NAME, None)
#         return outTomos
#
#     #TODO: add def checkTomoMasks, add vol
#     def _checkTomos(self, inTomoSet):
#         self.checkTomoMask(inTomoSet,
#                            expectedSetSize=inTomoSet.getSize(),
#                            expectedSRate=inTomoSet.getSamplingRate())  #                   expectedDimensions=inTomoSet.getFirstItems().getDimensions())
#
#     def testMembraneSegmentation(self):
#         instanceOrSemantic = [INSTANCE_SEGMENTATION, SEMANTIC_SEGMENTATION]
#         whatSegment = MEMBRANE_SEGMENTATION
#         for segType in instanceOrSemantic:
#             segTomo = self._runTardis(inTomograms=self.importedTomo, recMethod=whatSegment, segMethod=segType)
#             print(segTomo)
#             self._checkTomos(segTomo)
#
#
# ###############################################################################################
#
# class TestTardisMicrotubuleSeg(TestBaseCentralizedLayer):
#
#     @classmethod
#     def setUpClass(cls):
#         setupTestProject(cls)
#         cls.ds = DataSet.getDataSet('microtubulesTomograms')
#         cls._runPreviousProtocols()
#
#     @classmethod
#     def _runPreviousProtocols(cls):
#         cls.importedTomo = cls._importTomograms()
#
#     @classmethod
#     def _importTomograms(cls):
#         print(magentaStr("\n==> Importing data - tomograms:"))
#         protImportTomogram = cls.newProtocol(ProtImportTomograms,
#                                              filesPath=cls.ds.getFile('micro'),
#                                              samplingRate=5.0)
#
#         cls.launchProtocol(protImportTomogram)
#         outputTomos = getattr(protImportTomogram, 'Tomograms', None)
#         cls.assertIsNotNone(outputTomos, 'No tomograms were genetated.')
#
#         return outputTomos
#
#     @classmethod
#     def _runTardis(cls, inTomograms=None, recMethod=None, segMethod=None):
#         whatSegment = 'MEMBRANE_SEGMENTATION' if recMethod is MEMBRANE_SEGMENTATION else 'MICROTUBULE_SEGMENTATION'
#
#         if segMethod == INSTANCE_SEGMENTATION:
#             method = '-> Instance'
#         elif segMethod == SEMANTIC_SEGMENTATION:
#             method = '-> Semantic'
#
#         # print(magentaStr(f"\n==> Segmenting the tomograms using the method {whatSegment} {method}:"))
#
#         protSegTomo = cls.newProtocol(ProtTardisMembransSeg,
#                                       inputSetOfTomograms=inTomograms,
#                                       segmentationType=TardisSegModes.semantic.value)
#
#         # protSegTomo.setObjLabel(f'Tomo seg {whatSegment}')
#         cls.launchProtocol(protSegTomo)
#         outTomos = getattr(protSegTomo, OUTPUT_TOMOMASK_NAME, None)
#         return outTomos
#
#     def _checkTomos(self, inTomoSet):
#         self.checkTomoMask(inTomoSet,
#                            expectedSetSize=inTomoSet.getSize(),
#                            expectedSRate=inTomoSet.getSamplingRate())  #                   expectedDimensions=inTomoSet.getFirstItems().getDimensions())
#
#     def testMicrotubuleSegmentation(self):
#
#         instanceOrSemantic = [INSTANCE_SEGMENTATION, SEMANTIC_SEGMENTATION]
#         whatSegment = MICROTUBULE_SEGMENTATION
#         for segType in instanceOrSemantic:
#             segTomo = self._runTardis(inTomograms=self.importedTomo, recMethod=whatSegment, segMethod=segType)
#             print(segTomo)
#             self._checkTomos(segTomo)
