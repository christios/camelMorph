# MIT License
#
# Copyright 2022 New York University Abu Dhabi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import re
from collections import OrderedDict
from tqdm import tqdm
import argparse
import os
import pickle
import sys
from itertools import product

import pandas as pd

try:
    from ..utils.utils import strip_brackets, Config, POS_NOMINAL
except:
    file_path = os.path.abspath(__file__).split('/')
    package_path = '/'.join(file_path[:len(file_path) - 1 - file_path[::-1].index('camel_morph')])
    sys.path.insert(0, package_path)
    from camel_morph.utils.utils import strip_brackets, Config, POS_NOMINAL


parser = argparse.ArgumentParser()
parser.add_argument("-paradigms", default='',
                    type=str, help="Configuration file containing the sets of paradigms from which we generate conjugation tables.")
parser.add_argument("-config_file", default='config_default.json',
                    type=str, help="Config file specifying which sheets to use from `specs_sheets`.")
parser.add_argument("-config_name", default='default_config',
                    type=str, help="Name of the configuration to load from the config file.")
parser.add_argument("-db", default='',
                    type=str, help="Name of the DB file which will be used with the generation module.")
parser.add_argument("-pos_type", default='', choices=['verbal', 'nominal', ''],
                    type=str, help="POS type of the lemmas for which we want to generate a representative sample.")
parser.add_argument("-pos", default=[], nargs='+',
                    type=str, help="POS of the lemmas for which we want to generate a representative sample.")
parser.add_argument("-feats", default='',
                    type=str, help="Features to generate the conjugation tables for.")
parser.add_argument("-dialect", default='', choices=['msa', 'glf', 'egy', ''],
                    type=str, help="Aspect to generate the conjugation tables for.")
parser.add_argument("-repr_lemmas", default='',
                    type=str, help="Name of the file in conjugation/repr_lemmas/ from which to load the representative lemmas from.")
parser.add_argument("-output_name", default='',
                    type=str, help="Name of the file to output the conjugation tables to in conjugation/tables/ directory.")
parser.add_argument("-output_dir", default='',
                    type=str, help="Path of the directory to output the tables to.")
parser.add_argument("-lemmas_dir", default='',
                    type=str, help="Path of the directory to output the tables to.")
parser.add_argument("-db_dir", default='',
                    type=str, help="Path of the directory to load the DB from.")
parser.add_argument("-lemma_debug", default=[], action='append',
                    type=str, help="Lemma (without _1) to debug. Use the following format after the flag: lemma pos:val gen:val num:val")
parser.add_argument("-camel_tools", default='local', choices=['local', 'official'],
                    type=str, help="Path of the directory containing the camel_tools modules.")
args, _ = parser.parse_known_args([] if "__file__" not in globals() else None)

if args.camel_tools == 'local':
    camel_tools_dir = 'camel_morph/camel_tools'
    sys.path.insert(0, camel_tools_dir)

from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.generator import Generator
from camel_tools.utils.charmap import CharMapper
from camel_tools.morphology.utils import strip_lex

from camel_morph.utils.utils import assign_pattern

bw2ar = CharMapper.builtin_mapper('bw2ar')
ar2bw = CharMapper.builtin_mapper('ar2bw')

CLITIC_FEATURES = ['prc0', 'prc1', 'prc1.5', 'prc2', 'prc3', 'enc0', 'enc1']
TEST_FEATS_VERB = ['pos', 'asp', 'vox', 'per', 'gen', 'num', 'mod'] + CLITIC_FEATURES
TEST_FEATS_NOM = ['pos', 'gen', 'num', 'stt', 'cas'] + CLITIC_FEATURES
TEST_FEATS_OTHER_OBLIG = ['asp', 'per', 'gen', 'num', 'vox', 'mod', 'stt', 'cas']
TEST_FEATS_OTHER = ['pos'] + TEST_FEATS_OTHER_OBLIG + CLITIC_FEATURES


AFFIX_STEM_CLASSES = ['[STEM-NOMINATIVE]', '[STEM-ACCUSATIVE]', '[STEM-GENITIVE]',
                      '[STEM-CONST]', '[STEM-NOM]', '[STEM-ADJ]']


# <POS>.<A><P><G><N>.<S><C><V><M>
SIGNATURE_PATTERN = re.compile(
    r'([^\.]+)\.([^\.]{,4})\.?([^\.]{,4})\.?P?(\d{,2})?\.?E?(\d{,2})?')

