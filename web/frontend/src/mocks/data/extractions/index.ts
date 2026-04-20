import page1 from './page_1.hocr'
import page2 from './page_2.hocr'
import page3 from './page_3.hocr'
import { BadgerDocExtraction, BadgerDocExtractionPage } from '@/shared/api/badgerdoc'

export const extractionMock: BadgerDocExtractionPage[] = [
  {
    page_number: 1,
    content: page1,
  },
  {
    page_number: 2,
    content: page2,
  },
  {
    page_number: 3,
    content: page3,
  },
]

export const createExtractionMock: BadgerDocExtraction = {
  id: 45,
  document_id: 398,
  created_by: 'admin',
  status: 'Started',
  temporal_job_id: null,
  comment: '',
  tags: ['deepseek-ocr-2'],
  created_at: '2026-03-27T06:17:46.420137Z',
  updated_at: '2026-03-27T06:17:46.420153Z',
}

export const extractionPageMock: BadgerDocExtractionPage = {
  id: 44,
  extraction_id: 45,
  page_number: 1,
  content:
    "<p>REP-0337001 v1.0 Status: Approved Approved Date: 12 Dec 2018</p><p>CofA | batch 1000008665 | Manufacture DS10123123</p><p>Certificate of Analysis</p><p>Lot number: 1921</p><p>Product: 9881</p><p>Product number Molecular formula (net) Molecular mass (average) Date of manufacture Date of release: hehe</p><p>Retest date Specification</p><p>Test procedure</p><p>Storage condition Batch size0032</p><p>Tests0051</p><p>Appearance</p><p>Appearance of solution</p><p>Idontification (MS)4141414</p><p>Identification (amino acid analysis)222</p><p>Purity (HPLC)6666</p><p>Related substances (HPLC)</p><p>~~ SOP-1-O00TS-ADY Rav71</p><p>Check this Printed by)</p><p>10000086659</p><p>MEDIO382 4082375 CorHaszNzOss 3728.12</p><p>November 12, 2018 December 11, 2018 May 2021 QS-4082375A/07 SAV-4082375/02 &lt;-15°C</p><p>3080.3 g</p><p>Specifications12312312</p><p>white to off-white powder</p><p>clear, colorless solution in 50% acetic acid (1 mg/ml)</p><p>m = 3725.8 + 0.5u (monoisotopic mass)</p><p>Asx 2.6-3.4 Ala 2.6-3.4 Ser detected Tyr 0.7-1.3 Gk 4.5-5.5 Val 0.7-1.3 Gly 2.6-3.4 lys 0.7-13 His 0.7-1.3 leu 16-24 Arg 1.6-2.4 Trp detected Thr 1.6-2.4</p><p>normelized to Phe = 2.0 = 97.0%</p><p>report each individual = 0.10%</p><p>&lt; 1.0% RRT 0.96, [8- Asp!°]MEDI0382, endo- Ala’®-MEDIO382 °, °°</p><p>&lt; 1.0% RRT 1.05, [B- Asp?|MEDI0382 °,</p><p>&lt; 0.7% RRT 1.25, des-His!- MEDIO382 °</p><p>&lt; 1.0% RRT 1.26, des-Ser'’- MEDIO382, des-Ala'® - MEDIO382, des-Ala”* - MEDIO382 °</p><p>Proliminary assigned mein structure “B” naming convention indicates the respective iso-isomer</p><p>Results</p><p>white powder</p><p>complies</p><p>m = 3725.8u</p><p>Ala 2.8 Tyr 09 Val 1.1 lys 1.0 lev 2.0 Trp detected</p><p>Asx Ser Gk Gly His Arg Thr</p><p>3.1 detected</p><p>mee 4s</p><p>98.7%</p><p>RRT 0.88 0.91 1.04 0.21%</p><p>area% 0.21 0.15 0.20</p><p>0.13% 0.13%</p><p>0.29%</p><p>t version of the document before use. on 24 May 2024 13:11 GMT+00:003333333</p><p>Page | of 3</p><p>BACHEM</p><p>Bachom AG Hauptstrasse 144 4416 Bubendort Switzerland</p><p>Tel +41 58595 2021</p><p>Certificate of Analysis</p><p>™ |</p><p></p>",
  created_at: '2026-03-27T06:17:46.454317Z',
  updated_at: '2026-03-27T06:17:46.454328Z',
}
