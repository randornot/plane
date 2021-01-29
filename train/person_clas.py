import os
import os.path as osp

import cv2
import paddle
import paddle.vision.transforms as vt
from util.model import HumanClas

data_dir = "/home/aistudio/plane/bend/"


class HumanClasDataset(paddle.io.Dataset):
    def __init__(self, mode="train"):
        super(HumanClasDataset, self).__init__()
        self.data_path = data_dir
        ps = os.listdir(osp.join(self.data_path, "p"))
        ns = os.listdir(osp.join(self.data_path, "n"))
        ps.sort()
        ns.sort()
        ps = [osp.join("p", n) for n in ps]
        ns = [osp.join("n", n) for n in ns]
        data = []
        if mode == "train":
            for idx in range(int(len(ps) * 0.8)):
                data.append([ps[idx], 1])
            for idx in range(int(len(ns) * 0.8)):
                data.append([ns[idx], 0])
        else:
            for idx in range(int(len(ps) * 0.8), len(ps)):
                data.append([ps[idx], 1])
            for idx in range(int(len(ns) * 0.8), len(ns)):
                data.append([ns[idx], 0])
        self.data = data
        self.transform = vt.Compose([vt.ToTensor()])  # TODO: 增加更多的数据增强

    def __getitem__(self, index):
        data = cv2.imread(osp.join(self.data_path, self.data[index][0]))
        data = self.transform(data)
        label = self.data[index][1]
        return data, label

    def __len__(self):
        return len(self.data)


train_dataset = HumanClasDataset(mode="train")
eval_dataset = HumanClasDataset(mode="eval")

clas = HumanClas()
model = clas.model
model.prepare(
    paddle.optimizer.Adam(parameters=ClasModel.parameters()),
    paddle.nn.CrossEntropyLoss(),
    paddle.metric.Accuracy(),
)
model.fit(train_dataset, batch_size=32, epochs=100, verbose=2)
model.save("../model/best/person_clas/person_clas", training=True)

model.evaluate(eval_dataset, verbose=1)