sig2feat = {
    'feats0': {
        'pos': ["ABBREV", "ADJ", "ADJ_COMP", "ADJ_NUM", "ADV",
                "ADV_INTERROG", "ADV_REL", "CONJ", "CONJ_SUB",
                "DIGIT", "FORIEGN", "INTERJ", "NOUN", "NOUN_NUM",
                "NOUN_PROP", "NOUN_QUANT", "PART", "PART_CONNECT",
                "PART_DET", "PART_EMPHATIC", "PART_FOCUS", "PART_FUT",
                "PART_INTERROG", "PART_NEG", "PART_PROG", "PART_RC",
                "PART_RESTRICT", "PART_VERB", "PART_VOC", "PREP",
                "PRON", "PRON_DEM", "PRON_EXCLAM", "PRON_INTERROG",
                "PRON_REL", "PUNC", "VERB", "VERB_NOM", "VERB_PSEUDO"]},
    'feats1': {
        'asp': ['P', 'I', 'C'],
        'per': ['1', '2', '3'], 
        'gen': ['M', 'F', 'U'], 
        'num': ['S', 'D', 'Q']},
    'feats2': {
        'stt': ['D', 'I', 'C'],
        'cas': ['N', 'G', 'A', 'U'],
        'vox': ['A', 'P'],
        'mod': ['S', 'I', 'J', 'E', 'X']},
    'feats3': {
        'prc0': {
            'NOM': ['Al_det']
        },
        'prc1.5': {
            'NOM': []
        },
        'prc1': {
            'NOM': [],
            'OTHER': ['bi_prep', 'li_prep']
        },
        'prc2': {
            'NOM': [],
            'OTHER': ['wa_conj']
        },
        'prc3': {
            'NOM': []
        },
    },
    'feats4': {
        'enc0': {
            'VERB':['3ms_dobj'],
            'NOM': ['3ms_poss', '1s_poss'],
            'OTHER': ['3ms_pron', 'mA_rel', 'mA_sub']
        },
        'enc1': {
            'VERB':['3ms_dobj'],
            'NOM': ['3ms_poss']
        }
    }
}

HEADER = [
    'line', 'status', 'count', 'signature', 'lemma', 'diac_ar', 'diac', 'freq',
    'qc', 'comments', 'pattern', 'stem', 'bw', 'gloss', 'cond-s', 'cond-t',
    'pref-cat', 'stem-cat', 'suff-cat', 'feats', 'debug', 'color'
]

def parse_signature(signature, pos):
    match = SIGNATURE_PATTERN.search(signature)
    feats0, feats1, feats2, feats3, feats4 = match.groups()
    feats = {'feats1': feats1, 'feats2': feats2, 'feats3': feats3, 'feats4': feats4}
    pos_type = feats0
    features_ = {'pos': [pos]}
    for sig_component, comp_content in feats.items():
        if comp_content:
            for feat, possible_values in sig2feat[sig_component].items():
                if (pos_type == 'VERB' and feat in ['stt', 'cas']) or \
                    (pos_type == 'NOM' and feat in ['per', 'asp', 'mod', 'vox']):
                    continue
                if sig_component in ['feats3', 'feats4']:
                    for comp_part in comp_content:
                        if comp_part == feat[3:]:
                            for possible_value in possible_values.get(pos_type, []):
                                features_.setdefault(feat, []).append(possible_value)
                else:
                    for possible_value in possible_values:
                        feat_present = comp_content.count(possible_value)
                        if feat_present:
                            features_.setdefault(feat, []).append(
                                'p' if feat == 'num' and possible_value == 'Q' else possible_value.lower())
                            features_[feat] = [v for v in features_[feat] if v != '']
                            break
                        else:
                            features_.setdefault(feat, []).append('')

    features_multiple, features_single = {}, {}
    for feat, values in features_.items():
        values_ = set(values)
        if values_ == {''}:
            continue
        elif len(values_) == 1:
            features_single.update({feat: values[0]})
        else:
            for v in values_:
                features_multiple.setdefault(feat, []).append((feat, v))
    
    features = []
    if features_multiple:
        for split_combs in product(*features_multiple.values()):
            features_temp = {comb[0]: comb[1] for comb in split_combs}
            features_temp.update(features_single)
            features.append(features_temp)
    else:
        features.append(features_single)
    
    return features

