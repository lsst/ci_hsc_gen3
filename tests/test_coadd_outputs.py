# This file is part of ci_hsc_gen3.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
import unittest
import numbers
import numpy as np

from lsst.daf.butler import Butler
import lsst.geom as geom
import lsst.meas.algorithms
import lsst.afw.image

from lsst.utils import getPackageDir

from lsst.ci.hsc.gen3 import DATA_IDS


class TestCoaddOutputs(unittest.TestCase):
    """Check that coadd outputs are as expected.

    Many tests here are ported from
    https://github.com/lsst/pipe_tasks/blob/
    fd7d5e23d3c71e5d440153bc4faae7de9d5918c5/tests/nopytest_test_coadds.py
    """

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             instrument="HSC", skymap="discrete/ci_hsc",
                             writeable=False, collections=["HSC/runs/ci_hsc"])

        self._tract = 0
        self._patch = 69
        self._bands = ['r', 'i']

    def test_forced_id_names(self):
        """Test that forced photometry ID fields are named as expected
        (DM-8210).

        Specifically, coadd forced photometry should have only "id" and
        "parent" fields, while CCD forced photometry should have those,
        "objectId", and "parentObjectId".
        """
        coadd_schema = self.butler.get("deepCoadd_forced_src_schema").schema
        self.assertIn("id", coadd_schema)
        self.assertIn("parent", coadd_schema)
        self.assertNotIn("objectId", coadd_schema)
        self.assertNotIn("parentObjectId", coadd_schema)
        ccd_schema = self.butler.get("forced_src_schema").schema
        self.assertIn("id", ccd_schema)
        self.assertIn("parent", ccd_schema)
        self.assertIn("objectId", ccd_schema)
        self.assertIn("parentObjectId", ccd_schema)

    def test_alg_metadata_output(self):
        """Test to see if algorithm metadata is persisted correctly
        from MeasureMergedCoaddSourcesTask.
        """
        for band in self._bands:
            cat = self.butler.get(
                "deepCoadd_meas",
                band=band,
                tract=self._tract,
                patch=self._patch
            )
            meta = cat.getTable().getMetadata()
            for circ_aperture_flux_radius in meta.getArray('BASE_CIRCULARAPERTUREFLUX_RADII'):
                self.assertIsInstance(circ_aperture_flux_radius, numbers.Number)
            # Each time the run method of a measurement task is executed,
            # algorithm metadata is appended to the algorithm metadata object.
            # Depending on how many times a measurement task is run,
            # a metadata entry may be a single value or multiple values.
            for n_offset in meta.getArray('NOISE_OFFSET'):
                self.assertIsInstance(n_offset, numbers.Number)
            for noise_src in meta.getArray('NOISE_SOURCE'):
                self.assertEqual(noise_src, 'measure')
            for noise_exp_id in meta.getArray('NOISE_EXPOSURE_ID'):
                self.assertIsInstance(noise_exp_id, numbers.Number)
            for noise_seed_mul in meta.getArray('NOISE_SEED_MULTIPLIER'):
                self.assertIsInstance(noise_seed_mul, numbers.Number)

    def test_schema_consistency(self):
        """Test that _schema catalogs are consistent with the data catalogs."""
        det_schema = self.butler.get("deepCoadd_det_schema").schema
        meas_schema = self.butler.get("deepCoadd_meas_schema").schema
        mergeDet_schema = self.butler.get("deepCoadd_mergeDet_schema").schema
        ref_schema = self.butler.get("deepCoadd_ref_schema").schema
        coadd_forced_schema = self.butler.get("deepCoadd_forced_src_schema").schema
        ccd_forced_schema = self.butler.get("forced_src_schema").schema
        for band in self._bands:
            det = self.butler.get("deepCoadd_det", band=band, tract=self._tract, patch=self._patch)
            self.assertEqual(det.schema, det_schema)
            mergeDet = self.butler.get("deepCoadd_mergeDet", band=band, tract=self._tract, patch=self._patch)
            self.assertEqual(mergeDet.schema, mergeDet_schema)
            meas = self.butler.get("deepCoadd_meas", band=band, tract=self._tract, patch=self._patch)
            self.assertEqual(meas.schema, meas_schema)
            ref = self.butler.get("deepCoadd_ref", band=band, tract=self._tract, patch=self._patch)
            self.assertEqual(ref.schema, ref_schema)
            coadd_forced_src = self.butler.get(
                "deepCoadd_forced_src",
                band=band,
                tract=self._tract,
                patch=self._patch
            )
            self.assertEqual(coadd_forced_src.schema, coadd_forced_schema)
        ccd_forced_src = self.butler.get(
            "forced_src",
            tract=self._tract,
            visit=DATA_IDS[0]["visit"],
            detector=DATA_IDS[0]["detector"]
        )
        self.assertEqual(ccd_forced_src.schema, ccd_forced_schema)

    def test_coadd_transmission_curves(self):
        """Test that coadded TransmissionCurves agree with the inputs."""
        wavelengths = np.linspace(4000, 7000, 10)
        n_object_test = 10
        ctx = np.random.RandomState(12345)

        for band in self._bands:
            n_tested = 0
            exp = self.butler.get("deepCoadd_calexp", band=band, tract=self._tract, patch=self._patch)
            cat = self.butler.get("objectTable", band=band, tract=self._tract, patch=self._patch)
            transmission_curve = exp.getInfo().getTransmissionCurve()
            inputs = exp.getInfo().getCoaddInputs().ccds
            wcs = exp.getWcs()

            to_check = ctx.choice(len(cat), size=n_object_test, replace=False)
            for index in to_check:
                coadd_coord = geom.SpherePoint(cat["coord_ra"].values[index]*geom.degrees,
                                               cat["coord_dec"].values[index]*geom.degrees)
                summed_throughput = np.zeros(wavelengths.shape, dtype=np.float64)
                weight_sum = 0.0
                for rec in inputs.subsetContaining(coadd_coord, includeValidPolygon=True):
                    det_pos = rec.getWcs().skyToPixel(coadd_coord)
                    det_trans = rec.getTransmissionCurve()
                    weight = rec.get("weight")
                    summed_throughput += det_trans.sampleAt(det_pos, wavelengths)*weight
                    weight_sum += weight
                if weight_sum == 0.0:
                    continue
                summed_throughput /= weight_sum
                coadd_pos = wcs.skyToPixel(coadd_coord)
                coadd_throughput = transmission_curve.sampleAt(coadd_pos, wavelengths)
                np.testing.assert_array_almost_equal(coadd_throughput, summed_throughput)
                n_tested += 1
            self.assertGreater(n_tested, 5)

    def test_mask_planes_exist(self):
        """Test that the input mask planes have been added."""
        for data_id in DATA_IDS:
            mask = self.butler.get("calexp.mask", data_id)
            self.assertIn("CROSSTALK", mask.getMaskPlaneDict())
            self.assertIn("NOT_DEBLENDED", mask.getMaskPlaneDict())

    # Expected to fail until DM-5174 is fixed.
    @unittest.expectedFailure
    def test_masks_removed(self):
        """Test that certain mask planes have been removed from the coadds.

        This is expected to fail until DM-5174 is fixed.
        """
        for band in self._bands:
            mask = self.butler.get("deepCoadd_calexp.mask", band=band, tract=self._tract, patch=self._patch)
            self.assertNotIn("CROSSTALK", mask.getMaskPlaneDict())
            self.assertNotIn("NOT_DEBLENDED", mask.getMaskPlaneDict())

    def test_warp_inputs(self):
        """Test that the warps have the correct inputs."""
        skymap = self.butler.get("skyMap")
        tract_info = skymap[self._tract]
        for warp_type in ["directWarp", "psfMatchedWarp"]:
            datasets = set(self.butler.registry.queryDatasets(f"deepCoadd_{warp_type}"))
            # We only need to test one dataset
            dataset = list(datasets)[0]

            warp = self.butler.getDirect(dataset)
            self.assertEqual(warp.wcs, tract_info.wcs)
            inputs = warp.getInfo().getCoaddInputs()
            self.assertEqual(len(inputs.visits), 1)
            visit_record = inputs.visits[0]
            self.assertEqual(visit_record.getWcs(), warp.wcs)
            self.assertEqual(visit_record.getBBox(), warp.getBBox())
            self.assertGreater(len(inputs.ccds), 0)

            wcs_cat = self.butler.get(
                "jointcalSkyWcsCatalog",
                visit=visit_record.getId(),
                tract=self._tract
            )
            pc_cat = self.butler.get(
                "jointcalPhotoCalibCatalog",
                visit=visit_record.getId(),
                tract=self._tract
            )

            # We only need to test one input ccd
            det_record = inputs.ccds[0]
            exp_bbox = self.butler.get(
                "calexp.bbox",
                visit=det_record["visit"],
                detector=det_record["ccd"]
            )
            exp_psf = self.butler.get(
                "calexp.psf",
                visit=det_record["visit"],
                detector=det_record["ccd"]
            )
            self.assertEqual(det_record.getWcs(), wcs_cat.find(det_record["ccd"]).getWcs())
            self.assertEqual(
                det_record.getPhotoCalib(),
                pc_cat.find(det_record["ccd"]).getPhotoCalib()
            )
            self.assertEqual(det_record.getBBox(), exp_bbox)
            self.assertIsNotNone(det_record.getTransmissionCurve())
            center = det_record.getBBox().getCenter()
            # TODO: DM-XXXXX This needs to be updated to the "final" psf
            # when that is made the default.
            np.testing.assert_array_almost_equal(
                det_record.getPsf().computeKernelImage(center).array,
                exp_psf.computeKernelImage(center).array
            )

    def test_coadd_inputs(self):
        """Test that the coadds have the correct inputs."""
        skymap = self.butler.get("skyMap")
        tract_info = skymap[self._tract]
        for band in self._bands:
            wcs = self.butler.get("deepCoadd_calexp.wcs", band=band, tract=self._tract, patch=self._patch)
            self.assertEqual(wcs, tract_info.wcs)
            inputs = self.butler.get(
                "deepCoadd_calexp.coaddInputs",
                band=band,
                tract=self._tract,
                patch=self._patch
            )
            # We only need to test one input ccd
            det_record = inputs.ccds[0]
            wcs_cat = self.butler.get(
                "jointcalSkyWcsCatalog",
                visit=det_record["visit"],
                tract=self._tract
            )
            pc_cat = self.butler.get(
                "jointcalPhotoCalibCatalog",
                visit=det_record["visit"],
                tract=self._tract
            )
            exp_bbox = self.butler.get(
                "calexp.bbox",
                visit=det_record["visit"],
                detector=det_record["ccd"]
            )
            exp_psf = self.butler.get(
                "calexp.psf",
                visit=det_record["visit"],
                detector=det_record["ccd"]
            )
            self.assertEqual(det_record.getWcs(), wcs_cat.find(det_record["ccd"]).getWcs())
            self.assertEqual(det_record.getPhotoCalib(), pc_cat.find(det_record["ccd"]).getPhotoCalib())
            self.assertEqual(det_record.getBBox(), exp_bbox)
            self.assertIsNotNone(det_record.getTransmissionCurve())
            center = det_record.getBBox().getCenter()
            # TODO: DM-XXXXX This needs to be updated to the "final" psf
            # when that is made the default.
            np.testing.assert_array_almost_equal(
                det_record.getPsf().computeKernelImage(center).array,
                exp_psf.computeKernelImage(center).array
            )
            self.assertIsNotNone(inputs.visits.find(det_record["visit"]))

    def test_psf_installation(self):
        """Test that the coadd psf is installed."""
        for band in self._bands:
            wcs = self.butler.get("deepCoadd_calexp.wcs", band=band, tract=self._tract, patch=self._patch)
            inputs = self.butler.get(
                "deepCoadd_calexp.coaddInputs",
                band=band,
                tract=self._tract,
                patch=self._patch
            )
            coadd_psf = self.butler.get(
                "deepCoadd_calexp.psf",
                band=band,
                tract=self._tract,
                patch=self._patch
            )
            new_psf = lsst.meas.algorithms.CoaddPsf(inputs.ccds, wcs)
            self.assertEqual(coadd_psf.getComponentCount(), len(inputs.ccds))
            self.assertEqual(new_psf.getComponentCount(), len(inputs.ccds))
            for n, record in enumerate(inputs.ccds):
                center = record.getBBox().getCenter()
                np.testing.assert_array_almost_equal(
                    coadd_psf.getPsf(n).computeKernelImage(center).array,
                    record.getPsf().computeKernelImage(center).array
                )
                np.testing.assert_array_almost_equal(
                    new_psf.getPsf(n).computeKernelImage(center).array,
                    record.getPsf().computeKernelImage(center).array
                )
                self.assertEqual(coadd_psf.getWcs(n), record.getWcs())
                self.assertEqual(new_psf.getWcs(n), record.getWcs())
                self.assertEqual(coadd_psf.getBBox(n), record.getBBox())
                self.assertEqual(new_psf.getBBox(n), record.getBBox())

    def test_coadd_psf(self):
        """Test that the stars on the coadd are well represented by
        the attached PSF.
        """
        n_object_test = 10
        n_good_test = 5
        ctx = np.random.RandomState(12345)

        for band in self._bands:
            exp = self.butler.get("deepCoadd_calexp", band=band, tract=self._tract, patch=self._patch)
            coadd_psf = exp.getPsf()
            cat = self.butler.get("objectTable", band=band, tract=self._tract, patch=self._patch)

            star_cat = cat[(cat["i_extendedness"] < 0.5)
                           & (cat["detect_isPrimary"])
                           & (cat[f"{band}_psfFlux"] > 0.0)
                           & (cat[f"{band}_psfFlux"]/cat[f"{band}_psfFluxErr"] > 50.0)
                           & (cat[f"{band}_psfFlux"]/cat[f"{band}_psfFluxErr"] < 200.0)]

            to_check = ctx.choice(len(star_cat), size=n_object_test, replace=False)
            n_good = 0
            for index in to_check:
                position = geom.Point2D(star_cat["x"].values[index], star_cat["y"].values[index])
                psf_image = coadd_psf.computeImage(position)
                psf_image_bbox = psf_image.getBBox()
                star_image = lsst.afw.image.ImageF(
                    exp.maskedImage.image,
                    psf_image_bbox
                ).convertD()
                star_image /= star_image.array.sum()
                psf_image /= psf_image.array.sum()
                residuals = lsst.afw.image.ImageD(star_image, True)
                residuals -= psf_image
                # This is just a sanity check
                if np.max(np.abs(residuals.array)) < 0.01:
                    n_good += 1

            self.assertGreater(n_good, n_good_test)


if __name__ == "__main__":
    unittest.main()
