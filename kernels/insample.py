import os
import re
import gc
import string
import unicodedata
import operator
import numpy as np
import pandas as pd

from sklearn import utils
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras import backend as K
from keras import initializers, regularizers, constraints
from keras.engine.topology import Layer
from keras.layers import (Input, Embedding, SpatialDropout1D, Bidirectional,
                          CuDNNLSTM, CuDNNGRU, GlobalMaxPool1D, Concatenate,
                          Dropout, Dense)
from keras.models import Model
from keras.callbacks import (EarlyStopping, ModelCheckpoint,
                             ReduceLROnPlateau)

from tqdm import tqdm
tqdm.pandas()

"""
utils
"""


def load_data(datapath):
    print("loading data ......")
    df_train = pd.read_csv(os.path.join(datapath, "train.csv"))
    df_test = pd.read_csv(os.path.join(datapath, "test.csv"))
    print("train data with shape : ", df_train.shape)
    print("test data with shape : ", df_test.shape)
    return df_train, df_test


"""
nlp
"""


def clean_misspell(text):
    """
    misspell list (quora vs. glove)
    """
    misspell_to_sub = {
        'Terroristan': 'terrorist Pakistan',
        'terroristan': 'terrorist Pakistan',
        'BIMARU': 'Bihar, Madhya Pradesh, Rajasthan, Uttar Pradesh',
        'Hinduphobic': 'Hindu phobic',
        'hinduphobic': 'Hindu phobic',
        'Hinduphobia': 'Hindu phobic',
        'hinduphobia': 'Hindu phobic',
        'Babchenko': 'Arkady Arkadyevich Babchenko faked death',
        'Boshniaks': 'Bosniaks',
        'Dravidanadu': 'Dravida Nadu',
        'mysoginists': 'misogynists',
        'MGTOWS': 'Men Going Their Own Way',
        'mongloid': 'Mongoloid',
        'unsincere': 'insincere',
        'meninism': 'male feminism',
        'jewplicate': 'jewish replicate',
        'unoin': 'Union',
        'daesh': 'Islamic State of Iraq and the Levant',
        'Kalergi': 'Coudenhove-Kalergi',
        'Bhakts': 'Bhakt',
        'bhakts': 'Bhakt',
        'Tambrahms': 'Tamil Brahmin',
        'Pahul': 'Amrit Sanskar',
        'SJW': 'social justice warrior',
        'SJWs': 'social justice warrior',
        ' incel': ' involuntary celibates',
        ' incels': ' involuntary celibates',
        'emiratis': 'Emiratis',
        'weatern': 'western',
        'westernise': 'westernize',
        'Pizzagate': 'Pizzagate conspiracy theory',
        'naïve': 'naive',
        'Skripal': 'Sergei Skripal',
        'Remainers': 'British remainer',
        'remainers': 'British remainer',
        'bremainer': 'British remainer',
        'antibrahmin': 'anti Brahminism',
        'HYPSM': ' Harvard, Yale, Princeton, Stanford, MIT',
        'HYPS': ' Harvard, Yale, Princeton, Stanford',
        'kompromat': 'compromising material',
        'Tharki': 'pervert',
        'tharki': 'pervert',
        'mastuburate': 'masturbate',
        'Zoë': 'Zoe',
        'indans': 'Indian',
        ' xender': ' gender',
        'Naxali ': 'Naxalite ',
        'Naxalities': 'Naxalites',
        'Bathla': 'Namit Bathla',
        'Mewani': 'Indian politician Jignesh Mevani',
        'clichéd': 'cliche',
        'cliché': 'cliche',
        'clichés': 'cliche',
        'Wjy': 'Why',
        'Fadnavis': 'Indian politician Devendra Fadnavis',
        'Awadesh': 'Indian engineer Awdhesh Singh',
        'Awdhesh': 'Indian engineer Awdhesh Singh',
        'Khalistanis': 'Sikh separatist movement',
        'madheshi': 'Madheshi',
        'BNBR': 'Be Nice, Be Respectful',
        'Bolsonaro': 'Jair Bolsonaro',
        'XXXTentacion': 'Tentacion',
        'Padmavat': 'Indian Movie Padmaavat',
        'Žižek': 'Slovenian philosopher Slavoj Žižek',
        'Adityanath': 'Indian monk Yogi Adityanath',
        'Brexit': 'British Exit',
        'Brexiter': 'British Exit supporter',
        'Brexiters': 'British Exit supporters',
        'Brexiteer': 'British Exit supporter',
        'Brexiteers': 'British Exit supporters',
        'Brexiting': 'British Exit',
        'Brexitosis': 'British Exit disorder',
        'brexit': 'British Exit',
        'brexiters': 'British Exit supporters',
        'jallikattu': 'Jallikattu',
        'fortnite': 'Fortnite ',
        'Swachh': 'Swachh Bharat mission campaign ',
        'Quorans': 'Quoran',
        'Qoura ': 'Quora ',
        'quoras': 'Quora',
        'Quroa': 'Quora',
        'QUORA': 'Quora',
        'narcissit': 'narcissist',
        # extra in sample
        'Doklam': 'Tibet',
        'Drumpf ': 'Donald Trump fool ',
        'Drumpfs': 'Donald Trump fools',
        'Strzok': 'Hillary Clinton scandal',
        'rohingya': 'Rohingya ',
        'wumao ': 'cheap Chinese stuff',
        'wumaos': 'cheap Chinese stuff',
        'Sanghis': 'Sanghi',
        'Tamilans': 'Tamils',
        'biharis': 'Biharis',
        'Rejuvalex': 'hair growth formula',
        'Feku': 'The Man of India ',
        'deplorables': 'deplorable',
        'muhajirs': 'Muslim immigrant',
        'Gujratis': 'Gujarati',
        'Chutiya': 'Tibet people ',
        'Chutiyas': 'Tibet people ',
        'thighing': 'masturbate',
        '卐': 'Nazi Germany',
        'Pribumi': 'Native Indonesian',
        'Gurmehar': 'Gurmehar Kaur Indian student activist',
        'Novichok': 'Soviet Union agents',
        'Khazari': 'Khazars',
        'Demonetization': 'demonetization',
        'demonetisation': 'demonetization',
        'demonitisation': 'demonetization',
        'demonitization': 'demonetization',
        'demonetisation': 'demonetization',
        'cryptocurrencies': 'cryptocurrency',
        'Hindians': 'North Indian who hate British',
        'vaxxer': 'vocal nationalist ',
        'remoaner': 'remainer ',
        'bremoaner': 'British remainer ',
        'Jewism': 'Judaism',
        'Eroupian': 'European',
        'WMAF': 'White male married Asian female',
        'moeslim': 'Muslim',
        'cishet': 'cisgender and heterosexual person',
        'Eurocentric': 'Eurocentrism ',
        'Jewdar': 'Jew dar',
        'Asifa': 'abduction, rape, murder case ',
        'marathis': 'Marathi',
        'Trumpanzees': 'Trump chimpanzee fool',
        'Crimean': 'Crimea people ',
        'atrracted': 'attract',
        'LGBT': 'lesbian, gay, bisexual, transgender',
        'Boshniak': 'Bosniaks ',
        'Myeshia': 'widow of Green Beret killed in Niger',
        'demcoratic': 'Democratic',
        'raaping': 'rape',
        'Dönmeh': 'Islam',
        'feminazism': 'feminism nazi',
        'langague': 'language',
        'Hongkongese': 'HongKong people',
        'hongkongese': 'HongKong people',
        'Kashmirians': 'Kashmirian',
        'Chodu': 'fucker',
        'penish': 'penis',
        'micropenis': 'tiny penis',
        'Madridiots': 'Real Madrid idiot supporters',
        'Ambedkarite': 'Dalit Buddhist movement ',
        'ReleaseTheMemo': 'cry for the right and Trump supporters',
        'harrase': 'harass',
        'Barracoon': 'Black slave',
        'Castrater': 'castration',
        'castrater': 'castration',
        'Rapistan': 'Pakistan rapist',
        'rapistan': 'Pakistan rapist',
        'Turkified': 'Turkification',
        'turkified': 'Turkification',
        'Dumbassistan': 'dumb ass Pakistan',
        'facetards': 'Facebook retards',
        'rapefugees': 'rapist refugee',
        'superficious': 'superficial',
        # extra from kagglers
        'colour': 'color',
        'centre': 'center',
        'favourite': 'favorite',
        'travelling': 'traveling',
        'counselling': 'counseling',
        'theatre': 'theater',
        'cancelled': 'canceled',
        'labour': 'labor',
        'organisation': 'organization',
        'wwii': 'world war 2',
        'citicise': 'criticize',
        'youtu ': 'youtube ',
        'sallary': 'salary',
        'Whta': 'What',
        'narcisist': 'narcissist',
        'narcissit': 'narcissist',
        'howdo': 'how do',
        'whatare': 'what are',
        'howcan': 'how can',
        'howmuch': 'how much',
        'howmany': 'how many',
        'whydo': 'why do',
        'doI': 'do I',
        'theBest': 'the best',
        'howdoes': 'how does',
        'mastrubation': 'masturbation',
        'mastrubate': 'masturbate',
        'mastrubating': 'masturbating',
        'pennis': 'penis',
        'Etherium': 'Ethereum',
        'bigdata': 'big data',
        '2k17': '2017',
        '2k18': '2018',
        'qouta': 'quota',
        'exboyfriend': 'ex boyfriend',
        'airhostess': 'air hostess',
        'whst': 'what',
        'watsapp': 'whatsapp',
        # extra
        'bodyshame': 'body shaming',
        'bodyshoppers': 'body shopping',
        'bodycams': 'body cams',
        'Cananybody': 'Can any body',
        'deadbody': 'dead body',
        'deaddict': 'de addict',
        'Northindian': 'North Indian ',
        'northindian': 'north Indian ',
        'northkorea': 'North Korea',
        'Whykorean': 'Why Korean',
        'koreaboo': 'Korea boo ',
        'Brexshit': 'British Exit bullshit',
        'shithole': ' shithole ',
        'shitpost': 'shit post',
        'shitslam': 'shit Islam',
        'shitlords': 'shit lords',
        'Fck': 'Fuck',
        'fck': 'fuck',
        'Clickbait': 'click bait ',
        'clickbait': 'click bait ',
        'mailbait': 'mail bait',
        'healhtcare': 'healthcare',
        'trollbots': 'troll bots',
        'trollled': 'trolled',
        'trollimg': 'trolling',
        'cybertrolling': 'cyber trolling',
        'sickular': 'India sick secular ',
        'suckimg': 'sucking',
        'Idiotism': 'idiotism',
        'Niggerism': 'Nigger',
        'Niggeriah': 'Nigger'
    }
    misspell_re = re.compile('(%s)' % '|'.join(misspell_to_sub.keys()))

    def _replace(match):
        """
        reference: https://www.kaggle.com/hengzheng/attention-capsule-why-not-both-lb-0-694 # noqa
        """
        try:
            word = misspell_to_sub.get(match.group(0))
        except KeyError:
            word = match.group(0)
            print('!!Error: Could Not Find Key: {}'.format(word))
        return word
    return misspell_re.sub(_replace, text)