def expand_paradigm(paradigms, pos_type, paradigm_key):
    paradigm = paradigms[pos_type][paradigm_key]
    paradigm_ = paradigm['paradigm'][:]
    if pos_type == 'verbal':
        if paradigm.get('passive'):
            paradigm_ += [re.sub('A', 'P', signature)
                          for signature in paradigm['paradigm']]
        else:
            paradigm_ = paradigm['paradigm'][:]
    elif pos_type == 'nominal':
        pass
    
    if paradigm.get('enclitics'):
        paradigm_ += [signature + '.E0' for signature in paradigm_]
            
    return paradigm_


def _generate_other_pos_paradigm_slot(info, pos_type, defaults, defines):
    test_feats_other = TEST_FEATS_OTHER_OBLIG + CLITIC_FEATURES
    chosen_features = [f for f in test_feats_other if defaults[f] != 'na']
    features_ = {}
    for f in chosen_features:
        if f in info and strip_brackets(info[f]):
            features_.setdefault('fixed', []).append(f)
        else:
            features_.setdefault('variable', []).append(f)
    
    feature_combs = [[None]] * len(test_feats_other)
    if 'variable' in features_:
        for f in features_['variable']:
            if f in CLITIC_FEATURES:
                sig = 'feats3' if 'prc' in f else 'feats4'
                values = sig2feat[sig][f].get('OTHER', [])
                values = [None] + [v for v in defines[f] if v in values]
                if values:
                    feature_combs[test_feats_other.index(f)] = values
            else:
                feature_combs[test_feats_other.index(f)] = [
                    v for v in defines[f] if v not in ['na', 'b'] and (f == 'cas' or v != 'u')]
    if 'fixed' in features_ :
        for f in features_['fixed']:
            feature_combs[test_feats_other.index(f)] = [strip_brackets(info[f])]

    feature_combs = list(product(*feature_combs))
    paradigm = []
    for feature_comb in feature_combs:
        if pos_type == 'verbal':
            pos_type_ = 'VERB'
        elif pos_type == 'nominal':
            pos_type_ = 'NOM'
        else:
            pos_type_ = pos_type
        
        slot = [pos_type_.upper()]
        slot += [''] * len(test_feats_other)
        for i, f in enumerate(test_feats_other):
            if feature_comb[i] is not None:
                if i < test_feats_other.index('prc0'):
                    slot[i + 1] = feature_comb[i].upper()
                else:
                    slot[i + 1] = f'{f[0].upper()}{f[-1]}_{feature_comb[i]}'

        slot.insert(1, '.'); slot.insert(6, '.'); slot.insert(8, '.')
        slot.insert(12, '.'); slot.insert(18, '.')
        

        slot = re.sub(r'\.+', '.', ''.join(slot))
        feats = {f: feature_comb[i] for i, f in enumerate(test_feats_other)
                 if feature_comb[i] is not None}
        feats['pos'] = strip_brackets(info['pos'])
        paradigm.append((feats,  ''.join(slot)))

    return paradigm


def filter_and_status(outputs):
    # If analysis is the same except for stemgloss, filter out (as duplicate)
    signature_outputs = []
    for output_no_gloss, outputs_same_gloss in outputs.items():
        output = outputs_same_gloss[0]
        signature_outputs.append(output)

    gloss2outputs = {}
    for so in signature_outputs:
        gloss2outputs.setdefault(so['gloss'], []).append(so)
    signature_outputs_ = []
    count = 0
    for outputs in gloss2outputs.values():
        for output in outputs:
            count += 1
            signature_outputs_.append(output)
            if len(set([tuple([o['diac'], o['bw']]) for o in outputs])) == 1 or \
                    len(re.findall(r'\[.+?\]', output['cond-s'])) == 6 and len(outputs) == 2:
                break
    for so in signature_outputs_:
        so['count'] = count
        so['status'] = 'OK-ONE' if count == 1 else 'CHECK-GT-ONE'

    if len(signature_outputs_) > 1:
        if len(set([(so['diac'], so['bw']) for so in signature_outputs_])) == 1 or \
            '-' in so['lemma'] and \
            len(set([(so['pref-cat'], re.sub('intrans', 'trans', so['stem-cat']), so['suff-cat']) for so in signature_outputs_])) == 1:
            for signature_output in signature_outputs_:
                signature_output['status'] = 'OK-GT-ONE'
    
    return signature_outputs_

