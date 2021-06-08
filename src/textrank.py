from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer

class GraphMatrix():
    def __init__(self):
        self.tfidf = TfidfVectorizer()
        self.cnt_vec = CountVectorizer()
        self.graph_sentence = []

    def build_words_graph(self, sentence):
        cnt_vec_mat = normalize(self.cnt_vec.fit_transform(sentence).toarray().astype(float), axis=0)
        vocab = self.cnt_vec.vocabulary_
        return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word]: word for word in vocab}

class Rank():
    def get_ranks(self, graph, d=0.85):
        A = graph
        matrix_size = A.shape[0]
        # tf-idf
        for id in range(matrix_size):
            A[id, id] = 0
            link_sum = np.sum(A[:, id])
            if link_sum != 0:
                A[:, id] /= link_sum
            A[:, id] *= -d
            A[id, id] = 1

        B = (1-d) * np.ones((matrix_size, 1))
        ranks = np.linalg.solve(A, B)
        return {idx: r[0] for idx, r in enumerate(ranks)}


class TextRank():
    def __init__(self, text):
        # text: 명사 추출 끝난 문장 (list of str type)
        self.nouns = text
        self.graph_matrix = GraphMatrix()
        self.words_graph, self.idx2word = self.graph_matrix.build_words_graph(
            self.nouns)

    def keywords(self, word_num=10):
        rank = Rank()
        rank_idx = rank.get_ranks(self.words_graph)  # rank_idx == index : rank
        sorted_rank_idx = sorted(
            rank_idx, key=lambda k: rank_idx[k], reverse=True)

        keywords = {}
        index = []
        for idx in sorted_rank_idx[:word_num]:
            index.append(idx)

        for idx in index:
            keywords[self.idx2word[idx]] = rank_idx[idx]

        return keywords
