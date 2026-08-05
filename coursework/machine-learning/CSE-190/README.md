# CSE 190 — Introduction to Deep Learning

Assignments and labs in PyTorch, written as Colab notebooks.

| File | Topic |
|---|---|
| `assignment-2.ipynb` | Implicit neural fields — implementing and training an MLP to represent an image as a continuous function |
| `bonus-assignment.ipynb` | N-gram language modelling, RNN gradient behaviour, and transformer questions, with written derivations |
| `lab-06-semantic-segmentation.ipynb` | Binary semantic segmentation with TernausNet, using Albumentations for augmentation |
| `lab-08.ipynb` | Linear attention and Flash Attention — implementation and timing comparison |
| `lab-09-graph-neural-network.py` | Graph neural networks (exported from the Colab notebook) |
| `lab-11-diffusion-model.ipynb` | Stable Diffusion — using `StableDiffusionPipeline` and working through the latent-diffusion internals |

## Running these

The notebooks were written for Google Colab with a GPU runtime; `lab-08` in particular
expects one. Dependencies are installed inline in the first cells of each notebook
(`torch`, `torchvision`, `diffusers`, `transformers`, `albumentations`, `ternausnet`).

Cell outputs have been cleared from `lab-11-diffusion-model.ipynb`. The saved copy with
generated-image outputs was 13.8 MB, past the size where GitHub renders a notebook in the
browser, so the cleared version is published instead — it holds the same 75 cells of code.