def strip_brackets(info):
    if info[0] == '[' and info[-1] == ']':
        info = info[1:-1]
    return info

def create_conjugation_tables(config,
                              paradigm_key,
                              repr_lemmas=None,
                              HEADER=HEADER):
    pos_type, paradigms, generator, repr_lemmas = setup(
        config, paradigm_key, repr_lemmas)

    lemmas_conj = []
    for info in tqdm(repr_lemmas):
        lemma, form = info['lemma'], info['form']
        gloss, bw = info.get('gloss', '_'), info.get('bw', '_')
        pos, gen, num = info['pos'], info.get('gen', '-'), info.get('num', '-')
        cond_s, cond_t = info['cond_s'], info['cond_t']
        lemma_raw = lemma[:]
        lemma = strip_lex(lemma)
        pattern = None
        pos_type_, paradigm_key_ = pos_type, paradigm_key
        if pos_type == 'other' and strip_brackets(info['morph_class']) in AFFIX_STEM_CLASSES:
            pos_type_ = 'nominal'
        
        if pos_type_ == 'verbal':
            pattern = assign_pattern(lemma)['pattern_conc']
        elif pos_type_ == 'nominal':
            match = re.search(r'([MF][SDP])', cond_t)
            form_gen, form_num = None, None
            if match:
                form_gen, form_num = match.groups()[0].lower()
            
            num = process_nom_gen_num_(
                num, form_num, form, cond_t, cond_s, gloss, lemma, pattern, pos, info.get('freq'))
            gen = process_nom_gen_num_(
                gen, form_gen, form, cond_t, cond_s, gloss, lemma, pattern, pos, info.get('freq'))
            if type(num) is dict or type(gen) is dict:
                outputs = {}
                outputs['N/A'] = num if type(num) is dict else gen 
                lemmas_conj.append(outputs)
                continue
            
            paradigm_key_ = f'gen:{gen} num:{num}'

        lemma_ar = bw2ar(lemma_raw)
        
        if pos_type == 'other' and strip_brackets(info['morph_class']) not in AFFIX_STEM_CLASSES:
            paradigm = _generate_other_pos_paradigm_slot(
                info, pos_type_, generator._db.defaults[strip_brackets(pos)], generator._db.defines)
        else:
            paradigm = expand_paradigm(paradigms, pos_type_, paradigm_key_)
        
        outputs = {}
        for signature in paradigm:
            if type(signature) is tuple:
                features, signature = signature
                features = [features]
            else:
                features = parse_signature(signature, strip_brackets(pos))
            # This assumes that if we have multiple feature sets, they are all similiar
            # in all feature dimensions except for one (thus the break).
            diff = ''
            if len(features) > 1:
                for k, v in features[0].items():
                    if v != features[1][k]:
                        diff = k
                        break
            for features_ in features:
                # if pos_type_ == 'other':
                #     discard = False
                #     for f, v in features_.items():
                #         if f != 'pos' and f in info:
                #             if v != _strip_brackets(info[f]):
                #                 discard = True
                #                 break
                #     if discard:
                #         continue

                # Using altered local copy of generator.py in camel_tools
                analyses, debug_message = generator.generate(lemma_ar, features_, debug=True)
                prefix_cats = [a[1] for a in analyses]
                stem_cats = [a[2] for a in analyses]
                suffix_cats = [a[3] for a in analyses]
                analyses = [a[0] for a in analyses]
                debug_info = dict(analyses=analyses,
                                  pos_type=pos_type_,
                                  gloss=gloss,
                                  bw=bw,
                                  form=form,
                                  gen=gen,
                                  num=num,
                                  enc0=info.get('enc0', ''),
                                  cond_s=cond_s,
                                  cond_t=cond_t,
                                  prefix_cats=prefix_cats,
                                  stem_cats=stem_cats,
                                  suffix_cats=suffix_cats,
                                  lemma=info['lemma'],
                                  morph_class=info['morph_class'],
                                  pattern=pattern,
                                  pos=pos,
                                  freq=info.get('freq'),
                                  features=features_,
                                  debug_message=debug_message)
                outputs[f"{signature}{f'_{features_[diff]}' if len(features) > 1 else ''}"] = debug_info

        lemmas_conj.append(outputs)

    outputs = process_outputs(lemmas_conj, pos_type, HEADER)
    outputs_ = {}
    for row in outputs[1:]:
        for h, value in row.items():
            outputs_.setdefault(h, []).append(value)
    outputs_df = pd.DataFrame(outputs_)

    return outputs_df