def spacing_misspell(text):
    """
    'deadbody' -> 'dead body'
    """
    misspell_list = [
        '(F|f)uck',
        'Trump',
        '\W(A|a)nti',
        '(W|w)hy',
        '(W|w)hat',
        'How',
        'care\W',
        '\Wover',
        'gender',
        'people',
    ]
    misspell_re = re.compile('(%s)' % '|'.join(misspell_list))
    return misspell_re.sub(r" \1 ", text)


def clean_latex(text):
    """
    convert r"[math]\vec{x} + \vec{y}" to English
    """
    # edge case
    text = re.sub(r'\[math\]', ' LaTex math ', text)
    text = re.sub(r'\[\/math\]', ' LaTex math ', text)
    text = re.sub(r'\\', ' LaTex ', text)

    pattern_to_sub = {
        r'\\mathrm': ' LaTex math mode ',
        r'\\mathbb': ' LaTex math mode ',
        r'\\boxed': ' LaTex equation ',
        r'\\begin': ' LaTex equation ',
        r'\\end': ' LaTex equation ',
        r'\\left': ' LaTex equation ',
        r'\\right': ' LaTex equation ',
        r'\\(over|under)brace': ' LaTex equation ',
        r'\\text': ' LaTex equation ',
        r'\\vec': ' vector ',
        r'\\var': ' variable ',
        r'\\theta': ' theta ',
        r'\\mu': ' average ',
        r'\\min': ' minimum ',
        r'\\max': ' maximum ',
        r'\\sum': ' + ',
        r'\\times': ' * ',
        r'\\cdot': ' * ',
        r'\\hat': ' ^ ',
        r'\\frac': ' / ',
        r'\\div': ' / ',
        r'\\sin': ' Sine ',
        r'\\cos': ' Cosine ',
        r'\\tan': ' Tangent ',
        r'\\infty': ' infinity ',
        r'\\int': ' integer ',
        r'\\in': ' in ',
    }
    # post process for look up
    pattern_dict = {k.strip('\\'): v for k, v in pattern_to_sub.items()}
    # init re
    patterns = pattern_to_sub.keys()
    pattern_re = re.compile('(%s)' % '|'.join(patterns))

    def _replace(match):
        """
        reference: https://www.kaggle.com/hengzheng/attention-capsule-why-not-both-lb-0-694 # noqa
        """
        try:
            word = pattern_dict.get(match.group(0).strip('\\'))
        except KeyError:
            word = match.group(0)
            print('!!Error: Could Not Find Key: {}'.format(word))
        return word
    return pattern_re.sub(_replace, text)


