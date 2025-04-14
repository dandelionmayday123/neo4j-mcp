# Neo4j MCP Server

这是一个基于MCP框架的Neo4j数据库操作服务。

## 功能特性

- 支持异步操作
- 提供Neo4j数据库的基本操作接口
- 支持代理服务器配置
- 完整的日志记录

## 安装

```bash
pip install -e .
```

## 配置

创建`.env`文件并设置以下环境变量：

```env
NEO4J_URI=http://your-neo4j-server:7474
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
HTTP_PROXY=http://your-proxy:port  # 可选
HTTPS_PROXY=http://your-proxy:port  # 可选
```

## 使用方法

1. 启动服务器：

```bash
python src/server.py
```

2. 使用MCP客户端调用服务：

```python
from mcp.client import Client

async with Client() as client:
    # 执行Cypher查询
    result = await client.execute_query("MATCH (n) RETURN n LIMIT 5")
    
    # 创建节点
    node = await client.create_node("Person", {"name": "张三", "age": 30})
    
    # 创建关系
    rel = await client.create_relationship(1, 2, "KNOWS", {"since": "2024"})
```

## 开发

1. 创建虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows
```

2. 安装开发依赖：

```bash
pip install -e ".[dev]"
```

3. 运行测试：

```bash
python -m pytest
```

## 许可证

MIT