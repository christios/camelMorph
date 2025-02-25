import os
import sys
import argparse
from tqdm import tqdm
import re
import pickle
import multiprocessing
from collections import Counter

from glf_pilot_utils import FEATS_INFLECT

parser = argparse.ArgumentParser()
parser.add_argument("-gumar_dir", required=True,
                    type=str, help=".")
parser.add_argument("-output_dir", default='sandbox_files/gumar_disambig',
                    type=str, help="Path of the directory to output evaluation results.")
parser.add_argument("-camel_tools", default='',
                    type=str, help="Path of the directory containing the camel_tools modules.")
parser.add_argument("-batch", default=32,
                    type=int, help="Number of partitions to split the Gumar files into.")
parser.add_argument("-n_part", default=10,
                    type=int, help="Number of partitions to split the Gumar files into.")
parser.add_argument("-part", default=-1,
                    type=int, help="Number of partitions to split the Gumar files into.")
parser.add_argument("-n_cpu", default=8,
                    type=int, help="Number of CPUs to use for multiprocessing.")
args = parser.parse_args([] if "__file__" not in globals() else None)

if args.camel_tools:
    sys.path.insert(0, args.camel_tools)

from camel_tools.utils.charmap import CharMapper
from camel_tools.disambig.bert import BERTUnfactoredDisambiguator

PUNC_REGEX = re.compile(r"([:.;'\"!%&)(?،؟؛])")
REPEATED_LETTER = re.compile(r'(.+?)\1{3,}')

ar2bw = CharMapper.builtin_mapper('ar2bw')
bw2ar = CharMapper.builtin_mapper('bw2ar')

unfactored = BERTUnfactoredDisambiguator.pretrained(
    'glf', batch_size=args.batch)

def token_preprocessing(token):
    token = PUNC_REGEX.sub(r'\1 ', token)
    tokens = []
    for token in token.split():
        # If letter is consecutively repeated more than 3 times, reduce it to 1.
        token = REPEATED_LETTER.sub(r'\1', token)
        tokens.append(token)
    return tokens

def disambig_file(gumar_path):
    with open(gumar_path) as f:
        sentences = []
        for line in f.readlines():
            sentence = []
            for token in line.strip().split():
                sentence += token_preprocessing(token)
            sentences.append(sentence)
    
    disambigs = unfactored.disambiguate_sentences(sentences)
    feat2lemma2lex = {}
    for disambig in disambigs:
        for token_analyses in disambig:
            analysis = token_analyses.analyses[0].analysis
            feat = tuple([analysis.get(k, '') for k in FEATS_INFLECT])
            lemma, diac, stem = '', '', ''
            if 'lex' in analysis:
                lemma, diac = analysis['lex'], analysis['diac']
            else:
                lemma, diac = '', token_analyses.word
            stem = analysis['stem'] if 'stem' in analysis else ''
            feat2lemma2lex.setdefault(feat, {}).setdefault(
                lemma, Counter()).update([(diac, stem)])
    
    return feat2lemma2lex


if __name__ == "__main__":
    os.makedirs(args.output_dir, exist_ok=True)
    part = args.path if args.part != -1 else 'all'
    output_path = os.path.join(args.output_dir, f'feat2lemma2lex_{part}.pkl')

    gumar_paths = [os.path.join(args.gumar_dir, name)
                   for name in os.listdir(args.gumar_dir)]
    
    if args.part == -1 or args.n_part == 1:
        gumar_paths_part = gumar_paths
    else:
        assert args.n_part >= args.part > 0
        start = len(gumar_paths) * (args.part - 1) // args.n_part
        end = len(gumar_paths) * args.part // args.n_part
        gumar_paths_part = gumar_paths[start:end]

    chunks = [gumar_paths_part[i:i + args.n_cpu]
              for i in range(0, len(gumar_paths_part), args.n_cpu)]
    if len(gumar_paths_part) == len(gumar_paths):
        feat2lemma2lex = dict()
        for chunk in tqdm(chunks):
            with multiprocessing.Pool(args.n_cpu) as p:
                results = list(tqdm(p.imap(disambig_file, chunk),
                                    total=len(chunk), smoothing=0.2))
            for feat2lemma2lex_ in results:
                for feat, lemma2lex in feat2lemma2lex_.items():
                    for lemma, lex_set in lemma2lex.items():
                        for lex in lex_set:
                            feat2lemma2lex.setdefault(feat, {}).setdefault(
                                lemma, Counter()).update([lex])
            with open(output_path, 'wb') as f:
                pickle.dump(feat2lemma2lex, f)
            
    else:
        feat2lemma2lex = {}
        for gumar_path in tqdm(gumar_paths_part):
            disambig_file(gumar_path)
    