def normalize_unicode(text):
    """
    unicode string normalization
    """
    return unicodedata.normalize('NFKD', text)


def remove_newline(text):
    """
    remove \n and  \t
    """
    text = re.sub('\n', ' ', text)
    text = re.sub('\t', ' ', text)
    text = re.sub('\b', ' ', text)
    text = re.sub('\r', ' ', text)
    return text


def decontracted(text):
    """
    de-contract the contraction
    """
    # specific
    text = re.sub(r"(W|w)on(\'|\’)t", "will not", text)
    text = re.sub(r"(C|c)an(\'|\’)t", "can not", text)
    text = re.sub(r"(Y|y)(\'|\’)all", "you all", text)
    text = re.sub(r"(Y|y)a(\'|\’)ll", "you all", text)

    # general
    text = re.sub(r"(I|i)(\'|\’)m", "i am", text)
    text = re.sub(r"(A|a)in(\'|\’)t", "is not", text)
    text = re.sub(r"n(\'|\’)t", " not", text)
    text = re.sub(r"(\'|\’)re", " are", text)
    text = re.sub(r"(\'|\’)s", " is", text)
    text = re.sub(r"(\'|\’)d", " would", text)
    text = re.sub(r"(\'|\’)ll", " will", text)
    text = re.sub(r"(\'|\’)t", " not", text)
    text = re.sub(r"(\'|\’)ve", " have", text)
    return text


