=========================
Scipion plugin for TARDIS
=========================
.. image:: https://img.shields.io/pypi/v/scipion-em-tardis.svg
        :target: https://pypi.python.org/pypi/scipion-em-tardis
        :alt: PyPI release

.. image:: https://img.shields.io/pypi/l/scipion-em-tardis.svg
        :target: https://pypi.python.org/pypi/scipion-em-tardis
        :alt: License

.. image:: https://img.shields.io/pypi/pyversions/scipion-em-tardis.svg
        :target: https://pypi.python.org/pypi/scipion-em-tardis
        :alt: Supported Python versions

.. image:: https://img.shields.io/sonar/quality_gate/scipion-em_scipion-em-tardis?server=https%3A%2F%2Fsonarcloud.io
        :target: https://sonarcloud.io/dashboard?id=scipion-em_scipion-em-tardis
        :alt: SonarCloud quality gate

.. image:: https://img.shields.io/pypi/dm/scipion-em-tardis
        :target: https://pypi.python.org/pypi/scipion-em-tardis
        :alt: Downloads

This plugin provide a wrapper around the program `TARDIS <https://github.com/SMLC-NYSBC/TARDIS>`_ to use it within
`Scipion <https://scipion-em.github.io/docs/release-3.0.0/index.html>`_ framework. It segments automatically membranes,
microtubules, and actin filaments for predicted semantic or instance segmentations in (cryo-)electron microscopy.
tomograms.

Installation
------------

You will need to use `3.0 <https://scipion-em.github.io/docs/release-3.0.0/docs/scipion-modes/how-to-install.html>`_ 
version of Scipion to be able to run these protocols. To install the plugin, you have two options:


a) Stable version:

.. code-block::

    scipion3 installp -p scipion-em-tardis

b) Developer's version

    * download the repository from github:

    .. code-block::

        git clone -b devel https://github.com/scipion-em/scipion-em-tardis.git

    * install:

    .. code-block::

        scipion3 installp -p /path/to/scipion-em-tardis --devel

To check the installation, simply run the following Scipion test for the plugin:

    .. code-block::

        scipion3 tests tardis.tests.tests_tardis

Licensing
---------

tardis software package is available under `BSD-2-Clause license <https://opensource.org/license/bsd-2-clause>`_

Protocols
---------

* **Tomogram segmentation:** Semantic or instance segmentation of microtubules, membranes, or actin filaments in tomograms.

Latest plugin versions
----------------------

If you want to check the latest version and release history go to `CHANGES <https://github.com/scipion-em/scipion-em-tardis/blob/master/CHANGES.txt>`_

References
----------------------
`DOI [BioRxiv] <http://doi.org/10.1101/2024.12.19.629196>`_
Kiewisz R. et.al. 2024. Accurate and fast segmentation of filaments and membranes in micrographs and tomograms with TARDIS.

`DOI [Microscopy and Microanalysis] <http://dx.doi.org/10.1093/micmic/ozad067.485>`_
Kiewisz R., Fabig G., Müller-Reichert T. Bepler T. 2023. Automated Segmentation of 3D Cytoskeletal Filaments from Electron Micrographs with TARDIS. Microscopy and Microanalysis 29(Supplement_1):970-972.

`Link: NeurIPS 2022 MLSB Workshop <https://www.mlsb.io/papers_2022/Membrane_and_microtubule_rapid_instance_segmentation_with_dimensionless_instance_segmentation_by_learning_graph_representations_of_point_clouds.pdf>`_
Kiewisz R., Bepler T. 2022. Membrane and microtubule rapid instance segmentation with dimensionless instance segmentation by learning graph representations of point clouds. Neurips 2022 - Machine Learning for Structural Biology Workshop.


