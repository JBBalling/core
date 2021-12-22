# -*- coding: utf-8 -*-

import os
import shutil

from pathlib import (
    Path
)
from unittest import (
    mock
)
from PIL import (
    Image
)

from ocrd_models.ocrd_page import OcrdPage

import pytest

from tests.base import (
    assets, 
    main
)

from ocrd.resolver import Resolver
from ocrd_utils import pushd_popd

from ocrd_modelfactory import (
    page_from_file
)


# set pylint once on module level
# pylint: disable=protected-access

METS_HEROLD = assets.url_of('SBB0000F29300010000/data/mets.xml')
FOLDER_KANT = assets.path_to('kant_aufklaerung_1784')
DATA_KANT = {'mets.xml': (os.path.join(FOLDER_KANT, 'data', 'mets.xml'), 'text/xml'),
             'INPUT_0017.tif': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-IMG', 'INPUT_0017.tif'), 'image/tiff'),
             'INPUT_0020.tif': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-IMG', 'INPUT_0020.tif'), 'image/tiff'),
             'PAGE_0017_ALTO.xml': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-GT-ALTO', 'PAGE_0017_ALTO.xml'), 'text/xml'),
             'PAGE_0020_ALTO.xml': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-GT-ALTO', 'PAGE_0020_ALTO.xml'), 'text/xml'),
             'PAGE_0017_PAGE.xml': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-GT-PAGE', 'PAGE_0017_PAGE.xml'), 'text/xml'),
             'PAGE_0020_PAGE.xml': (os.path.join(FOLDER_KANT, 'data', 'OCR-D-GT-PAGE', 'PAGE_0020_PAGE.xml'), 'text/xml'),
             }


def _get_kant_data(key):
    if key in DATA_KANT.keys():
        (path, mime) = DATA_KANT[key]
        with open(path, mode='rb') as _file:
            return (_file.read(), mime)


def request_behavior(*args):
    resp = mock.Mock()
    resp.status_code = 200
    resp.headers = {}
    the_key = args[0].split('/')[-1]
    if the_key in DATA_KANT:
        (cnt, mime) = _get_kant_data(the_key)
        resp.content = cnt
        resp.headers = {'Content-Type': mime}
    return resp


def test_workspace_from_url_bad():
    with pytest.raises(Exception) as exc:
        Resolver().workspace_from_url(None)

    # check exception
    assert "Must pass 'mets_url'" in str(exc)


@mock.patch("requests.get")
def test_workspace_from_url_kant(mock_request, tmp_path):

    # arrange
    url_src = 'https://raw.githubusercontent.com/OCR-D/assets/master/data/kant_aufklaerung_1784/data/mets.xml'
    mock_request.side_effect = request_behavior
    dst_dir = tmp_path / 'workspace_kant'
    dst_dir.mkdir()

    # act
    resolver = Resolver()
    resolver.workspace_from_url(
        url_src, mets_basename='foo.xml', dst_dir=dst_dir)

    # assert
    local_path = dst_dir / 'foo.xml'
    assert os.path.isfile(str(local_path))
    # 1 time data was requested
    assert mock_request.call_count == 1


@mock.patch("requests.get")
def test_workspace_from_url_kant_with_resources(mock_request, tmp_path):

    # arrange
    url_src = 'https://raw.githubusercontent.com/OCR-D/assets/master/data/kant_aufklaerung_1784/data/mets.xml'
    mock_request.side_effect = request_behavior
    dst_dir = tmp_path / 'workspace_kant'
    dst_dir.mkdir()

    # act
    resolver = Resolver()
    resolver.workspace_from_url(
        url_src,
        mets_basename='kant_aufklaerung_1784.xml',
        dst_dir=dst_dir,
        download=True)

    # assert files present under local tmp_path
    local_path_mets = dst_dir / 'kant_aufklaerung_1784.xml'
    assert os.path.isfile(str(local_path_mets))
    local_path_img1 = dst_dir / 'OCR-D-IMG' / 'INPUT_0017.tif'
    assert os.path.isfile(str(local_path_img1))
    local_path_page1 = dst_dir / 'OCR-D-GT-PAGE' / 'PAGE_0017_PAGE.xml'
    assert os.path.isfile(str(local_path_page1))

    # 1 METS/MODS + 2 images + 4 OCR files = 7 requests
    assert mock_request.call_count == 7


