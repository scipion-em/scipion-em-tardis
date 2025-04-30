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
from os.path import join
from pyworkflow.object import Set
from pyworkflow.utils import makePath, createLink
from tardis.protocols.protocol_membrane_prediction_base import ProtTardisBase, SEG_MODE, TardisSegModes
from tomo.objects import SetOfTomoMasks, TomoMask
from tardis import Plugin


class ProtTardisMicrotubuleSeg(ProtTardisBase):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'tomogram microtubules segmentation'
    program = 'tardis_mt'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # -------------------------- DEFINE param functions ------------------------
    # --------------------------- STEPS functions ------------------------------
    def segmentStep(self, tsId):
        tomo = self.inTomosDict[tsId]
        tomoPath = self._getExtraPath(tsId)
        makePath(tomoPath)
        createLink(tomo.getFileName(), self._getCurrentTomoFile(tsId))
        args = self._getCmdArgs(tsId)
        Plugin.runTardis(self, self.program, args)#, cwd=self._getCurrentTomoDir(tsId))

    def createOutputStep(self, tsId):
        with self._lock():
            inTomo = self.inTomosDict[tsId]
            outputSet = self._getOutputSet()
            tomoMask = TomoMask()
            tomoMask.setFileName(self._getOutputFileName(tsId))
            tomoMask.setVolName(inTomo.getFileName())
            tomoMask.copyInfo(inTomo)
            outputSet.append(tomoMask)
            self._store(outputSet)

    def _getOutputSet(self) -> SetOfTomoMasks:
        outSetSetAttrib = self._possibleOutputs.segmentations.name
        outputSet = getattr(self, outSetSetAttrib, None)
        if outputSet:
            outputSet.enableAppend()
        else:
            outTsSet = SetOfTomoMasks.create(self._getPath(), template='tomomasks%s.sqlite')
            outTsSet.copyInfo(self.getInTomos())
            outTsSet.setStreamState(Set.STREAM_OPEN)
            self._defineOutputs(**{outSetSetAttrib: outTsSet})
            self._defineSourceRelation(self.getInTomos(returnPointer=True), outTsSet)
        return outputSet

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

    # --------------------------- INFO functions -----------------------------------
    def _getOutputFileNameArg(self) -> str:
        return 'mrc_mrc' if getattr(self, SEG_MODE).get() == TardisSegModes.instance.value else 'mrc_None'

    def _getOutputFileName(self, tsId: str) -> str:
        return join(self._getExtraPath(tsId, 'Predictions'), f'{tsId}_{self._getSegMode()}.mrc')

