from torchvision.datasets import ImageFolder
from torchvision import transforms
from src.models import ConvSiameseNet
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import random
import torch
import yaml

import sys

font = {"weight": "bold", "size": 5}
matplotlib.rc("font", **font)

with open("./args.yml", "r", encoding="utf-8") as f:
    args = yaml.safe_load(f)

dtype = torch.float
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

checkpoint_filename = args["checkpoint_filename"]
checkpoint = torch.load(checkpoint_filename, map_location=device)

model = ConvSiameseNet(pretrained=False).to(device)
# model.load_state_dict(checkpoint["model"], strict=False)

new_size = (200, 200)
tr = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Resize(new_size),
    ]
)

x1_filename = "test_im_gucci.png"
x1 = Image.open(x1_filename).convert("RGB")
temp_x1 = x1.copy().convert("L")
temp_x1 = tr(temp_x1).unsqueeze(0).to(device)

dataset = ImageFolder(args["dataset_dirname"])
num_folders = len(dataset.classes)
total_num_imgs = len(dataset.targets)

arr = torch.tensor(dataset.targets)
memo = {index: None for index in range(num_folders)}

for x in memo.keys():
    indice = random.choice(torch.where(arr == x)[0].cpu().numpy())
    x2 = dataset.imgs[indice][0]
    x2 = Image.open(x2).convert("RGB")
    temp_x2 = x2.copy().convert("L")
    temp_x2 = tr(temp_x2).unsqueeze(0).to(device)
    out1, out2 = model(temp_x1, temp_x2)
    distance = torch.norm(out1 - out2)

    memo[x] = (indice, distance)

print()

best = min(memo.values(), key=lambda item: item[1])
best_label_indice = dataset.imgs[best[0]][1]
best_label = args["classes"][best_label_indice]


h, w = (num_folders + 1) // 2, 2
fig, axes = plt.subplots(h, w)
for i, (ax, m) in enumerate(zip(axes.flat, memo.values())):
    x2 = Image.open(dataset.imgs[m[0]][0]).convert("RGB")
    x2 = tr(x2)
    x2 = x2.cpu().numpy().transpose(1, 2, 0)
    x1 = tr(Image.open(x1_filename).convert("RGB"))
    x1 = x1.cpu().numpy().transpose(1, 2, 0)
    print(x1.shape, x2.shape)
    ax.imshow(
        np.concatenate([x1, x2], axis=1),
    )
    xlabel = f"distance {m[1]:.5f} - {args['classes'][dataset.imgs[m[0]][1]]}"
    if i == best_label_indice:
        ax.set_title(xlabel, color="red")
    else:
        ax.set_title(xlabel, color="black")
    ax.set_xticks([])
    ax.set_yticks([])

for ax in axes.flat:
    if not bool(ax.has_data()):
        fig.delaxes(ax)
fig.savefig("out_.jpg", dpi=300)
