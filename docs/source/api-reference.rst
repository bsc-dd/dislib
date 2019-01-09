API Reference
=============

dislib.data: Data handling utilities
------------------------------------

Classes
.......

:class:`data.Dataset <dislib.data.classes.Dataset>` - Main data structure for
handling distributed datasets. Dataset works as a list of Subset.

:class:`data.Subset <dislib.data.classes.Subset>` - Collection of samples and
(optionally) labels.


Functions
.........

:meth:`data.load_data <dislib.data.base.load_data>` - Build a
:class:`Dataset <dislib.data.classes.Dataset>` from an ndarray.

:meth:`data.load_libsvm_file <dislib.data.base.load_libsvm_file>` - Build a
:class:`Dataset <dislib.data.classes.Dataset>` from a file in LibSVM format
(sparse).

:meth:`data.load_libsvm_files <dislib.data.base.load_libsvm_files>` - Build a
:class:`Dataset <dislib.data.classes.Dataset>` from multiple files in LibSVM
format (sparse).

:meth:`data.load_libsvm_file <dislib.data.base.load_csv_file>` - Build a
:class:`Dataset <dislib.data.classes.Dataset>` from a file in CSV format.

:meth:`data.load_libsvm_files <dislib.data.base.load_csv_files>` - Build a
:class:`Dataset <dislib.data.classes.Dataset>` from multiple files in CSV
format.


dislib.utils: Other utility functions
-------------------------------------

:meth:`utils.as_grid <dislib.utils.base.as_grid>` - Re-organizes samples in a
:class:`Dataset <dislib.data.classes.Dataset>`
in a hyper-dimensional grid, where each
:class:`Subset <dislib.data.classes.Subset>` represents a region in this space.

:meth:`utils.shuffle <dislib.utils.base.shuffle>` - Randomly shuffles the
samples in a :class:`Dataset <dislib.data.classes.Dataset>`.


dislib.cluster: Clustering
--------------------------

Classes
.......

:class:`cluster.DBSCAN <dislib.cluster.dbscan.base.DBSCAN>` - Perform DBSCAN
clustering.

:class:`cluster.KMeans <dislib.cluster.kmeans.base.KMeans>` - Perform K-Means
clustering.

:class:`cluster.KMedoids <dislib.cluster.kmedoids.base.KMedoids>` - Perform
K-Medoids clustering.


dislib.classification: Classification
-------------------------------------

Classes
.......

:class:`classification.CascadeSVM <dislib.classification.csvm.base.CascadeSVM>`
- Distributed support vector classification using a cascade of classifiers.

:class:`classification.RandomForestClassifier <dislib.classification.rf.forest.RandomForestClassifier>` -
Build a random forest for classification.


Other functions
---------------

:meth:`fft <dislib.fft.base.fft>` - Distributed fast fourier transform
computation.