@mock.patch("requests.get")
def test_workspace_from_url_kant_with_resources_existing_local(mock_request, tmp_path):

    # arrange
    url_src = 'https://raw.githubusercontent.com/OCR-D/assets/master/data/kant_aufklaerung_1784/data/mets.xml'
    mock_request.side_effect = request_behavior
    dst_dir = tmp_path / 'workspace_kant'
    dst_dir.mkdir()
    src_mets = Path(assets.path_to(
        'kant_aufklaerung_1784-binarized/data/mets.xml'))
    dst_mets = Path(dst_dir, 'mets.xml')
    shutil.copyfile(src_mets, dst_mets)

    # act
    Resolver().workspace_from_url(url_src,
                                  clobber_mets=False,
                                  dst_dir=dst_dir)

    # assert
    # no real request was made, since mets already present
    assert mock_request.call_count == 0


@mock.patch("requests.get")
def test_workspace_from_url_404(mock_request):
    """Expected behavior when try create workspace from invalid online target
    """

    # arrange
    url_404 = 'https://raw.githubusercontent.com/OCR-D/assets/master/data/kant_aufklaerung_1784/data/mets.xmlX'
    mock_request.side_effect = Exception('HTTP request failed')

    with pytest.raises(Exception) as exc:
        Resolver().workspace_from_url(mets_url=url_404)

    # assert
    assert "HTTP request failed" in str(exc)
    assert mock_request.call_count == 1


def test_workspace_from_url_with_rel_dir(tmp_path):
    bogus_dst_dir = '../../../../../../../../../../../../../../../../%s' % str(tmp_path)[
        1:]

    # act
    with pushd_popd(FOLDER_KANT):
        ws1 = Resolver().workspace_from_url('data/mets.xml', dst_dir=bogus_dst_dir)

    # assert
    assert os.path.join(tmp_path, 'mets.xml') == ws1.mets_target
    assert str(tmp_path) == ws1.directory


def test_workspace_from_url0():

    # act
    workspace = Resolver().workspace_from_url(METS_HEROLD)
    input_files = workspace.mets.find_all_files(fileGrp='OCR-D-IMG')
    image_file = input_files[0]
    f = workspace.download_file(image_file)

    # assert
    assert '%s.tif' % f.ID == 'FILE_0001_IMAGE.tif'
    assert f.local_filename == 'OCR-D-IMG/FILE_0001_IMAGE.tif'


def test_resolve_image0():
    workspace = Resolver().workspace_from_url(METS_HEROLD)
    input_files = workspace.mets.find_all_files(fileGrp='OCR-D-IMG')
    f = input_files[0]
    img_pil1 = workspace._resolve_image_as_pil(f.url)
    assert img_pil1.size == (2875, 3749)
    img_pil2 = workspace._resolve_image_as_pil(f.url, [[0, 0], [1, 1]])
    assert img_pil2.size == (1, 1)


# @pytest.mark.skip(reason='usage unclear - neither #image_from_page nor #image_from_segment are drop-in replacements')
@pytest.mark.parametrize(
    "image_url,data_key,page_id,size1,size2",
    [('OCR-D-IMG-NRM/OCR-D-IMG-NRM_0017.png', 'INPUT_0017.tif', 'P_0017', (1457, 2083), (1, 1)),
     ('OCR-D-IMG-1BIT/OCR-D-IMG-1BIT_0017.png', 'INPUT_0020.tif', 'P_0020', (1457, 2083), (1, 1)),
     ])
