# Dataset Acknowledgments

All datasets used in the NBA World Model project.

---

## Datasets Used

### 1. NBA Games Historical Data
- **Source:** Kaggle Wyattowalsh NBA Dataset
- **Link:** [kaggle.com/datasets/wyattowalsh/basketball](https://www.kaggle.com/datasets/wyattowalsh/basketball)
- **License:** CC BY-SA 4.0
- **Usage:** Training Ensemble, Momentum Transformer, Chemistry GNN

### 2. NBA PBP Video Dataset
- **Source:** Ali Khalil (alijkhalil)
- **Link:** [github.com/alijkhalil/nba_pbp_video_dataset](https://github.com/alijkhalil/nba_pbp_video_dataset)
- **Description:** Large video dataset of individual NBA plays with labels
- **Usage:** Audio classifier training, Optical Flow extraction

### 3. Sports-1M Dataset (Reference)
- **Source:** Google Research / Andrej Karpathy
- **Link:** [github.com/gtoderici/sports-1m-dataset](https://github.com/gtoderici/sports-1m-dataset)
- **License:** CC BY 3.0 (Attribution)
- **Usage:** Referenced for multimodal architecture design

### 4. NBA Stats API
- **Source:** NBA Official
- **Link:** [stats.nba.com](https://stats.nba.com)
- **Usage:** Play-by-Play text extraction, real-time odds

---

## Key Research Papers

| Paper | Year | Contribution |
|-------|------|--------------|
| Amazon SageMaker Multimodal Sports | 2021 | Optical Flow + Audio fusion methodology |
| Multi-Modal Trajectory Prediction | 2021 | NBA tracking data fusion |
| NCAA Multimodal Benchmarking | 2024 | LLM + Tabular fusion framework |

---

## Citation Format

```bibtex
@misc{nba_pbp_video,
  author = {Khalil, Ali},
  title = {NBA Play-by-Play Video Dataset},
  year = {2016-2024},
  url = {https://github.com/alijkhalil/nba_pbp_video_dataset}
}

@misc{sports1m,
  author = {Karpathy, Andrej and Toderici, George},
  title = {Sports-1M Dataset},
  year = {2014},
  license = {CC BY 3.0},
  url = {https://github.com/gtoderici/sports-1m-dataset}
}

@misc{wyattowalsh_nba,
  author = {Wyatt O'Walsh},
  title = {Basketball Dataset},
  year = {2024},
  url = {https://www.kaggle.com/datasets/wyattowalsh/basketball}
}
```
