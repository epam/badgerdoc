def get_test_db_url(main_db_url: str) -> str:
    main_db_url_split = main_db_url.split("/")
    main_db_url_split[-1] = 'test_db'
    result = "/".join(main_db_url_split)
    return result
