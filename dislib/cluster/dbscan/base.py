import numpy as np
from pycompss.api.parameter import INOUT
from pycompss.api.task import task

from dislib.cluster.dbscan.classes import Region
from dislib.utils import as_grid


class DBSCAN():
    """ Perform DBSCAN clustering.

    This algorithm requires data to be arranged in a multidimensional grid.
    The default behavior is to re-arrange input data before running the
    clustering algorithm. See fit() for more details.


    Parameters
    ----------
    eps : float, optional (default=0.5)
        The maximum distance between two samples for them to be considered as
        in the same neighborhood.
    min_samples : int, optional (default=5)
        The number of samples (or total weight) in a neighborhood for a point
        to be considered as a core point. This includes the point itself.
    arrange_data: boolean, optional (default=True)
        Whether to re-arrange input data before performing clustering.
    n_regions : int, optional (default=1)
        Number of regions per dimension in which to divide the feature space.
        The total number of regions generated is equal to n_regions ^
        n_features.
    max_samples : int, optional (default=None)
        Setting max_samples to an integer results in the parallelization of
        the computation of distances inside each region of the grid. That
        is, each region is processed using various parallel tasks, where each
        task finds the neighbours of max_samples samples.

        This can be used to balance the load in scenarios where samples are not
        evenly distributed in the feature space.

    Examples
    --------
    >>> from dislib.cluster import DBSCAN
    >>> import numpy as np
    >>> x = np.array([[1, 2], [2, 2], [2, 3], [8, 7], [8, 8], [25, 80]])
    >>> from dislib.data import load_data
    >>> train_data = load_data(x, subset_size=2)
    >>> dbscan = DBSCAN(eps=3, min_samples=2)
    >>> dbscan.fit(train_data)
    >>> print(train_data.labels)

    Methods
    -------
    fit(dataset)
        Perform DBSCAN clustering.
    fit_predict(dataset)
        Same as fit().
    """

    def __init__(self, eps=0.5, min_samples=5, arrange_data=True, n_regions=1,
                 max_samples=None):
        assert n_regions >= 1, \
            "Number of regions must be greater or equal to 1."

        self._eps = eps
        self._min_samples = min_samples
        self._n_regions = n_regions
        self._arrange_data = arrange_data
        self._subset_sizes = []
        self._sorting = []
        self._max_samples = max_samples

    def fit(self, dataset):
        """ Perform DBSCAN clustering on data and sets dataset.labels.

        If arrange_data=True, data is initially rearranged in a
        multidimensional grid with n_regions regions per dimension. Regions
        are uniform in size.

        For example, suppose that data contains N partitions of 2-dimensional
        samples (n_features=2), where the first feature ranges from 1 to 5 and
        the second feature ranges from 0 to 1. Then, n_regions=10 re-arranges
        data into 10^2=100 new partitions, where each partition contains the
        samples that lie in one region of the grid. numpy.linspace() is
        employed to divide the feature space into uniform regions.

        If data is already arranged in a grid, then the number of partitions
        in data must be equal to n_regions ^ n_features. The equivalence
        between partition and region index is computed using
        numpy.ravel_multi_index().

        Parameters
        ----------
        dataset : Dataset
            Input data.
        """
        n_features = dataset.n_features

        if self._arrange_data:
            sorted_data, sorting_ind = as_grid(dataset, self._n_regions, True)
        else:
            self._n_regions = int(np.power(len(dataset), 1 / n_features))
            sorted_data = dataset

        grid = np.empty([self._n_regions] * n_features, dtype=object)
        region_widths = self._compute_region_widths(dataset)

        # Create regions
        for subset_idx, region_id in enumerate(np.ndindex(grid.shape)):
            subset = sorted_data[subset_idx]
            subset_size = sorted_data.subset_size(subset_idx)
            grid[region_id] = Region(region_id, subset, subset_size, self._eps)

        # Set region neighbours
        distances = np.ceil(self._eps / region_widths)

        for region_id in np.ndindex(grid.shape):
            self._add_neighbours(grid[region_id], grid, distances)

        # Run dbscan on each region
        for region_id in np.ndindex(grid.shape):
            region = grid[region_id]
            region.partial_dbscan(self._min_samples, self._max_samples)

        # Compute label equivalences between different regions
        equiv_list = []

        for region_id in np.ndindex(grid.shape):
            equiv_list.append(grid[region_id].get_equivalences())

        equivalences = _merge_dicts(*equiv_list)

        # Compute connected components
        components = _get_connected_components(equivalences)

        # Update region labels according to equivalences
        final_labels = []

        for region_id in np.ndindex(grid.shape):
            region = grid[region_id]
            region.update_labels(components)
            final_labels.append(region.labels)

        final_labels = _concatenate_labels(sorting_ind, *final_labels)
        begin = 0
        end = 0

        for subset_idx, subset in enumerate(dataset):
            end += dataset.subset_size(subset_idx)
            _set_labels(subset, begin, end, final_labels)
            begin = end

    def fit_predict(self, dataset):
        """ Perform DBSCAN clustering on dataset. This method does the same
        as fit(), and is provided for API standardization purposes.

        Parameters
        ----------
        dataset : Dataset
            Input data.

        See also
        --------
        fit
        """
        self.fit(dataset)

    @staticmethod
    def _add_neighbours(region, grid, distances):
        for ind in np.ndindex(grid.shape):
            if ind == region.id:
                continue

            d = np.abs(np.array(region.id) - np.array(ind))

            if (d <= distances).all():
                region.add_neighbour(grid[ind])

    def _compute_region_widths(self, dataset):
        min_ = dataset.min_features()
        max_ = dataset.max_features()
        widths = (max_ - min_) / self._n_regions
        return widths


@task(returns=1)
def _merge_dicts(*dicts):
    merged_dict = {}

    for dict in dicts:
        merged_dict.update(dict)

    return merged_dict


@task(returns=1)
def _get_connected_components(equiv):
    visited = set()
    connected = []

    for node, neighbours in equiv.items():
        if node in visited:
            continue

        connected.append([node])
        _visit_neighbours(equiv, neighbours, visited, connected)

    return connected


def _visit_neighbours(equiv, neighbours, visited, connected):
    to_visit = list(neighbours)

    while len(to_visit) > 0:
        neighbour = to_visit.pop()

        if neighbour in visited:
            continue

        visited.add(neighbour)
        connected[-1].append(neighbour)

        if neighbour in equiv:
            to_visit.extend(equiv[neighbour])


@task(returns=1)
def _concatenate_labels(sorting, *labels):
    final_labels = np.empty(0, dtype=int)

    for label_arr in labels:
        final_labels = np.concatenate((final_labels, label_arr))

    return final_labels[sorting]


@task(subset=INOUT)
def _set_labels(subset, begin, end, labels):
    subset.labels = labels[begin:end]
