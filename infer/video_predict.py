import os
import os.path as osp
import argparse

import cv2
from tqdm import tqdm
import numpy as np

from util.util import BB, crop, Stream, dbb, dpoint
from util.model import PdxDet, HumanClas

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-i",
    "--input",
    type=str,
    default="/home/aistudio/plane/vid-split/train",
    help="视频存放路径",
)
parser.add_argument("-o", "--output", type=str, default="/home/aistudio/plane/temp", help="结果帧存放路径")
parser.add_argument("-t", "--time", type=str, default="/home/aistudio/plane/time/all/", help="上撤轮挡时间标注")
parser.add_argument("--itv", type=int, default=25, help="抽帧间隔")
parser.add_argument("--bs", type=int, default=2, help="推理bs")
args = parser.parse_args()


def main():
    # 1. 定义模型对象
    flg_det = PdxDet(model_path="../model/best/flg_det/", bs=4)
    person_det = PdxDet(model_path="../model/best/person_det", bs=4, autoflush=False)
    person_clas = HumanClas(mode="predict")

    for vid_name in os.listdir(args.input):
        print(vid_name)
        os.mkdir(osp.join(args.output, vid_name))

        video = Stream(osp.join(args.input, vid_name), osp.join(args.time, vid_name.split(".")[0] + ".txt"))
        # TODO: 研究tqdm需要什么方法显示总数
        for fidx, img in video:
            # 检测出一个batch的起落架
            frames, fidxs, flgs_batch = flg_det.add(img, fidx)
            for frame, frame_idx, flgs in zip(frames, fidxs, flgs_batch):  # 对这些起落架中的每一个
                if len(flgs) != 0:
                    flg = flgs[0]
                    person_det.add(crop(frame, flg.square(256)), [flg, frame_idx, frame])  # 添加到检测人的任务list中
            # print("Gears detected: ", flgs_batch)
            if len(person_det.imgs) >= person_det.bs:
                r = person_det.flush()  # 进行人像检测
                for gear_square, info, people in zip(r[0], r[1], r[2]):  # 对一个batch中的每一张，每一张可能有多个人
                    flg = info[0]
                    fid = info[1]
                    f = info[2]
                    # TODO: 一个batch推理
                    for pid, person in enumerate(people):
                        patch = crop(f, flg.square(256).transpose(person).square(64))
                        res = person_clas.predict(patch)
                        dbb(f, flg.square(256).transpose(person), "G" if res else "R")

                    # dbb(f, flg, "B")
                    dpoint(f, flg.center(), "R")
                    dbb(f, flg.square(256), "B")
                    cv2.imshow("img", f)
                    cv2.waitKey()

                    # cv2.imwrite(osp.join(args.output, vid_name, str(fid) + ".png"), f)


if __name__ == "__main__":
    main()