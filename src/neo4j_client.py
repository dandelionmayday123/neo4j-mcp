import os
import logging
from .config import config
import httpx
from typing import Any, Dict, List, Optional
import json
import base64
import codecs

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        # 配置代理
        self.proxies = {}
        if config.HTTP_PROXY:
            self.proxies["http://"] = config.HTTP_PROXY
        if config.HTTPS_PROXY:
            self.proxies["https://"] = config.HTTPS_PROXY
        
        # 基本认证
        auth_string = f"{config.NEO4J_USERNAME}:{config.NEO4J_PASSWORD}"
        self.auth_header = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        
        # API端点
        self.transaction_endpoint = f"{config.NEO4J_URI}/db/data/transaction/commit"
        
        # 创建异步客户端
        transport = None
        if config.HTTP_PROXY:
            transport = httpx.AsyncHTTPTransport(proxy=config.HTTP_PROXY)
            
        self.client = httpx.AsyncClient(
            transport=transport,
            headers={
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json; charset=utf-8"
            },
            verify=False  # 如果需要跳过SSL验证
        )
        
        logger.info(f"Neo4j客户端初始化完成，连接到 {config.NEO4J_URI}")
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
        logger.info("Neo4j客户端连接已关闭")
        
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        try:
            # 准备请求数据
            data = {
                "statements": [{
                    "statement": query,
                    "parameters": params or {}
                }]
            }
            
            logger.debug(f"发送请求到 {self.transaction_endpoint}")
            logger.debug(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
            
            # 发送请求
            response = await self.client.post(
                self.transaction_endpoint,
                json=data
            )
            
            # 确保响应使用UTF-8解码
            response.encoding = 'utf-8'
            
            # 记录原始响应
            response_text = response.text
            logger.debug(f"收到原始响应: {response_text}")
            
            # 解析响应
            result = response.json()
            
            if "errors" in result and result["errors"]:
                error_msg = result["errors"][0].get("message", "未知错误")
                logger.error(f"查询错误: {error_msg}")
                # 如果是类型不匹配错误，尝试使用替代语法
                if "Type mismatch" in error_msg and "List<String>" in error_msg:
                    # 修改查询，使用ANY替代CONTAINS
                    modified_query = query.replace("labels(n) CONTAINS", "ANY(label IN labels(n) WHERE label =")
                    modified_query = modified_query.replace("RETURN", ") RETURN")
                    logger.info(f"使用修改后的查询重试: {modified_query}")
                    return await self.execute_query(modified_query, params)
                raise Exception(f"Neo4j查询错误: {error_msg}")
            
            # 处理结果
            data = result["results"][0].get("data", [])
            logger.info(f"查询成功，返回 {len(data)} 条结果")
            return data
            
        except Exception as e:
            logger.error(f"执行查询时出错: {str(e)}")
            raise
            
    async def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """创建节点"""
        query = f"CREATE (n:{label} $props) RETURN n"
        try:
            logger.info(f"创建节点 {label}")
            logger.debug(f"节点属性: {json.dumps(properties, ensure_ascii=False)}")
            result = await self.execute_query(query, {"props": properties})
            if result:
                logger.info("节点创建成功")
                return {
                    "row": result[0]["row"][0],
                    "meta": result[0]["meta"][0]
                }
            raise Exception("创建节点失败：没有返回结果")
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
        """创建关系"""
        query = """
        MATCH (from), (to)
        WHERE ID(from) = $from_id AND ID(to) = $to_id
        CREATE (from)-[r:$rel_type $props]->(to)
        RETURN r
        """
        try:
            logger.info(f"创建关系 {rel_type} 从节点 {from_node_id} 到节点 {to_node_id}")
            if properties:
                logger.debug(f"关系属性: {json.dumps(properties, ensure_ascii=False)}")
            
            result = await self.execute_query(
                query,
                {
                    "from_id": from_node_id,
                    "to_id": to_node_id,
                    "rel_type": rel_type,
                    "props": properties or {}
                }
            )
            
            if result:
                logger.info("关系创建成功")
                return {
                    "row": result[0]["row"][0],
                    "meta": result[0]["meta"][0]
                }
            raise Exception("创建关系失败：没有返回结果")
        except Exception as e:
            logger.error(f"创建关系失败: {str(e)}")
            raise