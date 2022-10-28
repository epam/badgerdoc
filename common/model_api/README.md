# Model-api
https://towardsdatascience.com/packages-part-2-how-to-publish-test-your-package-on-pypi-with-poetry-9fc7295df1a5
## Testing on Test PyPI
`poetry config repositories.testpypi https://test.pypi.org/legacy/`
`poetry publish –-build -r testpypi`
## Input
- __POST-request__  
```
{"input_path": "runs/jobId/fileId/previousStepId",
 "input": {"1": {"1": ["aab83828-cd8b-41f7-a3c3-943f13e67c2c","30e4d539-8e90-49c7-b49c-883073e2b8c8"],"3": [...]},"2": {"4": [...]}},
 "file": "files/fileId/fileId/some_document.pdf",
 "bucket": "tenant_name",
 "pages": [1, 2, 4, 5, 6, 7],
 "output_path": "runs/jobId/fileId/currentStepId",
 "output_bucket": "another_tenant_name",
 "args" = {"categories": [“1”, “3”]}}
```
- __“file”__  
a pdf document from minio
- __"input_path"__  
a json file with annotation-bboxes  
[{"page_num": 1, "size": {"width": 2550, "height": 3300},  
  "objs": [{"id": "aab83828-cd8b-41f7-a3c3-943f13e67c2c", "bbox": [1321, 2004, 2339, 2631], "category": "0"},  
           {"id": "30e4d539-8e90-49c7-b49c-883073e2b8c8", "bbox": [223, 2590, 1234, 2875], "category": "0"},  
           {"id": "df4e3a06-09ac-485c-bf12-ecebd14e7f74", "bbox": [237, 2364, 1226, 2448], "category": **"3"**},  
           {"id": "bf7344d0-3a1e-401f-b802-6236620cc01e", "bbox": [1318, 1690, 2328, 1859], "category": "0"},  
           {"id": "732f2735-3369-4305-9d29-fa3be99d72dd", "bbox": [1276, 1114, 2356, 1621], "category": **"3"**}]},  
 {"page_num": 5, "size": {"width": 2550, "height": 3300},  
  "objs": [{"id": "44d94e31-7079-470a-b8b5-74ce365353f7", "bbox": [1316, 2452, 2333, 2966], "category": "0"},  
           {"id": "ab1847e2-020d-453d-a218-3ac239ec5810", "bbox": [1330, 809, 2330, 1641], "category": "0"},  
           {"id": "7a4a2251-1263-4f52-a13b-fddf6b6f3bd1", "bbox": [230, 1695, 1226, 1914], "category": "0"},  
           {"id": "d86d467f-6ec1-404e-b4e6-ba8d78f93754", "bbox": [217, 399, 1225, 1589], "category": **"3"**}]}]  

## Output

## Model
