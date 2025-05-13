# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
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

"""
@article {Kiewisz2024.12.19.629196,
	author = {Kiewisz, Robert and Fabig, Gunar and Conway, Will and Johnston, Jake and Kostyuchenko, Victor A. and Tan, Aaron and Ba{\v r}inka, Cyril and Clarke, Oliver and Magaj, Magdalena and Yazdkhasti, Hossein and Vallese, Francesca and Lok, Shee-Mei and Redemann, Stefanie and M{\"u}ller-Reichert, Thomas and Bepler, Tristan},
	title = {Accurate and fast segmentation of filaments and membranes in micrographs and tomograms with TARDIS},
	elocation-id = {2024.12.19.629196},
	year = {2025},
	doi = {https://doi.org/10.1101/2024.12.19.629196},
	publisher = {Cold Spring Harbor Laboratory},
	abstract = {Segmentation of macromolecular structures is the primary bottleneck for studying biomolecules and their organization with electron microscopy in 2D/3D {\textendash} requiring months of manual effort. Transformer-based Rapid Dimensionless Instance Segmentation (TARDIS) is a deep learning framework that automatically and accurately annotates membranes and filaments. Pre-trained TARDIS models can segment electron tomography (ET) reconstructions from both 3D and 2D electron micrographs of cryo and plastic-embedded samples. Furthermore, by implementing a novel geometric transformer architecture, TARDIS is the only method to provide accurate instance segmentations of these structures. Reducing the annotation time for ET data from months to minutes, we demonstrate segmentation of membranes and filaments in over 13,000 tomograms in the CZII Data Portal. TARDIS thus enables quantitative biophysical analysis at scale for the first time. We show this in application to kinetochore-microtubule attachment and viral-membrane interactions. TARDIS can be extended to new biomolecules and applications and open-source at https://github.com/SMLC-NYSBC/TARDIS.Competing Interest StatementThe authors have declared no competing interest.},
	URL = {https://www.biorxiv.org/content/10.1101/2024.12.19.629196v2},
	eprint = {https://www.biorxiv.org/content/10.1101/2024.12.19.629196v2.full.pdf},
	journal = {bioRxiv}
}

@article{10.1093/micmic/ozad067.485,
    author = {Kiewisz, Robert and Fabig, Gunar and Müller-Reichert, Thomas and Bepler, Tristan},
    title = {Automated Segmentation of 3D Cytoskeletal Filaments from Electron Micrographs with TARDIS},
    journal = {Microscopy and Microanalysis},
    volume = {29},
    number = {Supplement_1},
    pages = {970-972},
    year = {2023},
    month = {07},
    abstract = {3D segmentation of cytoskeletal filaments and organelles is crucial for studying these structures in cellular (cryo-) electron microscopy (EM) and tomography (ET). Manual annotation remains the gold standard for labeling these objects, due to the limited accuracy of available tools. Existing semi-automatic [1] or fully automatic approaches (e.g. [2]-[4]) can speed up the process, but often require extensive case-by-case tuning by users or significant manual correction of their outputs. In order to scale analysis to the growing number of micrographs and tomograms and enable precise quantification of biological structures, high-accuracy automatic segmentation algorithms are required.},
    issn = {1431-9276},
    doi = {https://doi.org/10.1093/micmic/ozad067.485},
    url = {https://doi.org/10.1093/micmic/ozad067.485},
    eprint = {https://academic.oup.com/mam/article-pdf/29/Supplement\_1/970/50934275/ozad067.485.pdf},
}

"""