def spacing_punctuation(text):
    """
    add space before and after punctuation and symbols
    """
    regular_punct = list(string.punctuation)
    extra_punct = [
        ',', '.', '"', ':', ')', '(', '-', '!', '?', '|', ';', "'", '$', '&',
        '/', '[', ']', '>', '%', '=', '#', '*', '+', '\\', '•',  '~', '@', '£',
        '·', '_', '{', '}', '©', '^', '®', '`',  '<', '→', '°', '€', '™', '›',
        '♥', '←', '×', '§', '″', '′', 'Â', '█', '½', 'à', '…', '“', '★', '”',
        '–', '●', 'â', '►', '−', '¢', '²', '¬', '░', '¶', '↑', '±', '¿', '▾',
        '═', '¦', '║', '―', '¥', '▓', '—', '‹', '─', '▒', '：', '¼', '⊕', '▼',
        '▪', '†', '■', '’', '▀', '¨', '▄', '♫', '☆', 'é', '¯', '♦', '¤', '▲',
        'è', '¸', '¾', 'Ã', '⋅', '‘', '∞', '∙', '）', '↓', '、', '│', '（', '»',
        '，', '♪', '╩', '╚', '³', '・', '╦', '╣', '╔', '╗', '▬', '❤', 'ï', 'Ø',
        '¹', '≤', '‡', '√', '«', '»', '´', 'º', '¾', '¡', '§', '£', '₤']
    all_punct = ''.join(sorted(list(set(regular_punct + extra_punct))))
    re_tok = re.compile(f'([{all_punct}])')
    return re_tok.sub(r' \1 ', text)


