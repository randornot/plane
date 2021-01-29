import os
import os.path as osp
import argparse

import cv2
from tqdm import tqdm
import numpy as np

from util.util import BB, crop, Stream, dbb, dpoint
from util.model import PdxDet

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-i",
    "--input",
    type=str,
    default="/home/aistudio/plane/vid-split/train",
    help="视频存放路径",
)
parser.add_argument("-o", "--output", type=str, default="/home/aistudio/plane/temp", help="结果帧存放路径")
parser.add_argument("--itv", type=int, default=100, help="抽帧间隔")
parser.add_argument("--bs", type=int, default=2, help="推理bs")
args = parser.parse_args()


def main():
    # 1. 定义模型对象
    flg_det = PdxDet(model_path="../model/best/flg_det/", bs=4)
    person_det = PdxDet(model_path="../model/best/person_det", bs=8)

    for vid_name in os.listdir(args.input):
        print(vid_name)
        os.mkdir(osp.join(args.output, vid_name))

        # TODO: 研究tqdm需要什么方法显示总数
        for idx, img in enumerate(Stream(osp.join(args.input, vid_name))):
            # 检测出一个batch的起落架
            frames, fidxs, flgs_batch = flg_det.add(img, idx)
            for frame, frame_idx, flgs in zip(frames, fidxs, flgs_batch):  # 对这些起落架中的每一个
                if len(flgs) != 0:
                    flg = flgs[0]
                    person_det.add(crop(frame, flg.square(256)), [flg, frame_idx])  # 添加到检测人的任务list中

            count = 0
            r = person_det.flush()  # 进行人像检测
            for _, info, people in zip(r[0], r[1], r[2]):  # 对一个batch中的每一张，每一张可能有多个人
                print(people, info)
                f = frames[count]
                flg = info[0]
                fid = info[1]
                count += 1
                for person in people:
                    dbb(f, flg.square(256).transpose(person), "G")

                dbb(f, flg, "R")
                dpoint(f, flg.center(), "R")
                dbb(f, flg.square(256), "G")

                cv2.imwrite(osp.join(args.output, vid_name, str(fid) + ".png"), f)


if __name__ == "__main__":
    main()