# Read JSON from inbound, write to outbound
from loguru import logger  # pyright: ignore[reportMissingImports]
from os import getenv
from adapters.filesystem import list_json_files_in_directory, read_json_from_file
from os import path
from pathlib import Path


class ClientRepository:
    def __init__(self):
        logger.info("ClientRepository module initialized")

    def find_workorders(self, directory_path: str):
        logger.info(f"Getting workorders from '{directory_path}'")

        workorders = []

        json_files = list_json_files_in_directory(directory_path)

        for file in json_files:
            json_file_path = path.join(directory_path, file)
            workorders.append(read_json_from_file(json_file_path))

        return workorders

    def validate_workorder(self, workorder: dict):
        # {
        #     'orderNo': 10,
        #     'isCanceled': False,
        #     'isDeleted': False,
        #     'isDone': False,
        #     'isOnHold': False,
        #     'isPending': False,
        #     'summary': 'Example workorder #10',
        #     'creationDate': '2025-11-11T02:00:53.697748+00:00',
        #     'lastUpdateDate': '2025-11-11T03:00:53.697748+00:00',
        #     'deletedDate': None
        # }

        validated_workorder = {}

        # TODO: validator should be imported

        validated_workorder = workorder.copy()

        return validated_workorder
