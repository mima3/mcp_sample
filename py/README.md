# test
1. test


## install

```
npm install -g @anthropic-ai/claude-code
uv sync
```

.env.sampleをもとに.envを作成してください。

## running

### 静的解析

```
uv run ruff check 
```

```
uv run ruff check  --fix
```

### 型チェック

```
uv run pyrefly check
```