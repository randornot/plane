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
    default="H:/W_S/Graduation_Project/plane/train-video",
    help="视频存放路径",
)
parser.add_argument("-o", "--output", type=str, default="H:/W_S/Graduation_Project/plane/temp", help="结果帧存放路径")
parser.add_argument("-t", "--time", type=str, default="H:/W_S/Graduation_Project/plane/时间", help="上撤轮挡时间标注")
parser.add_argument("--itv", type=int, default=25, help="抽帧间隔")
parser.add_argument("--bs", type=int, default=2, help="推理bs")
args = parser.parse_args()


def main():
    # 1. 定义模型对象
    flg_det = PdxDet(model_path="../model/best/flg_det/", bs=4)
    person_det = PdxDet(model_path="../model/best/person_det_yolov3", bs=8, autoflush=False)

    for vid_name in os.listdir(args.input):
        print(vid_name)
        os.mkdir(osp.join(args.output, vid_name))

        video = Stream(osp.join(args.input, vid_name), osp.join(args.time, os.listdir(args.time)[0]))
        # TODO: 研究tqdm需要什么方法显示总数
        for fidx, img in video:
            # 检测出一个batch的起落架
            frames, fidxs, flgs_batch = flg_det.add(img, fidx)
            for frame, frame_idx, flgs in zip(frames, fidxs, flgs_batch):  # 对这些起落架中的每一个
                if len(flgs) != 0:
                    flg = flgs[0]
                    person_det.add(crop(frame, flg.square(256)), [flg, frame_idx])  # 添加到检测人的任务list中

            if len(flgs_batch) != 0:
                print("Gears detected: ", flgs_batch)

            if len(person_det.imgs) >= person_det.bs:
                count = 0
                r = person_det.flush()  # 进行人像检测
                print("People detected: ", r[2])
                for gear_square, info, people in zip(r[0], r[1], r[2]):  # 对一个batch中的每一张，每一张可能有多个人
                    f = frames[count]
                    flg = info[0]
                    fid = info[1]
                    count += 1
                    for pid, person in enumerate(people):
                        dbb(f, flg.square(256).transpose(person), "G")
                        patch = crop(f, flg.square(256).transpose(person).square(128))
                        if patch.shape == (128, 128, 3):
                            cv2.imwrite(
                                osp.join(args.output, vid_name, "{}-{}.png".format(pid, str(fid))), patch
                            )
                            # cv2.imshow("img", crop(gear_square, person))

                    dbb(f, flg, "R")
                    dpoint(f, flg.center(), "R")
                    dbb(f, flg.square(256), "B")
                    #
                    cv2.imshow("img", f)
                    cv2.waitKey(2)

            # cv2.imwrite(osp.join(args.output, vid_name, str(fid) + ".png"), f)


if __name__ == "__main__":
    main()
