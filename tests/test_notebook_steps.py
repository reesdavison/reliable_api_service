# from app.constants import NOTEBOOK_LIMIT

# from .client_fixture import client  # noqa


# def get_blob() -> dict:
#     return {
#         "name": "foo-bar",
#         "type": "markdown",
#         "content": "# hello world",
#     }


# def create_notebook(client) -> int:
#     response = client.post("/notebooks/", json={"name": "Test Notebook"})
#     assert response.status_code == 200
#     assert response.json()["name"] == "Test Notebook"
#     nb_id = response.json()["id"]
#     assert nb_id is not None
#     return nb_id


# def test_create_single_notebook_step(client):
#     # first create notebook
#     nb_id = create_notebook(client)

#     # then create step
#     response = client.post(
#         f"/notebooks/{nb_id}/steps/",
#         json=get_blob(),
#     )
#     assert response.status_code == 200
#     assert response.json()["name"] == "foo-bar"
#     assert response.json()["type"] == "markdown"
#     assert response.json()["content"] == "# hello world"
#     assert response.json()["index"] == 1
#     assert response.json()["notebook_id"] == nb_id


# def test_create_overlimit_steps(client):
#     # test adding a step to the end after adding incrementally

#     # first create notebook
#     nb_id = create_notebook(client)

#     # then create step
#     for i in range(NOTEBOOK_LIMIT):
#         response = client.post(
#             f"/notebooks/{nb_id}/steps/",
#             json=get_blob(),
#         )
#         assert response.status_code == 200
#         assert response.json()["name"] == "foo-bar"
#         assert response.json()["type"] == "markdown"
#         assert response.json()["content"] == "# hello world"
#         assert response.json()["index"] == i + 1
#         assert response.json()["notebook_id"] == nb_id

#     response = client.post(
#         f"/notebooks/{nb_id}/steps/",
#         json=get_blob(),
#     )
#     assert response.status_code == 400
#     assert response.json() == {
#         "detail": f"Notebook has too many steps. Max {NOTEBOOK_LIMIT}"
#     }


# def test_insert_overlimit_steps(client):
#     # test inserting a step in middle when over limit

#     # first create notebook
#     nb_id = create_notebook(client)

#     # then create step
#     for i in range(NOTEBOOK_LIMIT):
#         response = client.post(f"/notebooks/{nb_id}/steps/", json=get_blob())
#         assert response.status_code == 200
#         assert response.json()["name"] == "foo-bar"
#         assert response.json()["type"] == "markdown"
#         assert response.json()["content"] == "# hello world"
#         assert response.json()["index"] == i + 1
#         assert response.json()["notebook_id"] == nb_id

#     response = client.post(
#         f"/notebooks/{nb_id}/steps/",
#         json={
#             **get_blob(),
#             "prev_step_id": 50,
#         },
#     )
#     assert response.status_code == 400
#     assert response.json() == {
#         "detail": f"Notebook has too many steps. Max {NOTEBOOK_LIMIT}"
#     }


# def test_get_step_order(client):
#     # first create notebook
#     nb_id = create_notebook(client)

#     # add 10 steps
#     for i in range(10):
#         response = client.post(
#             f"/notebooks/{nb_id}/steps/",
#             json={
#                 "name": "foo-bar",
#                 "type": "markdown",
#                 "content": f"{i + 1}",
#             },
#         )
#         assert response.status_code == 200
#         assert response.json()["name"] == "foo-bar"
#         assert response.json()["type"] == "markdown"
#         assert response.json()["content"] == f"{i + 1}"
#         assert response.json()["index"] == i + 1
#         assert response.json()["notebook_id"] == nb_id

#     # get all steps for notebook
#     response = client.get(f"notebooks/{nb_id}/steps/")
#     assert response.status_code == 200
#     ordered_steps = response.json()
#     exp_content = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#     for i, step in enumerate(ordered_steps):
#         assert step["index"] == i + 1
#         assert step["content"] == str(exp_content[i])


# def test_insert_step(client):
#     # first create notebook
#     nb_id = create_notebook(client)

#     # add 10 steps
#     for i in range(10):
#         response = client.post(
#             f"/notebooks/{nb_id}/steps/",
#             json={
#                 "name": "foo-bar",
#                 "type": "markdown",
#                 "content": f"{i + 1}",
#             },
#         )
#         assert response.status_code == 200
#         assert response.json()["name"] == "foo-bar"
#         assert response.json()["type"] == "markdown"
#         assert response.json()["content"] == f"{i + 1}"
#         assert response.json()["index"] == i + 1
#         assert response.json()["notebook_id"] == nb_id

#     response = client.post(
#         f"/notebooks/{nb_id}/steps/",
#         json={
#             "name": "foo-bar",
#             "type": "markdown",
#             "content": "NEW CONTENT",
#             "prev_step_id": 5,
#         },
#     )
#     assert response.status_code == 200
#     assert response.json()["index"] == 6

#     response = client.get(f"notebooks/{nb_id}/steps/")
#     assert response.status_code == 200

#     ordered_steps = response.json()
#     exp_content = [1, 2, 3, 4, 5, "NEW CONTENT", 6, 7, 8, 9, 10]
#     for i, step in enumerate(ordered_steps):
#         assert step["index"] == i + 1
#         assert step["content"] == str(exp_content[i])


# def test_insert_past_non_existant_step(client):
#     # last step is 50

#     # first create notebook
#     nb_id = create_notebook(client)

#     # add 10 steps
#     for i in range(10):
#         response = client.post(
#             f"/notebooks/{nb_id}/steps/",
#             json={
#                 "name": "foo-bar",
#                 "type": "markdown",
#                 "content": f"{i + 1}",
#             },
#         )
#         assert response.status_code == 200

#     response = client.post(
#         f"/notebooks/{nb_id}/steps/",
#         json={
#             "name": "foo-bar",
#             "type": "markdown",
#             "content": "NEW CONTENT",
#             "prev_step_id": 50,
#         },
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "That step does not exist"}


# def test_delete_step(client):
#     # we delete at step index 5

#     # first create notebook
#     nb_id = create_notebook(client)

#     # add 10 steps
#     saved_step_id = None
#     for i in range(10):
#         response = client.post(
#             f"/notebooks/{nb_id}/steps/",
#             json={
#                 "name": "f",
#                 "type": "markdown",
#                 "content": f"{i + 1}",
#             },
#         )
#         assert response.status_code == 200
#         assert response.json()["content"] == f"{i + 1}"
#         assert response.json()["index"] == i + 1
#         assert response.json()["notebook_id"] == nb_id
#         if i == 4:
#             saved_step_id = response.json()["id"]

#     response = client.delete(
#         f"/steps/{saved_step_id}",
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Step deleted"

#     response = client.get(f"notebooks/{nb_id}/steps/")
#     assert response.status_code == 200

#     ordered_steps = response.json()
#     exp_content = [1, 2, 3, 4, 6, 7, 8, 9, 10]
#     for i, step in enumerate(ordered_steps):
#         assert step["index"] == i + 1
#         assert step["content"] == str(exp_content[i])


# def test_delete_non_existant_step(client):
#     # hacky but probably ok
#     non_existant_id = 999999999999

#     response = client.delete(
#         f"/steps/{non_existant_id}",
#     )
#     assert response.status_code == 404
#     assert response.json() == {"detail": "Step not found"}
