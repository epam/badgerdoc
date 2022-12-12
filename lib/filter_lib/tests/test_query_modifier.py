from ..src.enum_generator import get_enum_from_orm
from ..src.query_modificator import (
    _create_filter,
    _create_or_condition,
    _get_column,
    _get_entity,
    _op_is_not,
    form_query,
)
from .conftest import Address, Category, User


def test_get_entity(get_session):
    session = get_session
    query = session.query(User, Address)
    assert _get_entity(query, "User") == User
    assert _get_entity(query, "Address") == Address


def test_get_column_positive():
    assert _get_column(User, "id") == User.id
    assert _get_column(User, "name") == User.name
    assert _get_column(Address, "location") == Address.location


def test_create_filter(get_session):
    session = get_session
    user_1 = User(name="test_one")
    user_2 = User(name="test_two")
    session.add_all([user_1, user_2])
    session.commit()

    query = session.query(User)
    spec = {"model": "User", "field": "name", "op": "eq", "value": "test_one"}
    query = _create_filter(query, spec)
    assert len(query.all()) == 1


def test_create_filter_ltree_parent(get_session):
    # Arrange
    session = get_session

    query = session.query(Category)
    spec = {"model": "Category", "field": "tree", "op": "parent", "value": 2}

    # Act
    query = _create_filter(query, spec)

    expected_sql_str = (
        "SELECT categories.id, categories.tree \n"
        "FROM categories, "
        "(SELECT categories.tree AS tree \n"
        "FROM categories \n"
        "WHERE categories.id = :id_1) AS anon_1 \n"
        "WHERE subpath(categories.tree, :subpath_1, "
        "nlevel(anon_1.tree) - :nlevel_1) = categories.tree "
        "AND index(anon_1.tree, categories.tree) != :index_1 "
        "ORDER BY categories.tree DESC\n"
        " LIMIT :param_1"
    )

    compiled_statement = query.statement.compile()

    # Assert
    assert str(compiled_statement) == expected_sql_str
    assert compiled_statement.params == {
        "id_1": 2,
        "subpath_1": 0,
        "nlevel_1": 1,
        "index_1": -1,
        "param_1": 1,
    }


def test_create_filter_ltree_parents_recursive(get_session):
    # Arrange
    session = get_session

    query = session.query(Category)
    spec = {
        "model": "Category",
        "field": "tree",
        "op": "parents_recursive",
        "value": 2,
    }

    # Act
    query = _create_filter(query, spec)

    expected_sql_str = (
        "SELECT categories.id, categories.tree \n"
        "FROM categories, "
        "(SELECT categories.tree AS tree \n"
        "FROM categories \n"
        "WHERE categories.id = :id_1) AS anon_1 \n"
        "WHERE nlevel(anon_1.tree) != nlevel(categories.tree) "
        "AND index(anon_1.tree, categories.tree) != :index_1 "
        "ORDER BY categories.tree"
    )

    compiled_statement = query.statement.compile()

    # Assert
    assert str(compiled_statement) == expected_sql_str
    assert compiled_statement.params == {"id_1": 2, "index_1": -1}


def test_create_filter_ltree_children(get_session):
    # Arrange
    session = get_session

    query = session.query(Category)
    spec = {
        "model": "Category",
        "field": "tree",
        "op": "children",
        "value": 2,
    }

    # Act
    query = _create_filter(query, spec)

    expected_sql_str = (
        "SELECT categories.id, categories.tree \n"
        "FROM categories, "
        "(SELECT categories.tree AS tree \n"
        "FROM categories \n"
        "WHERE categories.id = :id_1) AS anon_1 \n"
        "WHERE (categories.tree <@ anon_1.tree) AND "
        "nlevel(categories.tree) = nlevel(anon_1.tree) + :nlevel_1"
    )

    compiled_statement = query.statement.compile()

    # Assert
    assert str(compiled_statement) == expected_sql_str
    assert compiled_statement.params == {"id_1": 2, "nlevel_1": 1}


def test_create_filter_ltree_children_recursive(get_session):
    # Arrange
    session = get_session

    query = session.query(Category)
    spec = {
        "model": "Category",
        "field": "tree",
        "op": "children_recursive",
        "value": 2,
    }

    # Act
    query = _create_filter(query, spec)

    expected_sql_str = (
        "SELECT categories.id, categories.tree \n"
        "FROM categories, "
        "(SELECT categories.tree AS tree \n"
        "FROM categories \n"
        "WHERE categories.id = :id_1) AS anon_1 \n"
        "WHERE (categories.tree <@ anon_1.tree) AND "
        "nlevel(categories.tree) > nlevel(anon_1.tree)"
    )

    compiled_statement = query.statement.compile()

    # Assert
    assert str(compiled_statement) == expected_sql_str
    assert compiled_statement.params == {"id_1": 2}


def test_create_filter_ltree_not_supported_operation(get_session):
    # Arrange
    session = get_session

    query = session.query(Category)
    spec = {
        "model": "Category",
        "field": "tree",
        "op": "not_supported_operation",
        "value": 2,
    }

    # Act
    query = _create_filter(query, spec)

    expected_sql_str = (
        "SELECT categories.id, categories.tree \nFROM categories"
    )

    compiled_statement = query.statement.compile()

    # Assert
    assert str(compiled_statement) == expected_sql_str
    assert compiled_statement.params == {}


