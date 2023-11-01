""""""
import os
import uvicorn
from fastapi import FastAPI
from src.start import classifier
from src.storage import ElasticClient
from src.config import logger, empty_result
from src.data_types import (TemplateIds,
                            SearchData)
from src.utils import timeit


os.environ["TOKENIZERS_PARALLELISM"] = "false"
app = FastAPI(title="ExpertBotEs")

worker = ElasticClient()


@app.post("/api/answers/delete")
def answers_delete(data: TemplateIds):
    """"""
    worker.delete_in_field("answers", "clusters", data.templateIds)
    worker.delete_in_field("answers", "answers", data.templateIds)
    worker.delete_in_field("answers", "unique_answers", data.templateIds)


@app.post("/api/search")
# @timeit
async def search(data: SearchData):
    """searching etalon by  incoming text"""
    logger.info("searched text: {}".format(str(data.text)))
    try:
        logger.info("searched text without spellcheck: {}".format(str(data.text)))
        # result = await classifier.kosgu_searching(str(data.text), data.pubid, 0.95)
        result = await classifier.kosgu_searching(str(data.text), data.pubid, topic="КОСГУ робот", special_patterns="косг|квр")
        return result
    except Exception:
        logger.exception("Searching problem with text {} in pubid {}".format(str(data.text), str(data.pubid)))
        return empty_result


if __name__ == "__main__":
    # uvicorn.run(app, host=service_host, port=service_port)
    uvicorn.run(app, host="0.0.0.0", port=8080)
