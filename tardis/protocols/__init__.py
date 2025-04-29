# -*- coding: utf-8 -*-
# **************************************************************************
# Module to declare protocols
# Find documentation here: https://scipion-em.github.io/docs/docs/developer/creating-a-protocol
# **************************************************************************
from typing import Tuple

from pyworkflow.tests import DataSet
from .protocol_membrane_prediction3D import ProtTardisMembrans3d


DataSet(name='microtubulos', folder='microtubulos',
        files={
            'micro': 'GMPCPP_S1_tomo1_rec.mrc',           
        })