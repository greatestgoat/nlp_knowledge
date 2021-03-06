from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, Embedding, LSTM, Bidirectional
import tensorflow as tf
from transformers import TFBertForTokenClassification, BertConfig

class UnidirectionalModel:

    def __init__(self, input_dim, output_dim, emb_dim=100, hid_dim=100):
        self.input = Input(shape=(None,), name='input')
        self.embedding = Embedding(input_dim=input_dim,
                                    output_dim=output_dim,
                                    mask_zero=True,
                                    name='embedding')
        
        self.lstm = LSTM(hid_dim,
                        return_sequences=True,              # デフォルトはFalseで最終の出力しかしないがTrueとすることで経過を出力し系列ラベリングが行えるようになる
                        name="lstm")
        self.fc = Dense(output_dim, activation='softmax')

    def build(self):
        x = self.input
        embedding = self.embedding(x)
        lstm = self.lstm(embedding)
        y = self.fc(lstm)
        return Model(inputs=x, outputs=y)

class BidirectionalModel:

    def __init__(self, input_dim, output_dim, emb_dim=100, hid_dim=100):
        self.input = Input(shape=(None,), name='input')
        self.embedding = Embedding(input_dim=input_dim,
                                    output_dim=output_dim,
                                    mask_zero=True,
                                    name='embedding')
        
        lstm = LSTM(hid_dim,
                        return_sequences=True,              # デフォルトはFalseで最終の出力しかしないがTrueとすることで経過を出力し系列ラベリングが行えるようになる
                        name="lstm")
        self.bilstm = Bidirectional(lstm, name='bilstm')
        self.fc = Dense(output_dim, activation='softmax')

    def build(self):
        x = self.input
        embedding = self.embedding(x)
        lstm = self.bilstm(embedding)
        y = self.fc(lstm)
        return Model(inputs=x, outputs=y)

def build_model(pretrained_model_name_or_path, num_labels):
    config = BertConfig.from_pretrained(
            pretrained_model_name_or_path,
            num_labels=num_labels
    )
    model = TFBertForTokenClassification.from_pretrained(
        pretrained_model_name_or_path,
        config=config
    )
    model.layers[-1].activation = tf.keras.activations.softmax
    return model

def loss_func(num_labels):
    loss_fct = tf.keras.losses.SparseCategoricalCrossentropy(reduction=tf.keras.losses.Reduction.NONE)

    def loss(y_true, y_pred):
        pad_token = 0
        input_mask = tf.not_equal(y_true, pad_token)
        logits = tf.reshape(y_pred, (-1, num_labels))
        active_loss = tf.reshape(input_mask, (-1,))
        active_logits = tf.boolean_mask(logits, active_loss)
        train_labels = tf.reshape(y_true, (-1,))
        active_labels = tf.boolean_mask(train_labels, active_loss)
        cross_entropy = loss_fct(active_labels, active_logits)
        return cross_entropy
    return loss