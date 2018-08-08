from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.callbacks import TensorBoard, ModelCheckpoint

import numpy as np

import os


class Model(object):
    def __init__(self, data=None, layers=[], model=None, model_path=None):
        """

        data: object of type data.Data
        layers: a list of dicts, each representing a layer
        model: object of type of model.Model
        model_path: filepath where a keras model is saved
        """
        if data:
            self.data = data.binarized
        if model:
            self.model = model.model
        elif model_path:
            self.model = load_model(model_path)
        else:
            self.model = self.__build_model(layers)
        self.inputs = []
        self.targets = []
        self.loss = -1
        self.accuracy = -2


    def __getitem__(self, *args):
        if isinstance(*args, str):
            return self.__dict__[str(*args)]
        keys = list(*args)
        return [self.__dict__[key] for key in keys]

    @property
    def input_dim(self):
        return self.data.shape[1] - 1 # not include the output dim

    @property
    def output_dim(self):
        return len(set(self.data.attack_types))

    def __build_model(self, layers):
        # layers = [{'neurons': neurons, 'activation': activation, ...}, 
                  # {'neurons': neurons, 'activation': activation, ...},
                  #  ... ]
        model = Sequential()
        model.add(Dense(layers[0]['neurons'], input_shape=(self.input_dim,), activation=layers[0]['activation']))
        for layer in layers[1:]:
            model.add(Dense(layer['neurons'], activation=layer['activation']))
        model.add(Dense(self.output_dim, activation='softmax'))
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        return model

    def train(self, batch_size=128, epochs=10, verbose=1):
        self.model.fit(self.data.X, self.data.Y, batch_size=batch_size, epochs=epochs, verbose=verbose)
        return self

    def test(self, data=None):
        if data:
            data = data.binarized
        else:
            data = self.data
        self.loss, self.accuracy = self.model.evaluate(data.X, data.Y)
        return self

    def save(self, path):
        loss, acc = round(self.loss, 4), round(100*self.accuracy, 2)
        to_file = 'kddcupmodel-loss{}-acc{}.h5'.format(loss, acc)
        self.model.save(os.path.join(path, to_file))
        return self

    def load(self, path):
        self.model = load_model(path)
        return self

    
class KddCupModel(object):
    def __init__(self, data=None, model=None, model_path=None):
        """

        data: object of type data.KddCupData
        model: object of type model.Model
        """
        if data:
            self.data = data
        if model_path:
            self.model = Model(model_path=model_path)
        else:
            self.model = model
        self.loss = -1
        self.accuracy = -2

    def __getitem__(self, *args):
        if isinstance(*args, str):
            return self.__dict__[str(*args)]
        keys = list(*args)
        return [self.__dict__[key] for key in keys]
    
    def train(self, inputs=[], targets=[], layers=[], batch_size=128, epochs=5, verbose=1):
        for d in self.data:
            self.model = Model(d[inputs][targets], layers=layers, model=self.model)
            if self.model.output_dim == len(targets):
                self.model.train(batch_size=batch_size, epochs=epochs, verbose=verbose)
            else:
                print("Skipping..")
        self.model.inputs, self.model.targets = inputs, targets
        return self

    def test(self, data=None, inputs=[], targets=[]):
        if not data:
            data = self.data
        if not inputs and not targets:
            inputs, targets = self.model.inputs, self.model.targets
        l_a = [self.model.test(d[inputs][targets])['loss', 'accuracy'] for d in data]
        loss, acc = np.array(l_a).mean(axis=0)
        self.loss = loss
        self.accuracy = acc
        return self

    def save(self, path):
        self.model.save(path)
        return self

    def load(self, path):
        self.model.load(path)
        return self