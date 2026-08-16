# Backend algorithm labs

各fileはproduction実装ではなく、algorithmの中心をprintして追う小実験です。

```bash
python3 labs/dominators.py
python3 labs/instruction_selection.py
python3 labs/linear_scan.py
```

| Lab | 入力 | 観察すること | 次の拡張 |
|---|---|---|---|
| `dominators.py` | CFG | fixed point、immediate dominanceの材料 | dominance frontier、tree |
| `instruction_selection.py` | expression tree | pattern coverとcost | DAG、target feature、flags |
| `linear_scan.py` | live intervals | expire、register割当、spill | holes、split、fixed register |

実装を変えたら`python3 -m unittest discover -s labs -p 'test_*.py' -v`を実行します。

