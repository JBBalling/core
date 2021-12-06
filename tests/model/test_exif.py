# -*- coding: utf-8 -*-

import sys

from PIL import Image, __version__ as pil_version

import pytest

from tests.base import assets

from ocrd_models import OcrdExif

pil_version_major, pil_version_minor = [
    int(x) for x in pil_version.split('.')][:2]
pil_below_83 = pil_version_major < 8 or (
    pil_version_major == 8 and pil_version_minor < 3)


@pytest.mark.parametrize("path,width,height,xResolution,yResolution,resolution,resolutionUnit,photometricInterpretation,compression", [
    ('SBB0000F29300010000/data/OCR-D-IMG/FILE_0001_IMAGE.tif',
     2875, 3749, 300, 300, 300, 'inches', 'RGB', 'jpeg'),
    ('kant_aufklaerung_1784-binarized/data/OCR-D-IMG-BIN/BIN_0020.png',
     1457, 2084, 295 if pil_below_83 else 294, 295 if pil_below_83 else 294, 295 if pil_below_83 else 294, 'inches', '1', None),
    ('scribo-test/data/OCR-D-PRE-BIN-SAUVOLA/OCR-D-PRE-BIN-SAUVOLA_0001-BIN_sauvola.png',
     2097, 3062, 1, 1, 1, 'inches', '1', None),
    ('leptonica_samples/data/OCR-D-IMG/OCR-D-IMG_1555_007.jpg',
     944, 1472, 1, 1, 1, 'inches', 'RGB', None),
    ('kant_aufklaerung_1784-jp2/data/OCR-D-IMG/INPUT_0020.jp2',
     1457, 2084, 1, 1, 1, 'inches', 'RGB', None)
])
def test_ocrd_exif(path, width, height, xResolution, yResolution, resolution, resolutionUnit, photometricInterpretation, compression):
    """Check EXIF attributes for different input formats
    * tiff
    * binarized png
    * png
    * jpg
    * jp2
    """

    with Image.open(assets.path_to(path)) as img:
        ocrd_exif = OcrdExif(img)
    assert ocrd_exif.width == width
    assert ocrd_exif.height == height
    assert ocrd_exif.xResolution == xResolution
    assert ocrd_exif.yResolution == yResolution
    assert ocrd_exif.resolution == resolution
    assert ocrd_exif.resolutionUnit == resolutionUnit
    assert ocrd_exif.photometricInterpretation == photometricInterpretation
    # pylint: disable=no-member
    assert ocrd_exif.compression == compression


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason="not platform-independent/stable")
def test_ocrd_exif_serialize_xml():
    with Image.open(assets.path_to('SBB0000F29300010000/data/OCR-D-IMG/FILE_0001_IMAGE.tif')) as img:
        exif = OcrdExif(img)
    expected = ('<exif>'
                '<width>2875</width>'
                '<height>3749</height>'
                '<photometricInterpretation>RGB</photometricInterpretation>'
                '<n_frames>1</n_frames>'
                '<compression>jpeg</compression>'
                '<photometric_interpretation>None</photometric_interpretation>'
                '<xResolution>300</xResolution>'
                '<yResolution>300</yResolution>'
                '<resolutionUnit>inches</resolutionUnit>'
                '<resolution>300</resolution>'
                '</exif>')
    assert expected == exif.to_xml()
