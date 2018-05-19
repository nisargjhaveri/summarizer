import os

from sentence import Sentence
from sentenceCollection import SentenceCollection

from utils import nlp

import logging
logger = logging.getLogger("corpus.py")


class Corpus(SentenceCollection):
    def __init__(self, dirname):
        super(Corpus, self).__init__()

        self._dirname = dirname

        self._prepareSentenceSplitter()

        self._documents = []

    def _prepareSentenceSplitter(self):
        self._sentenceSplitter = lambda doc: sum(
            map(lambda p: nlp.getSentenceSplitter()(p), doc.split("\n")),
            []
        )

    def load(self, params, translate=False, replaceOriginal=False):
        self.setSourceLang(params['sourceLang'])
        self.setTargetLang(params['targetLang'])

        # load corpus
        files = map(lambda f: os.path.join(self._dirname, f),
                    os.walk(self._dirname).next()[2])

        sentences = []

        for filename in files:
            with open(filename) as f:
                document = f.read().decode('utf-8')

                self._documents.append(document)
                sentences.extend(self._sentenceSplitter(document))

        sentences = map(lambda s: s.strip(), sentences)
        self.addSentences(map(Sentence, set(sentences)))

        logger.info("Simplifying sentences")
        self.simplify(self.sourceLang, replaceOriginal=True)

        if translate:
            if self.sourceLang != self.targetLang:
                logger.info("Translating sentences")
                self.translate(self.sourceLang,
                               self.targetLang,
                               replaceOriginal)

            if replaceOriginal:
                self.setSourceLang(self.targetLang)

            self.generateTranslationSentenceVectors()

        self.generateSentenceVectors()

        return self