def spacing_digit(text):
    """
    add space before and after digits
    """
    re_tok = re.compile('([0-9])')
    return re_tok.sub(r' \1 ', text)


def spacing_number(text):
    """
    add space before and after numbers
    """
    re_tok = re.compile('([0-9]{1,})')
    return re_tok.sub(r' \1 ', text)


def remove_number(text):
    """
    numbers are not toxic
    """
    return re.sub('\d+', ' ', text)


def remove_space(text):
    """
    remove extra spaces and ending space if any
    """
    text = re.sub('\s+', ' ', text)
    text = re.sub('\s+$', '', text)
    return text


"""
tokenizer
"""


def preprocess(text, remove_num=True):
    """
    preprocess text into clean text for tokenization

    NOTE:
        1. glove supports uppper case words
        2. glove supports digit
        3. glove supports punctuation
        5. glove supports domains e.g. www.apple.com
        6. glove supports misspelled words e.g. FUCKKK
    """
    # # 1. normalize
    # text = normalize_unicode(text)
    # # 2. remove new line
    # text = remove_newline(text)
    # 3. de-contract
    text = decontracted(text)
    # 4. clean misspell
    text = clean_misspell(text)
    # 5. space misspell
    text = spacing_misspell(text)
    # 6. clean_latex
    text = clean_latex(text)
    # 7. space
    text = spacing_punctuation(text)
    # 8. handle number
    if remove_num:
        text = remove_number(text)
    else:
        text = spacing_digit(text)
    # 9. remove space
    text = remove_space(text)
    return text


def tokenize(df_text, max_features):
    # preprocess
    df_text = df_text.progress_apply(preprocess)
    # tokenizer
    tokenizer = Tokenizer(
        num_words=max_features,
        filters='',
        lower=False,
        split=' ')
    # fit to data
    tokenizer.fit_on_texts(list(df_text))
    # tokenize the texts into sequences
    sequences = tokenizer.texts_to_sequences(df_text)
    return sequences, tokenizer


"""
pre-trained embeddeding vector loader
"""


def load_word_embedding(filepath):
    """
    given a filepath to embeddings file, return a word to vec
    dictionary, in other words, word_embedding

    E.g. {'word': array([0.1, 0.2, ...])}
    """
    def _get_vec(word, *arr):
        return word, np.asarray(arr, dtype='float32')

    print('load word embedding ......')
    try:
        word_embedding = dict(_get_vec(*w.split(' ')) for w in open(filepath))
    except UnicodeDecodeError:
        word_embedding = dict(_get_vec(*w.split(' ')) for w in open(
            filepath, encoding="utf8", errors='ignore'))
    # sanity check word vector length
    words_to_del = []
    for word, vec in word_embedding.items():
        if len(vec) != 300:
            words_to_del.append(word)
    for word in words_to_del:
        del word_embedding[word]
    return word_embedding


def create_embedding_weights(word_index, word_embedding,
                             max_features, paragram=False):
    """
    create weights for embedding layer where row is the word index
    and collumns are the embedding dense vector

    Parameters
    ----------
    word_index: dict, mapping of word to word index. E.g. {'the': 2}
        you can get word_index by keras.tokenizer.word_index

    word_embedding: dict, mapping of word to word embedding
        E.g. {'the': array([0.1, 0.2, ...])}
        you can get word_index by above function load_word_embedding and
        embedding filepath

    max_features: int, number of words that we want to keep

    paragram: HACK flag

    Return
    ------
    embedding weights: np.array, with shape (number of words, 300)
    """
    print('create word embedding weights ......')
    # get entire embedding matrix
    mat_embedding = np.stack(word_embedding.values())
    # get shape
    a, b = min(max_features, len(word_index)), mat_embedding.shape[1]
    print('embedding weights matrix with shape: ({}, {})'.format(a, b))
    # init embedding weight matrix
    embedding_mean, embedding_std = mat_embedding.mean(), mat_embedding.std()
    embedding_weights = np.random.normal(embedding_mean, embedding_std, (a, b))
    # mapping
    for word, idx in word_index.items():
        if idx >= a:
            continue
        if paragram:
            word_vec = word_embedding.get(word.lower(), None)
        else:
            word_vec = word_embedding.get(word, None)
        if word_vec is not None:
            embedding_weights[idx] = word_vec
    return embedding_weights


