# 🎙️ Audio Deepfake Detection — ResNet18 Backend

## Overview

This project implements an audio deepfake detection system using a **ResNet18** model trained on two distinct audio feature types. The backend is designed to run inference across multiple independently trained model checkpoints and return the most confident prediction to the user.

---

## Complete Python Code
The complete python which was used for testing and training in included in "Model Training and Testing Python Code and Models"/"Audio Deepfake Detection - FYP PHASE 1 COMPLETED.ipynb".

## Features Extracted

The model was trained using two separate audio feature representations:

| Feature | Description |
|---|---|
| **Mel-Spectrogram** | A time-frequency representation of audio based on the Mel scale, capturing perceptual frequency content |
| **LFCC** | Linear Frequency Cepstral Coefficients, capturing spectral envelope characteristics commonly used in speech/spoofing detection |

Each feature was used to train an **independent** ResNet18 model.

---

## Model Naming Convention

Models are saved using the following naming pattern:

```
best_resnet18_{feature}_{batch}.pth
```

### Examples

```
best_resnet18_mel_3.pth
best_resnet18_lfcc_3.pth
```

Where:
- `{feature}` → `melspectrogram` or `lfcc`
- `{batch}` → the name of the data batch the model was trained on (e.g., `data3`, `data5`, `data6`, `data8`)

---

## Dataset Structure

The full dataset is split into **4 non-overlapping batches**. Each batch has its own dedicated folder containing the trained model checkpoints:

```
Model Training and Testing Python Code and Models/
│
├── data3/
│   └── models/
│       ├── best_resnet18_mel_3.pth
│       └── best_resnet18_lfcc_3.pth
│
├── data5/
│   └── models/
│       ├── best_resnet18_mel_5.pth
│       └── best_resnet18_lfcc_data5.pth
│
├── data6/
│   └── models/
│       ├── best_resnet18_mel_data6.pth
│       └── best_resnet18_lfcc_6.pth
│
└── data8/
    └── models/
        ├── best_resnet18_mel_8.pth
        └── best_resnet18_lfcc_8.pth
```

> ⚠️ **Important:** The 4 batches are entirely disjoint — there is **no data overlap** between them. Each model only has knowledge of the batch it was trained on.

---

## Backend Inference Pipeline

Since no single model has seen the full dataset, the backend runs the input audio through **all 8 models** (4 batches × 2 features) in parallel and aggregates their outputs.

### Step-by-Step Flow

```
Input Audio
     │
     ├──► Extract Mel-Spectrogram
     │         ├──► Model: data1/melspectrogram  ──► Confidence Score
     │         ├──► Model: data2/melspectrogram  ──► Confidence Score
     │         ├──► Model: data3/melspectrogram  ──► Confidence Score
     │         └──► Model: data4/melspectrogram  ──► Confidence Score
     │
     └──► Extract LFCC
               ├──► Model: data1/lfcc            ──► Confidence Score
               ├──► Model: data2/lfcc            ──► Confidence Score
               ├──► Model: data3/lfcc            ──► Confidence Score
               └──► Model: data4/lfcc            ──► Confidence Score
                                                         │
                                                         ▼
                                              Aggregate All Scores
                                                         │
                                                         ▼
                                          Most Probable Prediction
                                        (shown to the user on frontend)
```

### Aggregation Strategy

All model outputs (confidence scores / softmax probabilities) are collected and the **most confident prediction** across all 8 models is selected as the final result shown to the user.

---

## Total Models Summary

| Batch | Mel-Spectrogram Model | LFCC Model |
|---|---|---|
| data3 | `best_resnet18_mel_3.pth` | `best_resnet18_lfcc_3.pth` |
| data5 | `best_resnet18_mel_5.pth` | `best_resnet18_lfcc_5.pth` |
| data6 | `best_resnet18_mel_6.pth` | `best_resnet18_lfcc_6.pth` |
| data8 | `best_resnet18_mel_8.pth` | `best_resnet18_lfcc_8.pth` |

**Total: 8 models loaded at inference time**

---

## Notes

- All batches are **mutually exclusive** — no audio sample appears in more than one batch.
- The model architecture is **ResNet18** for both feature types.
- The final prediction returned to the user is based on the **highest confidence score** among all model outputs, ensuring the most informed decision is surfaced regardless of which batch or feature best represents the input audio.