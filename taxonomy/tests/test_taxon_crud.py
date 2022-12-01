import uuid
from copy import deepcopy
from typing import Any, List, Optional

import pytest

from tests.override_app_dependency import TEST_HEADER

TAXON_PATH = "/taxons"


def prepare_taxon_body(
    name: Optional[str] = uuid.uuid4().hex,
    taxonomy_id: str = "parent_taxonomy",
    parent_id: Optional[str] = None,
    taxonomy_version: Optional[int] = None,
    id_: Optional[str] = None,
) -> dict:
    body = {
        "name": name,
        "taxonomy_id": taxonomy_id,
        "parent_id": parent_id,
        "taxonomy_version": taxonomy_version,
        "id": id_,
    }
    return {key: body[key] for key in sorted(body)}


def prepare_filtration_body(
    page_num: Optional[int] = 1,
    page_size: Optional[int] = 15,
    field: Optional[str] = "id",
    operator: Optional[str] = "eq",
    value: Optional[Any] = 1,
    sort_field: Optional[str] = "id",
    direction: Optional[str] = "asc",
    no_filtration: Optional[bool] = False,
    no_sort: Optional[bool] = False,
) -> dict:
    body = {
        "pagination": {
            "page_num": page_num,
            "page_size": page_size,
        },
        "filters": [
            {
                "field": field,
                "operator": operator,
                "value": value,
            }
        ],
        "sorting": [
            {
                "field": sort_field,
                "direction": direction,
            }
        ],
    }
    if no_filtration:
        body.pop("filters")
    if no_sort:
        body.pop("sorting")
    return body


def response_schema_from_request(
    taxon_response: dict,
    parents: List[dict] = [],
    is_leaf: Optional[bool] = None,
) -> dict:
    taxon_response = deepcopy(taxon_response)
    taxon_response["parents"] = parents
    taxon_response["is_leaf"] = is_leaf
    return taxon_response