def test_form_query(get_session):
    session = get_session
    user_1 = User(id=5, name="user")
    user_2 = User(id=10, name="user")
    user_3 = User(id=15)
    user_4 = User(id=20)
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {"model": "User", "field": "id", "op": "le", "value": 20},
            {"model": "User", "field": "name", "op": "like", "value": "user"},
        ],
    }
    query, pag = form_query(specs, query)
    assert len(query.all()) == 2
    assert (pag.page_num, pag.page_size, pag.min_pages_left, pag.total) == (
        1,
        15,
        1,
        2,
    )


def test_form_query_with_one_distinct_field(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name="Alexander")
    user_3 = User(id=15, name="Grigoriy")
    user_4 = User(id=20, name="Alexander")
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "distinct",
                "value": 20,
            },
        ],
    }
    query, pag = form_query(specs, query)
    assert query.all() == [("Fedor",), ("Alexander",), ("Grigoriy",)]


def test_form_query_with_distinct_and_like(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name="Alexander")
    user_3 = User(id=15, name="Grigoriy")
    user_4 = User(id=20, name="Alexander")
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "distinct",
                "value": 20,
            },
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "like",
                "value": "%or%",
            },
        ],
    }
    query, pag = form_query(specs, query)
    assert query.all() == [("Fedor",), ("Grigoriy",)]


def test_form_query_with_two_distinct_fields(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name="Alexander")
    user_3 = User(id=15, name="Grigoriy")
    user_4 = User(id=20, name="Alexander")
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {
                "model": "User",
                "field": user_enum.ID,
                "op": "distinct",
                "value": 20,
            },
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "distinct",
                "value": "%or%",
            },
        ],
    }
    query, pag = form_query(specs, query)
    assert query.all() == [
        (5, "Fedor"),
        (10, "Alexander"),
        (15, "Grigoriy"),
        (20, "Alexander"),
    ]


def test_form_query_with_distincts_and_filters_and_sorting(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name="Alexander")
    user_3 = User(id=15, name="Grigoriy")
    user_4 = User(id=20, name="Alexander")
    session.add_all([user_1, user_2, user_3, user_4])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "pagination": {"page_num": 1, "page_size": 15},
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "distinct",
                "value": 20,
            },
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "like",
                "value": "%or%",
            },
        ],
        "sorting": [
            {"model": "User", "field": user_enum.NAME, "direction": "desc"}
        ],
    }
    query, pag = form_query(specs, query)
    assert query.all() == [("Grigoriy",), ("Fedor",)]


def test_op_is_not_positive():
    fil1 = {"model": "User", "field": "name", "op": "ne", "value": "123"}
    fil2 = {"model": "User", "field": "name", "op": "not_in", "value": ["123"]}
    fil3 = {
        "model": "User",
        "field": "name",
        "op": "not_ilike",
        "value": "123",
    }
    assert _op_is_not(fil1)
    assert _op_is_not(fil2)
    assert _op_is_not(fil3)


def test_op_is_not_negative():
    fil1 = {"model": "User", "field": "name", "op": "eq", "value": "123"}
    fil2 = {"model": "User", "field": "name", "op": "in", "value": ["123"]}
    fil3 = {"model": "User", "field": "name", "op": "ilike", "value": "123"}
    fil4 = {"model": "User", "field": "name", "op": "is_null"}
    assert not _op_is_not(fil1)
    assert not _op_is_not(fil2)
    assert not _op_is_not(fil3)
    assert not _op_is_not(fil4)


def test_create_or_condition():
    fil1 = {"model": "User", "field": "name", "op": "ne", "value": "123"}
    fil2 = {"model": "User", "field": "name", "op": "not_in", "value": ["123"]}
    fil3 = {
        "model": "User",
        "field": "name",
        "op": "not_ilike",
        "value": "123",
    }

    assert _create_or_condition(fil1) == {
        "or": [
            {"model": "User", "field": "name", "op": "ne", "value": "123"},
            {
                "model": "User",
                "field": "name",
                "op": "is_null",
                "value": "123",
            },
        ]
    }
    assert _create_or_condition(fil2) == {
        "or": [
            {
                "model": "User",
                "field": "name",
                "op": "not_in",
                "value": ["123"],
            },
            {
                "model": "User",
                "field": "name",
                "op": "is_null",
                "value": ["123"],
            },
        ]
    }
    assert _create_or_condition(fil3) == {
        "or": [
            {
                "model": "User",
                "field": "name",
                "op": "not_ilike",
                "value": "123",
            },
            {
                "model": "User",
                "field": "name",
                "op": "is_null",
                "value": "123",
            },
        ]
    }


def test_filters_with_null_ne(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name=None)
    user_3 = User(id=15, name=None)
    session.add_all([user_1, user_2, user_3])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "ne",
                "value": "Fedor",
            }
        ]
    }
    query, pag = form_query(specs, query)
    ids = [el.id for el in query]
    assert ids == [10, 15]


def test_filters_with_null_not_in(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name=None)
    user_3 = User(id=15, name=None)
    session.add_all([user_1, user_2, user_3])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "not_in",
                "value": ["Fedor"],
            }
        ]
    }
    query, pag = form_query(specs, query)
    ids = [el.id for el in query]
    assert ids == [10, 15]


def test_filters_with_null_not_ilike(get_session):
    session = get_session
    user_1 = User(id=5, name="Fedor")
    user_2 = User(id=10, name=None)
    user_3 = User(id=15, name=None)
    session.add_all([user_1, user_2, user_3])
    session.commit()

    user_enum = get_enum_from_orm(User)
    query = session.query(User)
    specs = {
        "filters": [
            {
                "model": "User",
                "field": user_enum.NAME,
                "op": "not_ilike",
                "value": "Fedor",
            }
        ]
    }
    query, pag = form_query(specs, query)
    ids = [el.id for el in query]
    assert ids == [10, 15]
