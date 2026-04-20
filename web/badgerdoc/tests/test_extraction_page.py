from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from badgerdoc.models import document, extraction, extraction_page
from badgerdoc.tests.settings import mock_db_and_file_storage

sample_correct_hocr = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
  <meta name='ocr-system' content='tesseract 5.5.1' />
  <meta name='ocr-capabilities' content='ocr_photo ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_dir ocrp_lang ocrp_wconf'/>
 </head>
 <body>
  <div class='ocr_page' id='page_1' title='image "/tmp/ocrmypdf.io.oahictzn/000002_ocr.png"; bbox 0 0 1190 1683; ppageno 0; scan_res 144 144'>
   <div class='ocr_carea' id='block_1_1' title="bbox 227 14 963 56">
    <p class='ocr_par' id='par_1_1' lang='eng' title="bbox 227 14 963 56">
     <span class='ocr_line' id='line_1_1' title="bbox 227 14 963 34; baseline 0 -5">
      <span class='ocrx_word' id='word_1_1' title='bbox 227 14 350 29; x_wconf 92'>REP-0360735</span>
      <span class='ocrx_word' id='word_1_2' title='bbox 357 14 395 29; x_wconf 85'>v1.0</span>
      <span class='ocrx_word' id='word_1_3' title='bbox 418 14 476 29; x_wconf 85'>Status:</span>
      <span class='ocrx_word' id='word_1_4' title='bbox 483 14 570 34; x_wconf 91'>Approved</span>
      <span class='ocrx_word' id='word_1_5' title='bbox 593 14 680 34; x_wconf 91'>Approved</span>
      <span class='ocrx_word' id='word_1_6' title='bbox 687 14 732 29; x_wconf 95'>Date:</span>
      <span class='ocrx_word' id='word_1_7' title='bbox 743 14 761 29; x_wconf 95'>19</span>
      <span class='ocrx_word' id='word_1_8' title='bbox 767 14 792 29; x_wconf 96'>Jul</span>
      <span class='ocrx_word' id='word_1_9' title='bbox 799 14 841 29; x_wconf 63'>2022</span>
      <span class='ocrx_word' id='word_1_10' title='bbox 864 14 906 34; x_wconf 90'>Page</span>
      <span class='ocrx_word' id='word_1_11' title='bbox 913 14 923 29; x_wconf 96'>2</span>
      <span class='ocrx_word' id='word_1_12' title='bbox 929 14 949 29; x_wconf 96'>of</span>
      <span class='ocrx_word' id='word_1_13' title='bbox 958 14 963 29; x_wconf 96'>6</span>
     </span>
     <span class='ocr_line' id='line_1_2' title="bbox 374 36 817 56; baseline 0 -5">
      <span class='ocrx_word' id='word_1_14' title='bbox 374 36 469 51; x_wconf 92'>Cotadutide</span>
      <span class='ocrx_word' id='word_1_15' title='bbox 479 36 552 56; x_wconf 86'>Img-mL</span>
      <span class='ocrx_word' id='word_1_16' title='bbox 558 36 635 56; x_wconf 96'>cartridge</span>
      <span class='ocrx_word' id='word_1_17' title='bbox 642 36 683 51; x_wconf 93'>CoA</span>
      <span class='ocrx_word' id='word_1_18' title='bbox 689 36 817 51; x_wconf 92'>361845-00006</span>
     </span>
    </p>
   </div>
   <div class='ocr_carea' id='block_1_2' title="bbox 97 74 1115 173">
    <p class='ocr_par' id='par_1_3' lang='eng' title="bbox 97 80 1115 173">
     <span class='ocr_line' id='line_1_4' title="bbox 166 80 1115 126; baseline -0.005 -9">
      <span class='ocrx_word' id='word_1_27' title='bbox 166 80 274 126; x_wconf 92'>QUALI</span>
      <span class='ocrx_word' id='word_1_28' title='bbox 699 99 745 114; x_wconf 96'>Batch</span>
      <span class='ocrx_word' id='word_1_29' title='bbox 751 99 800 114; x_wconf 92'>00006</span>
      <span class='ocrx_word' id='word_1_30' title='bbox 807 94 817 122; x_wconf 90'>—</span>
      <span class='ocrx_word' id='word_1_31' title='bbox 822 99 863 113; x_wconf 96'>Code</span>
      <span class='ocrx_word' id='word_1_32' title='bbox 869 99 927 113; x_wconf 93'>361845</span>
      <span class='ocrx_word' id='word_1_33' title='bbox 933 107 943 109; x_wconf 88'>—</span>
      <span class='ocrx_word' id='word_1_34' title='bbox 949 98 1039 113; x_wconf 92'>Combi-seal</span>
      <span class='ocrx_word' id='word_1_35' title='bbox 1045 98 1115 116; x_wconf 96'>cartridge</span>
     </span>
     <span class='ocr_line' id='line_1_5' title="bbox 97 118 388 173; baseline -0.007 -26">
      <span class='ocrx_word' id='word_1_36' title='bbox 97 118 121 173; x_wconf 19'>5</span>
      <span class='ocrx_word' id='word_1_37' title='bbox 129 128 149 146; x_wconf 73'>4</span>
      <span class='ocrx_word' id='word_1_38' title='bbox 160 119 388 147; x_wconf 95'>ASSISTANCE</span>
     </span>
     <span class='ocr_line' id='line_1_6' title="bbox 157 153 381 167; baseline -0.004 -3">
      <span class='ocrx_word' id='word_1_39' title='bbox 157 154 216 164; x_wconf 96'>Contract</span>
      <span class='ocrx_word' id='word_1_40' title='bbox 222 153 288 164; x_wconf 94'>Research</span>
      <span class='ocrx_word' id='word_1_41' title='bbox 294 153 381 167; x_wconf 96'>Organisation</span>
     </span>
    </p>
   </div>
   <div class='ocr_photo' id='block_1_7' title="bbox 426 1660 534 1672"></div>
  </div>
 </body>
