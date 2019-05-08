import unittest
import sys
import io

import numpy as np
from numpy.random.mtrand import RandomState
from pycompss.api.api import compss_wait_on
from sklearn.datasets import make_blobs, load_iris
from sklearn.exceptions import ConvergenceWarning

from dislib.cluster import GaussianMixture
from dislib.data import Dataset, load_libsvm_file
from dislib.data import Subset
from dislib.data import load_data


class GaussianMixtureTest(unittest.TestCase):

    def test_init_params(self):
        """Tests that GaussianMixture params are set"""
        n_components = 2
        covariance_type = 'diag'
        tol = 1e-4
        reg_covar = 1e-5
        max_iter = 3
        init_params = 'random'
        weights_init = np.array([0.4, 0.6])
        means_init = np.array([[0, 0], [2, 3]])
        precisions_init = 'todo'
        random_state = RandomState(666)
        gm = GaussianMixture(n_components=n_components,
                             covariance_type=covariance_type,
                             tol=tol,
                             reg_covar=reg_covar,
                             max_iter=max_iter,
                             init_params=init_params,
                             weights_init=weights_init,
                             means_init=means_init,
                             precisions_init=precisions_init,
                             random_state=random_state)
        expected = (n_components, covariance_type, tol, reg_covar,
                    max_iter, init_params, weights_init, means_init,
                    precisions_init, random_state)
        real = (gm.n_components, gm.covariance_type, gm.tol, gm.reg_covar,
                gm.max_iter, gm.init_params, gm.weights_init, gm.means_init,
                gm.precisions_init, gm.random_state)
        self.assertEqual(expected, real)

    def test_fit(self):
        """Tests GaussianMixture.fit()"""
        dataset = Dataset(n_features=2)

        dataset.append(Subset(np.array([[1, 2], [2, 1], [-3, -3]])))
        dataset.append(Subset(np.array([[-1, -2], [-2, -1], [3, 3]])))

        gm = GaussianMixture(n_components=2, random_state=666)
        gm.fit(dataset)

        expected_weights = np.array([0.5, 0.5])
        expected_means = np.array([[-2, -2], [2, 2]])
        expected_cov = np.array([[[0.66671688, 0.33338255],
                                  [0.33338255, 0.66671688]],

                                 [[0.66671688, 0.33338255],
                                  [0.33338255, 0.66671688]]])
        expected_pc = np.array([[[1.22469875, -0.70714834],
                                 [0., 1.4141944]],

                                [[1.22469875, -0.70714834],
                                 [0., 1.4141944]]])

        gm.weights_ = compss_wait_on(gm.weights_)
        gm.means_ = compss_wait_on(gm.means_)
        gm.covariances_ = compss_wait_on(gm.covariances_)
        gm.precisions_cholesky_ = compss_wait_on(gm.precisions_cholesky_)

        self.assertTrue((np.allclose(gm.weights_, expected_weights)))
        self.assertTrue((np.allclose(gm.means_, expected_means)))
        self.assertTrue((np.allclose(gm.covariances_, expected_cov)))
        self.assertTrue((np.allclose(gm.precisions_cholesky_, expected_pc)))

    def test_predict(self):
        """Tests GaussianMixture.predict()"""
        dataset = Dataset(n_features=2)
        p0, p1, p2, p3 = [1, 2], [-1, -2], [2, 1], [-2, -1]

        dataset.append(Subset(np.array([p0, p1])))
        dataset.append(Subset(np.array([p2, p3])))

        gm = GaussianMixture(n_components=2, random_state=666)
        gm.fit(dataset)

        p4, p5 = [2, 2], [-1, -3]
        dataset.append(Subset(np.array([p4, p5])))
        gm.predict(dataset)
        prediction = dataset.labels

        self.assertTrue(prediction[0] != prediction[1])
        self.assertTrue(prediction[0] == prediction[2] == prediction[4])
        self.assertTrue(prediction[1] == prediction[3] == prediction[5])

    def test_fit_predict(self):
        """Tests GaussianMixture.fit_predict()"""
        x, y = make_blobs(n_samples=1500, random_state=170)
        x_filtered = np.vstack(
            (x[y == 0][:500], x[y == 1][:100], x[y == 2][:10]))
        y_real = np.concatenate((np.zeros(500), np.ones(100), 2*np.ones(10)))

        dataset = load_data(x_filtered, subset_size=300)

        gm = GaussianMixture(n_components=3, random_state=170)
        gm.fit_predict(dataset)
        prediction = dataset.labels

        self.assertEqual(len(prediction), 610)
        accuracy = np.count_nonzero(prediction == y_real) / len(prediction)
        self.assertGreater(accuracy, 0.99)

    def test_check_n_components(self):
        """Tests GaussianMixture n_components validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(n_components=0)
            gm.fit(dataset)

    def test_check_tol(self):
        """Tests GaussianMixture tol validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(tol=-0.1)
            gm.fit(dataset)

    def test_check_max_iter(self):
        """Tests GaussianMixture max_iter validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(max_iter=0)
            gm.fit(dataset)

    def test_check_reg_covar(self):
        """Tests GaussianMixture reg_covar validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(reg_covar=-0.1)
            gm.fit(dataset)

    def test_check_covariance_type(self):
        """Tests GaussianMixture covariance_type validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(covariance_type='')
            gm.fit(dataset)

    def test_check_init_params(self):
        """Tests GaussianMixture covariance_type validation"""
        x = np.array([[0, 0], [0, 1], [1, 0]])
        dataset = load_data(x, subset_size=10)
        with self.assertRaises(ValueError):
            gm = GaussianMixture(init_params='')
            gm.fit(dataset)

    def test_sparse(self):
        """ Tests GaussianMixture produces the same results using dense and
        sparse data structures """
        file_ = "tests/files/libsvm/2"

        sparse = load_libsvm_file(file_, 10, 780)
        dense = load_libsvm_file(file_, 10, 780, store_sparse=False)

        covariance_types = 'full', 'tied', 'diag', 'spherical'

        for cov_type in covariance_types:
            gm = GaussianMixture(n_components=4, random_state=0,
                                 covariance_type=cov_type)
            gm.fit_predict(sparse)
            gm.fit_predict(dense)
            self.assertTrue(np.array_equal(sparse.labels, dense.labels))

    def test_init_random(self):
        """ Tests GaussianMixture random initialization """
        np.random.seed(0)
        x = np.random.rand(50, 3)
        dataset = load_data(x, subset_size=10)
        gm = GaussianMixture(init_params='random', n_components=4,
                             random_state=170)
        gm.fit(dataset)
        self.assertGreater(gm.n_iter, 5)

    def test_covariance_types(self):
        """ Tests GaussianMixture covariance types """
        np.random.seed(0)
        n_samples = 600
        n_features = 2

        def create_anisotropic_dataset():
            """Create dataset with 2 anisotropic gaussians of different
            weight"""
            n0 = 2 * n_samples // 3
            n1 = n_samples // 3
            x0 = np.random.normal(size=(n0, n_features))
            x1 = np.random.normal(size=(n1, n_features))
            transformation = [[0.6, -0.6], [-0.4, 0.8]]
            x0 = np.dot(x0, transformation)
            x1 = np.dot(x1, transformation) + [0, 3]
            x = np.concatenate((x0, x1))
            y = np.concatenate((np.zeros(n0), np.ones(n1)))
            return x, y

        def create_spherical_blobs_dataset():
            """Create dataset with 2 spherical gaussians of different weight,
            variance and position"""
            n0 = 2 * n_samples // 3
            n1 = n_samples // 3
            x0 = np.random.normal(size=(n0, 2), scale=0.5, loc=[2, 0])
            x1 = np.random.normal(size=(n1, 2), scale=2.5)
            x = np.concatenate((x0, x1))
            y = np.concatenate((np.zeros(n0), np.ones(n1)))
            return x, y

        def create_uncorrelated_dataset():
            """Create dataset with 2 gaussians forming a cross of uncorrelated
            variables"""
            n0 = 2 * n_samples // 3
            n1 = n_samples // 3
            x0 = np.random.normal(size=(n0, n_features))
            x1 = np.random.normal(size=(n1, n_features))
            x0 = np.dot(x0, [[1.2, 0], [0, 0.5]]) + [0, 3]
            x1 = np.dot(x1, [[0.4, 0], [0, 2.5]]) + [1, 0]
            x = np.concatenate((x0, x1))
            y = np.concatenate((np.zeros(n0), np.ones(n1)))
            return x, y

        def create_correlated_dataset():
            """Create dataset with 2 gaussians forming a cross of correlated
            variables"""
            x, y = create_uncorrelated_dataset()
            x = np.dot(x, [[1, 1], [-1, 1]])
            return x, y

        datasets = {'aniso': create_anisotropic_dataset(),
                    'blobs': create_spherical_blobs_dataset(),
                    'uncorr': create_uncorrelated_dataset(),
                    'corr': create_correlated_dataset()}
        real_labels = {k: v[1] for k, v in datasets.items()}
        for k, v in datasets.items():
            datasets[k] = load_data(x=v[0], subset_size=200)

        covariance_types = 'full', 'tied', 'diag', 'spherical'

        def compute_accuracy(real, predicted):
            """ Computes classification accuracy for binary (0/1) labels"""
            equal_labels = np.count_nonzero(predicted == real)
            equal_ratio = equal_labels / len(real)
            return max(equal_ratio, 1-equal_ratio)

        accuracy = {}
        pred_labels = {}
        for cov_type in covariance_types:
            accuracy[cov_type] = {}
            pred_labels[cov_type] = {}
            gm = GaussianMixture(n_components=2, covariance_type=cov_type,
                                 random_state=0)
            for ds in datasets.values():
                gm.fit_predict(ds)
            for k, ds in datasets.items():
                pred = ds.labels
                pred_labels[cov_type][k] = pred
                accuracy[cov_type][k] = compute_accuracy(real_labels[k], pred)

        # Covariance type 'full'.
        # Assert good accuracy in all tested datasets.
        self.assertGreater(accuracy['full']['aniso'], 0.9)
        self.assertGreater(accuracy['full']['blobs'], 0.9)
        self.assertGreater(accuracy['full']['uncorr'], 0.9)
        self.assertGreater(accuracy['full']['corr'], 0.9)

        # Covariance type 'tied'.
        # Assert good accuracy only for 'aniso'.
        self.assertGreater(accuracy['tied']['aniso'], 0.9)
        self.assertLess(accuracy['tied']['blobs'], 0.9)
        self.assertLess(accuracy['tied']['uncorr'], 0.9)
        self.assertLess(accuracy['tied']['corr'], 0.9)

        # Covariance type 'diag'.
        # Assert good accuracy only for 'blobs' and 'uncorr'.
        self.assertLess(accuracy['diag']['aniso'], 0.9)
        self.assertGreater(accuracy['diag']['blobs'], 0.9)
        self.assertGreater(accuracy['diag']['uncorr'], 0.9)
        self.assertLess(accuracy['diag']['corr'], 0.9)

        # Covariance type 'spherical'.
        # Assert good accuracy only for 'blobs'.
        self.assertLess(accuracy['spherical']['aniso'], 0.9)
        self.assertGreater(accuracy['spherical']['blobs'], 0.9)
        self.assertLess(accuracy['spherical']['uncorr'], 0.9)
        self.assertLess(accuracy['spherical']['corr'], 0.9)

        # For a graphical plot of the results of this comparision, see
        # examples/gm_covariance_types_comparision.py

    def test_verbose(self):
        """ Tests GaussianMixture verbose mode prints text """
        saved_stdout = sys.stdout
        try:
            sys.stdout = io.StringIO()

            # Call code that has to print
            x = np.array([[0, 0], [0, 1], [1, 0]])
            dataset = load_data(x, subset_size=10)
            gm = GaussianMixture(verbose=True, max_iter=2)
            gm.fit(dataset)
            captured_output = sys.stdout.getvalue()

        finally:
            sys.stdout = saved_stdout

        self.assertTrue(len(captured_output) > 0)

    def test_not_converged_warning(self):
        with self.assertWarns(ConvergenceWarning):
            x, _ = load_iris(return_X_y=True)
            dataset = load_data(x, subset_size=75)
            gm = GaussianMixture(max_iter=1)
            gm.fit(dataset)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
