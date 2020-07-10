from abc import ABCMeta, abstractmethod

class baseModel(metaclass=ABCMeta):
    @abstractmethod
    def predict_score(self, user_id, item_id):
        pass

    @abstractmethod
    def recommend_items(self, user_id, num=6):
        pass