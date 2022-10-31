Installing
- poetry build
- tar xvzf dist/page_rendering-0.1.0.tar.gz
- poetry run add-logging
- poetry run get-setup
- python setup.py install

Examples

images render on a local document

    from page_rendering.page_rendering import RenderImages
    img_obj = RenderImages('file_name', 400, 'jpeg')
    img_obj.render([1, 2, 4], file_path=Path('local_path/test.pdf'))

images render on a minio document

    img_obj = RenderImages('file_name', 400, 'jpeg')
    img_obj.render_from_minio([1, 2], 'bucket', Path('minio_path'))