def process_nom_gen_num_(feat, form_feat,
                         form=None, cond_t=None, cond_s=None, gloss=None,
                         bw=None, lemma=None, pattern=None, pos=None,
                         freq=None):
    feat_ = strip_brackets(feat)
    if feat_ == '-':
        if form_feat:
            feat_ = form_feat
        else:
            debug_info = dict(analyses=[],
                              gloss=gloss,
                              bw=bw,
                              form=form,
                              cond_s=cond_s,
                              cond_t=cond_t,
                              prefix_cats=[],
                              stem_cats=[],
                              suffix_cats=[],
                              lemma=lemma,
                              pattern=pattern,
                              pos=pos,
                              freq=freq,
                              features={},
                              debug_message='')
            return debug_info
    return feat_


def process_outputs(lemmas_conj, pos_type, HEADER):
    conjugations = []
    color, line = 0, 1
    for paradigm in lemmas_conj:
        for signature, info in paradigm.items():
            output = {}
            form = strip_brackets(info['form'])
            pos = strip_brackets(info['pos'].upper())
            features = info['features']
            signature = re.sub('Q', 'P', signature)
            output['signature'] = signature
            output['stem'] = info['form']
            output['lemma'] = info['lemma']
            output['pattern'] = info['pattern']
            output['gloss'] = info['gloss']
            output['bw'] = info['bw']
            output['pos'] = info['pos']
            output['cond-s'] = info['cond_s']
            output['cond-t'] = info['cond_t']
            output['color'] = color
            output['freq'] = info['freq']
            output['debug'] = ' '.join([m[1] for m in info['debug_message']])
            output['qc'] = ''
            valid_analyses = False
            if info['analyses']:
                outputs = OrderedDict()
                for i, analysis in enumerate(info['analyses']):
                    if pos_type == 'nominal':
                        stem_bw = f"{bw2ar(form)}/{pos}"
                        test_feats = TEST_FEATS_NOM
                        if stem_bw not in analysis['bw'] or \
                            strip_brackets(info['gloss']) != analysis['stemgloss']:
                            continue
                    elif pos_type == 'verbal':
                        test_feats = TEST_FEATS_VERB
                        if info['lemma'] != ar2bw(analysis['lex']) or \
                            strip_brackets(info['gloss']) != analysis['stemgloss']:
                            continue
                    elif pos_type == 'other':
                        test_feats = TEST_FEATS_OTHER
                        if analysis['stem'] not in bw2ar(form) or \
                            strip_brackets(info['gloss']) != analysis['stemgloss']:
                            continue
                    valid_analyses = True
                    output_ = output.copy()
                    output_['diac'] = ar2bw(analysis['diac'])
                    output_['diac_ar'] = analysis['diac']
                    output_['bw'] = ar2bw(analysis['bw'])
                    output_['pref-cat'] = info['prefix_cats'][i]
                    output_['stem-cat'] = info['stem_cats'][i]
                    output_['suff-cat'] = info['suffix_cats'][i]
                    output_['feats'] = ' '.join(
                        [f"{feat}:{analysis[feat]}" for feat in test_feats if feat in analysis])
                    output_duplicates = outputs.setdefault(tuple(output_.values()), [])
                    output_['gloss'] = analysis['stemgloss']
                    output_duplicates.append(output_)
                outputs_filtered = filter_and_status(outputs)
                for output in outputs_filtered:
                    output['line'] = line
                    line += 1
                    if 'E0' in signature and features.get('vox') and features['vox'] == 'p':
                        output['status'] = 'CHECK-E0-PASS'
                for i, output in enumerate(outputs_filtered):
                    output_ = OrderedDict()
                    for h in HEADER:
                        output_[h.upper()] = output.get(h, '')
                    outputs_filtered[i] = output_
                conjugations += outputs_filtered
            
            if not valid_analyses:
                output_ = output.copy()
                output_['count'] = 0
                zero_check = re.findall(r'intrans|trans', info['cond_s'])
                if 'E0' in signature and len(set(zero_check)) == 1 and zero_check[0] == 'intrans':
                    output_['status'] = 'OK-ZERO-E0-INTRANS'
                elif 'E0' in signature and features.get('vox') == 'p':
                    output_['status'] = 'OK-ZERO-E0-PASS'
                elif 'C' in signature and features.get('vox') == 'p':
                    output_['status'] = 'OK-ZERO-CV-PASS'
                elif ('C1' in signature or 'C3' in signature) and features.get('asp') == 'c':
                    output_['status'] = 'OK-ZERO-CV-PER'
                elif 'Frozen' in output['cond-s'] and features.get('vox') == 'p':
                    output_['status'] = 'OK-ZERO-FROZEN-PASS'
                elif features.get('vox') == 'p':
                    output_['status'] = 'CHECK-ZERO-PASS'
                elif 'E0' in signature and features.get('stt') == 'd':
                    output_['status'] = 'OK-ZERO-E0-DEFINITE'
                elif pos.lower() == 'adj' and 'E0' in signature and features.get('stt') == 'c':
                    output_['status'] = 'OK-ZERO-E0-ADJ-CONSTRUCT'
                elif 'E0' in signature and re.search(r'\[STEM-(CONJ(-PREP)?|STANDALONE)\]', info['morph_class']):
                    output_['status'] = 'OK-ZERO-OTHER-PRON'
                elif 'P1' in signature and re.search(r'\[STEM-(CONJ(-PRON)?|STANDALONE|POSS)\]', info['morph_class']):
                    output_['status'] = 'OK-ZERO-OTHER-PREP'
                elif 'P2' in signature and re.search(r'\[STEM-STANDALONE\]', info['morph_class']):
                    output_['status'] = 'OK-ZERO-OTHER-CONJ'
                elif 'E0_mA' in signature and not bool(re.search(r'm[aA]', info['enc0'])):
                    output_['status'] = 'OK-ZERO-OTHER-MA'
                else:
                    output_['status'] = 'CHECK-ZERO'
                output_['line'] = line
                output_ordered = OrderedDict()
                for h in HEADER:
                    output_ordered[h.upper()] = output_.get(h, '')
                if 'OK-ZERO' not in output_ordered['STATUS']:
                    conjugations.append(output_ordered)
                    line += 1
            color = abs(color - 1)
    
    conjugations.insert(0, OrderedDict((i, x) for i, x in enumerate(map(str.upper, HEADER))))
    return conjugations


