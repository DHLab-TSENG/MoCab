# -*- coding: utf-8 -*-

import os
import requests
import json


def main(url, path):
    folders = os.listdir(path)
    # Exclude IDE folders
    folders.remove(".vscode")
    folders.remove(".idea")
    # folders.remove(".git")
    # Move Test Data folder to the end
    folders.remove("Test Data")
    folders.append("Test Data")
    for folder_name in folders:
        if not os.path.isdir(os.path.join(path, folder_name)):
            continue
        explore_files(url, os.path.join(path, folder_name))


def explore_files(url, path):
    has_folder = False
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            has_folder = True
            break
    if has_folder:
        for folder_name in os.listdir(path):
            if not os.path.isdir(os.path.join(path, folder_name)):
                continue
            explore_files(url, os.path.join(path, folder_name))
    else:
        create_resource(url, path)
    pass


def create_resource(
        url,
        path
):
    session = requests.session()
    for fname in os.listdir(path):
        input_file = open(os.path.join(path, fname), encoding="utf-8")
        if not fname.endswith(".json"):
            continue
        try:
            json_dict = json.load(input_file)
        except Exception as e:
            print("Name of file: {}".format(fname))
            raise e
        id = None

        try:
            resources = json_dict['resourceType']
        except KeyError:
            print(json_dict)
            raise KeyError
        try:
            id = json_dict['id']
        except KeyError:
            continue
        if id is not None:
            fhir_store_path = "{}/{}/{}/".format(
                url, resources, id
            )
        else:
            fhir_store_path = "{}/{}/".format(url, resources)

        headers = {"Content-Type": "application/fhir+json"}

        try:
            response = session.put(
                fhir_store_path, headers=headers, json=json_dict)
            # response.raise_for_status()
            resource = response.json()
            print("Created {} resource with ID {}".format(
                resources, resource["id"]))
        except Exception as e:
            print(e, id)
            continue


if __name__ == "__main__":
    url = input("請輸入FHIR Server base URL: ")
    path = os.getcwd()
    main(url, path)

    print("Done!")