"""
customized Keras layers for deep neural networks
"""


class Attention(Layer):
    def __init__(self, step_dim,
                 W_regularizer=None, b_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, **kwargs):
        """
        Keras Layer that implements an Attention mechanism for temporal data.
        Supports Masking.
        Follows the work of Raffel et al. [https://arxiv.org/abs/1512.08756]
        # Input shape
            3D tensor with shape: (samples, steps, features).
        # Output shape
            2D tensor with shape: (samples, features).
        :param kwargs:
        Just put it on top of an RNN Layer (GRU/LSTM/SimpleRNN) with return_sequences=True. # noqa
        The dimensions are inferred based on the output shape of the RNN.
        Example:
            model.add(LSTM(64, return_sequences=True))
            model.add(Attention())
        """
        self.supports_masking = True
        self.init = initializers.get('glorot_uniform')

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.step_dim = step_dim
        self.features_dim = 0
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 3

        self.W = self.add_weight((input_shape[-1],),
                                 initializer=self.init,
                                 name='{}_W'.format(self.name),
                                 regularizer=self.W_regularizer,
                                 constraint=self.W_constraint)
        self.features_dim = input_shape[-1]

        if self.bias:
            self.b = self.add_weight((input_shape[1],),
                                     initializer='zero',
                                     name='{}_b'.format(self.name),
                                     regularizer=self.b_regularizer,
                                     constraint=self.b_constraint)
        else:
            self.b = None

        self.built = True

    def compute_mask(self, input, input_mask=None):
        return None

    def call(self, x, mask=None):
        features_dim = self.features_dim
        step_dim = self.step_dim

        eij = K.reshape(K.dot(K.reshape(x, (-1, features_dim)),
                        K.reshape(self.W, (features_dim, 1))), (-1, step_dim))

        if self.bias:
            eij += self.b

        eij = K.tanh(eij)

        a = K.exp(eij)

        if mask is not None:
            a *= K.cast(mask, K.floatx())

        a /= K.cast(K.sum(a, axis=1, keepdims=True) + K.epsilon(), K.floatx())

        a = K.expand_dims(a)
        weighted_input = x * a
        return K.sum(weighted_input, axis=1)

    def compute_output_shape(self, input_shape):
        return input_shape[0],  self.features_dim


def get_model(embed_weights):
    input_layer = Input(shape=(MAX_LEN, ), name='input')
    # 1. embedding layer
    # get embedding weights
    print('load pre-trained embedding weights ......')
    input_dim = embed_weights.shape[0]
    output_dim = embed_weights.shape[1]
    x = Embedding(
        input_dim=input_dim,
        output_dim=output_dim,
        weights=[embed_weights],
        trainable=False,
        name='embedding'
    )(input_layer)
    # clean up
    del embed_weights, input_dim, output_dim
    gc.collect()
    # 2. dropout
    x = SpatialDropout1D(rate=0.2)(x)
    # 3. bidirectional lstm & gru
    x = Bidirectional(
        layer=CuDNNLSTM(RNN_UNITS, return_sequences=True),
        name='bidirectional_lstm'
    )(x)
    # (optional), get hidden states
    x = Bidirectional(
        layer=CuDNNGRU(RNN_UNITS, return_sequences=True),
        name='bidirectional_gru'
    )(x)
    # 4. concat global_max_pooling1d and attention
    max_pool = GlobalMaxPool1D(name='global_max_pooling1d')(x)
    atten = Attention(step_dim=MAX_LEN, name='attention')(x)
    x = Concatenate(axis=-1)([max_pool, atten])

    # 5. dense
    x = Dense(units=DENSE_UNITS_1, activation='relu', name='dense_1')(x)
    x = Dropout(rate=0.15)(x)
    x = Dense(units=DENSE_UNITS_2, activation='relu', name='dense_2')(x)
    # 6. output (sigmoid)
    output_layer = Dense(units=1, activation='sigmoid', name='output')(x)
    model = Model(inputs=input_layer, outputs=output_layer)
    # compile model
    model.compile(loss='binary_crossentropy', optimizer='adam')
    return model


