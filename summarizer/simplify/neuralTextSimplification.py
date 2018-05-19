import tempfile
import os
import subprocess
import shelve
from ..utils import nlp


def _simplify(sentences, lang):
    OPENNMT_PATH = os.getenv("NTS_OPENNMT_PATH", None)
    MODEL_PATH = os.getenv("NTS_MODEL_PATH", None)
    GPUS = os.getenv("NTS_GPUS", 0)

    if OPENNMT_PATH is None or MODEL_PATH is None:
        raise ValueError("Both NTS_OPENNMT_PATH and NTS_MODEL_PATH needs "
                         "to be set as environment variables")

    srcFile = tempfile.NamedTemporaryFile(suffix=".src", delete=False)
    outFile = tempfile.NamedTemporaryFile(suffix=".out", delete=False)

    sentences = map(nlp.getTokenizer(lang), sentences)

    srcFile.write("\n".join(sentences).encode('utf-8'))

    srcFile.close()
    outFile.close()

    # Run simplifier

    translateLua = os.path.join(OPENNMT_PATH, "translate.lua")
    beamSize = 5

    env = os.environ.copy()
    env['LUA_PATH'] = env.get("LUA_PATH", "") + ";" + OPENNMT_PATH + "/?.lua"
    command = (["th", translateLua] +
               ["-replace_unk"] +
               ["-beam_size", str(beamSize)] +
               ["-gpuid", str(GPUS)] +
               ["-model", MODEL_PATH] +
               ["-src", srcFile.name] +
               ["-output", outFile.name] +
               ["-log_level", "WARNING"]
               )

    subprocess.call(command, env=env)

    with open(outFile.name, "r") as output:
        simpleSentences = map(lambda s: s.decode('utf-8').strip(),
                              output.readlines())

    os.unlink(srcFile.name)
    os.unlink(outFile.name)
    os.unlink(outFile.name + "_h1")

    return simpleSentences


def simplify(sentences):
    def cacheKey(text):
        return "_".join([
            text.strip()
        ]).encode('utf-8')

    cache = shelve.open('.simplification-cache.nts')

    sentencesToSimplify = []

    for sentence in sentences:
        if cacheKey(sentence) not in cache:
            sentencesToSimplify.append(sentence)

    if len(sentencesToSimplify):
        simpleSentences = _simplify(sentencesToSimplify)

        if (len(sentencesToSimplify) != len(simpleSentences)):
            raise RuntimeError("SENTENCE_SIMPLIFICATION_ERROR")
        else:
            for origSentence, simpleSentence in zip(sentencesToSimplify,
                                                    simpleSentences):
                cache[cacheKey(origSentence)] = simpleSentence

    simpleSentences = []
    for sentence in sentences:
        simpleSentences.append(cache[cacheKey(sentence)])

    cache.close()

    return simpleSentences