def setup(config:Config, feats, repr_lemmas):
    db = MorphologyDB(config.get_db_path(), flags='gd')
    generator = Generator(db, variant=config.dialect)
    
    paradigms = args.paradigms if args.paradigms else config.paradigms_config
    dialect = args.dialect if args.dialect else config.dialect
    with open(paradigms) as f:
        paradigms = json.load(f)[dialect]
    
    pos_type = args.pos_type if args.pos_type else config.pos_type
    if pos_type == 'verbal':
        pos = ['verb']
    elif pos_type == 'nominal':
        pos = args.pos if args.pos else config.pos
        pos = pos if pos is not None else POS_NOMINAL
    elif pos_type == 'other':
        pos = args.pos
    else:
        pos = config.pos
    POS = pos if type(pos) is list else [pos]

    if args.lemma_debug:
        lemma_debug = args.lemma_debug[0].split()
        lemma = lemma_debug[0]
        feats = {feat.split(':')[0]: feat.split(':')[1] for feat in lemma_debug[1:]}
        repr_lemmas = {
            '': dict(
                form='-',
                lemma=lemma.replace('\\', ''),
                cond_t='-',
                cond_s='-',
                pos=feats['pos'],
                gen=feats['gen'],
                num=feats['num']
            )
        }
    elif repr_lemmas is None:
        with open(config.get_repr_lemmas_path(), 'rb') as f:
            repr_lemmas = pickle.load(f)
            repr_lemmas = list(repr_lemmas.values())

    repr_lemmas = [info for info in list(repr_lemmas.values())
                   if not POS or strip_brackets(info['pos']) in POS]
    return pos_type, paradigms, generator, repr_lemmas


if __name__ == "__main__":
    config = Config(args.config_file, args.config_name)
    
    output_dir = args.output_dir if args.output_dir else config.get_docs_tables_dir_path()
    os.makedirs(output_dir, exist_ok=True)
        
    outputs_df = create_conjugation_tables(config=config,
                                        paradigm_key=args.feats)
    
    if not args.lemma_debug:
        output_name = args.output_name if args.output_name \
            else config.debugging.debugging_feats.conj_tables
        output_path = os.path.join(output_dir, output_name)
        outputs_df.to_csv(output_path, sep='\t')
