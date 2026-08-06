# Dataset Acknowledgments

This repository contains **no** third-party data. Everything below has to be
downloaded by you, from the original source, under that source's own terms.

## Historical game results

- **Dataset:** Basketball (NBA) Dataset
- **Author:** Wyatt Walsh
- **Source:** <https://www.kaggle.com/datasets/wyattowalsh/basketball>
- **License:** CC BY-SA 4.0
- **Used for:** the game log that trains and evaluates the pregame ensemble —
  dates, teams, final scores and winners.

`scripts/data_prep/process_kaggle_games.py` reads `Games.csv` from this dataset
and writes a reduced game log. Neither the source file nor the derived log is
redistributed here; both are gitignored.

CC BY-SA 4.0 is a share-alike licence. If you redistribute this dataset or a
derivative of it, you must attribute the author and licence the derivative under
compatible terms. This repository avoids the question entirely by shipping no
data.

```bibtex
@misc{walsh_basketball_dataset,
  author = {Wyatt Walsh},
  title  = {Basketball (NBA) Dataset},
  url    = {https://www.kaggle.com/datasets/wyattowalsh/basketball},
  note   = {Licensed CC BY-SA 4.0}
}
```

## Methodological references

These informed the feature design; no data or code was taken from them.

| Source | Used for |
| --- | --- |
| FiveThirtyEight's NBA Elo work | margin-of-victory-adjusted Elo, home-court advantage constant |
| Basketball-Reference | the 13.91 exponent in the Pythagorean win expectation |

## A note on the NBA Stats API

Earlier versions of this project pulled from `stats.nba.com` via the `nba_api`
package. No code in this release does, so there is nothing to acknowledge on that
front for the current pipeline. If you add such a collector, note that
`stats.nba.com` is an undocumented endpoint with no public licence for bulk
redistribution, and check its terms before shipping anything derived from it.