</html>
"""


sample_incorrect_hocr = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title></title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
  <meta name='ocr-system' content='tesseract 5.5.1' />
  <meta name='ocr-capabilities' content='ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_dir ocrp_lang ocrp_wconf'/>
 </head>
 <body>
  <div class='ocr_page' id='page_1' title='image "/tmp/ocrmypdf.io.oahictzn/000002_ocr.png"; bbox 0 0 1190 1683; ppageno 0; scan_res 144 144'>
   <div class='ocr_carea' id='block_1_1' title="bbox  56">
    <div class='ocr_par' id='par_1_1' lang='eng' title="bbox  56">
     <span class='ocr_line' id='line_1_1' title="bbox  34; baseline 0 -5">
      <span class='ocrx_word' id='word_1_18' title='bbox  51; x_wconf 92'>361845-00006</span>
     </span>
    </div>
   </div>
   <div class='ocr_photo' id='block_1_7' title="bbox 426 1660 534 1672"></div>
  </div>
 </body>
</html>
"""


sample_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <p class="test">1</p>
    <p class="test">2</p>
    <p class="test">3</p>
</body>
</html>
"""


@mock_db_and_file_storage
class ExtractionPageAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.base_time = timezone.now()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@test.com", password="pass"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="pass",
            is_staff=True,
        )
        self.permission_user = User.objects.create_user(
            username="permission_user",
            email="permission@test.com",
            password="pass",
        )
        self.permission_user.user_permissions.add(
            Permission.objects.get(codename="view_other_users_document")
        )

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()

        self.document = document.Document.objects.create(
            file="test_document.pdf", uploaded_by=self.owner
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def _create_extraction(self, **kwargs) -> extraction.Extraction:
        defaults = dict(document=self.document, created_by=self.owner)
        defaults.update(kwargs)
        return extraction.Extraction.objects.create(**defaults)

    def _create_page(
        self, extraction_obj, page_number=1, content=None, created_at=None
    ):
        if content is None:
            content = {"data": "some text"}

        page = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_obj, page_number=page_number, content=content
        )
        if created_at:
            page.created_at = created_at
            page.save()
        return page

    def _url_create_page(self) -> str:
        return "/badgerdoc/extraction-page/"

    def _url_list_pages(self) -> str:
        return "/badgerdoc/extraction-pages/"

    def _url_latest(self, document_id: int) -> str:
        return f"/badgerdoc/document/{document_id}/extraction-page/latest/"

    def _url_latest_page(self, page_num: int, document_id: int) -> str:
        return f"/badgerdoc/document/{document_id}/extraction-page/latest/{page_num}/"

    def test_create_extraction_page_happy_path_correct_hocr(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("content", resp.data)
        self.assertEqual(resp.data["page_number"], 1)

    def test_create_extraction_page_happy_path_correct_html(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_html,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("content", resp.data)
        self.assertEqual(resp.data["page_number"], 1)

    def test_create_extraction_page_hocr_validation(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_incorrect_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_extraction_page_missing_fields(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )

        resp = self.client.post(
            self._url_create_page(), {"page_number": 1}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.client.post(
            self._url_create_page(),
            {"extraction_id": extraction_obj.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_extraction_page_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(
            self._url_create_page(),
            {"extraction_id": 99, "page_number": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pk", resp.data.get("error", ""))

    def test_create_extraction_page_not_creator_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        resp = self.client.post(
            self._url_create_page(),
            {"extraction_id": extraction_obj.id, "page_number": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_extraction_page_when_extraction_stopped(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        resp = self.client.post(
            self._url_create_page(),
            {"extraction_id": extraction_obj.id, "page_number": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stopped", resp.data.get("error", ""))

    def test_create_extraction_page_duplicate_page(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )

        self._create_page(extraction_obj, page_number=1)

        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unique", str(resp.data.get("error", "")))

    def test_create_extraction_page_invalid_page_number(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )

        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": -1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_extraction_page_unauthenticated(self):
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        resp = self.client.post(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_extraction_page_successful_update(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        page = self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], sample_correct_hocr)

    def test_patch_missing_content(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {"extraction_id": extraction_obj.id, "page_number": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_missing_extraction_id(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {"page_number": 1, "content": sample_html},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_missing_page_number(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {"extraction_id": extraction_obj.id, "content": sample_html},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_nonexistent_extraction(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": 9999,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_extraction_stopped(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stopped", resp.data.get("error", ""))

    def test_patch_page_not_found(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )

        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 99,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_invalid_page_number(self):
        self.client.force_authenticate(user=self.owner)
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": "invalid",
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_unauthenticated(self):
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        self._create_page(extraction_obj, page_number=1)

        resp = self.client.patch(
            self._url_create_page(),
            {
                "extraction_id": extraction_obj.id,
                "page_number": 1,
                "content": sample_correct_hocr,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_extraction_pages_filters_and_permissions(self):
        self.client.force_authenticate(user=self.owner)
        extraction_1 = self._create_extraction(
            status=extraction.ExtractionStatus.IN_PROGRESS
        )
        extraction_2 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.other_user,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        self._create_page(extraction_1, page_number=1)
        self._create_page(extraction_1, page_number=2)
        self._create_page(extraction_2, page_number=1)

        resp = self.client.get(self._url_list_pages())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get(self._url_list_pages())
        self.assertGreaterEqual(resp.data["count"], 3)

        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(
            f"{self._url_list_pages()}?extraction_id={extraction_1.id}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_get_latest_extraction_pages(self):
        self.client.force_authenticate(user=self.owner)

        extraction_1 = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        extraction_1.created_at = self.base_time - timedelta(hours=2)
        extraction_1.save()

        extraction_2 = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        extraction_2.created_at = self.base_time - timedelta(hours=1)
        extraction_2.save()

        self._create_page(
            extraction_1,
            page_number=1,
            created_at=self.base_time - timedelta(hours=2, minutes=5),
        )
        latest_page_extraction_2 = self._create_page(
            extraction_2,
            page_number=1,
            created_at=self.base_time - timedelta(hours=1, minutes=5),
        )

        resp = self.client.get(self._url_latest(self.document.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(
            resp.data["results"][0]["id"], latest_page_extraction_2.id
        )

    def test_get_latest_extraction_page_by_number(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        self._create_page(extraction_obj, page_number=1)
        self._create_page(extraction_obj, page_number=2)

        resp = self.client.get(self._url_latest_page(1, self.document.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["page_number"], 1)

        # non-existing page
        resp = self.client.get(self._url_latest_page(99, self.document.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_latest_endpoints_access_permissions(self):
        extraction_obj = self._create_extraction(
            status=extraction.ExtractionStatus.COMPLETED
        )
        self._create_page(extraction_obj, page_number=1)

        self.client.force_authenticate(user=self.other_user)
        resp = self.client.get(self._url_latest(self.document.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get(self._url_latest(self.document.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


@mock_db_and_file_storage
class LatestExtractionPagesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.base_time = timezone.now()

        self.owner = User.objects.create_user(
            username="owner", email="owner@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@test.com", password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.permission_user = User.objects.create_user(
            username="permission_user",
            email="permission@test.com",
            password="testpass123",
        )
        permission = Permission.objects.get(
            codename="view_other_users_document"
        )
        self.permission_user.user_permissions.add(permission)

        self.trigger_workflow_patch = patch(
            "badgerdoc.signals.trigger_automatic.workflow.trigger"
        )
        self.mock_trigger_workflow = self.trigger_workflow_patch.start()

        self.document = document.Document.objects.create(
            file="test_document.pdf", uploaded_by=self.owner
        )

    def tearDown(self):
        self.trigger_workflow_patch.stop()

    def test_basic_functionality_returns_latest_pages(self):
        """
        Test the main scenario: document with 3 extractions (A, B, C)
        A has pages 1, 2, 3 (oldest)
        B has pages 2, 3 (middle)
        C has page 3 (newest)
        Expected: A.1, B.2, C.3
        """
        self.client.force_authenticate(user=self.owner)

        extraction_a = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_a.created_at = self.base_time - timedelta(hours=3)
        extraction_a.save()

        extraction_b = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_b.created_at = self.base_time - timedelta(hours=2)
        extraction_b.save()

        extraction_c = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_c.created_at = self.base_time - timedelta(hours=1)
        extraction_c.save()

        page_a1 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_a,
            page_number=1,
            content=sample_html,
        )
        page_a1.created_at = self.base_time - timedelta(hours=3, minutes=10)
        page_a1.save()

        page_a2 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_a,
            page_number=2,
            content=sample_html,
        )
        page_a2.created_at = self.base_time - timedelta(hours=3, minutes=5)
        page_a2.save()

        page_a3 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_a,
            page_number=3,
            content=sample_html,
        )
        page_a3.created_at = self.base_time - timedelta(hours=3)
        page_a3.save()

        page_b2 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_b,
            page_number=2,
            content=sample_html,
        )
        page_b2.created_at = self.base_time - timedelta(hours=2, minutes=10)
        page_b2.save()

        page_b3 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_b,
            page_number=3,
            content=sample_html,
        )
        page_b3.created_at = self.base_time - timedelta(hours=2, minutes=5)
        page_b3.save()

        page_c3 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_c,
            page_number=3,
            content=sample_html,
        )
        page_c3.created_at = self.base_time - timedelta(hours=1)
        page_c3.save()

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        results = {
            page["page_number"]: page for page in response.data["results"]
        }

        self.assertEqual(results[1]["id"], page_a1.id)
        self.assertEqual(results[1]["extraction_id"], extraction_a.id)
        self.assertEqual(results[1]["content"], sample_html)

        self.assertEqual(results[2]["id"], page_b2.id)
        self.assertEqual(results[2]["extraction_id"], extraction_b.id)
        self.assertEqual(results[2]["content"], sample_html)

        self.assertEqual(results[3]["id"], page_c3.id)
        self.assertEqual(results[3]["extraction_id"], extraction_c.id)
        self.assertEqual(results[3]["content"], sample_html)

    def test_returns_empty_list_when_no_extractions(self):
        self.client.force_authenticate(user=self.owner)

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_returns_empty_list_when_extractions_have_no_pages(self):
        self.client.force_authenticate(user=self.owner)

        extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_returns_404_for_nonexistent_document(self):
        self.client.force_authenticate(user=self.owner)

        url = "/badgerdoc/document/999/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_access_their_document(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_obj,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_owner_cannot_access_document(self):
        self.client.force_authenticate(user=self.other_user)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_obj,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Permission denied", response.data["error"])

    def test_admin_can_access_any_document(self):
        self.client.force_authenticate(user=self.admin_user)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_obj,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_with_permission_can_access_any_document(self):
        self.client.force_authenticate(user=self.permission_user)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_obj,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_access(self):
        """Test that unauthenticated user cannot access the endpoint."""
        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_multiple_pages_same_timestamp_returns_both(self):
        self.client.force_authenticate(user=self.owner)

        extraction_a = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_b = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        same_time = self.base_time - timedelta(hours=1)

        page_a1 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_a,
            page_number=1,
            content=sample_html,
        )
        page_a1.created_at = same_time
        page_a1.save()

        page_b1 = extraction_page.ExtractionPage.objects.create(
            extraction=extraction_b,
            page_number=1,
            content=sample_html,
        )
        page_b1.created_at = same_time
        page_b1.save()

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        returned_ids = {page["id"] for page in response.data["results"]}
        self.assertEqual(returned_ids, {page_a1.id, page_b1.id})

    def test_latest_page_across_many_extractions(self):
        self.client.force_authenticate(user=self.owner)

        extraction_objs = []
        for i in range(5):
            ext = extraction.Extraction.objects.create(
                document=self.document,
                created_by=self.owner,
                status=extraction.ExtractionStatus.COMPLETED,
            )
            extraction_objs.append(ext)

        latest_page = None
        for i, ext in enumerate(extraction_objs):
            page = extraction_page.ExtractionPage.objects.create(
                extraction=ext,
                page_number=1,
                content=sample_html,
            )
            page.created_at = self.base_time - timedelta(hours=5 - i)
            page.save()
            if i == 4:
                latest_page = page

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], latest_page.id)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_results_ordered_by_page_number(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        pages = []
        for page_num in [3, 1, 5, 2, 4]:
            page = extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=page_num,
                content=sample_html,
            )
            pages.append(page)

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

        page_numbers = [
            page["page_number"] for page in response.data["results"]
        ]
        self.assertEqual(page_numbers, [1, 2, 3, 4, 5])

    def test_complex_scenario_multiple_pages_multiple_extractions(self):
        """
        Test complex scenario with multiple pages and extractions.
        Extraction 1: pages 1, 2, 3 (oldest)
        Extraction 2: pages 2, 4 (middle)
        Extraction 3: pages 1, 3, 5 (newest)
        Expected: Ext3.1, Ext2.2, Ext3.3, Ext2.4, Ext3.5
        """
        self.client.force_authenticate(user=self.owner)

        ext1 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        ext1.created_at = self.base_time - timedelta(hours=3)
        ext1.save()

        ext2 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        ext2.created_at = self.base_time - timedelta(hours=2)
        ext2.save()

        ext3 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        ext3.created_at = self.base_time - timedelta(hours=1)
        ext3.save()

        page1_1 = extraction_page.ExtractionPage.objects.create(
            extraction=ext1,
            page_number=1,
            content=sample_html,
        )
        page1_1.created_at = self.base_time - timedelta(hours=3, minutes=10)
        page1_1.save()

        page1_2 = extraction_page.ExtractionPage.objects.create(
            extraction=ext1,
            page_number=2,
            content=sample_html,
        )
        page1_2.created_at = self.base_time - timedelta(hours=3, minutes=5)
        page1_2.save()

        page1_3 = extraction_page.ExtractionPage.objects.create(
            extraction=ext1,
            page_number=3,
            content=sample_html,
        )
        page1_3.created_at = self.base_time - timedelta(hours=3)
        page1_3.save()

        page2_2 = extraction_page.ExtractionPage.objects.create(
            extraction=ext2,
            page_number=2,
            content=sample_html,
        )
        page2_2.created_at = self.base_time - timedelta(hours=2, minutes=10)
        page2_2.save()

        page2_4 = extraction_page.ExtractionPage.objects.create(
            extraction=ext2,
            page_number=4,
            content=sample_html,
        )
        page2_4.created_at = self.base_time - timedelta(hours=2, minutes=5)
        page2_4.save()

        page3_1 = extraction_page.ExtractionPage.objects.create(
            extraction=ext3,
            page_number=1,
            content=sample_html,
        )
        page3_1.created_at = self.base_time - timedelta(hours=1, minutes=10)
        page3_1.save()

        page3_3 = extraction_page.ExtractionPage.objects.create(
            extraction=ext3,
            page_number=3,
            content=sample_html,
        )
        page3_3.created_at = self.base_time - timedelta(hours=1, minutes=5)
        page3_3.save()

        page3_5 = extraction_page.ExtractionPage.objects.create(
            extraction=ext3,
            page_number=5,
            content=sample_html,
        )
        page3_5.created_at = self.base_time - timedelta(hours=1)
        page3_5.save()

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

        results = {
            page["page_number"]: page for page in response.data["results"]
        }

        self.assertEqual(results[1]["id"], page3_1.id)
        self.assertEqual(results[1]["extraction_id"], ext3.id)

        self.assertEqual(results[2]["id"], page2_2.id)
        self.assertEqual(results[2]["extraction_id"], ext2.id)

        self.assertEqual(results[3]["id"], page3_3.id)
        self.assertEqual(results[3]["extraction_id"], ext3.id)

        self.assertEqual(results[4]["id"], page2_4.id)
        self.assertEqual(results[4]["extraction_id"], ext2.id)

        self.assertEqual(results[5]["id"], page3_5.id)
        self.assertEqual(results[5]["extraction_id"], ext3.id)

    def test_pagination_default_page_size(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 6):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 5)

    def test_pagination_custom_page_size(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 11):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=3"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 3)

    def test_pagination_multiple_pages(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 11):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=3"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 3)

        page_numbers_page1 = [
            page["page_number"] for page in response.data["results"]
        ]
        self.assertEqual(page_numbers_page1, [1, 2, 3])

        next_url = response.data["next"]
        self.assertIn("page=2", next_url)
        self.assertIn("page_size=3", next_url)

        full_url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/{next_url}"
        response_page2 = self.client.get(full_url)
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_page2.data["count"], 10)
        self.assertIsNotNone(response_page2.data["next"])
        self.assertIsNotNone(response_page2.data["previous"])
        self.assertEqual(len(response_page2.data["results"]), 3)

        page_numbers_page2 = [
            page["page_number"] for page in response_page2.data["results"]
        ]
        self.assertEqual(page_numbers_page2, [4, 5, 6])

    def test_pagination_last_page(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 6):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=3&page=2"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 2)

        page_numbers = [
            page["page_number"] for page in response.data["results"]
        ]
        self.assertEqual(page_numbers, [4, 5])

    def test_pagination_page_beyond_available(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 6):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=3&page=10"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 2)

    def test_pagination_max_page_size(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 51):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=100"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 50)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 50)

    def test_pagination_page_size_exceeds_maximum(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 151):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=200"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 150)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 100)

    def test_pagination_empty_results_structure(self):
        self.client.force_authenticate(user=self.owner)

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(response.data["results"], [])

    def test_pagination_invalid_page_number(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 6):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page=invalid"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 5)

    def test_pagination_invalid_page_size(self):
        self.client.force_authenticate(user=self.owner)

        extraction_obj = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        for i in range(1, 26):
            extraction_page.ExtractionPage.objects.create(
                extraction=extraction_obj,
                page_number=i,
                content=sample_html,
            )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?page_size=invalid"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["results"]), 20)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.owner)

        extraction_completed = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_pending = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
        )

        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_completed,
            page_number=1,
            content=sample_html,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_pending,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?status=Completed"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_filter_by_created_by(self):
        self.client.force_authenticate(user=self.owner)

        extraction_owner = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_other = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.other_user,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_owner,
            page_number=1,
            content=sample_html,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_other,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?created_by={self.owner.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_filter_by_temporal_job_id(self):
        self.client.force_authenticate(user=self.owner)

        extraction_job1 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
            temporal_job_id="job-123",
        )
        extraction_job2 = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
            temporal_job_id="job-456",
        )

        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_job1,
            page_number=1,
            content=sample_html,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_job2,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?temporal_job_id=job-123"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_filter_combines_multiple_filters(self):
        self.client.force_authenticate(user=self.owner)

        extraction_match = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
            temporal_job_id="job-123",
            tags=["important"],
        )
        extraction_no_match = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.IN_PROGRESS,
            temporal_job_id="job-123",
            tags=["important"],
        )

        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_match,
            page_number=1,
            content=sample_html,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_no_match,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?status=Completed&temporal_job_id=job-123"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_filter_access_permissions(self):
        self.client.force_authenticate(user=self.owner)

        extraction_owner = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.COMPLETED,
        )
        extraction_other = extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.other_user,
            status=extraction.ExtractionStatus.COMPLETED,
        )

        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_owner,
            page_number=1,
            content=sample_html,
        )
        extraction_page.ExtractionPage.objects.create(
            extraction=extraction_other,
            page_number=1,
            content=sample_html,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["content"], sample_html)

    def test_filter_with_no_matching_extractions(self):
        self.client.force_authenticate(user=self.owner)

        extraction.Extraction.objects.create(
            document=self.document,
            created_by=self.owner,
            status=extraction.ExtractionStatus.STARTED,
        )

        url = f"/badgerdoc/document/{self.document.id}/extraction-page/latest/?status=Started"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
