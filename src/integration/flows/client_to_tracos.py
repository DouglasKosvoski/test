from loguru import logger  # pyright: ignore[reportMissingImports]
from pathlib import Path
from integration.system.client.repository import ClientRepository
from integration.system.tracos.repository import TracOSRepository
from integration.translators.client_to_tracos import translate_client_to_tracos


class ClientToTracOSFlow:
    def __init__(self):
        self.client_repository = ClientRepository()
        self.tracos_repository = TracOSRepository()

    async def sync(self, directory_path: Path):
        logger.info("Syncing Client data with TracOS...")

        try:
            workorders = self.client_repository.find_workorders(str(directory_path))
        except FileNotFoundError:
            logger.error(f"Inbound directory not found: '{directory_path}'")
            return
        except PermissionError:
            logger.error(f"Permission denied accessing inbound directory: '{directory_path}'")
            return

        logger.debug(f"Found {len(workorders)} workorders in '{directory_path}'")

        for workorder in workorders:
            order_number = workorder.get('orderNo', 'unknown')
            try:
                validated_workorder = self.client_repository.validate_workorder(workorder)

                if validated_workorder is None:
                    logger.warning(f"Workorder {order_number} is not valid")
                    continue

                translated_workorder_into_tracos_format = translate_client_to_tracos(validated_workorder)

                await self.tracos_repository.save_workorder(translated_workorder_into_tracos_format)
            except Exception:
                logger.error(f"Failed to process workorder {order_number}")
                continue
