import os
import logging
from .config import config
from .neo4j_client import Neo4jClient
from mcp import FastMCP
from typing import Any, Dict, List, Optional

# 设置系统编码为UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Neo4jMCPServer(FastMCP):
    def __init__(self):
        super().__init__()
        self.client = None
        logger.info("Neo4j MCP服务器初始化完成")
        
    async def startup(self):
        """服务器启动时的初始化操作"""
        logger.info("正在初始化Neo4j客户端...")
        self.client = Neo4jClient()
        
    async def shutdown(self):
        """服务器关闭时的清理操作"""
        if self.client:
            logger.info("正在关闭Neo4j客户端...")
            await self.client.close()
            
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询
        
        Args:
            query: Cypher查询语句
            params: 查询参数（可选）
            
        Returns:
            查询结果列表
        """
        try:
            logger.info(f"执行查询: {query}")
            if params:
                logger.debug(f"查询参数: {params}")
                
            result = await self.client.execute_query(query, params)
            return result
            
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise
            
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建节点
        
        Args:
            label: 节点标签
            properties: 节点属性
            
        Returns:
            创建的节点信息
        """
        try:
            logger.info(f"创建节点 {label}")
            logger.debug(f"节点属性: {properties}")
            
            result = await self.client.create_node(label, properties)
            return result
            
        except Exception as e:
            logger.error(f"创建节点失败: {str(e)}")
            raise
            
    async def create_relationship(
        self,
        from_node_id: int,
        to_node_id: int,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建关系
        
        Args:
            from_node_id: 起始节点ID
            to_node_id: 目标节点ID
            rel_type: 关系类型
            properties: 关系属性（可选）
            
        Returns:
            创建的关系信息
        """
        try:
            logger.info(f"创建关系 {rel_type} 从节点 {from_node_id} 到节点 {to_node_id}")
            if properties:
                logger.debug(f"关系属性: {properties}")
                
            result = await self.client.create_relationship(
                from_node_id,
                to_node_id,
                rel_type,
                properties
            )
            return result
            
        except Exception as e:
            logger.error(f"创建关系失败: {str(e)}")
            raise

if __name__ == "__main__":
    server = Neo4jMCPServer()
    server.run()