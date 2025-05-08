# ***************************************************************************
# *
# * Authors:     Scipion Team ()
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
from tomo.tests import EMD_10439, DataSetEmd10439, MICROTUBULES_TOMOS_DATASET, DataSet_MicrotubulesTomos, \
    ACTIN_TOMOS_DATASET, DataSet_ActinTomos
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
        print(magentaStr('\n==> Binning the tomograms with IMOD:'))
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
            IN_TOMOS: self.binnedTomos,
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
                   f'\n\t- Seg Target = {segTargetStr}'
                   f'\n\t- Seg Mode = {segModeStr}')
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

    def testMembraneSeg(self):
        segMode = TardisSegModes.both.value
        segmentations, meshes = self._runTardis(self.segTarget, segMode)
        # Check the segmentations
        self.checkTomoMasks(segmentations,
                            expectedSetSize=1,
                            expectedSRate=self.unbinnedSRate * self.binFactor,
                            expectedDimensions=DataSetEmd10439.getBinnedDims(self.binFactor))
        # Check the meshes
        # TODO: check if it is deterministic, and in case it is not, expand the TCL with a no. coords tol.


class TestTardisMicrotubuleSeg(TestTardisBase, ABC):

    @classmethod
    def setupChildTest(cls):
        cls.ds = DataSet.getDataSet(MICROTUBULES_TOMOS_DATASET)
        cls.unbinnedSRate = DataSet_MicrotubulesTomos.unbinnedSRate.value
        cls.segTarget = TardisSegTargets.microtubules.value
        cls.binFactor = 2

    # @classmethod
    # def _runPreviousProtocols(cls):
    #     cls._importTomograms()
    #     cls._runBinTomograms()


class TestTardisActinSeg(TestTardisBase, ABC):

    @classmethod
    def setupChildTest(cls):
        cls.ds = DataSet.getDataSet(ACTIN_TOMOS_DATASET)
        cls.unbinnedSRate = DataSet_ActinTomos.unbinnedSRate.value
        cls.segTarget = TardisSegTargets.actin.value
        cls.binFactor = 2

    # @classmethod
    # def _runPreviousProtocols(cls):
    #     cls._importTomograms()
    #     cls._runBinTomograms()