@pytest.mark.integration
def test_add_taxon_taxonomy_does_not_exist(overrided_token_client):
    data = prepare_taxon_body(
        name=uuid.uuid4().hex,
        taxonomy_id=uuid.uuid4().hex,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxonomy with this id doesn't exist" in response.text


@pytest.mark.integration
def test_add_taxon_duplicate_name(
    overrided_token_client,
    prepared_taxon_entity_in_db,
    prepared_taxonomy_record_in_db,
):
    data = prepare_taxon_body(
        name=prepared_taxon_entity_in_db.name,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxon name must be unique" in response.text


@pytest.mark.integration
def test_add_taxon_self_parent(
    overrided_token_client,
    prepared_taxonomy_record_in_db,
):
    taxon_id = uuid.uuid4().hex
    data = prepare_taxon_body(
        id_=taxon_id,
        name=taxon_id,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
        parent_id=taxon_id,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxon cannot be its own parent" in response.text


@pytest.mark.integration
def test_add_taxon_without_name(
    overrided_token_client,
    prepared_taxonomy_record_in_db,
):
    data = prepare_taxon_body(
        taxonomy_id=prepared_taxonomy_record_in_db.id,
    )
    data.pop("name")
    response = overrided_token_client.post(
        TAXON_PATH,
        json=data,
        headers=TEST_HEADER,
    )
    assert response.status_code == 422
    assert "field required" in response.text


@pytest.mark.integration
def test_add_taxon_name_empty_string(
    overrided_token_client,
    prepared_taxonomy_record_in_db,
):
    data = prepare_taxon_body(
        name="",
        taxonomy_id=prepared_taxonomy_record_in_db.id,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxon name can not be empty" in response.text


@pytest.mark.integration
def test_add_taxon_specify_version(
    overrided_token_client,
    prepared_taxonomy_record_in_db,
):
    id_ = uuid.uuid4().hex
    data = prepare_taxon_body(
        id_=id_,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
        taxonomy_version=prepared_taxonomy_record_in_db.version,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 201
    assert response_schema_from_request(data) == response.json()


@pytest.mark.integration
@pytest.mark.parametrize(
    "taxon_name",
    (uuid.uuid4().hex, "My-Taxon", "!!Another_taxon", "#$^&)Taxon123"),
)
def test_add_unique_name(
    overrided_token_client, prepared_taxonomy_record_in_db, taxon_name
):
    id_ = uuid.uuid4().hex
    data = prepare_taxon_body(
        id_=id_,
        name=taxon_name,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
        taxonomy_version=prepared_taxonomy_record_in_db.version,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 201
    assert response_schema_from_request(data) == response.json()


@pytest.mark.integration
def test_add_taxon_id_exists(
    overrided_token_client,
    prepared_taxon_entity_in_db,
    prepared_taxonomy_record_in_db,
):
    data = prepare_taxon_body(
        id_=prepared_taxon_entity_in_db.id,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
    )
    response = overrided_token_client.post(
        TAXON_PATH, json=data, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxon id must be unique" in response.text


@pytest.mark.integration
def test_get_taxon_exists_no_parents(
    overrided_token_client,
    prepared_taxon_entity_in_db,
    prepared_taxonomy_record_in_db,
):
    taxon_id = prepared_taxon_entity_in_db.id
    expected_data_no_parents = prepare_taxon_body(
        name=prepared_taxon_entity_in_db.name,
        taxonomy_id=prepared_taxonomy_record_in_db.id,
        parent_id=prepared_taxon_entity_in_db.parent_id,
        taxonomy_version=prepared_taxonomy_record_in_db.version,
        id_=taxon_id,
    )
    response = overrided_token_client.get(
        f"{TAXON_PATH}/{taxon_id}", headers=TEST_HEADER
    )

    assert response.status_code == 200

    response_json = response.json()
    response_json.pop("parents")
    response_json.pop("is_leaf")
    assert expected_data_no_parents == response_json


@pytest.mark.integration
def test_get_taxon_parents_isleaf(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    leaf = prepare_three_taxons_parent_each_other[-1]
    expected_parents = [
        {**parent.to_dict(), "parents": [], "is_leaf": False}
        for parent in prepare_three_taxons_parent_each_other[:-1]
    ]

    response = overrided_token_client.get(
        f"{TAXON_PATH}/{leaf.id}", headers=TEST_HEADER
    )

    assert response.status_code == 200

    response_json = response.json()
    assert response_json["is_leaf"] == True  # noqa E712
    assert response_json["parents"] == expected_parents


@pytest.mark.integration
def test_get_taxon_does_not_exist(overrided_token_client):
    id_ = uuid.uuid4().hex
    response = overrided_token_client.get(
        f"{TAXON_PATH}/{id_}", headers=TEST_HEADER
    )
    assert response.status_code == 404
    assert f"Taxon with id: {id_} doesn't exist" in response.text


@pytest.mark.integration
def test_update_taxon_does_not_exist(overrided_token_client):
    id_ = uuid.uuid4().hex
    taxon_update = prepare_taxon_body(id_=id_)
    taxon_update.pop("id")

    response = overrided_token_client.put(
        f"{TAXON_PATH}/{id_}", json=taxon_update, headers=TEST_HEADER
    )
    assert response.status_code == 404
    assert "Cannot update taxon that doesn't exist" in response.text


@pytest.mark.integration
def test_update_taxon_duplicate_name(
    overrided_token_client,
    prepare_two_taxons_different_names,
):
    id_ = prepare_two_taxons_different_names[1].id
    taxon_update = prepare_taxon_body(
        name=prepare_two_taxons_different_names[0].name
    )
    taxon_update.pop("id")

    response = overrided_token_client.put(
        f"{TAXON_PATH}/{id_}", json=taxon_update, headers=TEST_HEADER
    )
    assert response.status_code == 400
    assert "Taxon name must be unique" in response.text


@pytest.mark.integration
def test_update_tree_set_parent_to_none(
    overrided_token_client, prepare_three_taxons_parent_each_other
):
    single_taxon = prepare_three_taxons_parent_each_other[0]
    new_root = prepare_three_taxons_parent_each_other[1]
    leaf_from_root = prepare_three_taxons_parent_each_other[2]

    new_root_body = new_root.to_dict()
    new_root_id = new_root_body.pop("id")
    new_root_body["parent_id"] = None

    response = overrided_token_client.put(
        f"{TAXON_PATH}/{new_root_id}", json=new_root_body, headers=TEST_HEADER
    )
    assert response.status_code == 200

    taxon_responses = []

    for id_ in [single_taxon.id, new_root.id, leaf_from_root.id]:
        taxon_responses.append(
            overrided_token_client.get(
                f"{TAXON_PATH}/{id_}", headers=TEST_HEADER
            ).json()
        )

    assert taxon_responses[0] == response_schema_from_request(
        taxon_responses[0], parents=[], is_leaf=True
    )
    assert taxon_responses[1] == response_schema_from_request(
        taxon_responses[1], parents=[], is_leaf=False
    )
    assert taxon_responses[2] == response_schema_from_request(
        taxon_responses[2], parents=[taxon_responses[1]], is_leaf=True
    )


@pytest.mark.integration
def test_update_tree_change_parent_to_another(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    root = prepare_three_taxons_parent_each_other[0]
    lost_child = prepare_three_taxons_parent_each_other[1]
    changed_parent = prepare_three_taxons_parent_each_other[2]

    changed_parent_body = changed_parent.to_dict()
    changed_parent_id = changed_parent_body.pop("id")
    changed_parent_body["parent_id"] = root.id

    response = overrided_token_client.put(
        f"{TAXON_PATH}/{changed_parent_id}",
        json=changed_parent_body,
        headers=TEST_HEADER,
    )
    assert response.status_code == 200

    taxon_responses = []

    for id_ in [root.id, lost_child.id, changed_parent.id]:
        taxon_responses.append(
            overrided_token_client.get(
                f"{TAXON_PATH}/{id_}", headers=TEST_HEADER
            ).json()
        )

    assert taxon_responses[0] == response_schema_from_request(
        taxon_responses[0], parents=[], is_leaf=False
    )
    assert taxon_responses[1] == response_schema_from_request(
        taxon_responses[1], parents=[taxon_responses[0]], is_leaf=True
    )
    assert taxon_responses[2] == response_schema_from_request(
        taxon_responses[2], parents=[taxon_responses[0]], is_leaf=True
    )


@pytest.mark.integration
def test_cascade_delete_parent(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    ids_to_delete = [tax.id for tax in prepare_three_taxons_parent_each_other]

    delete_response = overrided_token_client.delete(
        f"{TAXON_PATH}/{ids_to_delete[0]}", headers=TEST_HEADER
    )
    assert delete_response.status_code == 204

    for id_ in ids_to_delete:
        response = overrided_token_client.get(
            f"{TAXON_PATH}/{id_}", headers=TEST_HEADER
        )
        assert response.status_code == 404


@pytest.mark.integration
def test_delete_taxon_does_not_exist(
    overrided_token_client,
):
    delete_response = overrided_token_client.delete(
        f"{TAXON_PATH}/{uuid.uuid4().hex}", headers=TEST_HEADER
    )
    assert delete_response.status_code == 404
    assert (
        "Cannot delete taxon that doesn't exist"
        in delete_response.json()["detail"]
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ["page_num", "page_size", "result_length"],
    [(1, 15, 15), (2, 15, 1), (3, 15, 0), (1, 30, 16)],
)
def test_search_pagination_should_work(
    page_num,
    page_size,
    result_length,
    overrided_token_client,
    prepared_taxon_hierarchy,
    other_tenants_taxon,
):
    # given
    search_request_data = prepare_filtration_body(
        page_num=page_num, page_size=page_size, no_filtration=True
    )
    # when
    response = overrided_token_client.post(
        f"{TAXON_PATH}/search", json=search_request_data, headers=TEST_HEADER
    )

    taxons = response.json()["data"]
    pagination = response.json()["pagination"]
    assert response.status_code == 200
    assert pagination["page_num"] == page_num
    assert pagination["page_size"] == page_size
    assert len(taxons) == result_length


@pytest.mark.integration
def test_search_result_should_be_empty_if_taxon_not_exists(
    overrided_token_client,
    prepared_taxon_hierarchy,
    other_tenants_taxon,
):
    # given
    search_request_data = prepare_filtration_body(value="antarctica")
    # when
    response = overrided_token_client.post(
        f"{TAXON_PATH}/search", json=search_request_data, headers=TEST_HEADER
    )
    # then
    assert response
    assert response.status_code == 200

    categories = response.json()["data"]
    total = response.json()["pagination"]["total"]
    assert not categories
    assert not total


@pytest.mark.integration
@pytest.mark.parametrize(
    ["taxon_id", "expected_total"],
    (
        ("madagascar", 0),
        ("australia", 1),
    ),
)
def test_search_should_return_only_allowed_taxon_for_current_tenant(
    taxon_id,
    expected_total,
    overrided_token_client,
    prepared_taxon_hierarchy,
    common_taxon,
    other_tenants_taxon,
):
    # given
    search_request_data = prepare_filtration_body(value=taxon_id)
    # when
    response = overrided_token_client.post(
        f"{TAXON_PATH}/search", json=search_request_data, headers=TEST_HEADER
    )
    # then
    assert response
    assert response.status_code == 200

    total = response.json()["pagination"]["total"]
    assert total == expected_total


@pytest.mark.integration
@pytest.mark.parametrize(
    ["operator", "value", "expected"],
    [("like", "%G%", 2), ("like", "%D%1_", 1), ("ilike", "%D%1_", 1)],
)
def test_search_filter_name_like(
    operator, value, expected, prepared_taxon_hierarchy, overrided_token_client
):
    # given
    search_request_data = prepare_filtration_body(
        field="name", operator=operator, value=value
    )
    # when
    response = overrided_token_client.post(
        f"{TAXON_PATH}/search", json=search_request_data, headers=TEST_HEADER
    )
    # then
    assert response
    taxons = response.json()["data"]
    assert len(taxons) == expected


@pytest.mark.integration
def test_search_children_tree(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    root = prepare_three_taxons_parent_each_other[0]
    second = prepare_three_taxons_parent_each_other[1]

    search_request_data = prepare_filtration_body(
        field="tree", operator="children", value=root.id
    )

    response = overrided_token_client.post(
        f"{TAXON_PATH}/search",
        json=search_request_data,
        headers=TEST_HEADER,
    )
    assert response.status_code == 200
    taxons = response.json()["data"]
    child = taxons[0]

    assert len(taxons) == 1
    assert child == response_schema_from_request(
        second.to_dict(),
        parents=[response_schema_from_request(root.to_dict(), is_leaf=False)],
        is_leaf=False,
    )


@pytest.mark.integration
def test_search_children_recursive_tree(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    root, second, third = prepare_three_taxons_parent_each_other

    search_request_data = prepare_filtration_body(
        field="tree",
        operator="children_recursive",
        value=root.id,
        sort_field="tree",
    )

    response = overrided_token_client.post(
        f"{TAXON_PATH}/search",
        json=search_request_data,
        headers=TEST_HEADER,
    )
    assert response.status_code == 200
    taxons = response.json()["data"]
    child_1 = taxons[0]
    child_2 = taxons[1]

    assert len(taxons) == 2

    parents = []

    for node in [root, second]:
        parents.append(
            response_schema_from_request(
                node.to_dict(),
                parents=[],
                is_leaf=False,
            )
        )

    assert child_1 == response_schema_from_request(
        second.to_dict(), parents=[parents[0]], is_leaf=False
    )
    assert child_2 == response_schema_from_request(
        third.to_dict(), parents=parents, is_leaf=True
    )


@pytest.mark.integration
def test_search_parents_recursive_tree(
    overrided_token_client,
    prepare_three_taxons_parent_each_other,
):
    root, second, third = prepare_three_taxons_parent_each_other

    search_request_data = prepare_filtration_body(
        field="tree", operator="parents_recursive", value=third.id
    )

    response = overrided_token_client.post(
        f"{TAXON_PATH}/search",
        json=search_request_data,
        headers=TEST_HEADER,
    )
    assert response.status_code == 200
    taxons = response.json()["data"]
    parent_1 = taxons[0]
    parent_2 = taxons[1]

    assert len(taxons) == 2

    assert parent_1 == response_schema_from_request(
        root.to_dict(), is_leaf=False
    )
    assert parent_2 == response_schema_from_request(
        second.to_dict(),
        parents=[response_schema_from_request(root.to_dict(), is_leaf=False)],
        is_leaf=False,
    )
