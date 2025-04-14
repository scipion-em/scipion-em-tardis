=======================
Scipion plugin for TARDIS
=======================
.. image:: https://img.shields.io/badge/python-3-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3

.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0
   :alt: License: GPL v3

This plugin allows to use `TARDIS <https://github.com/SMLC-NYSBC/TARDIS>`_ to run automatic membrane and microtubule
segmentation for predicted semantic or instance segmentation on (cryo-)electron microscopy tomograms.

==========================
Installation
==========================

You will need to use 3.0+ version of Scipion to be able to run these protocols.

==========================
Installing the plugin
==========================

In order to install the plugin follow these instructions:

.. code-block::
    
    scipion installp -p scipion-em-tardis

==========================
To install in development mode
==========================

Clone or download the plugin repository:

    git clone https://github.com/scipion-em/scipion-em-tardis.git

Install the plugin in developer mode:

    scipion installp -p local/path/to/scipion-em-tardis --devel

==========================
Protocols
==========================

This plugin integrates only one protocol to run membrane and/or microtubule segmentation. 
The options available are dissected separately below for clarity:

* **Membrane segmentation:** Run semantic or instance segmentation on 3D membrane images. 
* **Microtubule segmentation:** Run semantic or instance segmentation on 3D microtubule images. 

==========================
Tests
==========================
The installation can be checked out running some tests. To list all of them, execute:

.. code-block::

    scipion3 test --grep tardis

To run all of them, execute:

.. code-block::

    scipion3 tests --grep tardis --run

==========================
Tutorial and test results
==========================
The tests generate a workflow that can be used as a guide for running membrane and/or microtubule segmentation.
The input datasets used for running these tests were:

- Membrane segmentation: `EMD_10439 <https://www.ebi.ac.uk/emdb/>`_.
- Microtubule segmentation: `GMPCPP_S1_tomo1_rec <https://www.ebi.ac.uk/emdb/>`_.

==========================
References
==========================
- `TARDIS-em Documentation <https://smlc-nysbc.github.io/TARDIS/>`_. SMLC-NYSBC. (n.d.).
- `TARDIS GitHub page <https://github.com/SMLC-NYSBC/TARDIS>`_.
