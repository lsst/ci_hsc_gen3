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

from lsst.ci.hsc.gen3 import (
    DATA_IDS,
    ASTROMETRY_FAILURE_DATA_IDS,
    INSUFFICIENT_TEMPLATE_COVERAGE_FAILURE_DATA_IDS,
)
from lsst.daf.butler import Butler, DataCoordinate
from lsst.pipe.base import QuantumGraph
import lsst.pipe.base.quantum_provenance_graph as qpg
from lsst.utils import getPackageDir


def to_set_of_tuples(list_of_dicts):
    """Convert a list of dictionary {visit, detector} data IDs into a set of
    (visit, detector) tuples
    """
    return {(d["visit"], d["detector"]) for d in list_of_dicts}


class TestValidateOutputs(unittest.TestCase):
    """Check that ci_hsc_gen3 outputs are as expected."""

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             instrument="HSC", skymap="discrete/ci_hsc",
                             writeable=False, collections=["HSC/runs/ci_hsc"])

        self._raws = to_set_of_tuples(DATA_IDS)
        self._forced_astrom_failures = to_set_of_tuples(ASTROMETRY_FAILURE_DATA_IDS)
        # Four detectors have template coverage < 0.2 soft limit, but two
        # succeed anyway.  These are just the failures.
        self._insufficient_template_coverage_failures = to_set_of_tuples(
            INSUFFICIENT_TEMPLATE_COVERAGE_FAILURE_DATA_IDS
        )
        self._num_visits = len({data_id["visit"] for data_id in DATA_IDS})
        self._num_tracts = 1
        self._num_patches = 1
        self._num_bands = len({data_id["physical_filter"] for data_id in DATA_IDS})
        self._min_sources = 100
        # Check that DIA catalogs have nonzero length
        self._min_diasources = 0

    def check_pipetasks(self, names, n_metadata, n_log):
        """Check general pipetask outputs (metadata, log, config).

        Parameters
        ----------
        names : `list` [`str`]
            Task label names.
        n_metadata : `int`
            Number of expected metadata quanta.
        n_log : `int`
            Number of expected log quanta
        """
        for name in names:
            self.check_datasets([f"{name}_config"], 1)
            self.check_datasets([f"{name}_metadata"], n_metadata)
            self.check_datasets([f"{name}_log"], n_log)

    def check_datasets(self, dataset_types, n_expected, max_expected=None, additional_checks=[], **kwargs):
        """Check dataset existence, and run additional checks.

        Parameters
        ----------
        dataset_types : `list` [`str`]
            List of dataset types to check.
        n_expected : `int`
            Number of each dataset_type expected in repo.
            If `max_expected` is not `None` then this is the lower
            bound on the number of datasets.
        max_expected : `int`
            Maximum number of each dataset_type expected in repo.
        additional_checks : `list` [`func`], optional
            List of additional check functions to run on each dataset.
        **kwargs : `dict`, optional
            Additional keywords to send to ``additional_checks``.
        """
        for dataset_type in dataset_types:

            datasets = set(self.butler.registry.queryDatasets(dataset_type))

            if max_expected is not None:
                self.assertGreaterEqual(len(datasets), n_expected, msg=f"Number of {dataset_type}")
                self.assertLessEqual(len(datasets), max_expected, msg=f"Number of {dataset_type}")
            else:
                self.assertEqual(len(datasets), n_expected, msg=f"Number of {dataset_type}")

            stored = self.butler.stored_many(datasets)
            for dataset in datasets:
                self.assertTrue(stored[dataset], msg=f"File exists for {dataset}")

                if additional_checks:
                    data = self.butler.get(dataset)
                    for additional_check in additional_checks:
                        additional_check(data, **kwargs)

    def check_sources(self, source_dataset_types, n_expected, min_src,
                      max_expected=None, additional_checks=[], **kwargs):
        """Check that the source catalogs have enough sources and
        run additional checks.

        Parameters
        ----------
        dataset_types : `list` [`str`]
            List of dataset types to check.
        n_expected : `int`
            Number of each dataset_type expected in repo.
            If `max_expected` is not `None` then this is the lower
            bound on the number of datasets.
        max_expected : `int`
            Maximum number of each dataset_type expected in repo.
        min_src : `int`
            Minimum number of sources for each dataset.
        additional_checks : `list` [`func`], optional
            List of additional check functions to run on each dataset.
        **kwargs : `dict`, optional
            Additional keywords to send to ``additional_checks``.
        """
        for source_dataset_type in source_dataset_types:

            datasets = set(self.butler.registry.queryDatasets(source_dataset_type))

            if max_expected is None:
                self.assertEqual(len(datasets), n_expected, msg=f"Number of {source_dataset_type}")
            else:
                self.assertGreaterEqual(len(datasets), n_expected, msg=f"Number of {source_dataset_type}")
                self.assertLessEqual(len(datasets), max_expected, msg=f"Number of {source_dataset_type}")

            for dataset in datasets:
                catalog = self.butler.get(dataset)
                self.assertGreater(len(catalog), min_src, msg=f"Number of sources in {dataset}")

                for additional_check in additional_checks:
                    additional_check(catalog, **kwargs)

    def test_raw(self):
        """Test existence of raw exposures."""
        self.check_datasets(["raw"], len(self._raws))

    def test_isr_calibrateImage(self):
        """Test existence of isr/calibration related files."""
        self.check_pipetasks(
            ["isr", "calibrateImage"],
            len(self._raws),
            len(self._raws)
        )
        self.check_datasets(
            ["postISRCCD", "calexp", "calexpBackground"],
            len(self._raws)
        )
        self.check_datasets(["src_schema"], 1)
        self.check_sources(
            ["src"],
            len(self._raws),
            self._min_sources,
            additional_checks=[self.check_aperture_corrections,
                               self.check_psf_stars_and_flags]
        )

    def test_source_tables(self):
        """Test existence of source tables."""
        self.check_pipetasks(
            ["reprocessVisitImage", "transformSourceTable"],
            len(self._raws),
            len(self._raws)
        )
        self.check_pipetasks(["consolidateSourceTable"], self._num_visits, self._num_visits)
        self.check_sources(["sourceTable"], len(self._raws), self._min_sources)
        self.check_sources(["sourceTable_visit"], self._num_visits, self._min_sources)

    def test_visit_summary(self):
        """Test existence of visit summaries."""
        self.check_pipetasks(["consolidateVisitSummary"], self._num_visits, self._num_visits)
        self.check_datasets(["visitSummary"], self._num_visits)

    def test_isolated_star_association(self):
        """Test existence of isolated star tables."""
        self.check_pipetasks(["isolatedStarAssociation"], self._num_tracts, self._num_tracts)
        self.check_datasets(
            ["isolated_star_presource_associations", "isolated_star_presources"],
            self._num_tracts
        )

    def test_consolidate_finalize_characterization(self):
        """Test existence of finalized characterization outputs."""
        self.check_pipetasks(["consolidateFinalizeCharacterization"], self._num_visits, self._num_visits)
        self.check_datasets(
            ["finalized_psf_ap_corr_catalog", "finalized_src_table"],
            self._num_visits
        )

    def test_make_tables(self):
        """Test existence of ccd and visit tables."""
        self.check_pipetasks(["makeCcdVisitTable", "makeVisitTable"], 1, 1)
        self.check_datasets(["ccdVisitTable", "visitTable"], 1)

    def test_make_direct_warp(self):
        """Test existence of direct warps."""
        self.check_pipetasks(["makeDirectWarp"], self._num_visits, self._num_visits)
        self.check_datasets(["deepCoadd_directWarp"], self._num_visits)

    def test_make_psfMatched_warp(self):
        """Test existence of PSF-matched warps."""
        self.check_pipetasks(["makePsfMatchedWarp"], self._num_visits, self._num_visits)
        self.check_datasets(["deepCoadd_psfMatchedWarp"], self._num_visits)

    def test_assemble_coadd(self):
        """Test existence of coadds."""

        def check_bright_star_mask(coadd):
            mask = coadd.getMaskedImage().getMask()
            mask_val = mask.getPlaneBitMask("BRIGHT_OBJECT")
            num_bright = (mask.getArray() & mask_val).sum()
            self.assertGreater(num_bright, 0, msg="Some pixels are masked as BRIGHT_OBJECT")

        def check_transmission_curves(coadd):
            self.assertTrue(coadd.getInfo().getTransmissionCurve() is not None,
                            msg="TransmissionCurves are attached to coadds")

        n_output = self._num_patches*self._num_bands
        self.check_pipetasks(["assembleCoadd"], n_output, n_output)
        self.check_datasets(
            ["deepCoadd"],
            n_output,
            additional_checks=[check_bright_star_mask,
                               check_transmission_curves]
        )

    def test_healsparse_property_maps(self):
        """Test existence of healsparse property maps."""
        self.check_pipetasks(
            ["healSparsePropertyMaps"],
            self._num_tracts*self._num_bands,
            self._num_tracts*self._num_bands
        )
        self.check_pipetasks(["consolidateHealSparsePropertyMaps"], self._num_bands, self._num_bands)
        self.check_datasets(
            ["deepCoadd_dcr_ddec_map_weighted_mean",
             "deepCoadd_dcr_dra_map_weighted_mean",
             "deepCoadd_dcr_e1_map_weighted_mean",
             "deepCoadd_dcr_e2_map_weighted_mean",
             "deepCoadd_exposure_time_map_sum",
             "deepCoadd_psf_e1_map_weighted_mean",
             "deepCoadd_psf_e2_map_weighted_mean",
             "deepCoadd_psf_maglim_map_weighted_mean",
             "deepCoadd_psf_size_map_weighted_mean",
             "deepCoadd_sky_background_map_weighted_mean",
             "deepCoadd_sky_noise_map_weighted_mean",
             "deepCoadd_epoch_map_mean",
             "deepCoadd_epoch_map_min",
             "deepCoadd_epoch_map_max"],
            self._num_tracts*self._num_bands
        )
        self.check_datasets(
            ["deepCoadd_dcr_ddec_consolidated_map_weighted_mean",
             "deepCoadd_dcr_dra_consolidated_map_weighted_mean",
             "deepCoadd_dcr_e1_consolidated_map_weighted_mean",
             "deepCoadd_dcr_e2_consolidated_map_weighted_mean",
             "deepCoadd_exposure_time_consolidated_map_sum",
             "deepCoadd_psf_e1_consolidated_map_weighted_mean",
             "deepCoadd_psf_e2_consolidated_map_weighted_mean",
             "deepCoadd_psf_maglim_consolidated_map_weighted_mean",
             "deepCoadd_psf_size_consolidated_map_weighted_mean",
             "deepCoadd_sky_background_consolidated_map_weighted_mean",
             "deepCoadd_sky_noise_consolidated_map_weighted_mean",
             "deepCoadd_epoch_consolidated_map_mean",
             "deepCoadd_epoch_consolidated_map_min",
             "deepCoadd_epoch_consolidated_map_max"],
            self._num_bands
        )

    def check_strip_footprints(self, catalog):
        """Test that heavy footprints were stripped from the catalog."""
        children = catalog[catalog["parent"] != 0]
        for child in children:
            self.assertEqual(child.getFootprint(), None)

    def test_coadd_detection(self):
        """Test existence of coadd detection catalogs."""
        n_output = self._num_patches*self._num_bands
        self.check_pipetasks(["detection", "measure"], n_output, n_output)
        self.check_pipetasks(["mergeDetections", "deblend", "mergeMeasurements"], 1, 1)
        self.check_datasets(
            ["deepCoadd_calexp",
             "deepCoadd_calexp_background"],
            n_output
        )
        self.check_datasets(["deepCoadd_calexp"], self._num_patches*self._num_bands)
        self.check_sources(
            ["deepCoadd_det",
             "deepCoadd_meas"],
            n_output,
            self._min_sources,
            additional_checks=[self.check_strip_footprints]
        )

        self.check_sources(
            ["deepCoadd_deblendedCatalog"],
            self._num_patches,
            self._min_sources
        )

        self.check_datasets(
            ["deepCoadd_scarletModelData"],
            self._num_patches,
        )

        def check_propagated_flags(catalog, **kwargs):
            self.assertTrue("calib_psf_candidate" in catalog.schema,
                            msg="calib_psf_candidate field exists in deepCoadd_meas catalog")
            self.assertTrue("calib_psf_used" in catalog.schema,
                            msg="calib_psf_used field exists in deepCoadd_meas catalog")
            self.assertTrue("calib_astrometry_used" in catalog.schema,
                            msg="calib_astrometry_used field exists in deepCoadd_meas catalog")
            self.assertTrue("calib_photometry_used" in catalog.schema,
                            msg="calib_photometry_used field exists in deepCoadd_meas catalog")
            self.assertTrue("calib_psf_reserved" in catalog.schema,
                            msg="calib_psf_reserved field exists in deepCoadd_meas catalog")

        def check_failed_children(catalog, **kwargs):
            children_failed = []
            for column in catalog.schema:
                if column.field.getName().startswith("merge_footprint"):
                    for parent in catalog.getChildren(0):
                        for child in catalog.getChildren(parent.getId()):
                            if child[column.key] != parent[column.key]:
                                children_failed.append(child.getId())

            self.assertEqual(len(children_failed), 0,
                             msg=f"merge_footprint from parent propagated to children {children_failed}")

        def check_deepcoadd_stellar_fraction(catalog):
            # Check that at least 90% of the stars we used to model the PSF end
            # up classified as stars on the coadd.  We certainly need much more
            # purity than that to build good PSF models, but this should verify
            # that flag propagation, aperture correction, and extendendess are
            # all running and configured reasonably (but it may not be
            # sensitive enough to detect subtle bugs).
            # 2020-1-13: There is an issue with the PSF that was
            # identified in DM-28294 and will be fixed in DM-12058,
            # which affects scarlet i-band models. So we set the
            # minStellarFraction based on the deblender and band used.
            # TODO: Once DM-12058 is merged this band-aid can be removed.
            min_stellar_fraction = 0.9
            if "deblend_scarletFlux" in catalog.schema.getNames():
                min_stellar_fraction = 0.7
            self.check_psf_stars_and_flags(
                catalog,
                min_stellar_fraction=min_stellar_fraction,
                do_check_flags=False
            )

        self.check_sources(
            ["deepCoadd_meas"],
            n_output,
            self._min_sources,
            additional_checks=[self.check_aperture_corrections,
                               check_propagated_flags,
                               check_failed_children,
                               check_deepcoadd_stellar_fraction]
        )

        self.check_sources(["deepCoadd_ref", "deepCoadd_mergeDet"], self._num_patches, self._min_sources)

        self.check_datasets(
            ["deepCoadd_det_schema",
             "deepCoadd_meas_schema",
             "deepCoadd_mergeDet_schema",
             "deepCoadd_peak_schema",
             "deepCoadd_ref_schema"],
            1
        )

    def test_object_tables(self):
        """Test existence of object tables."""
        self.check_pipetasks(
            ["writeObjectTable", "transformObjectTable"],
            self._num_patches,
            self._num_patches
        )
        self.check_pipetasks(["consolidateObjectTable"], self._num_tracts, self._num_tracts)
        self.check_datasets(
            ["deepCoadd_obj",
             "objectTable"],
            self._num_patches
        )
        self.check_datasets(
            ["objectTable_tract"],
            self._num_tracts
        )

    def test_reprocess_visit_image(self):
        """Test the existence of ReprocessVisitImageTask's outputs."""
        # While the external WCS files might someday let us recover from the
        # forced astrometry failures at this stage, at present that failure
        # prevents isolated star association for generating matches for this
        # detector, and that prevents the second round of PSF determination and
        # aperture correction from working.  This manifests as an
        # UpstreamFailureNoWorkFound, and hence we expect metadata outputs but
        # not source catalogs or PVIs for the forced-failure data IDs.
        self.check_pipetasks(["reprocessVisitImage"], len(self._raws), len(self._raws))
        self.check_sources(
            ["sources_footprints_detector"],
            len(self._raws - self._forced_astrom_failures),
            self._min_sources,
            additional_checks=[self.check_aperture_corrections]
        )
        self.check_datasets(["sources_schema"], 1)
        self.check_datasets(["pvi", "pvi_background"], len(self._raws - self._forced_astrom_failures))

    def test_forced_phot_detector(self):
        """Test existence of forced photometry tables (sources)."""
        # Lack of PVI (from reprocessVisitImage) leads to NoWorkFound for the
        # forced astrometry failure data IDs, which affects regular-output
        # counts, but not logs or metadata.
        self.check_pipetasks(["forcedPhotObjectDetector"], len(self._raws), len(self._raws))
        self.check_sources(
            ["mergedForcedSource"],
            len(self._raws - self._insufficient_template_coverage_failures - self._forced_astrom_failures),
            self._min_sources,
            additional_checks=[self.check_dataframe_aperture_corrections],
            # We only measure psfFlux in single-detector forced photometry.
            aperture_algorithms=("base_PsfFlux", ),
        )
        self.check_datasets(
            ["mergedForcedSource"],
            len(self._raws - self._forced_astrom_failures - self._insufficient_template_coverage_failures)
        )

    def test_forced_phot_coadd(self):
        """Test existence of forced photometry tables (objects)."""
        n_output = self._num_patches*self._num_bands
        self.check_pipetasks(["forcedPhotCoadd"], n_output, n_output)
        self.check_sources(
            ["deepCoadd_forced_src"],
            n_output,
            self._min_sources,
            additional_checks=[self.check_aperture_corrections, self.check_strip_footprints]
        )

    def test_forced_phot_dia(self):
        """Test existence of forced photometry tables (dia)."""
        # Lack of PVI (from reprocessVisitImage) leads to NoWorkFound for the
        # forced astrometry failure data IDs, which affects regular-output
        # counts, but not logs or metadata.
        self.check_pipetasks(
            ["forcedPhotDiaObjectDetector"],
            len(self._raws),
            len(self._raws),
        )
        self.check_sources(
            ["mergedForcedSourceOnDiaObject"],
            len(self._raws - self._insufficient_template_coverage_failures - self._forced_astrom_failures),
            self._min_diasources,
            max_expected=len(self._raws - self._forced_astrom_failures),
        )

    def test_templates(self):
        """Test existence of templates."""
        self.check_pipetasks(["buildTemplate"], len(self._raws), len(self._raws))
        self.check_pipetasks(
            ["templateGen", "selectGoodSeeingVisits"],
            self._num_patches*self._num_bands,
            self._num_patches*self._num_bands
        )
        # No templates get produced for the detectors with astrometry failures
        self.check_datasets(
            ["goodSeeingDiff_templateExp"],
            len(self._raws - self._forced_astrom_failures),
        )
        self.check_datasets(["goodSeeingDiff_diaSrc_schema"], 1)

    def test_image_difference(self):
        """Test existence of image differences."""
        self.check_pipetasks(
            ["subtractImages", "detectAndMeasureDiaSources"],
            len(self._raws),
            len(self._raws)
        )
        # Lack of PVI (from reprocessVisitImage) leads to NoWorkFound for the
        # forced astrometry failure data IDs, which affects regular-output
        # counts, but not logs or metadata.
        self.check_datasets(
            ["goodSeeingDiff_differenceExp"],
            len(self._raws - self._insufficient_template_coverage_failures - self._forced_astrom_failures),
            max_expected=len(self._raws - self._forced_astrom_failures),
        )
        self.check_datasets(["goodSeeingDiff_diaSrc_schema"], 1)

    def test_dia_source_tables(self):
        """Test existence of dia source tables."""
        self.check_pipetasks(["consolidateAssocDiaSourceTable"], 1, 1)
        self.check_pipetasks(["consolidateDiaSourceTable"], self._num_visits, self._num_visits)
        self.check_sources(["diaSourceTable"], self._num_visits, self._min_diasources)
        self.check_sources(["diaSourceTable_tract"], self._num_tracts, self._min_diasources)

    def test_forced_source_tables(self):
        """Test existence of forces source tables."""
        self.check_pipetasks(
            ["transformForcedSourceTable",
             "transformForcedSourceOnDiaObjectTable",
             "consolidateForcedSourceTable",
             "consolidateForcedSourceOnDiaObjectTable"],
            1,
            1
        )

    def test_skymap(self):
        """Test existence of skymap."""
        self.check_datasets(["skyMap"], 1)

    def test_skycorr(self):
        """Test existence of skycorr."""
        self.check_pipetasks(["skyCorr"], self._num_visits, self._num_visits)
        self.check_datasets(["skyCorr"], len(self._raws))

    def check_aperture_corrections(self, catalog, aperture_algorithms=("base_PsfFlux", "base_GaussianFlux"),
                                   **kwargs):
        for alg in aperture_algorithms:
            self.assertTrue(f"{alg}_apCorr" in catalog.schema, msg=f"{alg}_apCorr in schema")
            self.assertTrue(f"{alg}_apCorrErr" in catalog.schema, msg=f"{alg}_apCorrErr in schema")
            self.assertTrue(f"{alg}_flag_apCorr" in catalog.schema, msg=f"{alg}_flag_apCorr in schema")

    def check_dataframe_aperture_corrections(
        self,
        dataframe,
        aperture_algorithms=("base_PsfFlux", "base_GaussianFlux"),
        **kwargs,
    ):
        for alg in aperture_algorithms:
            self.assertTrue(
                f"{alg}_apCorr" in dataframe.columns.levels[1],
                msg=f"{alg}_apCorr in columns",
            )
            self.assertTrue(
                f"{alg}_apCorrErr" in dataframe.columns.levels[1],
                msg=f"{alg}_apCorrErr in columns",
            )
            self.assertTrue(
                f"{alg}_flag_apCorr" in dataframe.columns.levels[1],
                msg=f"{alg}_flag_apCorr in columns",
            )

    def check_psf_stars_and_flags(self, catalog, min_stellar_fraction=0.95, do_check_flags=True, **kwargs):
        primary = catalog["detect_isPrimary"]

        psf_stars_used = catalog["calib_psf_used"] & primary

        ext_stars = catalog["base_ClassificationExtendedness_value"] < 0.5
        self.assertGreater(
            (ext_stars & psf_stars_used).sum(),
            min_stellar_fraction*psf_stars_used.sum(),
            msg=f"At least {min_stellar_fraction} of PSF sources are classified as stars"
        )

        if do_check_flags:
            psf_stars_reserved = catalog["calib_psf_reserved"]
            psf_stars_candidate = catalog["calib_psf_candidate"]
            self.assertGreaterEqual(
                psf_stars_candidate.sum(),
                psf_stars_used.sum() + psf_stars_reserved.sum(),
                msg="Number of candidate PSF stars >= sum of used and reserved stars"
            )

    def test_qg_datasets(self):
        """Test that the datasets predicted by the QG were actually produced,
        except in the few cases where we expect NoWorkFound to have been
        raised.
        """
        qg = QuantumGraph.loadUri("ci_hsc.qg")
        prov = qpg.QuantumProvenanceGraph()
        prov.assemble_quantum_provenance_graph(self.butler, [qg])
        # Identify the quanta that we expect to be affected by the expected
        # success caveats (NoWorkFound etc): quanta downstream of the failures
        # themselves that have the same {visit, detector}; note that this does
        # not include visit-level aggregates that are downstream (or any other
        # kind of downstream aggregate).
        expected_keys_with_caveats: set[qpg.QuantumKey | qpg.DatasetKey] = set()
        for task_label, exc_type, dict_data_ids in [
            ("calibrateImage", "lsst.meas.astrom.exceptions.BadAstrometryFit", ASTROMETRY_FAILURE_DATA_IDS),
            ("subtractImages", None, INSUFFICIENT_TEMPLATE_COVERAGE_FAILURE_DATA_IDS),
        ]:
            dimensions = qg.pipeline_graph.tasks[task_label].dimensions
            for dict_data_id in dict_data_ids:
                data_id = DataCoordinate.standardize(dict_data_id, dimensions=dimensions, instrument="HSC")
                quantum_key = qpg.QuantumKey(task_label, data_id.required_values)
                _, quantum_run = qpg.QuantumRun.find_final(prov.get_quantum_info(quantum_key))
                if exc_type is not None:
                    self.assertEqual(quantum_run.exception.type_name, exc_type)
                else:
                    self.assertIsNone(quantum_run.exception)
                expected_keys_with_caveats.add(quantum_key)
                for downstream_key, downstream_info in prov.iter_downstream(quantum_key):
                    downstream_data_id = downstream_info["data_id"]
                    if (
                        "visit" in downstream_data_id.dimensions.names
                        and "detector" in downstream_data_id
                        and downstream_data_id["visit"] == data_id["visit"]
                        and downstream_data_id["detector"] == data_id["detector"]
                    ):
                        expected_keys_with_caveats.add(downstream_key)
        for task_label, quanta in prov.quanta.items():
            for quantum_key in quanta:
                quantum_info = prov.get_quantum_info(quantum_key)
                _, quantum_run = qpg.QuantumRun.find_final(prov.get_quantum_info(quantum_key))
                if quantum_run.caveats and quantum_key not in expected_keys_with_caveats:
                    not_produced = [
                        f"{dataset_key.dataset_type_name}@{dataset_info['data_id']}"
                        for dataset_key in prov.iter_outputs_of(quantum_key)
                        if (
                            (dataset_info := prov.get_dataset_info(dataset_key))["status"]
                            == qpg.DatasetInfoStatus.PREDICTED_ONLY
                        )
                    ]
                    raise AssertionError(
                        f"{quantum_key.task_label}@{quantum_info['data_id']} should not have caveats "
                        f"{quantum_info.caveats}; missing datasets: {', '.join(not_produced)}."
                    )


if __name__ == "__main__":
    unittest.main()
