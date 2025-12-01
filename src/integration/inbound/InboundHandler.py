from loguru import logger  # pyright: ignore[reportMissingImports]
from os import getenv
from helpers.directory import list_json_files_in_directory
from helpers.json import read_json_from_file
from os import path
from pathlib import Path

class InboundHandler:
    def __init__(self):
        logger.info("InboundHandler module initialized")


    def sync_with_tracOS(self, directory_path: Path):
        logger.info(f"Syncing Inbound data with TracOS...")

        workorders = self.find_workorders(directory_path)
        workorders = workorders[:1]

        logger.info(f"Found {len(workorders)} workorders in '{directory_path}'")

        for workorder in workorders:
            validated_workorder = self.validate_workorder(workorder)
            self.save_workorder_to_database(validated_workorder)


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


    def save_workorder_to_database(self, workorder: dict):
        DATABASE_DRIVER = getenv("DATABASE_DRIVER")

        if DATABASE_DRIVER is None:
            raise ValueError("DATABASE_DRIVER is not set")

        if DATABASE_DRIVER == "mongodb":
            self.save_workorder_to_mongodb(workorder)
        else:
            raise ValueError(f"Unsupported database driver: {DATABASE_DRIVER}")


    def save_workorder_to_mongodb(self, workorder: dict):
        # TODO: save the workorder to MongoDB
        pass