from src.texts_processing import TextsTokenizer
from src.config import (stopwords,
                        parameters,
                        logger)
from src.classifiers import FastAnswerClassifier

tokenizer = TextsTokenizer()
tokenizer.add_stopwords(stopwords)
classifier = FastAnswerClassifier(tokenizer, parameters)
logger.info("service started...")
