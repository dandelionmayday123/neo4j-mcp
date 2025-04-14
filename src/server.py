import os
import sys
import logging
from pathlib import Path
import asyncio

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from src.neo4j_client import Neo4jClient
from typing import Any, Dict, List, Optional
from src.config import config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(project_root, 'neo4j_mcp.log'))
    ]
)

logger = logging.getLogger(__name__)

class Neo4jMCPServer(FastMCP):
    def __init__(self):
        super().__init__()
        self.neo4j_client = Neo4jClient()
        logging.info(f"初始化Neo4j MCP服务器 - 连接到 {config.NEO4J_URI}")
        
        # 注册工具
        self.add_tool(
            self.execute_query,
            name="execute_query",
            description="执行Cypher查询"
        )
        
        self.add_tool(
            self.create_node,
            name="create_node",
            description="创建新节点"
        )
        
        self.add_tool(
            self.create_relationship,
            name="create_relationship",
            description="创建关系"
        )
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        try:
            logging.info(f"执行查询: {query}")
            # 设置超时时间为30秒
            result = await asyncio.wait_for(
                self.neo4j_client.execute_query(query, params),
                timeout=30.0
            )
            logging.info(f"查询成功, 返回 {len(result)} 条结果")
            return result
        except asyncio.TimeoutError:
            logging.error("查询执行超时")
            raise Exception("查询执行超时，请检查查询语句或增加超时时间")
        except Exception as e:
            logging.error(f"查询执行失败: {str(e)}")
            raise
    
    async def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """创建新节点"""
        try:
            logging.info(f"创建节点 {label}: {properties}")
            result = await self.neo4j_client.create_node(label, properties)
            logging.info("节点创建成功")
            return result
        except Exception as e:
            logging.error(f"节点创建失败: {str(e)}")
            raise
    
    async def create_relationship(
        self,
        from_node_id: int,
        to_node_id: int,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建关系"""
        try:
            logging.info(f"创建关系 {rel_type} 从节点 {from_node_id} 到节点 {to_node_id}")
            result = await self.neo4j_client.create_relationship(
                from_node_id,
                to_node_id,
                rel_type,
                properties
            )
            logging.info("关系创建成功")
            return result
        except Exception as e:
            logging.error(f"关系创建失败: {str(e)}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        logging.info("关闭Neo4j客户端连接")
        await self.neo4j_client.close()

if __name__ == "__main__":
    try:
        server = Neo4jMCPServer()
        logging.info("启动Neo4j MCP服务器")
        server.run()
    except Exception as e:
        logging.error(f"服务器启动失败: {str(e)}")
        sys.exit(1)