def test_resolve_image_grayscale(image_url, data_key, page_id, size1, size2):
    url_path = assets.url_of('kant_aufklaerung_1784-binarized/data/mets.xml')
    workspace = Resolver().workspace_from_url(url_path)
    pil_image = Image(url_path)
    img_pil1 = workspace.image_from_segment('segment', pil_image, [[0, 0], [size1[0], size1[1]]])
    assert img_pil1.size == size1
    img_pil2 = workspace._resolve_image_as_pil(image_url, [[0, 0], [1, 1]])
    assert img_pil2.size == size2


def test_resolve_image_as_pil_deprecated():
    url_path = os.path.join(assets.url_of(
        'kant_aufklaerung_1784-binarized'), 'data/mets.xml')
    workspace = Resolver().workspace_from_url(url_path)
    with pytest.warns(DeprecationWarning) as record:
        workspace.resolve_image_as_pil('OCR-D-IMG-NRM/OCR-D-IMG-NRM_0017.png')

    # assert
    assert len(record) == 1
    assert 'Call to deprecated method resolve_image_as_pil.' in str(record[0].message)


def test_workspace_from_nothing():
    ws1 = Resolver().workspace_from_nothing(None)
    assert ws1.mets


def test_workspace_from_nothing_makedirs(tmp_path):
    non_existant_dir = tmp_path / 'target'
    ws1 = Resolver().workspace_from_nothing(non_existant_dir)
    assert ws1.directory == non_existant_dir


def test_workspace_from_nothing_noclobber(tmp_path):
    """Attempt to re-create workspace shall fail because already created
    """

    ws2 = Resolver().workspace_from_nothing(tmp_path)
    assert ws2.directory == tmp_path

    with pytest.raises(Exception) as exc:
        Resolver().workspace_from_nothing(tmp_path)

    # assert
    the_msg = "METS 'mets.xml' already exists in '%s' and clobber_mets not set" % tmp_path
    assert the_msg in str(exc)


@pytest.mark.parametrize(
    "url,basename,exc_msg",
    [(None, None, "'url' must be a string"),
     (None, 'foo', "'directory' must be a string")]
)
def test_download_to_directory_with_badargs(url, basename, exc_msg):

    with pytest.raises(Exception) as exc:
        Resolver().download_to_directory(url, basename)

    # assert exception message contained
    assert exc_msg in str(exc)


@pytest.fixture(name='fixture_copy_kant')
def _fixture_copy_kant(tmp_path):
    temporary_phil = tmp_path / 'kant_aufklaerung_1784'
    shutil.copytree(FOLDER_KANT, temporary_phil)
    yield temporary_phil


def test_download_to_directory_default(fixture_copy_kant):
    tmp_root = fixture_copy_kant.parent
    phil_data = fixture_copy_kant / 'data' / 'mets.xml'
    fn = Resolver().download_to_directory(str(tmp_root), str(phil_data))
    assert Path(tmp_root, fn).exists()
    assert fn == 'mets.xml'


def test_download_to_directory_basename(fixture_copy_kant):
    tmp_root = fixture_copy_kant.parent
    phil_data = fixture_copy_kant / 'data' / 'mets.xml'
    fn = Resolver().download_to_directory(
        str(tmp_root), str(phil_data), basename='foo')
    assert Path(tmp_root, fn).exists()
    assert fn == 'foo'


def test_download_to_directory_subdir(fixture_copy_kant):
    tmp_root = fixture_copy_kant.parent
    phil_data = fixture_copy_kant / 'data' / 'mets.xml'
    fn = Resolver().download_to_directory(
        str(tmp_root), str(phil_data), subdir='baz')
    assert Path(tmp_root, fn).exists()
    assert fn == 'baz/mets.xml'


if __name__ == '__main__':
    main(__file__)
