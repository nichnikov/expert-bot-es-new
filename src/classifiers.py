"""
классификатор KNeighborsClassifier в /home/an/Data/Yandex.Disk/dev/03-jira-tasks/aitk115-support-questions
"""
import re
from src.data_types import Parameters
from src.storage import ElasticClient
from src.texts_processing import TextsTokenizer
from src.utils import timeout, jaccard_similarity
from src.config import logger

# https://stackoverflow.com/questions/492519/timeout-on-a-function-call

tmt = float(10)  # timeout

def search_result_rep(search_result: []):
    return [{**d["_source"],
             **{"id": d["_id"]},
             **{"score": d["_score"]}} for d in search_result]



class FastAnswerClassifier:
    
    
    def __init__(self, tokenizer: TextsTokenizer, parameters: Parameters):
        self.es = ElasticClient()
        self.tkz = tokenizer
        self.prm = parameters

    async def get_answer(self, templateId, pubid):
        answer_query = {"bool": {"must": [{"match_phrase": {"templateId": templateId}}, {"match_phrase": {"pubId": pubid}},]}}
        resp = await self.es.search_by_query(self.prm.answers_index, answer_query)
        if resp["hits"]["hits"]:
            search_result = search_result_rep(resp["hits"]["hits"])
            return {"templateId": search_result[0]["templateId"],
                    "templateText": search_result[0]["templateText"]}
        else:
            logger.info("not found answer with templateId {} and pub_id {}".format(str(templateId), str(pubid)))
            return {"templateId": 0, "templateText": ""}

    async def searching(self, text: str, pubid: int, score: float):
        """"""
        """searching etalon by  incoming text"""
        try:
            tokens = self.tkz([text])
            if tokens[0]:
                tokens_str = " ".join(tokens[0])
                query = {"match": {"LemCluster": tokens_str}}
                search_result = await self.es.search_by_query(self.prm.clusters_index, query)
                if search_result["hits"]["hits"]:
                    etalons_search_result = search_result_rep(search_result["hits"]["hits"])
                    if etalons_search_result:
                        for d in etalons_search_result:
                            if pubid in d["ParentPubList"] and jaccard_similarity(tokens_str, d["LemCluster"]) >= score:
                                answer = await self.get_answer(d["ID"], pubid)
                                return answer
                        logger.info("Jaccard Similarity of {} less then score {}".format(str(tokens_str), str(score)))
                        return {"templateId": 0, "templateText": ""}
                    else:
                        logger.info("es didn't find anything for text of tokens {}".format(str(tokens_str)))
                        return {"templateId": 0, "templateText": ""}
                else:
                    logger.info("es returned empty value for input text {}".format(str(text)))
                    return {"templateId": 0, "templateText": ""}
            else:
                logger.info("tokenizer returned empty value for input text {}".format(str(text)))
                return {"templateId": 0, "templateText": ""}
        except Exception:
            logger.exception("Searching problem with text: {}".format(str(text)))
            return {"templateId": 0, "templateText": ""}

    async def kosgu_searching(self, input_text: str, pubid: int, topic: str, special_patterns: str):
        """
        поиск по особым правилам, (для косгу)
        выбирается самый длинный эталон, входящий в исходный запрос
        special_patterns must be lematized
        """
        try:
            lem_input_text = " ".join(self.tkz([input_text])[0])
            # kosgu_find = re.findall(special_patterns, lem_input_text)
            if re.findall(special_patterns, lem_input_text):
                lem_input_text = re.sub(special_patterns, "", lem_input_text)
                kosgu_query={"bool": {"must": [{"match_phrase": {"Topic": topic}}, 
                                            {"match": {"LemCluster": lem_input_text}}]}}
                results = await self.es.search_by_query(self.prm.clusters_index, query=kosgu_query)
                ids_tuples = [(d["_source"]["ID"], re.sub(special_patterns, "", d["_source"]["LemCluster"]), 
                                 len(d["_source"]["LemCluster"].split())) for d in results["hits"]["hits"]]
                for i, p, l in sorted(ids_tuples, key=lambda x: x[2], reverse=True):
                    serch_result = re.findall(p, lem_input_text)
                    if serch_result:
                        answer = await self.get_answer(i, pubid)
                        return answer
                return {"templateId": 0, "templateText": ""}
            else:
                return {"templateId": 0, "templateText": ""}
        except:
            logger.exception("Searching problem with text: {}".format(str(input_text)))
            return {"templateId": 0, "templateText": ""}

    
'''
if __name__ == "__main__":
    import os
    import time
    import pandas as pd
    from src.config import PROJECT_ROOT_DIR, logger

    t = time.time()
    tknzr = TextsTokenizer()
    stopwords = []
    stopwords_roots = [os.path.join(PROJECT_ROOT_DIR, "data", "greetings.csv"),
                       os.path.join(PROJECT_ROOT_DIR, "data", "stopwords.csv")]

    for root in stopwords_roots:
        stopwords_df = pd.read_csv(root, sep="\t")
        stopwords += list(stopwords_df["text"])
    tknzr.add_stopwords(stopwords)
    print("TextsTokenizer upload:", time.time() - t)

    t0 = time.time()
    c = FastAnswerClassifier(tknzr)
    print("FastAnswerClassifier upload:", time.time() - t0)

    t1 = time.time()
    r = c.searching("как вернули госпошлины по решение судов", 6, 0.95)
    print("searching time:", time.time() - t1)
    print(r)

    t2 = time.time()
    r = c.searching("электрическая электростанция, чебуркша", 6, 0.95)
    print("searching time:", time.time() - t2)
    print(r)

    print("all working time:", time.time() - t)
'''