#!/usr/bin/env sh
COLLECTION=shared/ci_hsc_output

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
pipetask -d "patch.patch = 69" -j "$1" -b "$CI_HSC_GEN3_DIR"/butler.yaml -p lsst.meas.base -p lsst.ip.isr -p \
lsst.pipe.tasks -i calib,shared/ci_hsc -o "$COLLECTION" run \
--register-dataset-types \
-t isrTask.IsrTask:isr -C isr:"$CI_HSC_GEN3_DIR"/configs/isr.py \
-t characterizeImage.CharacterizeImageTask:cit -C cit:"$CI_HSC_GEN3_DIR"/configs/charImage.py \
-t calibrate.CalibrateTask:ct -C ct:"$CI_HSC_GEN3_DIR"/configs/calibrate.py \
-t makeCoaddTempExp.MakeWarpTask:mwt -C mwt:"$CI_HSC_GEN3_DIR"/configs/makeWarp.py \
-t assembleCoadd.CompareWarpAssembleCoaddTask:cwact -C cwact:"$CI_HSC_GEN3_DIR"/configs/compareWarpAssembleCoadd.py \
-t multiBand.DetectCoaddSourcesTask:dcst -C dcst:"$CI_HSC_GEN3_DIR"/configs/detectCoaddSources.py \
-t mergeDetections.MergeDetectionsTask:mdt -C mdt:"$CI_HSC_GEN3_DIR"/configs/mergeCoaddDetections.py \
-t deblendCoaddSourcesPipeline.DeblendCoaddSourcesSingleTask:dcsst -C dcsst:"$CI_HSC_GEN3_DIR"/configs/deblendCoaddSourcesSingle.py \
-t multiBand.MeasureMergedCoaddSourcesTask:mmcst -C mmcst:"$CI_HSC_GEN3_DIR"/configs/measureCoaddSources.py \
-t mergeMeasurements.MergeMeasurementsTask:mmt -C mmt:"$CI_HSC_GEN3_DIR"/configs/mergeCoaddMeasurements.py \
-t forcedPhotCcd.ForcedPhotCcdTask:fpccdt -C fpccdt:"$CI_HSC_GEN3_DIR"/configs/forcedPhotCcd.py \
-t forcedPhotCoadd.ForcedPhotCoaddTask:fpct -C fpct:"$CI_HSC_GEN3_DIR"/configs/forcedPhotCoadd.py \