def get_callbacks():
    earlystopping = EarlyStopping(monitor='val_loss',
                                  min_delta=0.0001,
                                  patience=2,
                                  verbose=2,
                                  mode='auto')
    checkpoint = ModelCheckpoint(filepath=MODEL_PATH,
                                 monitor='val_loss',
                                 save_best_only=True,
                                 mode='min',
                                 verbose=2)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss',
                                  min_lr=0.0001,
                                  factor=0.6,
                                  patience=1,
                                  verbose=2)
    return [earlystopping, checkpoint, reduce_lr]


"""
metric
"""


def f1_smart(y_true, y_proba):
    scores = {}
    for thres in np.arange(0.1, 0.51, 0.01):
        thres = round(thres, 3)
        scores[thres] = f1_score(y_true, (y_proba > thres).astype(int))
    # get max
    best_thres, best_score = max(scores.items(), key=operator.itemgetter(1))
    return best_score, best_thres


if __name__ == '__main__':
    # config
    DATA_PATH = '../input/'
    GLOVE_PATH = '../input/embeddings/glove.840B.300d/glove.840B.300d.txt'
    PARAGRAM_PATH = '../input/embeddings/paragram_300_sl999/paragram_300_sl999.txt' # noqa
    MODEL_PATH = "weights_best.hdf5"
    HOLDOUT = 0.1
    SEED = 18
    # mdoel config
    BALANCED = False
    BATCH_SIZE = 512
    EPOCHS = 6
    MAX_FEATURES = int(2.5e5)  # total word count = 227,538; clean word count = 186,551   # noqa
    MAX_LEN = 75    # mean_len = 12; Q99_len = 40; max_len = 189;
    RNN_UNITS = 40
    DENSE_UNITS_1 = 128
    DENSE_UNITS_2 = 16

    # load data
    df_train, df_test = load_data(DATA_PATH)
    y_train = df_train.target
    # get split index
    train_test_cut = df_train.shape[0]
    # get all text
    df_text = pd.concat(
        [df_train['question_text'], df_test['question_text']],
        axis=0).reset_index(drop=True)

    # tokenize text
    print('tokenizing text ......')
    sequences, tokenizer = tokenize(df_text, max_features=MAX_FEATURES)
    print('pad sequences ......')
    X = pad_sequences(sequences, maxlen=MAX_LEN, padding='pre', truncating='post')  # noqa
    X_train = X[:train_test_cut]
    # load word embeddings
    print('[1] loading embedding file and create weights')
    glove_word_embed = load_word_embedding(GLOVE_PATH)
    paragram_word_embed = load_word_embedding(PARAGRAM_PATH)
    # create embedding weights matrix
    print('[2] create embedding weights')
    glove_weights = create_embedding_weights(tokenizer.word_index, glove_word_embed, MAX_FEATURES, False)  # noqa
    paragram_weights = create_embedding_weights(tokenizer.word_index, paragram_word_embed, MAX_FEATURES, True)  # noqa
    print('done creating paragram embedding weights')
    # average weights
    embed_weights = np.mean((glove_weights, paragram_weights), axis=0)
    print('embedding weights with shape: {}'.format(embed_weights.shape))

    # train models
    X_t, X_v, y_t, y_v = train_test_split(
        X_train, y_train,
        test_size=HOLDOUT,
        random_state=SEED,
        shuffle=True,
        stratify=y_train)
    # get model
    model = get_model(embed_weights)
    print(model.summary())
    # get class weight
    weights = None
    if BALANCED:
        weights = utils.class_weight.compute_class_weight('balanced', np.unique(y_t), y_t)    # noqa
    # train
    model.fit(
        X_t, y_t,
        batch_size=BATCH_SIZE, epochs=EPOCHS,
        validation_split=0.1,
        verbose=2, callbacks=get_callbacks(),
        class_weight=weights)
    # reload best model
    model.load_weights(MODEL_PATH)
    # get f1 threshold
    y_proba = model.predict([X_v], batch_size=1024, verbose=2)
    f1, threshold = f1_smart(np.squeeze(y_v), np.squeeze(y_proba))
    print('optimal F1: {:.4f} at threshold: {:.4f}'.format(f1, threshold))
